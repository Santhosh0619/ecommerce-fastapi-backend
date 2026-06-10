import hmac
import hashlib
import time
import requests
import json
import os

# Configuration
WEBHOOK_URL = "http://localhost:8000/api/v1/payments/webhook"
# Read secret from .env relative to project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

webhook_secret = None
with open(dotenv_path, "r") as f:
    for line in f:
        if line.startswith("STRIPE_WEBHOOK_SECRET="):
            webhook_secret = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not webhook_secret:
    print("Failed to find STRIPE_WEBHOOK_SECRET in .env file.")
    exit(1)

print(f"Using Webhook Secret: {webhook_secret}")

# Construct mock stripe payment_intent.succeeded event
event_data = {
    "id": "evt_test_succeeded",
    "object": "event",
    "api_version": "2020-08-27",
    "created": int(time.time()),
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": "pi_3TgO7zPuMOwmrsTv2FpNaMZb",
            "object": "payment_intent",
            "status": "succeeded",
            "amount": 14040498,
            "currency": "usd"
        }
    }
}

payload_str = json.dumps(event_data, separators=(',', ':'))
payload_bytes = payload_str.encode('utf-8')

# Calculate signature
timestamp = str(int(time.time()))
signed_payload = f"{timestamp}.".encode('utf-8') + payload_bytes
signature = hmac.new(
    webhook_secret.encode('utf-8'),
    signed_payload,
    hashlib.sha256
).hexdigest()

stripe_signature_header = f"t={timestamp},v1={signature}"

print("Sending webhook payload...")
headers = {
    "Content-Type": "application/json",
    "Stripe-Signature": stripe_signature_header
}

response = requests.post(WEBHOOK_URL, data=payload_bytes, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
