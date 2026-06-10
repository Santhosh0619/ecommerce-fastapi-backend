# Order Management Test Cases

## Scenario 1: Order Creation (Buy Now)
- **Action**: Call `POST /api/v1/orders/` with `checkout_type = buy_now`, passing a single `product_id` and `quantity`.
- **Expected Result**: 
  - Status Code `201 Created`
  - Order is successfully created with status `Pending`.
  - Payment status is `Pending`.
  - Total amount is correctly calculated based on product price * quantity.

## Scenario 2: Order Creation (Cart)
- **Action**: Add multiple items to the cart, then call `POST /api/v1/orders/` with `checkout_type = cart`.
- **Expected Result**: 
  - Status Code `201 Created`
  - Order is created containing all items from the cart.
  - Cart is subsequently emptied.

## Scenario 3: Order Idempotency
- **Action**: Call `POST /api/v1/orders/` twice with the exact same `Idempotency-Key` header.
- **Expected Result**:
  - The second request is intercepted by the idempotency lock.
  - Returns the exact same `order_id` and data as the first request without creating a duplicate order.

## Scenario 4: User Order Isolation (Data Privacy)
- **Action**: Login as User B and attempt to call `GET /api/v1/orders/{User_A_Order_ID}`.
- **Expected Result**:
  - Status Code `404 Not Found` (Masking the existence of the order for security).

## Scenario 5: View Order History
- **Action**: Call `GET /api/v1/orders/` as an authenticated user.
- **Expected Result**:
  - Returns a list of all orders belonging ONLY to the logged-in user.
