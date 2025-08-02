"""
Authentication service for user management, JWT tokens, and API keys.

This service provides:
1. User registration and authentication
2. JWT token generation and validation
3. API key generation and management
4. Password hashing and verification
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from ..database.models import User, ApiKey
from ..logging_utils import get_logger

logger = get_logger(__name__)

class AuthService:
    """Service for authentication and user management."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", token_expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
            
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            logger.info(
                "JWT token created",
                extra={
                    "user_id": data.get("sub"),
                    "expires_at": expire.isoformat(),
                    "algorithm": self.algorithm
                }
            )
            
            return encoded_jwt
            
        except Exception as e:
            logger.error(
                "Failed to create JWT token",
                extra={"error": str(e), "data_keys": list(data.keys())},
                exc_info=True
            )
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is expired (jwt.decode should handle this, but double-check)
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token expired", extra={"exp": exp})
                return None
                
            logger.debug(
                "Token verified successfully",
                extra={
                    "user_id": payload.get("sub"),
                    "expires_at": datetime.utcfromtimestamp(exp).isoformat() if exp else None
                }
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired during verification")
            return None
        except jwt.JWTError as e:
            logger.warning(
                "Invalid token",
                extra={"error": str(e), "error_type": type(e).__name__}
            )
            return None
        except Exception as e:
            logger.error(
                "Token verification error",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    async def register_user(
        self, 
        db: AsyncSession, 
        username: str, 
        email: str, 
        password: str,
        is_admin: bool = False
    ) -> Optional[User]:
        """Register a new user."""
        try:
            # Check if username or email already exists
            result = await db.execute(
                select(User).filter(
                    or_(User.username == username, User.email == email)
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                if existing_user.username == username:
                    logger.warning(f"Registration failed: username '{username}' already exists")
                    return None
                else:
                    logger.warning(f"Registration failed: email '{email}' already exists")
                    return None
            
            # Create new user
            hashed_password = self.hash_password(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                is_admin=is_admin,
                created_at=datetime.utcnow()
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            logger.info(
                "User registered successfully",
                extra={
                    "user_id": new_user.id,
                    "username": username,
                    "email": email,
                    "is_admin": is_admin
                }
            )
            
            return new_user
            
        except Exception as e:
            logger.error(
                "User registration failed",
                extra={
                    "username": username,
                    "email": email,
                    "error": str(e)
                },
                exc_info=True
            )
            await db.rollback()
            return None
    
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/email and password."""
        try:
            # Allow login with either username or email
            result = await db.execute(
                select(User).filter(
                    and_(
                        or_(User.username == username, User.email == username),
                        User.is_active == True
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found or inactive")
                return None
            
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await db.commit()
            
            logger.info(
                "User authenticated successfully",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            )
            
            return user
            
        except Exception as e:
            logger.error(
                "User authentication error",
                extra={"username": username, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            result = await db.execute(
                select(User).filter(
                    and_(User.id == user_id, User.is_active == True)
                )
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(
                "Failed to get user by ID",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def generate_api_key(
        self, 
        db: AsyncSession, 
        user_id: str, 
        name: str,
        expires_days: Optional[int] = None,
        permissions: Optional[List[str]] = None
    ) -> Optional[Dict[str, str]]:
        """Generate a new API key for a user."""
        try:
            # Generate key components
            key_id = secrets.token_urlsafe(16)  # Public identifier
            secret_key = secrets.token_urlsafe(32)  # Secret part
            
            # Create full key in format: key_id.secret_key
            full_key = f"{key_id}.{secret_key}"
            
            # Hash the secret for storage
            key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Create API key record
            api_key = ApiKey(
                user_id=user_id,
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                expires_at=expires_at,
                permissions=",".join(permissions) if permissions else None,
                created_at=datetime.utcnow()
            )
            
            db.add(api_key)
            await db.commit()
            await db.refresh(api_key)
            
            logger.info(
                "API key generated",
                extra={
                    "user_id": user_id,
                    "key_id": key_id,
                    "name": name,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
            return {
                "key_id": key_id,
                "full_key": full_key,  # Return this only once!
                "name": name,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
            
        except Exception as e:
            logger.error(
                "API key generation failed",
                extra={"user_id": user_id, "name": name, "error": str(e)},
                exc_info=True
            )
            await db.rollback()
            return None
    
    async def verify_api_key(self, db: AsyncSession, api_key: str) -> Optional[User]:
        """Verify an API key and return the associated user."""
        try:
            # Parse the API key
            if "." not in api_key:
                logger.warning("Invalid API key format")
                return None
                
            key_id, secret_key = api_key.split(".", 1)
            
            # Find the API key record
            result = await db.execute(
                select(ApiKey).filter(
                    and_(
                        ApiKey.key_id == key_id,
                        ApiKey.is_active == True
                    )
                )
            )
            api_key_record = result.scalar_one_or_none()
            
            if not api_key_record:
                logger.warning(f"API key not found: {key_id}")
                return None
            
            # Check if expired
            if api_key_record.is_expired():
                logger.warning(f"API key expired: {key_id}")
                return None
            
            # Verify the secret
            secret_hash = hashlib.sha256(secret_key.encode()).hexdigest()
            if secret_hash != api_key_record.key_hash:
                logger.warning(f"Invalid API key secret: {key_id}")
                return None
            
            # Get the user
            user = await self.get_user_by_id(db, api_key_record.user_id)
            if not user:
                logger.warning(f"User not found for API key: {key_id}")
                return None
            
            # Update last used
            api_key_record.last_used = datetime.utcnow()
            await db.commit()
            
            logger.info(
                "API key verified",
                extra={
                    "key_id": key_id,
                    "user_id": user.id,
                    "username": user.username
                }
            )
            
            return user
            
        except Exception as e:
            logger.error(
                "API key verification error",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    async def list_user_api_keys(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """List all API keys for a user (without secrets)."""
        try:
            result = await db.execute(
                select(ApiKey).filter(ApiKey.user_id == user_id)
            )
            api_keys = result.scalars().all()
            
            return [
                {
                    "key_id": key.key_id,
                    "name": key.name,
                    "is_active": key.is_active,
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "created_at": key.created_at.isoformat() if key.created_at else None,
                    "is_expired": key.is_expired()
                }
                for key in api_keys
            ]
            
        except Exception as e:
            logger.error(
                "Failed to list user API keys",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            return []
    
    async def revoke_api_key(self, db: AsyncSession, user_id: str, key_id: str) -> bool:
        """Revoke (deactivate) an API key."""
        try:
            result = await db.execute(
                select(ApiKey).filter(
                    and_(
                        ApiKey.user_id == user_id,
                        ApiKey.key_id == key_id
                    )
                )
            )
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                logger.warning(f"API key not found for revocation: {key_id}")
                return False
            
            api_key.is_active = False
            await db.commit()
            
            logger.info(
                "API key revoked",
                extra={"user_id": user_id, "key_id": key_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to revoke API key",
                extra={"user_id": user_id, "key_id": key_id, "error": str(e)},
                exc_info=True
            )
            return False
