"""
Authentication middleware for JWT and API key validation.

This middleware provides:
1. JWT token validation from Authorization headers
2. API key validation from X-API-Key headers
3. User context injection into requests
4. Protected route enforcement
"""

from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response

from ..services.auth_service import AuthService
from ..database.connection import get_database_pools
from ..database.models import User
from ..logging_utils import get_logger

logger = get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and authorization."""
    
    def __init__(
        self,
        app: ASGIApp,
        auth_service: AuthService,
        exempt_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.auth_service = auth_service
        
        # Default exempt paths (no authentication required)
        self.exempt_paths = exempt_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/",
            "/health/*",
            "/auth/login",
            "/auth/register",
        ]
        
        logger.info(
            "Authentication middleware initialized",
            extra={"exempt_paths": self.exempt_paths}
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request through authentication middleware."""
        
        # Skip authentication for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Authenticate the request
        user = await self._authenticate_request(request)
        
        if not user:
            logger.warning(
                "Authentication failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Inject user into request state
        request.state.user = user
        request.state.user_id = user.id
        request.state.is_admin = user.is_admin
        
        logger.info(
            "Request authenticated",
            extra={
                "user_id": user.id,
                "username": user.username,
                "path": request.url.path,
                "method": request.method,
                "is_admin": user.is_admin
            }
        )
        
        # Continue with the request
        response = await call_next(request)
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if a path is exempt from authentication."""
        
        # Exact match
        if path in self.exempt_paths:
            return True
        
        # Pattern matching for paths like /health/*
        for exempt_path in self.exempt_paths:
            if exempt_path.endswith("*"):
                prefix = exempt_path[:-1]
                if path.startswith(prefix):
                    return True
            elif exempt_path.endswith("/") and path.startswith(exempt_path):
                return True
        
        return False
    
    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """Authenticate a request using JWT or API key."""
        
        # Try JWT authentication first
        user = await self._authenticate_jwt(request)
        if user:
            return user
        
        # Try API key authentication
        user = await self._authenticate_api_key(request)
        if user:
            return user
        
        return None
    
    async def _authenticate_jwt(self, request: Request) -> Optional[User]:
        """Authenticate using JWT token from Authorization header."""
        try:
            # Get Authorization header
            authorization = request.headers.get("Authorization")
            logger.info(f"Authorization header: {authorization[:50]}..." if authorization else "No Authorization header")
            if not authorization:
                return None
            
            # Extract token
            if not authorization.startswith("Bearer "):
                logger.debug("Invalid Authorization header format")
                return None
            
            token = authorization[7:]  # Remove "Bearer " prefix
            logger.info(f"Extracted token: {token[:50]}...")
            
            # Verify token
            payload = self.auth_service.verify_token(token)
            logger.info(f"Token payload: {payload}")
            if not payload:
                return None
            
            # Get user ID from token
            user_id = payload.get("sub")
            logger.info(f"User ID from token: {user_id}")
            if not user_id:
                logger.warning("Token missing user ID (sub claim)")
                return None
            
            # Get user from database
            db_pools = get_database_pools()
            async with db_pools.get_async_session() as db:
                user = await self.auth_service.get_user_by_id(db, user_id)
                logger.info(f"Retrieved user: {user.username if user else 'None'}")
                return user
                
        except Exception as e:
            logger.error(
                "JWT authentication error",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    async def _authenticate_api_key(self, request: Request) -> Optional[User]:
        """Authenticate using API key from X-API-Key header."""
        try:
            # Get API key header
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return None
            
            # Verify API key
            db_pools = get_database_pools()
            async with db_pools.get_async_session() as db:
                user = await self.auth_service.verify_api_key(db, api_key)
                return user
                
        except Exception as e:
            logger.error(
                "API key authentication error",
                extra={"error": str(e)},
                exc_info=True
            )
            return None


# Security schemes for OpenAPI documentation
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(request: Request) -> User:
    """Dependency to get the current authenticated user."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def get_current_active_user(request: Request) -> User:
    """Dependency to get the current active user."""
    user = get_current_user(request)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user

def get_current_admin_user(request: Request) -> User:
    """Dependency to get the current admin user."""
    user = get_current_active_user(request)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

def require_auth(exempt_paths: Optional[list[str]] = None):
    """Decorator to create authentication middleware with custom exempt paths."""
    def create_middleware(auth_service: AuthService):
        return AuthMiddleware(
            app=None,  # Will be set when added to FastAPI
            auth_service=auth_service,
            exempt_paths=exempt_paths
        )
    return create_middleware

# Route protection decorators
def protected_route(func):
    """Decorator to mark a route as requiring authentication."""
    func.__auth_required__ = True
    return func

def admin_route(func):
    """Decorator to mark a route as requiring admin access."""
    func.__admin_required__ = True
    return func

def api_key_route(func):
    """Decorator to mark a route as supporting API key authentication."""
    func.__api_key_supported__ = True
    return func


# FastAPI Dependencies for route protection
async def require_auth(request: Request) -> User:
    """FastAPI dependency to require authentication."""
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user


async def require_admin(request: Request) -> User:
    """FastAPI dependency to require admin access."""
    user = await require_auth(request)
    
    if not getattr(user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


async def optional_auth(request: Request) -> Optional[User]:
    """FastAPI dependency for optional authentication."""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None
