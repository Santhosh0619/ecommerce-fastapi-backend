# Functional Requirements Document (FRD): Buy Again Feature

## 1. Introduction
This document defines the system behavior for the "Buy Again" feature. It outlines the specific endpoints, validation logic, and exact failure reasons expected by the system.

## 2. API Specifications

### 2.1 Endpoint
`POST /api/v1/orders/{order_id}/buy-again`

**Request:**
- **URL Params**: `order_id` (Integer)
- **Headers**: `Authorization: Bearer <token>`
- **Body**: None

**Response Data Structure (`BuyAgainResponse` Schema):**
```json
{
  "message": "Summary string of the operation",
  "added_items": [
    {
      "product_id": 123,
      "product_name": "Example Product",
      "quantity_added": 2,
      "current_price": 25.00,
      "price_changed": true
    }
  ],
  "unavailable_items": [
    {
      "product_id": 456,
      "product_name": "Old Product",
      "reason": "Product is currently unavailable."
    }
  ],
  "cart_total_items": 4
}
```

## 3. Business Logic & Validation

### 3.1 Order Validation
1. **Not Found**: If the `order_id` does not exist in the database, return:
   - `HTTP 404: Order not found.`
2. **Ownership**: If the order exists but the `user_id` does not match the authenticated user, return:
   - `HTTP 403: Order belongs to another user.`
3. **Order Status**: If the order belongs to the user but the status is not `Delivered`, return:
   - `HTTP 400: Order is not eligible for Buy Again because it is not Delivered.`

### 3.2 Product and Stock Validation
Iterate through all `OrderItem` records tied to the order:
1. **Deleted Product**: If the product query returns `None`, mark as unavailable.
   - Exact Reason: `"Product no longer exists."`
2. **Inactive Product**: If `product.product_status != 'Active'`, mark as unavailable.
   - Exact Reason: `"Product is currently unavailable."`
3. **Insufficient Stock**: If `product.product_stock < order_item.quantity`, skip the item entirely (do not decrement quantity).
   - Exact Reason: `"Insufficient stock."`

### 3.3 Cart Integration
1. **Add to Cart**: For all items passing validation, they are added to the user's active Cart.
2. **Current Pricing**: The item added to the cart MUST use the `product.product_price` (the current database price), NOT the `order_item.product_price` (historical price).
3. **Price Change Flag**: The system must compare historical and current prices. If they differ, flag `price_changed = true` in the response array.
4. **Merge Quantities**: If the cart already has the exact `product_id`, the system must sum the existing quantity and the repurchased quantity, saving a single row in the cart rather than creating duplicates.
5. **All Items Unavailable**: If all items from the original order fail validation (i.e. are unavailable), the system must return:
   - `added_items = []`
   - `unavailable_items` populated with the exact reasons.
   - `message = "No products could be added to the cart."`
6. **Flow Termination**: The backend process ends by returning the response payload. It does not generate a checkout session or order directly.
