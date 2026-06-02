# Products Feature Test Cases

## Summary
These test cases ensure the robustness of the Products domain, specifically validating CRUD operations, Role-Based Access Control (RBAC), automatic slug generation, image uploads, and visibility rules.

| Test Category | Test Case Name | Description | Status |
|---|---|---|---|
| **Product Creation** | `test_create_product_positive` | Verifies a Vendor can create a valid product, and asserts default status, correct slug generation, and DB insertion. | Passed |
| **Product Creation** | `test_create_product_negative_validation` | Attempts to create a product with a negative price to verify Pydantic throws a `422 Unprocessable Entity` validation error. | Passed |
| **Product Creation** | `test_create_product_negative_customer` | Attempts to create a product as a Customer role, verifying they receive a `403 Forbidden` response. | Passed |
| **Product Ownership** | `test_update_product_ownership` | Creates a product using Vendor 1. Then verifies Vendor 1 can update it, while Vendor 2 gets a `403 Forbidden` attempting to update Vendor 1's product. | Passed |
| **Admin Controls** | `test_admin_is_featured` | Verifies a Vendor gets a `403 Forbidden` when attempting to set `is_featured=True`. Verifies an Admin can successfully set it to `True`. | Passed |
| **Admin Controls** | `test_admin_delete_product` | Verifies an Admin can successfully soft-delete (`Archived`) any product regardless of vendor ownership. | Passed |
| **Visibility Logic** | `test_product_visibility` | Creates a product with `Inactive` status. Verifies the owning Vendor can see it in searches, while a Customer gets `0` search results and `404 Not Found` when requesting by slug. | Passed |
| **Image Validation** | `test_image_upload_validation` | Attempts to upload a `.txt` file (`text/plain`) and an oversized image (`>5MB`) to verify the system rejects both with a `400 Bad Request`. | Passed |
| **Image Management** | `test_image_upload_and_delete` | Tests `multipart/form-data` uploads, primary image toggle via `PUT`, ownership isolation, `204 No Content` deletion, and verifies primary image reassignment if the active primary image is deleted (explicitly validating the persisted database state). | Passed |
| **Edge Cases** | `test_slug_collision_retry` | Mocks UUID generation to force a duplicate slug collision. Verifies the system retries 3 times before correctly surfacing a `409 Conflict`. | Passed |

## Execution Results
- **Total Tests**: 10
- **Success**: 10
- **Warnings**: 2 (Deprecation warnings for pydantic `BaseSettings` and python `crypt`)
- **Errors**: 0

The module is fully functional, secure, and production-ready!
