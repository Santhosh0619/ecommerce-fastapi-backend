import pytest
from httpx import AsyncClient

@pytest.fixture
async def active_product(async_client: AsyncClient, admin_token: str, vendor_token: str):
    # 1. Create a category
    res_cat = await async_client.post("/api/v1/categories/", headers={"Authorization": f"Bearer {admin_token}"}, json={"category_name": "Test Cart Category"})
    cat_id = res_cat.json()["category_id"]
    
    # 2. Create an Active product
    res_prod = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Test Cart Product", "product_description": "Description", "product_price": 100.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"}
    )
    return res_prod.json()

@pytest.fixture
async def inactive_product(async_client: AsyncClient, admin_token: str, vendor_token: str):
    # 1. Create a category
    res_cat = await async_client.post("/api/v1/categories/", headers={"Authorization": f"Bearer {admin_token}"}, json={"category_name": "Test Cart Category 2"})
    cat_id = res_cat.json()["category_id"]
    
    # 2. Create an Inactive product
    res_prod = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Test Inactive Product", "product_description": "Description", "product_price": 100.0, "product_stock": 10, "category_id": cat_id, "product_status": "Inactive"}
    )
    return res_prod.json()

@pytest.mark.asyncio
async def test_add_to_cart_and_calculations(async_client: AsyncClient, customer_token: str, active_product: dict):
    prod_id = active_product["product_id"]
    
    # 1. Add product to cart
    res_add = await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": prod_id, "quantity": 2}
    )
    assert res_add.status_code == 200
    cart = res_add.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["is_selected"] is True
    # Count should be 1 (distinct item), subtotal should be 200.0 (100.0 * 2)
    assert cart["selected_item_count"] == 1
    assert cart["selected_subtotal"] == 200.0
    
    # 2. Add SAME product again (quantity should increase)
    res_add2 = await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": prod_id, "quantity": 3}
    )
    assert res_add2.status_code == 200
    cart2 = res_add2.json()
    assert len(cart2["items"]) == 1
    assert cart2["items"][0]["quantity"] == 5
    assert cart2["selected_item_count"] == 1
    assert cart2["selected_subtotal"] == 500.0

@pytest.mark.asyncio
async def test_add_inactive_product(async_client: AsyncClient, customer_token: str, inactive_product: dict):
    prod_id = inactive_product["product_id"]
    res_add = await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": prod_id, "quantity": 1}
    )
    assert res_add.status_code == 400
    assert "inactive" in res_add.json()["detail"].lower()

@pytest.mark.asyncio
async def test_stock_limits_and_warnings(async_client: AsyncClient, customer_token: str, vendor_token: str, active_product: dict):
    prod_id = active_product["product_id"]
    
    # 1. Add valid quantity
    await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": prod_id, "quantity": 5}
    )
    
    # 2. Vendor updates product stock to 2
    res_upd = await async_client.put(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_stock": 2}
    )
    assert res_upd.status_code == 200
    
    # 3. Customer fetches cart, expects stock_warning = True
    res_cart = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_cart.status_code == 200
    cart = res_cart.json()
    assert cart["items"][0]["stock_warning"] is True
    
    # 4. Attempt to explicitly update quantity to 3 (which > 2 stock) -> should fail
    item_id = cart["items"][0]["cart_item_id"]
    res_put = await async_client.put(
        f"/api/v1/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"quantity": 3}
    )
    assert res_put.status_code == 400

@pytest.mark.asyncio
async def test_product_unavailable_flag(async_client: AsyncClient, customer_token: str, vendor_token: str, active_product: dict):
    prod_id = active_product["product_id"]
    
    # 1. Add to cart
    await async_client.post(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"product_id": prod_id, "quantity": 1}
    )
    
    # 2. Vendor marks product inactive
    await async_client.delete(f"/api/v1/products/{prod_id}", headers={"Authorization": f"Bearer {vendor_token}"})
    
    # 3. Customer fetches cart, expects product_unavailable = True
    res_cart = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_cart.status_code == 200
    assert res_cart.json()["items"][0]["product_unavailable"] is True

@pytest.mark.asyncio
async def test_admin_cannot_use_cart(async_client: AsyncClient, admin_token: str, active_product: dict):
    res_cart = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_cart.status_code == 403
    
