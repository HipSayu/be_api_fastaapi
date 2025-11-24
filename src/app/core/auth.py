from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db.database import async_get_db
from ..core.security import verify_token, TokenType
from ..crud.crud_users import crud_users
from ..models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        token_data = await verify_token(
            token=credentials.credentials, 
            expected_token_type=TokenType.ACCESS, 
            db=db
        )
        
        if token_data is None:
            raise credentials_exception
        
        # Get user from database
        if "@" in token_data.username_or_email:
            user_dict = await crud_users.get(db=db, email=token_data.username_or_email, is_deleted=False)
        else:
            user_dict = await crud_users.get(db=db, username=token_data.username_or_email, is_deleted=False)
        
        if user_dict is None:
            raise credentials_exception
        
        # Convert dict to User object if needed
        if isinstance(user_dict, dict):
            # Create User object from dict with all required fields
            user = User(
                id=user_dict["id"],
                name=user_dict["name"],
                username=user_dict["username"],
                email=user_dict["email"],
                hashed_password=user_dict["hashed_password"],
                profile_image_url=user_dict.get("profile_image_url", ""),
                uuid=user_dict["uuid"],
                created_at=user_dict["created_at"],
                updated_at=user_dict.get("updated_at"),
                deleted_at=user_dict.get("deleted_at"),
                is_deleted=user_dict.get("is_deleted", False),
                is_superuser=user_dict.get("is_superuser", False),
                is_online=user_dict.get("is_online", False),
                last_online_at=user_dict.get("last_online_at"),
                tier_id=user_dict.get("tier_id")
            )
            return user
        else:
            return user_dict
        
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current active user (not deleted)"""
    # Handle both dict and User object cases
    is_deleted = current_user.is_deleted if hasattr(current_user, 'is_deleted') else current_user.get('is_deleted', False)
    
    if is_deleted:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current superuser"""
    # Handle both dict and User object cases
    is_superuser = current_user.is_superuser if hasattr(current_user, 'is_superuser') else current_user.get('is_superuser', False)
    
    if not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Optional authentication - returns None if no token
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(async_get_db)
) -> User | None:
    """Get current user if token is provided, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None