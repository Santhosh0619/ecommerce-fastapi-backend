# Categories Non-Functional Requirements (NFR)

## 1. Performance
- **Eager Loading**: The `GET /api/v1/categories/` endpoint must not suffer from N+1 query problems. It must use SQLAlchemy's `selectinload` to fetch immediate subcategories efficiently in exactly 2 queries instead of 1+N queries.
- **Indexing**: `category_name` and `parent_category_id` must be indexed, as they are heavily queried for duplicates and tree-building.

## 2. Security
- Strict enforcement of RBAC dependencies (`RequireRole`).
- Path and query parameters must be validated via Pydantic to prevent SQL injection.

## 3. Data Integrity
- The database schema must enforce a composite unique constraint `uq_category_name_parent_id`.
- The SQLAlchemy relationship purposefully **omits** `cascade="all, delete-orphan"`. This guarantees that even at the database level, deleting a parent category cannot accidentally wipe out an entire product hierarchy. Subcategories must be handled explicitly.

## 4. Maintainability
- The Category codebase must strictly adhere to the established layered architecture: Router → Service → CRUD → Models.
