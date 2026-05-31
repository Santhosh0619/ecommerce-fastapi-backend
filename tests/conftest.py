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
from app.features.vendors.models import VendorApplication
from app.core.config import settings

# Use an in-memory SQLite database for fast, isolated testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the FastAPI dependency to use our fake database
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
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
            
    yield
    
    # Auto-cleanup after all tests finish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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
