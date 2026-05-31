from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.redis import redis_client
from app.features.users import crud as user_crud
from app.features.roles import crud as role_crud
from app.features.users.schemas import UserCreate
from app.features.auth.schemas import LoginRequest, TokenResponse, RefreshTokenRequest
import jwt
import time
from app.core.config import settings

async def register_user(db: AsyncSession, user_data: UserCreate):
    # 1. Check if email exists
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        
    # 2. Check if Customer role exists (Fallback protection)
    customer_role = await role_crud.get_role_by_name(db, "Customer")
    if not customer_role:
        # In a real app, you'd want to seed the database with this role on startup
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default Customer role not found in system")
        
    # 3. Create user (Password hashing is handled inside user_crud)
    new_user = await user_crud.create_user(db, user_data)
    
    # 4. Assign Customer role automatically
    await user_crud.assign_role_to_user(db, new_user.user_id, customer_role.role_id)
    
    return {"message": "User registered successfully"}

async def authenticate_user(db: AsyncSession, login_data: LoginRequest) -> TokenResponse:
    # 1. Find user by email
    user = await user_crud.get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
    # 2. Verify password hash
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
    # 3. Generate Tokens
    access_token = create_access_token(subject=user.user_id)
    refresh_token = create_refresh_token(subject=user.user_id)
    
    return TokenResponse(
        id=user.user_id,
        mail=user.email,
        access_token=access_token,
        refresh_token=refresh_token
    )

async def logout_user(token: str):
    """
    Decodes the token to find its exact expiration time, and stores it in the
    Redis blocklist with a TTL (Time-To-Live) equal to its remaining lifespan.
    """
    try:
        # verify_exp=False because we just want to read the expiration time, even if it just expired a second ago
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        exp = payload.get("exp")
        now = int(time.time())
        ttl = exp - now
        
        if ttl > 0:
            # Store token in Redis blocklist for the exact amount of time it has left to live
            await redis_client.setex(f"blocklist:{token}", ttl, "blocked")
            
    except Exception:
        pass # If token is completely unparseable, it's invalid anyway, so logout "succeeds"
        
    return {"message": "Successfully logged out"}

async def refresh_access_token(db: AsyncSession, refresh_data: RefreshTokenRequest) -> TokenResponse:
    token = refresh_data.refresh_token
    
    # 1. Check if token is in Redis blocklist
    is_blocked = await redis_client.get(f"blocklist:{token}")
    if is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been logged out")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id_str is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        
    user = await user_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    access_token = create_access_token(subject=user.user_id)
    
    return TokenResponse(
        id=user.user_id,
        mail=user.email,
        access_token=access_token,
        refresh_token=token  # Return the exact same refresh token
    )
