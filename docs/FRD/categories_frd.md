# Categories Functional Requirements Document (FRD)

## 1. Data Requirements
The `Category` entity must contain:
- `category_id` (Primary Key, integer)
- `category_name` (String, unique within the same parent context)
- `category_status` (Boolean, active/inactive)
- `parent_category_id` (Foreign Key to `Category`, nullable)

## 2. API Endpoints
- **`GET /api/v1/categories/`**
  - Fetches all root categories (categories where `parent_category_id` is null).
  - Must eager-load the immediate `subcategories`.
  - Roles: Admin, Vendor, Customer
- **`GET /api/v1/categories/{id}`**
  - Fetches a single category and its immediate `subcategories`.
  - Roles: Admin, Vendor, Customer
- **`POST /api/v1/categories/`**
  - Creates a new category.
  - Validates that the exact name does not already exist under the given parent.
  - Roles: Admin only
- **`PUT /api/v1/categories/{id}`**
  - Updates category name, status, or parent.
  - Prevents circular hierarchies (a category cannot be its own parent).
  - Roles: Admin only
- **`DELETE /api/v1/categories/{id}`**
  - Deletes the specified category.
  - Fails with 400 Bad Request if `subcategories` exist.
  - Roles: Admin only

## 3. Business Rules
1. **Duplicate Rule**: A parent category cannot have two children with the same name (case-insensitive).
2. **Circular Dependency Rule**: An update operation cannot assign a category's `parent_category_id` to its own `category_id`.
3. **Orphan Prevention Rule**: Deletion is blocked if the category has children. Admin must manually reassign or delete children first.
