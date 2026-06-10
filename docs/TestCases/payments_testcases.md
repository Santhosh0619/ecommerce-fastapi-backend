# Payment & Webhook Test Cases

## Scenario 1: Initiate COD Payment
- **Action**: Call `POST /api/v1/payments/initiate` passing an `order_id` and `payment_method = COD`.
- **Expected Result**: 
  - Status Code `200 OK`
  - Database payment record is created with method `COD` and status `Pending`.
  - Order transaction is instantly confirmed (Order status -> `Confirmed`).
  - Stock is decremented.

## Scenario 2: Initiate Online Payment
- **Action**: Call `POST /api/v1/payments/initiate` passing an `order_id` and `payment_method = Card`.
- **Expected Result**: 
  - Status Code `200 OK`
  - Communicates with Stripe to create a PaymentIntent.
  - Returns a `client_secret`.
  - Database payment record is created with status `Pending` and the Stripe `intent_id`.

## Scenario 3: Payment Idempotency
- **Action**: Call `POST /api/v1/payments/initiate` twice for the same pending order.
- **Expected Result**:
  - Returns the same existing payment session and `client_secret` instead of creating a new PaymentIntent.

## Scenario 4: Stripe Webhook Success Processing
- **Action**: Simulate a Stripe `payment_intent.succeeded` webhook targeting `/api/v1/payments/webhook`.
- **Expected Result**:
  - Verifies Stripe signature successfully.
  - Locates the payment record via `intent_id`.
  - Updates `payments.payment_status` to `Success`.
  - Updates `orders.order_status` to `Confirmed` and `orders.payment_status` to `Success`.
  - Decrements product stock.

## Scenario 5: Stripe Webhook Failure Processing
- **Action**: Simulate a Stripe `payment_intent.payment_failed` webhook.
- **Expected Result**:
  - Updates `payments.payment_status` to `Failed`.
  - `orders.order_status` remains `Pending`.
  - Stock is NOT decremented.

## Scenario 6: Concurrent Webhook Race Condition
- **Action**: Fire two `payment_intent.succeeded` webhooks for the same payment simultaneously.
- **Expected Result**:
  - Row-level database locking (`with_for_update()`) serializes the requests.
  - The first request processes the confirmation.
  - The second request recognizes the payment is already `Success` and safely returns an "Already processed" response without double-decrementing stock.
