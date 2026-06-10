import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_notifications_flow_and_authorization(async_client: AsyncClient, customer_token: str, vendor_a_token: str, setup_test_db):
    # Customer gets notifications
    res = await async_client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    data = res.json()
    
    # Even if empty, it should be a list
    assert isinstance(data, list)
    
    # We can test authorization by trying to read a dummy notification with another user
    # Or assuming the webhook test generated some notifications
    notifications = [n for n in data if n["notification_type"] in ("ORDER_CONFIRMED", "PAYMENT_FAILED")]
    
    if notifications:
        notif_id = notifications[0]["notification_id"]
        
        # Test Authorization: Vendor (User B) tries to read Customer's (User A) notification
        res_auth_fail = await async_client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {vendor_a_token}"}
        )
        assert res_auth_fail.status_code in (403, 404) # Not Found or Forbidden
        
        # Test success read
        res_read = await async_client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert res_read.status_code == 200
        assert res_read.json()["is_read"] is True
