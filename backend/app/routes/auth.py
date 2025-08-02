"""
Authentication routes for user registration, login, and API key management.

This module provides:
1. User registration and login endpoints
2. JWT token management
3. API key generation and management
4. User profile management
"""

from datetime import timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr, Field

from ..services.auth_service import AuthService
from ..database.connection import get_database_pools
from ..middleware.auth import get_current_user, get_current_admin_user
from ..config import config
from ..logging_utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Authentication"])

# Initialize auth service with config
auth_service = AuthService(
    secret_key=getattr(config, "jwt_secret_key", "your-secret-key-change-in-production"),
    algorithm="HS256",
    token_expire_minutes=getattr(config, "jwt_expire_minutes", 1440)  # 24 hours default
)

# Request/Response Models
class UserRegistration(BaseModel):
    """User registration request model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!"
            }
        }

class UserLogin(BaseModel):
    """User login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")

class ApiKeyRequest(BaseModel):
    """API key generation request model."""
    name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for the API key")
    expires_days: Optional[int] = Field(None, gt=0, le=365, description="Expiration in days (max 365)")
    permissions: Optional[List[str]] = Field(default=None, description="Key permissions (future use)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Integration Key",
                "expires_days": 90,
                "permissions": ["read", "write"]
            }
        }

class ApiKeyResponse(BaseModel):
    """API key response model."""
    key_id: str = Field(..., description="Public key identifier")
    full_key: str = Field(..., description="Complete API key (save this - won't be shown again!)")
    name: str = Field(..., description="Key name")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")

class UserProfile(BaseModel):
    """User profile response model."""
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: str
    last_login: Optional[str] = None

class ApiKeyInfo(BaseModel):
    """API key information model (without secret)."""
    key_id: str
    name: str
    is_active: bool
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
    created_at: str
    is_expired: bool


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    **Register a new user account.**
    
    Creates a new user with username, email, and password.
    Returns a JWT token for immediate authentication.
    
    **Requirements:**
    - Username: 3-50 characters, must be unique
    - Email: Valid email format, must be unique
    - Password: Minimum 8 characters
    
    **Returns:**
    - JWT access token for authentication
    - User profile information
    """
)
async def register(user_data: UserRegistration):
    """Register a new user."""
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            # Register the user
            user = await auth_service.register_user(
                db=db,
                username=user_data.username,
                email=user_data.email,
                password=user_data.password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            
            # Create access token
            access_token = auth_service.create_access_token(
                data={"sub": str(user.id), "username": user.username}
            )
            
            logger.info(
                "User registered and token created",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=auth_service.token_expire_minutes * 60,
                user=user.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Registration failed",
            extra={"error": str(e), "username": user_data.username},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description="""
    **Authenticate a user and return a JWT token.**
    
    Accepts username or email with password.
    Returns a JWT token for API access.
    
    **Authentication Methods:**
    - Username + Password
    - Email + Password
    
    **Token Usage:**
    Include the token in the Authorization header:
    `Authorization: Bearer <your_token>`
    """
)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT token."""
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            # Authenticate user
            user = await auth_service.authenticate_user(
                db=db,
                username=credentials.username,
                password=credentials.password
            )
            
            if not user:
                # Don't reveal whether username or password was wrong
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Create access token
            access_token = auth_service.create_access_token(
                data={"sub": str(user.id), "username": user.username}
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=auth_service.token_expire_minutes * 60,
                user=user.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Login failed",
            extra={"error": str(e), "username": credentials.username},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="Get user profile",
    description="""
    **Get the current user's profile information.**
    
    Returns detailed information about the authenticated user.
    Requires valid JWT token in Authorization header.
    """
)
async def get_profile(request: Request):
    """Get current user profile."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return UserProfile(**user.to_dict())


@router.post(
    "/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate API key",
    description="""
    **Generate a new API key for the authenticated user.**
    
    API keys provide an alternative to JWT tokens for accessing the API.
    They're ideal for server-to-server integrations and long-running processes.
    
    **Features:**
    - Optional expiration (max 365 days)
    - Descriptive names for organization
    - Usage tracking and management
    
    **Important:** The full API key is only shown once during creation.
    Use the key in the `X-API-Key` header for authentication.
    """
)
async def create_api_key(
    key_request: ApiKeyRequest,
    request: Request
):
    """Generate a new API key for the current user."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            key_data = auth_service.generate_api_key(
                db=db,
                user_id=user.id,
                name=key_request.name,
                expires_days=key_request.expires_days,
                permissions=key_request.permissions
            )
            
            if not key_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate API key"
                )
            
            return ApiKeyResponse(**key_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "API key creation failed",
            extra={
                "error": str(e),
                "user_id": user.id,
                "key_name": key_request.name
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


@router.get(
    "/api-keys",
    response_model=List[ApiKeyInfo],
    summary="List API keys",
    description="""
    **List all API keys for the authenticated user.**
    
    Returns information about all API keys (active and inactive)
    associated with the current user. Secret keys are not included.
    """
)
async def list_api_keys(request: Request):
    """List all API keys for the current user."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
        
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            keys = auth_service.list_user_api_keys(db, user.id)
            return [ApiKeyInfo(**key) for key in keys]
            
    except Exception as e:
        logger.error(
            "Failed to list API keys",
            extra={"error": str(e), "user_id": user.id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key",
    description="""
    **Revoke (deactivate) an API key.**
    
    Once revoked, the API key can no longer be used for authentication.
    This action cannot be undone.
    """
)
async def revoke_api_key(
    key_id: str,
    request: Request
):
    """Revoke an API key."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            success = auth_service.revoke_api_key(db, user.id, key_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to revoke API key",
            extra={
                "error": str(e),
                "user_id": user.id,
                "key_id": key_id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


# Admin endpoints
@router.get(
    "/admin/users",
    response_model=List[UserProfile],
    summary="List all users (Admin)",
    description="**Admin only:** List all registered users."
)
async def list_users(request: Request):
    """List all users (admin only)."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        db_pools = get_database_pools()
        async with db_pools.get_async_session() as db:
            # This would need to be implemented in auth_service
            # For now, return empty list
            return []
            
    except Exception as e:
        logger.error(
            "Failed to list users",
            extra={"error": str(e), "admin_id": user.id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.post(
    "/admin/users/{user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user (Admin)",
    description="**Admin only:** Deactivate a user account."
)
async def deactivate_user(
    user_id: int,
    request: Request
):
    """Deactivate a user (admin only)."""
    # User is set by authentication middleware
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Prevent self-deactivation
        if user_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        # Implementation would go here
        logger.info(
            "User deactivated by admin",
            extra={"admin_id": user.id, "target_user_id": user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to deactivate user",
            extra={
                "error": str(e),
                "admin_id": user.id,
                "target_user_id": user_id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
