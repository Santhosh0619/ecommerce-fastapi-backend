import pytest
from httpx import AsyncClient
import uuid

@pytest.fixture
async def pending_order(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    idem_key = str(uuid.uuid4())
    res = await async_client.post(
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
    return res.json()

@pytest.mark.asyncio
async def test_initiate_payment_cod(async_client: AsyncClient, customer_token: str, pending_order: dict):
    res = await async_client.post(
        "/api/v1/payments/initiate",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "order_id": pending_order["order_id"],
            "payment_method": "COD"
        }
    )
    assert res.status_code == 200, res.json()
    data = res.json()
    assert data["message"] == "COD Order Confirmed successfully. Payment is Pending upon delivery."
    
    # Verify order is confirmed
    order_res = await async_client.get(f"/api/v1/orders/{pending_order['order_id']}", headers={"Authorization": f"Bearer {customer_token}"})
    assert order_res.json()["order_status"] == "Confirmed"

@pytest.mark.asyncio
async def test_initiate_payment_stripe(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # Create another pending order
    idem_key = str(uuid.uuid4())
    order_res = await async_client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": idem_key},
        json={"checkout_type": "buy_now", "address_id": test_address["address_id"], "product_id": active_products_multivendor["vendor_a_product"]["product_id"], "quantity": 1}
    )
    pending_order = order_res.json()
    
    res = await async_client.post(
        "/api/v1/payments/initiate",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "order_id": pending_order["order_id"],
            "payment_method": "Card"
        }
    )
    assert res.status_code == 200, res.json()
    data = res.json()
    assert "client_secret" in data
    assert data["gateway_provider"] in ("stripe", "mock")
    
    # Check idempotency
    res2 = await async_client.post(
        "/api/v1/payments/initiate",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "order_id": pending_order["order_id"],
            "payment_method": "Card"
        }
    )
    assert res2.status_code == 200
    assert res2.json()["client_secret"] == data["client_secret"]
