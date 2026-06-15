# Non-Functional Requirements Document (NFR): Buy Again Feature

## 1. Performance and Scalability
1. **Query Optimization**: Fetching `OrderItem`s and current `Product`s must utilize efficient `JOIN`s or optimized IN clauses (e.g., `WHERE product_id IN (...)`) rather than executing N+1 queries.
2. **Response Time**: The `POST /api/v1/orders/{order_id}/buy-again` endpoint must resolve within 300ms at the 95th percentile, given average order sizes (1-10 items).
3. **Cart Operations**: Merging items into the cart must minimize writes. If 5 items are repurchased, cart database updates should be batched or optimally transacted.

## 2. Security and Authorization
1. **IDOR Prevention (Insecure Direct Object Reference)**: The system must absolutely guarantee that a user cannot input an `order_id` belonging to another user. Standard ownership checks (`order.user_id == current_user.id`) are strictly required.
2. **Data Leakage**: Under no circumstances should the system leak information about another user's order when returning `403 Forbidden` or `404 Not Found` errors.
3. **Audit Logging**: The system shall log all Buy Again requests (including `user_id` and `order_id`) for troubleshooting and audit purposes.

## 3. Reliability and Availability
1. **Transaction Integrity**: Adding multiple items to the cart must be handled within a single database transaction or reliable unit of work. If an unexpected server error occurs during the cart merge loop, the database should rollback rather than leaving partial ghost records.
2. **Idempotency Guidance**: While adding to a cart is generally not idempotent (hitting it twice adds double quantities), the response must cleanly represent the current state so the frontend can prevent accidental double-submissions.

## 4. Maintainability
1. **Code Reusability**: The logic to add items and merge quantities **must** reuse the existing cart service method (e.g., `cart_service.add_to_cart()`) to avoid duplicating cart calculation logic and violating DRY principles.
2. **Testing Coverage**: The feature must be backed by a suite of Pytest automated tests ensuring >90% coverage for the new service functions, explicitly targeting edge cases (price changes, missing products, stock boundary limits).
