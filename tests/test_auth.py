import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    # 1. Register
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Test User", "email": "customer@test.com", "password": "password123"}
    )
    assert response.status_code == 201
    
    # 2. Login
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "customer@test.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # 3. Refresh Token
    refresh_response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": data["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    # 1. Register first user
    await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Test User 2", "email": "duplicate@test.com", "password": "password123"}
    )
    # 2. Register same email again
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Test User 3", "email": "duplicate@test.com", "password": "password456"}
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Test User 4", "email": "wrongpass@test.com", "password": "password123"}
    )
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_jwt_token(async_client: AsyncClient):
    response = await async_client.get(
        "/api/v1/users/1",
        headers={"Authorization": "Bearer invalid_token_abc"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_refresh_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_refresh_token_xyz"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_logout_and_access_protected_route(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={"user_name": "Logout Test", "email": "logout@test.com", "password": "password123"}
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "logout@test.com", "password": "password123"}
    )
    access_token = login_res.json()["access_token"]
    
    # 2. Access protected route (should succeed or return 403 if wrong user, but not 401)
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = await async_client.get("/api/v1/users/100", headers=headers)
    assert profile_res.status_code != 401
    
    # 3. Logout
    logout_res = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    
    # 4. Access protected route again (should fail with 401)
    profile_res_after_logout = await async_client.get("/api/v1/users/100", headers=headers)
    assert profile_res_after_logout.status_code == 401
