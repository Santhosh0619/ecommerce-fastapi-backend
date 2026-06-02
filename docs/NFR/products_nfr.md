# Non-Functional Requirements (NFR): Products Feature

## 1. Security & Access Control
- **RBAC**: Strict role-based access control must be enforced at the router level.
  - Write operations (`POST`, `PUT`, `DELETE`) require `Vendor` or `Admin` roles.
  - Vendors can only execute write operations if `product.vendor_id == current_user.user_id`.
- **File Upload Security**: Uploaded files must be validated to ensure they are safe image formats (e.g., JPEG, PNG, WEBP) to prevent malicious script uploads.

## 2. Performance & Optimization
- **Database Indexing**: The `product_slug` column must be indexed (`index=True`) to ensure `GET /products/{slug}` lookups are `O(1)` or extremely fast.
- **Pagination**: All list endpoints must implement limit/offset pagination to prevent memory exhaustion when querying large catalogs.
- **Lazy Loading**: Relationship loads for galleries (`product_images`) should use `selectinload` in SQLAlchemy to avoid the N+1 query problem during bulk fetches.

## 3. Data Integrity & Storage
- **Local Storage Management**: Physical files must be actively managed. The system must explicitly call `os.remove()` when deleting images to prevent disk space leaks.
- **Precision Currency**: The `product_price` must utilize `DECIMAL(10,2)` at the database level to ensure exact financial calculations without floating-point inaccuracies.
- **Soft Deletion**: Products must never be hard-deleted from the database to preserve referential integrity for future `Order` tables.

## 4. Maintainability
- **Separation of Concerns**: Adhere strictly to the project's layered architecture (`router.py` -> `services.py` -> `crud.py` -> `models.py`). Business logic (like slug generation and file I/O) must reside in `services.py`.
