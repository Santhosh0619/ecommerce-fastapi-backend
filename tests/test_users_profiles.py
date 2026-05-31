import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.fixture
async def customer_tokens(async_client: AsyncClient):
    # Customer 1
    await async_client.post("/api/v1/auth/register", json={"user_name": "User One", "email": "one@test.com", "password": "123"})
    res1 = await async_client.post("/api/v1/auth/login", json={"email": "one@test.com", "password": "123"})
    c1 = res1.json()
    
    # Customer 2
    await async_client.post("/api/v1/auth/register", json={"user_name": "User Two", "email": "two@test.com", "password": "123"})
    res2 = await async_client.post("/api/v1/auth/login", json={"email": "two@test.com", "password": "123"})
    c2 = res2.json()
    
    return c1, c2

@pytest.mark.asyncio
async def test_user_can_edit_own_profile(async_client: AsyncClient, customer_tokens):
    c1, _ = customer_tokens
    headers = {"Authorization": f"Bearer {c1['access_token']}"}
    
    response = await async_client.put(
        f"/api/v1/users/{c1['id']}/profile",
        headers=headers,
        json={"bio": "I am user one"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_user_cannot_edit_other_profile(async_client: AsyncClient, customer_tokens):
    c1, c2 = customer_tokens
    headers = {"Authorization": f"Bearer {c1['access_token']}"}
    
    # User 1 tries to edit User 2's profile
    response = await async_client.put(
        f"/api/v1/users/{c2['id']}/profile",
        headers=headers,
        json={"bio": "Hacked!"}
    )
    assert response.status_code == 403

    # User 1 tries to view User 2's profile
    get_response = await async_client.get(
        f"/api/v1/users/{c2['id']}/profile",
        headers=headers
    )
    assert get_response.status_code == 403
