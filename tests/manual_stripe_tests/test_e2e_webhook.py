import requests
import json
import time
import uuid
import hmac
import hashlib
import os

# Configuration
BASE_URL = "http://localhost:8000"
# Read secret from .env relative to project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# 1. Read secret from .env
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

# Generate unique details
uid = str(uuid.uuid4())[:8]
email = f"e2e_{uid}@test.com"
password = "password123"

# Helper for JSON printing
def print_json(data):
    print(json.dumps(data, indent=2))

# 2. Register
print(f"\n1. Registering user {email}...")
reg_res = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={"user_name": f"E2E User {uid}", "email": email, "password": password}
)
assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
print("Registration successful.")

# 3. Login
print("\n2. Logging in...")
login_res = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": email, "password": password}
)
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful.")

# 4. Create Address
print("\n3. Creating Address...")
addr_res = requests.post(
    f"{BASE_URL}/api/v1/addresses/",
    headers=headers,
    json={
        "title": "Home",
        "full_name": "Test Customer",
        "phone_number": "1234567890",
        "address_line_1": "123 Test Street",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "is_default": True
    }
)
assert addr_res.status_code == 201, f"Address creation failed: {addr_res.text}"
address_id = addr_res.json()["address_id"]
print(f"Address created with ID: {address_id}")

# 5. Check initial product stock
# We'll use product_id = 4
prod_id = 4
prod_res = requests.get(f"{BASE_URL}/api/v1/products/")
initial_stock = None
for prod in prod_res.json():
    if prod["product_id"] == prod_id:
        initial_stock = prod["product_stock"]
        break

print(f"\n4. Initial stock of Product {prod_id}: {initial_stock}")

# 6. Create Order
print("\n5. Creating Order...")
idem_key = str(uuid.uuid4())
order_res = requests.post(
    f"{BASE_URL}/api/v1/orders/",
    headers={**headers, "Idempotency-Key": idem_key},
    json={
        "checkout_type": "buy_now",
        "address_id": address_id,
        "product_id": prod_id,
        "quantity": 1
    }
)
assert order_res.status_code == 201, f"Order creation failed: {order_res.text}"
order_data = order_res.json()
order_id = order_data["order_id"]
print(f"Order created with ID: {order_id}. Initial status: {order_data['order_status']}, payment: {order_data['payment_status']}")

# 7. Initiate Payment
print("\n6. Initiating Payment...")
pay_res = requests.post(
    f"{BASE_URL}/api/v1/payments/initiate",
    headers=headers,
    json={
        "order_id": order_id,
        "payment_method": "Card"
    }
)
assert pay_res.status_code == 200, f"Payment initiation failed: {pay_res.text}"
pay_data = pay_res.json()
client_secret = pay_data["client_secret"]
intent_id = client_secret.split("_secret_")[0]
print(f"Payment initiated. Intent ID: {intent_id}")

# 8. Send Signed Stripe Webhook
print("\n7. Constructing and sending Stripe webhook succeeded event...")
event_data = {
    "id": f"evt_e2e_{uid}",
    "object": "event",
    "api_version": "2020-08-27",
    "created": int(time.time()),
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": intent_id,
            "object": "payment_intent",
            "status": "succeeded",
            "amount": int(float(order_data["total_amount"]) * 100),
            "currency": "usd"
        }
    }
}

payload_str = json.dumps(event_data, separators=(',', ':'))
payload_bytes = payload_str.encode('utf-8')

# Calculate Stripe webhook signature
timestamp = str(int(time.time()))
signed_payload = f"{timestamp}.".encode('utf-8') + payload_bytes
signature = hmac.new(
    webhook_secret.encode('utf-8'),
    signed_payload,
    hashlib.sha256
).hexdigest()

stripe_signature_header = f"t={timestamp},v1={signature}"

headers_webhook = {
    "Content-Type": "application/json",
    "Stripe-Signature": stripe_signature_header
}

webhook_res = requests.post(
    f"{BASE_URL}/api/v1/payments/webhook",
    data=payload_bytes,
    headers=headers_webhook
)
print(f"Webhook Status Code: {webhook_res.status_code}")
print(f"Webhook Response: {webhook_res.text}")
assert webhook_res.status_code == 200, "Webhook endpoint failed"

# 9. Verify updated Order and Payment status
print("\n8. Verifying updated Order status...")
order_check = requests.get(
    f"{BASE_URL}/api/v1/orders/{order_id}",
    headers=headers
)
assert order_check.status_code == 200
final_order = order_check.json()
print("Final Order Details:")
print_json(final_order)

assert final_order["order_status"] == "Confirmed", f"Expected Confirmed, got {final_order['order_status']}"
assert final_order["payment_status"] == "Success", f"Expected Success, got {final_order['payment_status']}"
print("Order status verification passed!")

# 10. Verify stock was decremented
print("\n9. Verifying stock decrement...")
prod_res_final = requests.get(f"{BASE_URL}/api/v1/products/")
final_stock = None
for prod in prod_res_final.json():
    if prod["product_id"] == prod_id:
        final_stock = prod["product_stock"]
        break

print(f"Final stock of Product {prod_id}: {final_stock}")

assert initial_stock is not None, f"Product {prod_id} initial stock could not be fetched (product might be Archived/Inactive)"
assert final_stock is not None, f"Product {prod_id} final stock could not be fetched"

if final_order["order_status"] == "Cancelled":
    print("Order was Cancelled (likely due to out-of-stock). Verifying stock remained 0.")
    assert final_stock == 0, f"Expected stock to remain 0, got {final_stock}"
    assert initial_stock == 0, f"Expected initial stock to be 0, got {initial_stock}"
else:
    assert final_stock == initial_stock - 1, f"Expected stock {initial_stock - 1}, got {final_stock}"
    print("Stock decrement verification passed!")

print("\n=== E2E WEBHOOK VERIFICATION SUCCESSFUL ===")
