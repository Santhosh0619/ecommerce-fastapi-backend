import pytest
from httpx import AsyncClient

@pytest.fixture
async def active_product(async_client: AsyncClient, admin_token: str, vendor_a_token: str):
    import uuid
    uid = str(uuid.uuid4())[:8]
    res_cat = await async_client.post("/api/v1/categories/", headers={"Authorization": f"Bearer {admin_token}"}, json={"category_name": f"Cat_{uid}"})
    cat_id = res_cat.json()["category_id"]
    
    res_prod = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_a_token}"},
        json={"product_name": f"Prod_{uid}", "product_description": "Valid Description", "product_price": 100.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"}
    )
    return res_prod.json()

@pytest.mark.asyncio
async def test_checkout_buy_now_success(async_client: AsyncClient, customer_token: str, active_product: dict, test_address: dict):
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"],
            "product_id": active_product["product_id"],
            "quantity": 2
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["financial_summary"]["subtotal"] == 200.0
    assert data["financial_summary"]["grand_total"] == 205.0 # with 5.0 delivery fee
    assert len(data["items"]) == 1

@pytest.mark.asyncio
async def test_checkout_buy_now_missing_product(async_client: AsyncClient, customer_token: str, test_address: dict):
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"]
            # Missing product_id and quantity
        }
    )
    assert res.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_checkout_cart_success(async_client: AsyncClient, customer_token: str, active_product: dict, test_address: dict):
    # Empty cart
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    
    # Add to cart
    await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": active_product["product_id"], "quantity": 1}
    )
    
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"]
        }
    )
    assert res.status_code == 200
    assert res.json()["financial_summary"]["subtotal"] == 100.0

@pytest.mark.asyncio
async def test_checkout_cart_rejects_product_id(async_client: AsyncClient, customer_token: str, test_address: dict):
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"],
            "product_id": 1,
            "quantity": 1
        }
    )
    assert res.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_checkout_invalid_address(async_client: AsyncClient, customer_token: str, active_product: dict):
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "buy_now",
            "address_id": 99999,
            "product_id": active_product["product_id"],
            "quantity": 1
        }
    )
    assert res.status_code == 400
    assert "valid delivery address is required" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_checkout_cart_empty_blocks(async_client: AsyncClient, customer_token: str, test_address: dict):
    # Empty cart
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"]
        }
    )
    assert res.status_code == 400
    assert "no items selected" in res.json()["detail"].lower() or "cart is empty" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_checkout_buy_now_insufficient_stock(async_client: AsyncClient, customer_token: str, active_product: dict, test_address: dict):
    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"],
            "product_id": active_product["product_id"],
            "quantity": 9999 # More than 10 stock
        }
    )
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_checkout_buy_now_inactive_product(async_client: AsyncClient, customer_token: str, active_product: dict, vendor_a_token: str, test_address: dict):
    # Make product inactive
    await async_client.put(
        f"/api/v1/products/{active_product['product_id']}",
        headers={"Authorization": f"Bearer {vendor_a_token}"},
        json={"product_status": "Inactive"}
    )

    res = await async_client.post(
        "/api/v1/checkout/preview",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"],
            "product_id": active_product["product_id"],
            "quantity": 1
        }
    )
    assert res.status_code == 400
    assert "inactive and cannot be purchased" in res.json()["detail"].lower() or "cannot be purchased" in res.json()["detail"].lower()
