import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_order_creation_success(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # Clear cart
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    
    # Add items to cart
    res_cart = await async_client.post(
        "/api/v1/cart/items", 
        headers={"Authorization": f"Bearer {customer_token}"}, 
        json={"product_id": active_products_multivendor["vendor_a_product"]["product_id"], "quantity": 1}
    )
    assert res_cart.status_code == 200, res_cart.json()
    
    # Create Order
    idem_key = str(uuid.uuid4())
    res = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": idem_key
        },
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"]
        }
    )
    assert res.status_code == 201, res.json()
    data = res.json()
    assert data["order_status"] == "Pending"
    assert data["order_number"].startswith("ORD-")
    assert len(data["items"]) == 1
    assert float(data["total_amount"]) == 105.0

@pytest.mark.asyncio
async def test_order_creation_idempotency(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # Clear cart first
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    
    # Add items to cart
    await async_client.post(
        "/api/v1/cart/items", 
        headers={"Authorization": f"Bearer {customer_token}"}, 
        json={"product_id": active_products_multivendor["vendor_b_product"]["product_id"], "quantity": 2}
    )
    
    idem_key = str(uuid.uuid4())
    payload = {
        "checkout_type": "cart",
        "address_id": test_address["address_id"]
    }
    
    # First request
    res1 = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": idem_key
        },
        json=payload
    )
    assert res1.status_code == 201, res1.json()
    order1 = res1.json()
    
    # Second identical request with same idempotency key
    res2 = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": idem_key
        },
        json=payload
    )
    
    # Redis lock should intercept and return existing order
    assert res2.status_code == 201, res2.json()
    order2 = res2.json()
    
    # Assert exact identical order returned
    assert order1["order_id"] == order2["order_id"]
    assert order1["order_number"] == order2["order_number"]

@pytest.mark.asyncio
async def test_get_user_orders(async_client: AsyncClient, customer_token: str):
    res = await async_client.get("/api/v1/orders/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

@pytest.mark.asyncio
async def test_get_order_by_id(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # First create an order
    idem_key = str(uuid.uuid4())
    create_res = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": idem_key
        },
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"],
            "product_id": active_products_multivendor["vendor_a_product"]["product_id"],
            "quantity": 1
        }
    )
    assert create_res.status_code == 201, create_res.json()
    order_id = create_res.json()["order_id"]
    
    # Retrieve order
    res = await async_client.get(f"/api/v1/orders/{order_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert res.json()["order_id"] == order_id

@pytest.mark.asyncio
async def test_get_order_unauthorized_access(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # Customer A creates order
    idem_key = str(uuid.uuid4())
    create_res = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": idem_key
        },
        json={
            "checkout_type": "buy_now",
            "address_id": test_address["address_id"],
            "product_id": active_products_multivendor["vendor_a_product"]["product_id"],
            "quantity": 1
        }
    )
    order_id = create_res.json()["order_id"]
    
    # Create Customer B
    await async_client.post("/api/v1/auth/register", json={"user_name": "Cust B", "email": "custb_unauth@test.com", "password": "123"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "custb_unauth@test.com", "password": "123"})
    cust_b_token = login_res.json()["access_token"]
    
    # Customer B attempts to get Customer A's order
    res = await async_client.get(f"/api/v1/orders/{order_id}", headers={"Authorization": f"Bearer {cust_b_token}"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
