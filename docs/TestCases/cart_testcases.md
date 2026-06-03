# Cart Feature - Test Cases & Report

## Execution Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 10 |
| Passed | 10 |
| Failed | 0 |
| Coverage | 100% on Core Paths & Edge Cases |

---

## Detailed Test Cases

### 1. **Add to Cart & Calculations**
- **Endpoint**: `POST /api/v1/cart/items`
- **Scenario**: 
  - Add a product to the cart with quantity 2.
  - Verify initial calculations (1 item type, subtotal correct).
  - Add the **same** product to the cart again with quantity 3.
  - Verify the quantity correctly increments to 5 instead of creating a duplicate entry.
  - Verify `selected_item_count` remains 1, while `selected_subtotal` reflects the new combined quantity.
- **Expected Result**: 200 OK. Dynamic subtotal correctly multiplies updated quantity by product price.
- **Status**: ✅ Passed

### 2. **Add Inactive Product**
- **Endpoint**: `POST /api/v1/cart/items`
- **Scenario**: Try to add a product that has its status set to `Inactive`.
- **Expected Result**: 400 Bad Request. Error message indicating product is inactive.
- **Status**: ✅ Passed

### 3. **Stock Limits & Soft Warnings**
- **Endpoint**: `POST /api/v1/cart/items`, `PUT /api/v1/products/{id}`, `GET /api/v1/cart/`
- **Scenario**: 
  - Customer adds 5 units of a product to their cart.
  - Out of band, a Vendor updates the product's global stock to 2.
  - Customer fetches their cart via GET request.
  - Customer explicitly tries to `PUT` their item quantity to 3 (which exceeds stock 2).
- **Expected Result**: 
  - GET returns 200 OK but the item has `stock_warning: True`.
  - PUT returns 400 Bad Request, stopping the update because stock is insufficient.
- **Status**: ✅ Passed

### 4. **Product Unavailable Flagging**
- **Endpoint**: `GET /api/v1/cart/`
- **Scenario**: 
  - Customer adds an active product to their cart.
  - Vendor deletes or marks the product as Inactive.
  - Customer fetches their cart.
- **Expected Result**: 200 OK. The item remains in the cart (preventing data loss) but has `product_unavailable: True` attached so the UI can prompt the user to remove it.
- **Status**: ✅ Passed

### 5. **Admin Access Block (RBAC)**
- **Endpoint**: `GET /api/v1/cart/`
- **Scenario**: An Admin user attempts to fetch or use a cart.
- **Expected Result**: 403 Forbidden. Admins are strictly blocked from interacting with cart endpoints.
- **Status**: ✅ Passed

### 6. **Delete Cart Items**
- **Endpoint**: `DELETE /api/v1/cart/items/{id}`, `DELETE /api/v1/cart/`
- **Scenario**: 
  - Customer deletes a specific cart item and verifies it's gone.
  - Customer triggers the global cart wipe endpoint to clear all items.
- **Expected Result**: 204 No Content. After global deletion, fetching the cart returns `items: []` but successfully maintains the cart's structural existence (cart_id remains valid).
- **Status**: ✅ Passed

### 7. **Empty Cart Auto-Creation**
- **Endpoint**: `GET /api/v1/cart/`
- **Scenario**: A user with no pre-existing cart queries the endpoint.
- **Expected Result**: 200 OK. The system seamlessly auto-generates a new `Cart` record and returns it with an empty items array.
- **Status**: ✅ Passed

### 8. **Add Nonexistent Product**
- **Endpoint**: `POST /api/v1/cart/items`
- **Scenario**: Try to add a product ID (`99999`) that does not exist in the database.
- **Expected Result**: 404 Not Found.
- **Status**: ✅ Passed

### 9. **Update Nonexistent Cart Item**
- **Endpoint**: `PUT /api/v1/cart/items/{id}`
- **Scenario**: Attempt to modify the quantity or selection state of an item ID (`99999`) that is not in the cart.
- **Expected Result**: 404 Not Found.
- **Status**: ✅ Passed

### 10. **Multiple Products & Subtotal Toggle**
- **Endpoint**: `PUT /api/v1/cart/items/{id}`
- **Scenario**: 
  - Add two separate, distinct products (P1 and P2) to the cart.
  - Verify total `selected_item_count` is 2, and `selected_subtotal` combines both correctly.
  - Update P2 to be `is_selected: False`.
  - Verify `selected_item_count` drops to 1, and `selected_subtotal` now *only* represents the sum of P1.
- **Expected Result**: 200 OK. The business logic perfectly dynamically ignores unselected items when computing counts and totals.
- **Status**: ✅ Passed
