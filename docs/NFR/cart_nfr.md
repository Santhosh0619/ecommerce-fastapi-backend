# Cart Feature: Non-Functional Requirements Document (NFR)

## 1. Data Integrity & Consistency
- **Concurrency**: The unique constraint on `(cart_id, product_id)` at the database level ensures that concurrent `POST /cart/items` requests for the same product do not result in duplicate row insertions.
- **Dynamic Aggregation**: `selected_item_count` and `selected_subtotal` must strictly be calculated at runtime (either via Python logic or SQL aggregation) and never stored statically in the database. This prevents data desynchronization if product prices change asynchronously.

## 2. Performance
- **Eager Loading**: The `GET /api/v1/cart/` endpoint must utilize SQLAlchemy `selectinload` or `joinedload` to fetch `CartItems`, related `Products`, and `ProductImages` in as few queries as possible to avoid the N+1 query problem.

## 3. Security
- **Data Isolation**: All cart service functions must strictly scope queries using `user_id` to ensure absolute horizontal data isolation (users cannot query or manipulate cart IDs that do not belong to them).
- **Endpoint Protection**: Admin roles must be completely blocked from accessing cart endpoints at the dependency or router level.

## 4. Maintainability
- **Modularity**: The cart feature must be isolated within `app/features/cart/`, maintaining its own `models.py`, `schemas.py`, `crud.py`, `services.py`, and `router.py`. Cross-domain calls (e.g., fetching product details) should use the respective domain's CRUD/Service layers where appropriate.
