import pytest
from httpx import AsyncClient
import io
from unittest.mock import patch

@pytest.fixture
async def sample_category(async_client: AsyncClient, admin_token: str):
    res = await async_client.post(
        "/api/v1/categories/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"category_name": f"Test Cat {id(admin_token)}"}
    )
    assert res.status_code == 201, res.json()
    return res.json()["category_id"]

@pytest.fixture
async def vendor2_token(async_client: AsyncClient, admin_token: str):
    await async_client.post("/api/v1/auth/register", json={"user_name": "Vendor Two", "email": "v2@test.com", "password": "123"})
    
    # Needs to import from conftest
    from tests.conftest import TestingSessionLocal
    async with TestingSessionLocal() as db:
        from app.features.users.models import User, UserRole
        from app.features.roles.models import Role
        from sqlalchemy.future import select
        
        user_res = await db.execute(select(User).filter(User.email == "v2@test.com"))
        user = user_res.scalars().first()
        role_res = await db.execute(select(Role).filter(Role.role_name == "Vendor"))
        vendor_role = role_res.scalars().first()
        if user and vendor_role:
            existing = await db.execute(select(UserRole).filter(UserRole.user_id == user.user_id, UserRole.role_id == vendor_role.role_id))
            if not existing.scalars().first():
                db.add(UserRole(user_id=user.user_id, role_id=vendor_role.role_id))
                await db.commit()
            
    fresh_login = await async_client.post("/api/v1/auth/login", json={"email": "v2@test.com", "password": "123"})
    return fresh_login.json()["access_token"]

@pytest.mark.asyncio
async def test_create_product_positive(async_client: AsyncClient, vendor_token: str, sample_category: int):
    res = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "product_name": "Awesome Product",
            "product_description": "This is a great product for testing.",
            "product_price": 99.99,
            "product_stock": 10,
            "category_id": sample_category,
            "product_status": "Active"
        }
    )
    assert res.status_code == 201, res.json()
    data = res.json()
    assert data["product_name"] == "Awesome Product"
    assert data["product_slug"].startswith("awesome-product-")
    assert data["product_stock"] == 10

@pytest.mark.asyncio
async def test_create_product_negative_validation(async_client: AsyncClient, vendor_token: str, sample_category: int):
    # Negative price
    res = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "product_name": "Bad Price",
            "product_description": "This is a great product for testing.",
            "product_price": -5.0,
            "product_stock": 10,
            "category_id": sample_category
        }
    )
    assert res.status_code == 422 # Validation error

    # Invalid category
    res_cat = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "product_name": "Valid Name",
            "product_description": "This is a great product for testing.",
            "product_price": 5.0,
            "product_stock": 10,
            "category_id": 999999
        }
    )
    assert res_cat.status_code == 404
    assert "Category not found" in res_cat.json()["detail"]

@pytest.mark.asyncio
async def test_create_product_negative_customer(async_client: AsyncClient, customer_token: str, sample_category: int):
    # Customers cannot create products
    res = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "product_name": "Cust Product",
            "product_description": "This is a great product for testing.",
            "product_price": 10.0,
            "product_stock": 1,
            "category_id": sample_category
        }
    )
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_update_product_ownership(async_client: AsyncClient, vendor_token: str, vendor2_token: str, sample_category: int):
    # Vendor 1 creates
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "product_name": "Vendor 1 Item",
            "product_description": "This is a great product for testing.",
            "product_price": 50.0,
            "product_stock": 5,
            "category_id": sample_category
        }
    )
    prod_id = res_create.json()["product_id"]
    
    # Vendor 1 updates (success)
    res_up1 = await async_client.put(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_price": 40.0}
    )
    assert res_up1.status_code == 200
    assert res_up1.json()["product_price"] == 40.0
    
    # Vendor 2 tries to update (403 Forbidden)
    res_up2 = await async_client.put(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {vendor2_token}"},
        json={"product_price": 10.0}
    )
    assert res_up2.status_code == 403

