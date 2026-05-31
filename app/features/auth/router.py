from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.features.auth import schemas, services
from app.features.users.schemas import UserCreate
from app.features.auth.dependencies import oauth2_scheme

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and assign the Customer role by default."""
    return await services.register_user(db, user_data)

@router.post("/login", response_model=schemas.TokenResponse)
async def login(login_data: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user using Email and Password to get Access and Refresh tokens."""
    return await services.authenticate_user(db, login_data)

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logout a user by adding their active JWT Access token to a Redis Blocklist.
    This requires a Bearer token in the Authorization header.
    """
    return await services.logout_user(token)

@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(refresh_data: schemas.RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid Refresh Token for a new Access Token."""
    return await services.refresh_access_token(db, refresh_data)
