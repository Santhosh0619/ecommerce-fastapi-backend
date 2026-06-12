import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
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
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False, autocommit=False
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
    """Mock Redis to avoid 'Event loop is closed' errors during async tests and support Idempotency."""
    redis_store = {}

    async def mock_get(key):
        return redis_store.get(key)

    async def mock_setex(key, time, value):
        redis_store[key] = value
        return True

    async def mock_setnx(key, value):
        if key in redis_store:
            return False
        redis_store[key] = value
        return True

    async def mock_set(key, value, ex=None, nx=False, **kwargs):
        if nx and key in redis_store:
            return None
        redis_store[key] = value
        return True

    async def mock_delete(key):
        if key in redis_store:
            del redis_store[key]
        return 1

    mock = AsyncMock()
    mock.get.side_effect = mock_get
    mock.setex.side_effect = mock_setex
    mock.setnx.side_effect = mock_setnx
    mock.set.side_effect = mock_set
    mock.delete.side_effect = mock_delete
    
    monkeypatch.setattr("app.features.auth.dependencies.redis_client", mock)
    monkeypatch.setattr("app.features.auth.services.redis_client", mock)
    monkeypatch.setattr("app.features.orders.services.redis_client", mock)
    return mock

@pytest_asyncio.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Mock Celery task .delay methods to avoid requiring a real Redis message broker in tests."""
    mock = AsyncMock()
    monkeypatch.setattr("app.features.notifications.tasks.process_order_confirmation_task.delay", mock)
    monkeypatch.setattr("app.features.notifications.tasks.send_email_notification_task.delay", mock)
    return mock

@pytest_asyncio.fixture(autouse=True)
def mock_stripe(monkeypatch):
    """Mock Stripe API calls to prevent live HTTP requests during tests."""
    def mock_create(*args, **kwargs):
        import uuid
        class MockIntent:
            id = f"pi_mock_{uuid.uuid4().hex}"
            client_secret = f"{id}_secret_mock"
        return MockIntent()
        
    def mock_construct_event(payload, *args, **kwargs):
        import json
        from types import SimpleNamespace
        payload_data = json.loads(payload)
        
        intent = SimpleNamespace(id=payload_data.get("intent_id", "pi_mock_intent_123"))
        event_data = SimpleNamespace(object=intent)
        
        evt_type = "payment_intent.succeeded" if payload_data.get("status") in ("success", "succeeded") else "payment_intent.payment_failed"
        event = SimpleNamespace(type=evt_type, data=event_data)
        
        return event

    monkeypatch.setattr("stripe.PaymentIntent.create", mock_create)
    monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)
    return True

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
async def vendor_a_token(async_client: AsyncClient, admin_token: str):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Vendor A", "email": "vendora@test.com", "password": "123"})
    
    async with TestingSessionLocal() as db:
        from app.features.users.models import User, UserRole
        from app.features.roles.models import Role
        from sqlalchemy.future import select
        
        user_res = await db.execute(select(User).filter(User.email == "vendora@test.com"))
        user = user_res.scalars().first()
        role_res = await db.execute(select(Role).filter(Role.role_name == "Vendor"))
        vendor_role = role_res.scalars().first()
        if user and vendor_role:
            existing = await db.execute(select(UserRole).filter(UserRole.user_id == user.user_id, UserRole.role_id == vendor_role.role_id))
            if not existing.scalars().first():
                db.add(UserRole(user_id=user.user_id, role_id=vendor_role.role_id))
                await db.commit()
            
    fresh_login = await async_client.post("/api/v1/auth/login", json={"email": "vendora@test.com", "password": "123"})
    return fresh_login.json()["access_token"]

@pytest_asyncio.fixture
async def vendor_b_token(async_client: AsyncClient, admin_token: str):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Vendor B", "email": "vendorb@test.com", "password": "123"})
    
    async with TestingSessionLocal() as db:
        from app.features.users.models import User, UserRole
        from app.features.roles.models import Role
        from sqlalchemy.future import select
        
        user_res = await db.execute(select(User).filter(User.email == "vendorb@test.com"))
        user = user_res.scalars().first()
        role_res = await db.execute(select(Role).filter(Role.role_name == "Vendor"))
        vendor_role = role_res.scalars().first()
        if user and vendor_role:
            existing = await db.execute(select(UserRole).filter(UserRole.user_id == user.user_id, UserRole.role_id == vendor_role.role_id))
            if not existing.scalars().first():
                db.add(UserRole(user_id=user.user_id, role_id=vendor_role.role_id))
                await db.commit()
            
    fresh_login = await async_client.post("/api/v1/auth/login", json={"email": "vendorb@test.com", "password": "123"})
    return fresh_login.json()["access_token"]

@pytest_asyncio.fixture
async def test_address(async_client: AsyncClient, customer_token: str):
    res = await async_client.post(
        "/api/v1/addresses/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"title": "Home", "full_name": "John", "phone_number": "1234567890", "address_line_1": "123 St", "city": "NY", "state": "NY", "postal_code": "10001", "is_default": True}
    )
    return res.json()

@pytest_asyncio.fixture
async def active_products_multivendor(async_client: AsyncClient, admin_token: str, vendor_a_token: str, vendor_b_token: str):
    import uuid
    uid = str(uuid.uuid4())[:8]
    res_cat = await async_client.post("/api/v1/categories/", headers={"Authorization": f"Bearer {admin_token}"}, json={"category_name": f"Cat_{uid}"})
    cat_id = res_cat.json()["category_id"]
    
    # Vendor A Product
    res_prod_a = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_a_token}"},
        json={"product_name": f"ProdA_{uid}", "product_description": "Vendor A Product", "product_price": 100.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"}
    )
    
    # Vendor B Product
    res_prod_b = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_b_token}"},
        json={"product_name": f"ProdB_{uid}", "product_description": "Vendor B Product", "product_price": 200.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"}
    )
    
    return {
        "vendor_a_product": res_prod_a.json(),
        "vendor_b_product": res_prod_b.json()
    }

@pytest_asyncio.fixture
async def vendor_token(vendor_a_token: str):
    return vendor_a_token
