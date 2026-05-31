import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.fixture
async def admin_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD}
    )
    return response.json()["access_token"]

@pytest.fixture
async def customer_token(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Standard User", "email": "rbac@test.com", "password": "password123"}
    )
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "rbac@test.com", "password": "password123"}
    )
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_customer_cannot_access_roles(async_client: AsyncClient, customer_token: str):
    headers = {"Authorization": f"Bearer {customer_token}"}
    response = await async_client.get("/api/v1/roles/", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_access_roles(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/api/v1/roles/", headers=headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_customer_cannot_access_other_admin_endpoints(async_client: AsyncClient, customer_token: str):
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 1. POST /roles
    res = await async_client.post("/api/v1/roles/", headers=headers, json={"role_name": "Hacker"})
    assert res.status_code == 403

    # 2. GET /permissions
    res = await async_client.get("/api/v1/permissions/", headers=headers)
    assert res.status_code == 403

    # 3. POST /permissions
    res = await async_client.post("/api/v1/permissions/", headers=headers, json={"resource": "all", "action": "delete"})
    assert res.status_code == 403

    # 4. GET /vendors/applications
    res = await async_client.get("/api/v1/vendors/applications", headers=headers)
    assert res.status_code == 403

    # 5. POST /users/{id}/roles
    res = await async_client.post("/api/v1/users/1/roles", headers=headers, json={"role_id": 1})
    assert res.status_code == 403

    # 6. POST /users/{id}/permissions
    res = await async_client.post("/api/v1/users/1/permissions", headers=headers, json={"permission_id": 1})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_create_new_user_manually(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Test POST /users/ with Admin token
    res = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json={"user_name": "Admin Created", "email": "admincreated@test.com", "password": "password123"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "admincreated@test.com"
    assert "password" not in data  # Ensure password is not returned
