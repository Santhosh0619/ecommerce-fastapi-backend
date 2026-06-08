# Notifications - Non-Functional Requirements Document (NFR)

## 1. Performance
- Notification dispatching must be asynchronous and should not noticeably impact API response times.

## 2. Reliability & Retries
- Celery tasks should be configured with automatic retry policies (e.g., exponential backoff) in case the SMTP server is temporarily unreachable.

## 3. Availability
- Redis must be kept highly available, as it acts as the message broker for all background communications.

## 4. Configuration
- All email credentials (SMTP host, port, user, app password) must be securely pulled from `.env` and never hardcoded.
