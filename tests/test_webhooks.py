import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_payment_webhook_success_and_failure(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    # Create order
    idem_key = str(uuid.uuid4())
    order_res = await async_client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": idem_key},
        json={"checkout_type": "buy_now", "address_id": test_address["address_id"], "product_id": active_products_multivendor["vendor_a_product"]["product_id"], "quantity": 1}
    )
    pending_order = order_res.json()
    order_id = pending_order["order_id"]
    
    # Initiate payment
    pay_res = await async_client.post(
        "/api/v1/payments/initiate",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"order_id": order_id, "payment_method": "Card"}
    )
    client_secret = pay_res.json()["client_secret"]
    tx_id = client_secret.split("_secret_")[0]
    
    # Send Webhook Failure
    fail_payload = {
        "intent_id": tx_id,
        "status": "failed"
    }
    await async_client.post("/api/v1/payments/webhook", headers={"Stripe-Signature": "test_sig"}, json=fail_payload)
    
    # Verify order is Cancelled
    order_fail_check = await async_client.get(f"/api/v1/orders/{order_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert order_fail_check.json()["order_status"] == "Pending"
    assert order_fail_check.json()["payment_status"] == "Failed"
    
    # Create another order for Success test
    idem_key_2 = str(uuid.uuid4())
    order_res_2 = await async_client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": idem_key_2},
        json={"checkout_type": "buy_now", "address_id": test_address["address_id"], "product_id": active_products_multivendor["vendor_b_product"]["product_id"], "quantity": 1}
    )
    order_id_2 = order_res_2.json()["order_id"]
    
    pay_res_2 = await async_client.post(
        "/api/v1/payments/initiate",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"order_id": order_id_2, "payment_method": "Card"}
    )
    client_secret_2 = pay_res_2.json()["client_secret"]
    tx_id_2 = client_secret_2.split("_secret_")[0]
    
    # Send Webhook Success
    succ_payload = {
        "intent_id": tx_id_2,
        "status": "success"
    }
    await async_client.post("/api/v1/payments/webhook", headers={"Stripe-Signature": "test_sig"}, json=succ_payload)
    
    # Verify order is Confirmed
    order_succ_check = await async_client.get(f"/api/v1/orders/{order_id_2}", headers={"Authorization": f"Bearer {customer_token}"})
    assert order_succ_check.json()["order_status"] == "Confirmed"
    assert order_succ_check.json()["payment_status"] == "Success"
