import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.future import select
from unittest.mock import AsyncMock

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.core.security import get_password_hash
from app.features.roles.models import Role, RolePermission
from app.features.users.models import User, UserRole, UserProfile
from app.features.permissions.models import Permission
from app.features.categories.models import Category
from app.features.vendors.models import VendorApplication
from app.core.config import settings

# Use a local SQLite database for tests to prevent connection loss issues with in-memory DBs
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the FastAPI dependency to use our fake database
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Create all tables and seed default roles/admin before any tests run."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestingSessionLocal() as db:
        # Seed Roles
        roles = ["Admin", "Customer", "Vendor"]
        for r in roles:
            db.add(Role(role_name=r))
        await db.commit()
        
        # Seed Admin User
        admin = User(
            user_name="Test Admin",
            email=settings.FIRST_SUPERUSER_EMAIL,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        # Assign Admin role
        res = await db.execute(select(Role).filter(Role.role_name == "Admin"))
        admin_role = res.scalars().first()
        if admin_role:
            db.add(UserRole(user_id=admin.user_id, role_id=admin_role.role_id))
            await db.commit()
            
    return

@pytest_asyncio.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis to avoid 'Event loop is closed' errors during async tests."""
    blocked_tokens = {}

    async def mock_get(key):
        return blocked_tokens.get(key)

    async def mock_setex(key, time, value):
        blocked_tokens[key] = value
        return True

    mock = AsyncMock()
    mock.get.side_effect = mock_get
    mock.setex.side_effect = mock_setex
    
    monkeypatch.setattr("app.features.auth.dependencies.redis_client", mock)
    monkeypatch.setattr("app.features.auth.services.redis_client", mock)
    return mock

@pytest_asyncio.fixture
async def async_client():
    """Fixture to provide an async HTTP client for API requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def customer_token(async_client: AsyncClient):
    # Ignore 409 if already registered (tests run in same DB sometimes if not careful, but sqlite in-memory drops it. Still good to be safe)
    await async_client.post("/api/v1/auth/register", json={"user_name": "Test Cust", "email": "cust2@test.com", "password": "123"})
    response = await async_client.post("/api/v1/auth/login", json={"email": "cust2@test.com", "password": "123"})
    assert response.status_code == 200, "Customer login failed"
    return response.json()["access_token"]

@pytest_asyncio.fixture
async def vendor_token(async_client: AsyncClient, admin_token: str):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Test Vendor App", "email": "vendorapp2@test.com", "password": "123"})
    
    async with TestingSessionLocal() as db:
        from app.features.users.models import User, UserRole
        from app.features.roles.models import Role
        from sqlalchemy.future import select
        
        user_res = await db.execute(select(User).filter(User.email == "vendorapp2@test.com"))
        user = user_res.scalars().first()
        role_res = await db.execute(select(Role).filter(Role.role_name == "Vendor"))
        vendor_role = role_res.scalars().first()
        if user and vendor_role:
            existing = await db.execute(select(UserRole).filter(UserRole.user_id == user.user_id, UserRole.role_id == vendor_role.role_id))
            if not existing.scalars().first():
                db.add(UserRole(user_id=user.user_id, role_id=vendor_role.role_id))
                await db.commit()
            
    fresh_login = await async_client.post("/api/v1/auth/login", json={"email": "vendorapp2@test.com", "password": "123"})
    assert fresh_login.status_code == 200, "Vendor relogin failed"
    return fresh_login.json()["access_token"]
