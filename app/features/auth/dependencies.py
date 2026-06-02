from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.redis import redis_client
from app.database.session import get_db
from app.features.users import crud as user_crud

# This tells FastAPI where the client should send the email/password to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Dependency that verifies the JWT, checks the Redis blocklist, and returns the User.
    Use this dependency on any route that requires a logged-in user.
    """
    # 1. Check if token is in Redis blocklist (Logout)
    is_blocked = await redis_client.get(f"blocklist:{token}")
    if is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been logged out")
    
    # 2. Decode and verify JWT
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    # 3. Get user from DB
    user = await user_crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return user

async def get_optional_current_user(token: str = Depends(oauth2_scheme_optional), db: AsyncSession = Depends(get_db)):
    if not token:
        return None
        
    # Check blocklist
    is_blocked = await redis_client.get(f"blocklist:{token}")
    if is_blocked:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
    except Exception:
        return None
        
    return await user_crud.get_user_by_id(db, user_id=user_id)

class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        from app.features.roles import crud as role_crud
        user_roles = await role_crud.get_user_roles_names(db, current_user.user_id)
        
        for role in self.allowed_roles:
            if role in user_roles:
                return current_user
                
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

async def require_self_or_admin(user_id: int, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.user_id == user_id:
        return current_user
        
    from app.features.roles import crud as role_crud
    user_roles = await role_crud.get_user_roles_names(db, current_user.user_id)
    if "Admin" in user_roles:
        return current_user
        
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to access another user's data")
