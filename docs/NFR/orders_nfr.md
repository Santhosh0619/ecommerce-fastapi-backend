# Orders - Non-Functional Requirements Document (NFR)

## 1. Data Integrity & Consistency
- Transactional integrity must be maintained using SQLAlchemy Async sessions when creating `orders` and `order_items` together.

## 2. Concurrency
- Transactional isolation must prevent overselling during stock deduction.

## 3. Future Considerations
- When scale requires it, row-level locking (e.g., `SELECT ... FOR UPDATE` or optimistic locking) should be utilized for stock deduction concurrency control.

## 3. Scalability
- Order numbers should be generated using a unique collision-resistant format (e.g., `ORD-YYYYMMDD-XXXX`).

## 4. Security
- Order endpoints must strictly check `user_id` to prevent IDOR (Insecure Direct Object Reference) attacks.
