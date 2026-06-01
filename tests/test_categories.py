import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.fixture
async def admin_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD}
    )
    return response.json()["access_token"]

@pytest.fixture
async def customer_token(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Test Cust", "email": "cust2@test.com", "password": "123"})
    response = await async_client.post("/api/v1/auth/login", json={"email": "cust2@test.com", "password": "123"})
    return response.json()["access_token"]

@pytest.fixture
async def vendor_token(async_client: AsyncClient, admin_token: str):
    # Create user
    await async_client.post("/api/v1/auth/register", json={"user_name": "Test Vendor", "email": "vendor2@test.com", "password": "123"})
    # Assign vendor role via admin endpoint (from previous features)
    # We will just fetch user ID and apply the Vendor role, but wait, the roles endpoint was /roles or /users/{id}/roles
    # Let's try registering, then we use admin to assign role.
    # First, get user by email? We don't have that endpoint. 
    # Wait, the customer gets automatically assigned the Customer role.
    # For a Vendor role, in test_vendors.py, they apply to be a vendor, and admin approves them.
    # To keep it simple, I'll use the vendor_application flow if needed, OR just use the Admin token to directly assign the role if that route exists.
    # We know `POST /api/v1/users/` allows manual creation by Admin. Let's use that.
    res = await async_client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_name": "Test Vendor Direct", "email": "vendor3@test.com", "password": "123", "role_id": 2} # Assuming role_id 2 is Vendor
    )
    # It might fail if role 2 is not vendor, but let's assume it works or we just login.
    # Actually, a simpler way is to just create a user, and then manually insert the role into the DB, but we are using API client.
    # Let's use the Vendor application flow.
    await async_client.post("/api/v1/auth/register", json={"user_name": "Test Vendor App", "email": "vendorapp2@test.com", "password": "123"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "vendorapp2@test.com", "password": "123"})
    token = login_res.json()["access_token"]
    
    # Submit application
    app_res = await async_client.post(
        "/api/v1/vendors/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"store_name": "Test Store", "company_registration_number": "123"}
    )
    app_id = app_res.json().get("application_id")
    
    # Admin approves
    await async_client.put(
        f"/api/v1/vendors/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Approved"}
    )
    # Get a fresh token now that they are a vendor
    fresh_login = await async_client.post("/api/v1/auth/login", json={"email": "vendorapp2@test.com", "password": "123"})
    return fresh_login.json()["access_token"]


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
