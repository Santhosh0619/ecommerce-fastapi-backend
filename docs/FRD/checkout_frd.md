# Functional Requirements Document (FRD)

## 1. User Addresses

### 1.1 Data Model
Table: `user_addresses`
Columns:
- `address_id` (PK, INT)
- `user_id` (FK, INT)
- `title` (VARCHAR, e.g., "Home", "Office")
- `full_name` (VARCHAR)
- `phone_number` (VARCHAR, validated)
- `address_line_1` (VARCHAR)
- `address_line_2` (VARCHAR, Nullable)
- `city` (VARCHAR)
- `state` (VARCHAR)
- `postal_code` (VARCHAR, validated)
- `is_default` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### 1.2 Address Logic
- **FR_ADDR_01**: Users can create, read, update, and delete their own addresses.
- **FR_ADDR_02**: If `is_default=True` is passed during address creation/update, all other addresses for this user MUST automatically be set to `is_default=False`.
- **FR_ADDR_03**: The very first address a user creates MUST be automatically marked as default, regardless of input.
- **FR_ADDR_04**: If the default address is deleted, the system MUST automatically assign `is_default=True` to the remaining address that has the most recent `updated_at` timestamp.

## 2. Checkout Preview

### 2.1 Preview Payload Rules
- **FR_CHK_01**: The checkout request must contain a valid `address_id` belonging to the user.
- **FR_CHK_02**: Request requires a `checkout_type` enum (`buy_now` or `cart`).
- **FR_CHK_03**: If `checkout_type == "buy_now"`, the payload MUST require `product_id` and `quantity`.
- **FR_CHK_04**: If `checkout_type == "cart"`, the payload MUST explicitly REJECT `product_id` and `quantity`.

### 2.2 Validation Engine
- **FR_CHK_05**: If `checkout_type == "cart"`, the system must verify the user has at least 1 `is_selected=True` item in their cart. If 0 items, block with `400 Bad Request`.
- **FR_CHK_06**: The system must verify that the requested quantities do not exceed the `product_stock`.
- **FR_CHK_07**: The system must verify that the requested product's status is `Active` and has not been deleted.
- **FR_CHK_08**: Violations in FR_CHK_06 and FR_CHK_07 must block the checkout entirely with a `400 Bad Request` specifying the offending product.

### 2.3 Financial Calculation
- **FR_CHK_09**: Subtotal is calculated dynamically (`unit_price * quantity`) for all target products.
- **FR_CHK_10**: A flat Delivery Fee (e.g., $5.00) is added.
- **FR_CHK_11**: Grand Total is calculated as `Subtotal + Delivery Fee`.

### 2.4 Delivery Date Calculation
- **FR_CHK_12**: Expected delivery is calculated as: `Processing Time (1 business day) + Transit Time (3 to 5 business days)`.
- **FR_CHK_13**: The algorithm must detect and skip weekend days (Saturday/Sunday) to provide realistic business-day estimates.
- **FR_CHK_14**: Response returns string formats like "Expected Delivery: June 8, 2026 - June 10, 2026".

## 3. API Endpoint Definitions

### 3.1 Address Management Endpoints
- `POST /api/v1/addresses/`: Create a new user address.
- `GET /api/v1/addresses/`: Retrieve all addresses for the authenticated user.
- `GET /api/v1/addresses/{address_id}`: Retrieve a specific address.
- `PUT /api/v1/addresses/{address_id}`: Update an address (handles `is_default` logic).
- `DELETE /api/v1/addresses/{address_id}`: Delete an address (handles fallback default logic).

### 3.2 Checkout Preview Endpoint
- `POST /api/v1/checkout/preview`: Generate the checkout preview.

**Request Payload Structure:**
```json
{
  "checkout_type": "buy_now", // or "cart"
  "address_id": 1,
  "product_id": 12, // Required only for buy_now
  "quantity": 2    // Required only for buy_now
}
```

**Expected Response Structure:**
```json
{
  "checkout_type": "buy_now",
  "delivery_address": {
    "address_id": 1,
    "title": "Home",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "address_line_1": "123 Main St",
    "address_line_2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "is_default": true
  },
  "items": [
    {
      "product_id": 12,
      "product_name": "Wireless Mouse",
      "quantity": 2,
      "unit_price": 25.00,
      "line_total": 50.00
    }
  ],
  "financial_summary": {
    "subtotal": 50.00,
    "delivery_fee": 5.00,
    "grand_total": 55.00
  },
  "expected_delivery_date": "June 8, 2026 - June 10, 2026"
}
```
