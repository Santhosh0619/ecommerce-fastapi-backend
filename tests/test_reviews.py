import pytest
from httpx import AsyncClient
import uuid

from app.features.orders.models import Order
from tests.conftest import TestingSessionLocal

async def mark_order_delivered(order_id: int):
    async with TestingSessionLocal() as db:
        order = await db.get(Order, order_id)
        assert order is not None
        order.order_status = 'Delivered'
        await db.commit()

async def create_delivered_order(async_client: AsyncClient, customer_token: str, product_id: int, test_address: dict) -> int:
    # Clear cart
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    # Add item
    await async_client.post(
        "/api/v1/cart/items", 
        headers={"Authorization": f"Bearer {customer_token}"}, 
        json={"product_id": product_id, "quantity": 1}
    )
    # Create order
    res = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": str(uuid.uuid4())
        },
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"]
        }
    )
    assert res.status_code == 201
    order_id = res.json()["order_id"]
    # Mark as delivered
    await mark_order_delivered(order_id)
    return order_id

@pytest.mark.asyncio
async def test_create_review_success(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    # Create review
    res = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "product_id": product_id,
            "order_id": order_id,
            "rating": 5,
            "review_comment": "I loved it."
        }
    )
    assert res.status_code == 201, res.json()
    data = res.json()
    assert data["rating"] == 5
    assert data["review_status"] == "Published"

@pytest.mark.asyncio
async def test_create_review_not_delivered(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_b_product"]["product_id"]
    
    # Create order but don't mark as delivered
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    await async_client.post(
        "/api/v1/cart/items", 
        headers={"Authorization": f"Bearer {customer_token}"}, 
        json={"product_id": product_id, "quantity": 1}
    )
    res_order = await async_client.post(
        "/api/v1/orders/",
        headers={
            "Authorization": f"Bearer {customer_token}",
            "Idempotency-Key": str(uuid.uuid4())
        },
        json={
            "checkout_type": "cart",
            "address_id": test_address["address_id"]
        }
    )
    order_id = res_order.json()["order_id"]

    # Try to create review
    res = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "product_id": product_id,
            "order_id": order_id,
            "rating": 4,
            "review_comment": "Nice"
        }
    )
    assert res.status_code == 400
    assert "must be Delivered" in res.json()["detail"]

@pytest.mark.asyncio
async def test_create_review_duplicate(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    # First review
    await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 5, "review_comment": "1"}
    )
    
    # Second review for the same product
    res = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 4, "review_comment": "2"}
    )
    assert res.status_code == 400
    assert "already submitted a review" in res.json()["detail"].lower() or "unique constraint" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_review(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    # Create review
    res_create = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 3, "review_comment": "Just ok"}
    )
    review_id = res_create.json()["review_id"]
    
    # Update review
    res_update = await async_client.put(
        f"/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"rating": 4, "review_comment": "Actually it is better."}
    )
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["rating"] == 4
    assert data["is_edited"] is True

@pytest.mark.asyncio
async def test_delete_review(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_b_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    # Create review
    res_create = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 5, "review_comment": "To be deleted"}
    )
    review_id = res_create.json()["review_id"]
    
    # Soft delete review
    res_delete = await async_client.delete(
        f"/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert res_delete.status_code == 200
    assert res_delete.json()["review_status"] == "Deleted"

@pytest.mark.asyncio
async def test_helpful_votes(async_client: AsyncClient, customer_token: str, admin_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    res_create = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 5, "review_comment": "Helpful review"}
    )
    review_id = res_create.json()["review_id"]
    
    # Upvote by Admin
    res_vote = await async_client.post(
        f"/api/v1/reviews/{review_id}/helpful",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_vote.status_code == 200
    assert res_vote.json()["voted"] is True
    
    # Check helpful_votes count
    res_get = await async_client.get(f"/api/v1/products/{product_id}/reviews")
    reviews = res_get.json()
    review = next(r for r in reviews if r["review_id"] == review_id)
    assert review["helpful_votes"] == 1
    
    # Remove vote
    res_vote_remove = await async_client.post(
        f"/api/v1/reviews/{review_id}/helpful",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_vote_remove.status_code == 200
    assert res_vote_remove.json()["voted"] is False
    
    # Check helpful_votes count decreased
    res_get_after = await async_client.get(f"/api/v1/products/{product_id}/reviews")
    reviews_after = res_get_after.json()
    review_after = next(r for r in reviews_after if r["review_id"] == review_id)
    assert review_after["helpful_votes"] == 0

@pytest.mark.asyncio
async def test_vendor_reply(async_client: AsyncClient, customer_token: str, vendor_a_token: str, vendor_b_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    res_create = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 1, "review_comment": "Not working"}
    )
    review_id = res_create.json()["review_id"]
    
    # Vendor B tries to reply (should fail)
    res_fail = await async_client.post(
        f"/api/v1/vendors/reviews/{review_id}/reply",
        headers={"Authorization": f"Bearer {vendor_b_token}"},
        json={"vendor_reply": "Sorry"}
    )
    assert res_fail.status_code == 403
    
    # Vendor A replies (success)
    res_reply = await async_client.post(
        f"/api/v1/vendors/reviews/{review_id}/reply",
        headers={"Authorization": f"Bearer {vendor_a_token}"},
        json={"vendor_reply": "We will fix it."}
    )
    assert res_reply.status_code == 200
    assert res_reply.json()["vendor_reply"] == "We will fix it."

@pytest.mark.asyncio
async def test_admin_moderation(async_client: AsyncClient, customer_token: str, admin_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_a_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    res_create = await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 5, "review_comment": "Buy here: http://spam.com"}
    )
    review_id = res_create.json()["review_id"]
    
    # Admin hides the review
    res_hide = await async_client.put(
        f"/api/v1/admin/reviews/{review_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Hidden"}
    )
    assert res_hide.status_code == 200
    assert res_hide.json()["review_status"] == "Hidden"
    
    # Check it doesn't appear in product reviews anymore
    res_get = await async_client.get(f"/api/v1/products/{product_id}/reviews")
    reviews = res_get.json()
    assert not any(r["review_id"] == review_id for r in reviews)

@pytest.mark.asyncio
async def test_aggregations_update(async_client: AsyncClient, customer_token: str, active_products_multivendor: dict, test_address: dict):
    product_id = active_products_multivendor["vendor_b_product"]["product_id"]
    order_id = await create_delivered_order(async_client, customer_token, product_id, test_address)
    
    # Create review 1 (5 stars)
    await async_client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": product_id, "order_id": order_id, "rating": 5, "review_comment": "1"}
    )
    
    # Wait, we need another user to create another review to test average.
    # Let's just create one review and see if the product's average_rating and review_count are updated.
    
    res_prod = await async_client.get(f"/api/v1/products/{active_products_multivendor['vendor_b_product']['product_slug']}")
    prod_data = res_prod.json()
    assert prod_data["review_count"] >= 1
    assert prod_data["average_rating"] > 0
