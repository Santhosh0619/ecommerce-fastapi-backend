# Functional Requirements Document (FRD): Products Feature

## 1. System Behavior

### 1.1 Product Creation
- **Action**: A Vendor or Admin submits product details (name, description, price, stock, category).
- **System**:
  - Validates all fields (e.g., price > 0, stock >= 0).
  - Automatically generates a unique `product_slug` by lowercasing, hyphenating the `product_name`, and appending a unique 4-6 character alphanumeric ID.
  - Sets initial `review_count` to 0 and `average_rating` to 0.

### 1.2 Image Upload & Management
- **Action**: A Vendor or Admin uploads multipart/form-data images for a specific product.
- **System**:
  - Validates file type and size.
  - Saves the physical file to the local server (`uploads/products/`).
  - Records the image URL in the `product_images` table.
  - If it is the first image, it is automatically marked as `is_primary = True`.

### 1.3 Image Deletion
- **Action**: A Vendor or Admin deletes an image.
- **System**:
  - Intercepts the request and explicitly calls Python's `os.remove()` to delete the physical file from the local server to prevent orphaned files.
  - Deletes the record from the `product_images` table.

### 1.4 Product Search & Listing
- **Action**: A Customer requests the product list.
- **System**:
  - Applies RBAC visibility rules: Customers only see `product_status == 'Active'`. Vendors see global Active + own Inactive/Archived. Admins see all.
  - Supports query parameters: `keyword` (searches name/description), `category_id`, `is_featured`, `sort`, `limit`, and `skip`.
  - Returns product data alongside the primary image thumbnail.

### 1.5 Soft Deletion
- **Action**: A Vendor or Admin deletes a product.
- **System**:
  - Updates `product_status` to `Archived`.
  - Does NOT physically delete the database row to preserve future Order history constraints.

### 1.6 Featured Products Management
- **Action**: An Admin updates a product to mark it as featured.
- **System**:
  - Toggles the `is_featured` boolean on the product.
  - When the frontend requests `GET /api/v1/products/?is_featured=true`, the system returns only the explicitly featured products, perfectly accommodating dynamic homepage displays without a dedicated endpoint.

### 1.7 Product Ownership & Authorization
- **Action**: A Vendor attempts to update or delete a product.
- **System**:
  - Verifies that `product.vendor_id == current_user.user_id`.
  - If the Vendor owns the product, the operation is allowed.
  - If the Vendor does not own the product, the system returns 403 Forbidden.
  - Admins can update or delete any product regardless of ownership.

### 1.8 Primary Image Management
- **Action**: A Vendor or Admin marks an image as primary.
- **System**:
  - Ensures only one image per product has `is_primary = True`.
  - Automatically updates the previous primary image to `is_primary = False`.

## 2. API Endpoints

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/v1/products/` | `GET` | Public | List products (RBAC filtered) |
| `/api/v1/products/{slug}` | `GET` | Public | View single product details & gallery |
| `/api/v1/products/` | `POST` | Vendor/Admin | Create a new product |
| `/api/v1/products/{id}` | `PUT` | Vendor/Admin | Update product details |
| `/api/v1/products/{id}` | `DELETE` | Vendor/Admin | Soft delete (Archive) product |
| `/api/v1/products/{id}/images` | `POST` | Vendor/Admin | Upload a local product image |
| `/api/v1/products/{id}/images/{img_id}`| `DELETE` | Vendor/Admin | Delete local image and DB record |
