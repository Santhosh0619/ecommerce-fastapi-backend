# Orders - Functional Requirements Document (FRD)

## 1. System Workflows
1. **Create Order:** Triggered by the checkout service. The order is inserted as `Pending`.
2. **Update Order Status:** Triggered by the Payment Gateway Webhook (if success -> `Confirmed`, if fail -> `Cancelled` or remains `Pending`).

## 2. Database Schema
### Table: `orders`
- `order_id` (PK)
- `order_number` (String, Unique)
- `user_id` (FK -> users)
- `address_id` (FK -> user_addresses)
- `order_status` (Enum: Pending, Confirmed, Packed, Out For Delivery, Delivered, Cancelled)
- `payment_status` (Enum: Pending, Success, Failed, Cancelled)
- `total_amount` (Decimal/Float)
- `expected_delivery_date` (Date)
- `created_at`, `updated_at`

### Table: `order_items`
- `order_item_id` (PK)
- `order_id` (FK -> orders)
- `product_id` (FK -> products)
- `quantity` (Int)
- `product_price` (Decimal/Float)
- `created_at`

## 3. Business Rules
- **Idempotent Status Updates:** An order cannot transition from `Confirmed` back to `Pending`.
- **Stock Deduction:** Occurs **only** when `order_status` transitions from `Pending` to `Confirmed`. Do not deduct stock multiple times.
- **RBAC:** Customers can only read their own orders. Vendors can only read order items containing their products.

## 4. API Endpoints
- `POST /api/v1/orders/` (Internal/Protected): Initialize a new order.
- `GET /api/v1/orders/` (Customer): Retrieve order history.
- `GET /api/v1/orders/{id}` (Customer): Retrieve order details.