@pytest.mark.asyncio
async def test_delete_cart_items(async_client: AsyncClient, customer_token: str, active_product: dict):
    prod_id = active_product["product_id"]
    # Add
    res_add = await async_client.post("/api/v1/cart/items", headers={"Authorization": f"Bearer {customer_token}"}, json={"product_id": prod_id, "quantity": 1})
    item_id = res_add.json()["items"][0]["cart_item_id"]
    
    # Delete specific item
    res_del_item = await async_client.delete(f"/api/v1/cart/items/{item_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_del_item.status_code == 204
    
    res_cart1 = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert len(res_cart1.json()["items"]) == 0
    
    # Add again
    await async_client.post("/api/v1/cart/items", headers={"Authorization": f"Bearer {customer_token}"}, json={"product_id": prod_id, "quantity": 1})
    
    # Empty cart entirely
    res_del_all = await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_del_all.status_code == 204
    
    res_cart2 = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert len(res_cart2.json()["items"]) == 0
    # Cart still exists but is empty
    assert res_cart2.json()["cart_id"] is not None

@pytest.mark.asyncio
async def test_get_empty_cart_auto_creates(async_client: AsyncClient, customer_token: str):
    # This customer might already have a cart from previous tests if db isn't cleanly wiped per test, 
    # but empty it just in case, then fetch to verify structure
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    res_cart = await async_client.get("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_cart.status_code == 200
    assert "cart_id" in res_cart.json()
    assert res_cart.json()["items"] == []

@pytest.mark.asyncio
async def test_add_nonexistent_product(async_client: AsyncClient, customer_token: str):
    res_add = await async_client.post("/api/v1/cart/items", headers={"Authorization": f"Bearer {customer_token}"}, json={"product_id": 99999, "quantity": 1})
    assert res_add.status_code == 404

@pytest.mark.asyncio
async def test_update_cart_item_edge_cases(async_client: AsyncClient, customer_token: str, active_product: dict):
    # Try updating a non-existent item
    res_upd = await async_client.put(f"/api/v1/cart/items/99999", headers={"Authorization": f"Bearer {customer_token}"}, json={"quantity": 2})
    assert res_upd.status_code == 404

@pytest.mark.asyncio
async def test_multiple_products_subtotal(async_client: AsyncClient, customer_token: str, admin_token: str, vendor_token: str):
    import uuid
    uid = str(uuid.uuid4())[:8]
    
    # Create two products
    res_cat = await async_client.post("/api/v1/categories/", headers={"Authorization": f"Bearer {admin_token}"}, json={"category_name": f"Cat_{uid}"})
    cat_id = res_cat.json()["category_id"]
    
    prod1 = await async_client.post("/api/v1/products/", headers={"Authorization": f"Bearer {vendor_token}"}, json={"product_name": f"P1_{uid}", "product_description": "Valid Description 1", "product_price": 50.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"})
    if prod1.status_code != 200:
        print(f"PROD1 ERROR: {prod1.json()}")
    prod2 = await async_client.post("/api/v1/products/", headers={"Authorization": f"Bearer {vendor_token}"}, json={"product_name": f"P2_{uid}", "product_description": "Valid Description 2", "product_price": 20.0, "product_stock": 10, "category_id": cat_id, "product_status": "Active"})
    if prod2.status_code != 200:
        print(f"PROD2 ERROR: {prod2.json()}")
    p1_id = prod1.json()["product_id"]
    p2_id = prod2.json()["product_id"]
    
    # Empty cart
    await async_client.delete("/api/v1/cart/", headers={"Authorization": f"Bearer {customer_token}"})
    
    # Add both
    await async_client.post("/api/v1/cart/items", headers={"Authorization": f"Bearer {customer_token}"}, json={"product_id": p1_id, "quantity": 2})
    res_add2 = await async_client.post("/api/v1/cart/items", headers={"Authorization": f"Bearer {customer_token}"}, json={"product_id": p2_id, "quantity": 3})
    
    cart = res_add2.json()
    assert cart["selected_item_count"] == 2
    assert cart["selected_subtotal"] == 160.0 # (50*2) + (20*3)
    
    # Deselect the second product
    item2 = next(item for item in cart["items"] if item["product_id"] == p2_id)
    res_upd = await async_client.put(f"/api/v1/cart/items/{item2['cart_item_id']}", headers={"Authorization": f"Bearer {customer_token}"}, json={"is_selected": False})
    
    cart_updated = res_upd.json()
    assert cart_updated["selected_item_count"] == 1 # Only 1 distinct selected item
    assert cart_updated["selected_subtotal"] == 100.0 # Only (50*2) from P1

