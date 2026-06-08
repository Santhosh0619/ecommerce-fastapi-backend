# Notifications - Functional Requirements Document (FRD)

## 1. System Workflows
1. **Trigger Event:** Core logic (e.g., Payment Webhook) calls `celery_app.send_task()`.
2. **Task Execution:** Celery Worker picks up the job from Redis, constructs the Email via `fastapi-mail` or `smtplib`, and transmits it.
3. **Database Logging:** The system logs the notification in the `notifications` table for user dashboard viewing later.

## 2. Database Schema
### Table: `notifications`
- `notification_id` (PK)
- `notification_type` (Enum: PAYMENT_SUCCESS, PAYMENT_FAILED, ORDER_CONFIRMED, ORDER_PACKED, ORDER_DELIVERED, ORDER_CANCELLED, NEW_VENDOR_ORDER)
- `user_id` (FK -> users)
- `title` (String)
- `message` (Text)
- `is_read` (Boolean, Default: False)
- `created_at`

## 3. Business Rules
- **Vendor Privacy:** The Vendor alert must ONLY contain information regarding their own products from the order, not the entire cart if multiple vendors were involved.
- **Async Execution:** API endpoints must never await the SMTP transmission.

## 4. API Endpoints
- `GET /api/v1/notifications/` (Customer/Vendor): View notification history.
- `PUT /api/v1/notifications/{id}/read` (Customer/Vendor): Mark as read.
