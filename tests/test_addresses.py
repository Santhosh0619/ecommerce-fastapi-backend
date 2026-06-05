import pytest
from httpx import AsyncClient

@pytest.fixture
async def user_address(async_client: AsyncClient, customer_token: str):
    res = await async_client.post(
        "/api/v1/addresses/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Home",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "address_line_1": "123 Main St",
            "city": "Metropolis",
            "state": "NY",
            "postal_code": "10001",
            "is_default": True
        }
    )
    return res.json()

@pytest.mark.asyncio
async def test_create_address_auto_default(async_client: AsyncClient, customer_token: str):
    # First address should automatically be default
    res = await async_client.post(
        "/api/v1/addresses/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "First",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "address_line_1": "123 Main St",
            "city": "Metropolis",
            "state": "NY",
            "postal_code": "10001",
            "is_default": False # Will be overridden
        }
    )
    assert res.status_code == 201
    assert res.json()["is_default"] is True

@pytest.mark.asyncio
async def test_update_default_unsets_others(async_client: AsyncClient, customer_token: str, user_address: dict):
    # Create second address as not default
    res2 = await async_client.post(
        "/api/v1/addresses/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Office",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "address_line_1": "456 Work St",
            "city": "Metropolis",
            "state": "NY",
            "postal_code": "10002",
            "is_default": False
        }
    )
    assert res2.status_code == 201
    addr2_id = res2.json()["address_id"]

    # Now update second address to be default
    res_upd = await async_client.put(
        f"/api/v1/addresses/{addr2_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"is_default": True}
    )
    assert res_upd.status_code == 200

    # Verify first address is no longer default
    res_get1 = await async_client.get(f"/api/v1/addresses/{user_address['address_id']}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_get1.json()["is_default"] is False

@pytest.mark.asyncio
async def test_delete_default_auto_fallback(async_client: AsyncClient, customer_token: str):
    # Clear addresses to test cleanly
    addrs = await async_client.get("/api/v1/addresses/", headers={"Authorization": f"Bearer {customer_token}"})
    for addr in addrs.json():
        await async_client.delete(f"/api/v1/addresses/{addr['address_id']}", headers={"Authorization": f"Bearer {customer_token}"})

    # Create A (default)
    res_a = await async_client.post("/api/v1/addresses/", headers={"Authorization": f"Bearer {customer_token}"}, json={"title": "Address A", "full_name": "User X", "phone_number": "1234567890", "address_line_1": "Street A", "city": "City A", "state": "State A", "postal_code": "11111", "is_default": True})
    assert res_a.status_code == 201
    
    # Create B (not default)
    res_b = await async_client.post("/api/v1/addresses/", headers={"Authorization": f"Bearer {customer_token}"}, json={"title": "Address B", "full_name": "User X", "phone_number": "1234567890", "address_line_1": "Street B", "city": "City B", "state": "State B", "postal_code": "11111", "is_default": False})
    assert res_b.status_code == 201

    # Delete A
    await async_client.delete(f"/api/v1/addresses/{res_a.json()['address_id']}", headers={"Authorization": f"Bearer {customer_token}"})

    # Verify B is now default
    res_b_check = await async_client.get(f"/api/v1/addresses/{res_b.json()['address_id']}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_b_check.json()["is_default"] is True

@pytest.mark.asyncio
async def test_invalid_phone_and_postal_code(async_client: AsyncClient, customer_token: str):
    res = await async_client.post(
        "/api/v1/addresses/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Home",
            "full_name": "X",
            "phone_number": "invalid!", # Invalid characters
            "address_line_1": "A",
            "city": "A",
            "state": "A",
            "postal_code": "11", # Too short
            "is_default": True
        }
    )
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_get_address_not_found_or_forbidden(async_client: AsyncClient, customer_token: str):
    res = await async_client.get("/api/v1/addresses/99999", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_update_address_unset_default_blocked(async_client: AsyncClient, customer_token: str):
    # Create default address
    res = await async_client.post("/api/v1/addresses/", headers={"Authorization": f"Bearer {customer_token}"}, json={"title": "Address A", "full_name": "User X", "phone_number": "1234567890", "address_line_1": "Street A", "city": "City A", "state": "State A", "postal_code": "11111", "is_default": True})
    assert res.status_code == 201
    addr_id = res.json()["address_id"]
    
    # Try to update is_default = False directly
    res_upd = await async_client.put(
        f"/api/v1/addresses/{addr_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"is_default": False}
    )
    assert res_upd.status_code == 400
    assert "Cannot unset the default address directly" in res_upd.json()["detail"]
