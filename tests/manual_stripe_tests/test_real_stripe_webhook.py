import requests
import json
import time
import uuid
import stripe
import os

# Configuration
BASE_URL = "http://localhost:8000"
# Read secret from .env relative to project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# Read Stripe API key from .env
stripe_api_key = None
with open(dotenv_path, "r") as f:
    for line in f:
        if line.startswith("STRIPE_API_KEY="):
            stripe_api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not stripe_api_key:
    print("Failed to find STRIPE_API_KEY in .env file.")
    exit(1)

stripe.api_key = stripe_api_key
print(f"Stripe SDK configured with API Key: {stripe_api_key[:15]}...")

# Generate unique details
uid = str(uuid.uuid4())[:8]
email = f"real_stripe_{uid}@test.com"
password = "password123"

# Helper for JSON printing
def print_json(data):
    print(json.dumps(data, indent=2))

# 1. Register
print(f"\n1. Registering user {email}...")
reg_res = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={"user_name": f"Real User {uid}", "email": email, "password": password}
)
assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
print("Registration successful.")

# 2. Login
print("\n2. Logging in...")
login_res = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": email, "password": password}
)
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful.")

# 3. Create Address
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

# 4. Check initial product stock
prod_id = 4
prod_res = requests.get(f"{BASE_URL}/api/v1/products/")
initial_stock = None
for prod in prod_res.json():
    if prod["product_id"] == prod_id:
        initial_stock = prod["product_stock"]
        break

print(f"\n4. Initial stock of Product {prod_id}: {initial_stock}")

# 5. Create Order
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

# 6. Initiate Payment
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

# 7. Confirm Stripe PaymentIntent directly on Stripe's server
print("\n7. Confirming Stripe PaymentIntent on Stripe server using test card pm_card_visa...")
try:
    stripe_confirm = stripe.PaymentIntent.confirm(
        intent_id,
        payment_method="pm_card_visa"
    )
    print(f"Stripe Confirmation Success. Status returned by Stripe: {stripe_confirm.status}")
except Exception as e:
    print(f"Stripe Confirmation Failed: {str(e)}")
    exit(1)

# 8. Wait for Stripe CLI to receive and forward the webhook
wait_time = 10
print(f"\n8. Waiting {wait_time} seconds for webhook processing over CLI...")
time.sleep(wait_time)

# 9. Verify updated Order and Payment status in our database
print("\n9. Verifying updated Order status...")
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
print("\n10. Verifying stock decrement...")
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

print("\n=== REAL STRIPE CLI E2E WEBHOOK VERIFICATION SUCCESSFUL ===")
