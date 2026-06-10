# Payments - Non-Functional Requirements Document (NFR)

## 1. Security & Compliance
- Never store sensitive raw credit card data on our servers. All sensitive data must be handled by the Payment Gateway (Stripe).
- Webhook endpoints must verify cryptographic signatures sent by the gateway (e.g., Stripe Webhook Secret verification) to prevent malicious actors from faking payment successes.

## 2. Reliability
- In the event of network failures during webhook reception, the API must respond with a `5xx` error so the gateway knows to re-attempt the webhook delivery.

## 3. Extensibility
- The abstract provider layer must be designed so that adding Razorpay or Cashfree later requires exactly zero changes to the core business logic or router layer.
