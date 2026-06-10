# Notification & Background Task Test Cases

## Scenario 1: Order Confirmation (Stripe/Online)
- **Action**: Process a successful Stripe payment webhook.
- **Expected Result**: 
  - Celery background task `process_order_confirmation_task` triggers.
  - Identifies the `Success` payment record.
  - `notifications` table gets a new `ORDER_CONFIRMED` entry indicating "Online Payment (Successful)" with the Stripe Intent ID.
  - Email dispatch updates `delivery_status` to `SENT`.

## Scenario 2: Order Confirmation (COD)
- **Action**: Initiate a COD payment.
- **Expected Result**: 
  - Celery background task triggers immediately.
  - Identifies the `Pending` COD payment record.
  - `notifications` table gets a new `ORDER_CONFIRMED` entry explicitly stating "Cash on Delivery (Pending upon delivery)" with the generated COD-xxxx ID.
  - Email dispatch updates `delivery_status` to `SENT`.

## Scenario 3: Vendor New Order Notification
- **Action**: Confirm an order containing products from multiple distinct vendors.
- **Expected Result**:
  - The system groups the order items by `vendor_id`.
  - `notifications` table gets distinct `NEW_VENDOR_ORDER` entries for each individual vendor.
  - Vendors only see their own products in the notification payload.

## Scenario 4: Payment Failed Notification
- **Action**: Process a Stripe `payment_intent.payment_failed` webhook.
- **Expected Result**:
  - Triggers the `send_email_notification_task` directly for the customer.
  - `notifications` table gets a `PAYMENT_FAILED` entry.
  - `delivery_status` updates to `SENT`.

## Scenario 5: Admin Alert (Task Retry Exhaustion)
- **Action**: Force a Celery task exception and wait for the `max_retries=3` limit to exhaust.
- **Expected Result**:
  - The framework catches the exhaustion and triggers `_create_admin_alert_async`.
  - Queries all users with the `Admin` role.
  - `notifications` table gets an `ADMIN_ALERT` entry for every admin user detailing the task failure.
