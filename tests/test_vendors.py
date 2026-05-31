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
async def vendor_candidate(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Wants Vendor", "email": "vendor@test.com", "password": "123"})
    response = await async_client.post("/api/v1/auth/login", json={"email": "vendor@test.com", "password": "123"})
    return response.json()

@pytest.mark.asyncio
async def test_vendor_application_flow(async_client: AsyncClient, admin_token: str, vendor_candidate: dict):
    # 1. Customer applies
    customer_headers = {"Authorization": f"Bearer {vendor_candidate['access_token']}"}
    apply_res = await async_client.post(
        "/api/v1/vendors/apply",
        headers=customer_headers,
        json={"store_name": "My Store", "business_details": "Selling shoes"}
    )
    assert apply_res.status_code == 201
    app_id = apply_res.json()["application_id"]
    
    # 2. Admin reviews application
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    review_res = await async_client.put(
        f"/api/v1/vendors/applications/{app_id}/status",
        headers=admin_headers,
        json={"status": "approved"}
    )
    # 3. Explicitly verify Vendor role assignment via the API
    # We dynamically add a test endpoint that requires the "Vendor" role
    from app.main import app
    from fastapi import APIRouter, Depends
    from app.features.auth.dependencies import RequireRole
    
    test_router = APIRouter()
    @test_router.get("/test-vendor-only", dependencies=[Depends(RequireRole(["Vendor"]))])
    async def vendor_only_route():
        return {"success": True}
        
    app.include_router(test_router)
    
    # Now hit the endpoint with the vendor's token
    vendor_headers = {"Authorization": f"Bearer {vendor_candidate['access_token']}"}
    verify_res = await async_client.get("/test-vendor-only", headers=vendor_headers)
    
    # If the user has the Vendor role, this will be 200 OK. If not, 403 Forbidden.
    assert verify_res.status_code == 200
    assert verify_res.json()["success"] == True
