# Payments - Functional Requirements Document (FRD)

## 1. System Workflows
1. **Initialize Payment:** Triggered by the user attempting to pay for a Pending Order. A `payments` row is created (`Pending`), and a gateway intent is generated.
2. **Webhook Callback (Online Payments):** The Gateway sends an event. The system maps the `transaction_reference` to the local `payment_id`, updates the status to `Success`, and triggers Order confirmation and Notifications.
3. **Cash On Delivery (COD) Workflow:** COD bypasses the webhook flow. The system instantly creates the `payments` row as `Pending` and the `orders` row status is updated to `Confirmed` immediately to proceed with delivery. **CRITICAL:** For COD orders, stock is explicitly deducted/reserved when the order is confirmed, while the `payment_status` remains `Pending` until delivery is confirmed (which then transitions payment to `Success`).

## 2. Database Schema
### Table: `payments`
- `payment_id` (PK)
- `gateway_provider` (String - Stripe, Mock, Razorpay)
- `order_id` (FK -> orders)
- `payment_method` (Enum: UPI, Card, COD)
- `payment_status` (Enum: Pending, Success, Failed, Cancelled)
- `payment_amount` (Decimal/Float)
- `gateway_response` (JSON/String, Nullable)
- `stripe_payment_intent_id` (String, Nullable)
- `transaction_reference` (String, Unique)
- `created_at`, `updated_at`

## 3. Business Rules
- **Idempotency:** A webhook payload cannot process the same payment twice. If `payment_status` is already `Success`, ignore the webhook.
- **Provider Abstraction:** The codebase must use a common `PaymentProvider` interface for `create_intent` and `verify_payment`.
- **One Order -> Many Payments:** Users can generate multiple `payments` rows per `order_id` in the event of retries.

## 4. API Endpoints
- `POST /api/v1/payments/initiate` (Customer): Initiate payment for an Order.
- `POST /api/v1/payments/webhook/{provider}` (Public): Webhook listener for Gateway events.