@pytest.mark.asyncio
async def test_admin_is_featured(async_client: AsyncClient, admin_token: str, vendor_token: str, sample_category: int):
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Feature Me", "product_description": "Feature me please.", "product_price": 10, "product_stock": 1, "category_id": sample_category}
    )
    prod_id = res_create.json()["product_id"]
    
    # Vendor tries to feature it -> 403
    res_fail = await async_client.put(f"/api/v1/products/{prod_id}", headers={"Authorization": f"Bearer {vendor_token}"}, json={"is_featured": True})
    assert res_fail.status_code == 403
    
    # Admin features it -> 200
    res_success = await async_client.put(f"/api/v1/products/{prod_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"is_featured": True})
    assert res_success.status_code == 200
    assert res_success.json()["is_featured"] is True

@pytest.mark.asyncio
async def test_admin_delete_product(async_client: AsyncClient, vendor_token: str, admin_token: str, sample_category: int):
    # Vendor creates
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Admin Delete Me", "product_description": "Description here ok", "product_price": 10, "product_stock": 1, "category_id": sample_category}
    )
    assert res_create.status_code == 201
    prod_id = res_create.json()["product_id"]
    
    # Admin deletes (soft delete)
    res_del = await async_client.delete(f"/api/v1/products/{prod_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_del.status_code == 200
    assert res_del.json()["product_status"] == "Archived"

@pytest.mark.asyncio
async def test_product_visibility(async_client: AsyncClient, vendor_token: str, customer_token: str, sample_category: int):
    # Vendor creates Inactive product
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Secret Item", "product_description": "Hidden item", "product_price": 10, "product_stock": 1, "category_id": sample_category, "product_status": "Inactive"}
    )
    prod_id = res_create.json()["product_id"]
    slug = res_create.json()["product_slug"]
    
    # Vendor sees it in list
    res_v_list = await async_client.get(f"/api/v1/products/?keyword=Secret", headers={"Authorization": f"Bearer {vendor_token}"})
    assert len(res_v_list.json()) == 1
    
    # Customer does not see it in list
    res_c_list = await async_client.get(f"/api/v1/products/?keyword=Secret", headers={"Authorization": f"Bearer {customer_token}"})
    assert len(res_c_list.json()) == 0
    
    # Customer cannot fetch by slug
    res_c_slug = await async_client.get(f"/api/v1/products/{slug}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_c_slug.status_code == 404

@pytest.mark.asyncio
async def test_image_upload_validation(async_client: AsyncClient, vendor_token: str, sample_category: int):
    # Create product
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Image Val Item", "product_description": "Has image description", "product_price": 10, "product_stock": 1, "category_id": sample_category}
    )
    prod_id = res_create.json()["product_id"]
    
    # Upload invalid image type
    file_content = b"fake image bytes"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    data = {"is_primary": "true"}
    
    res_img = await async_client.post(
        f"/api/v1/products/{prod_id}/images",
        headers={"Authorization": f"Bearer {vendor_token}"},
        data=data,
        files=files
    )
    assert res_img.status_code == 400
    assert "Invalid file type" in res_img.json()["detail"]
    
    # Upload oversized image (>5MB)
    large_content = b"0" * (5 * 1024 * 1024 + 1)
    files_large = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}
    res_large = await async_client.post(
        f"/api/v1/products/{prod_id}/images",
        headers={"Authorization": f"Bearer {vendor_token}"},
        data={"is_primary": "true"},
        files=files_large
    )
    assert res_large.status_code == 400
    assert "File too large" in res_large.json()["detail"]

@pytest.mark.asyncio
async def test_image_upload_and_delete(async_client: AsyncClient, vendor_token: str, vendor2_token: str, sample_category: int):
    # Create product
    res_create = await async_client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"product_name": "Image Item", "product_description": "Has image description", "product_price": 10, "product_stock": 1, "category_id": sample_category}
    )
    assert res_create.status_code == 201, res_create.json()
    prod_id = res_create.json()["product_id"]
    
    # Upload image 1
    file_content = b"fake image bytes"
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    data = {"is_primary": "true"}
    
    res_img = await async_client.post(
        f"/api/v1/products/{prod_id}/images",
        headers={"Authorization": f"Bearer {vendor_token}"},
        data=data,
        files=files
    )
    assert res_img.status_code == 201
    img_id = res_img.json()["product_image_id"]
    assert res_img.json()["is_primary"] is True
    
    # Upload image 2
    files2 = {"file": ("test2.jpg", io.BytesIO(file_content), "image/jpeg")}
    data2 = {"is_primary": "false"}
    res_img2 = await async_client.post(
        f"/api/v1/products/{prod_id}/images",
        headers={"Authorization": f"Bearer {vendor_token}"},
        data=data2,
        files=files2
    )
    img_id2 = res_img2.json()["product_image_id"]
    assert res_img2.json()["is_primary"] is False
    
    # Try to set primary as another vendor (403)
    res_set_primary_fail = await async_client.put(
        f"/api/v1/products/{prod_id}/images/{img_id2}/primary",
        headers={"Authorization": f"Bearer {vendor2_token}"}
    )
    assert res_set_primary_fail.status_code == 403
    
    # Set image 2 as primary
    res_set_primary = await async_client.put(
        f"/api/v1/products/{prod_id}/images/{img_id2}/primary",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    assert res_set_primary.status_code == 200
    
    # Delete image 2 (which is primary)
    res_del = await async_client.delete(
        f"/api/v1/products/{prod_id}/images/{img_id2}",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    assert res_del.status_code == 204
    
    # Verify image 1 is now primary
    slug = res_create.json()["product_slug"]
    res_prod = await async_client.get(f"/api/v1/products/{slug}")
    assert res_prod.status_code == 200
    product_data = res_prod.json()
    assert len(product_data["images"]) == 1
    assert product_data["images"][0]["is_primary"] is True
    assert product_data["images"][0]["product_image_id"] == img_id

@pytest.mark.asyncio
async def test_slug_collision_retry(async_client: AsyncClient, vendor_token: str, sample_category: int):
    with patch("app.features.products.services.uuid.uuid4") as mock_uuid:
        import uuid
        # Force a constant UUID so slugs collide
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        
        # First creation should succeed
        res1 = await async_client.post(
            "/api/v1/products/",
            headers={"Authorization": f"Bearer {vendor_token}"},
            json={"product_name": "Collision Item", "product_description": "Description here", "product_price": 10, "product_stock": 1, "category_id": sample_category}
        )
        assert res1.status_code == 201
        
        # Second creation should hit the retry limit and fail with 409
        res2 = await async_client.post(
            "/api/v1/products/",
            headers={"Authorization": f"Bearer {vendor_token}"},
            json={"product_name": "Collision Item", "product_description": "Description here", "product_price": 10, "product_stock": 1, "category_id": sample_category}
        )
        assert res2.status_code == 409
        assert "unique product slug" in res2.json()["detail"]
