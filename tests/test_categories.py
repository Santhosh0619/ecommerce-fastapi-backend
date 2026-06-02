import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_create_category_hierarchy(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Root
    res1 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Electronics"})
    assert res1.status_code == 201
    root_id = res1.json()["category_id"]
    
    # Create Subcategory
    res2 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Mobile", "parent_category_id": root_id})
    assert res2.status_code == 201

@pytest.mark.asyncio
async def test_prevent_duplicate_and_case_insensitive(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    res_root = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Fashion"})
    root_id = res_root.json()["category_id"]
    
    await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Shirts", "parent_category_id": root_id})
    
    # Exact duplicate
    res_dup1 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Shirts", "parent_category_id": root_id})
    assert res_dup1.status_code == 409
    
    # Case-insensitive duplicate
    res_dup2 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "sHiRts", "parent_category_id": root_id})
    assert res_dup2.status_code == 409

@pytest.mark.asyncio
async def test_prevent_circular_dependency(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    res1 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Home"})
    root_id = res1.json()["category_id"]
    
    res2 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Furniture", "parent_category_id": root_id})
    child_id = res2.json()["category_id"]
    
    # Prevent being own parent
    res_self = await async_client.put(f"/api/v1/categories/{root_id}", headers=headers, json={"parent_category_id": root_id})
    assert res_self.status_code == 400
    
    # Prevent child as parent
    res_child = await async_client.put(f"/api/v1/categories/{root_id}", headers=headers, json={"parent_category_id": child_id})
    assert res_child.status_code == 400

@pytest.mark.asyncio
async def test_prevent_deletion_with_children(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    res1 = await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Groceries"})
    root_id = res1.json()["category_id"]
    
    await async_client.post("/api/v1/categories/", headers=headers, json={"category_name": "Fruits", "parent_category_id": root_id})
    
    res_del = await async_client.delete(f"/api/v1/categories/{root_id}", headers=headers)
    assert res_del.status_code == 400

@pytest.mark.asyncio
async def test_rbac_category_access(async_client: AsyncClient, customer_token: str, vendor_token: str, admin_token: str):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    vend_headers = {"Authorization": f"Bearer {vendor_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # GET - Allowed for all
    assert (await async_client.get("/api/v1/categories/", headers=cust_headers)).status_code == 200
    assert (await async_client.get("/api/v1/categories/", headers=vend_headers)).status_code == 200
    assert (await async_client.get("/api/v1/categories/", headers=admin_headers)).status_code == 200
    
    # POST/PUT/DELETE - Customer
    assert (await async_client.post("/api/v1/categories/", headers=cust_headers, json={"category_name": "Fail"})).status_code == 403
    assert (await async_client.put("/api/v1/categories/1", headers=cust_headers, json={"category_name": "Fail"})).status_code == 403
    assert (await async_client.delete("/api/v1/categories/1", headers=cust_headers)).status_code == 403
    
    # POST/PUT/DELETE - Vendor
    assert (await async_client.post("/api/v1/categories/", headers=vend_headers, json={"category_name": "Fail"})).status_code == 403
    assert (await async_client.put("/api/v1/categories/1", headers=vend_headers, json={"category_name": "Fail"})).status_code == 403
    assert (await async_client.delete("/api/v1/categories/1", headers=vend_headers)).status_code == 403
    
    # Admin successful POST/PUT/DELETE
    res_post = await async_client.post("/api/v1/categories/", headers=admin_headers, json={"category_name": "AdminOnly"})
    assert res_post.status_code == 201
    cat_id = res_post.json()["category_id"]
    
    res_put = await async_client.put(f"/api/v1/categories/{cat_id}", headers=admin_headers, json={"category_name": "AdminUpdated"})
    assert res_put.status_code == 200
    
    res_del = await async_client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert res_del.status_code == 200
