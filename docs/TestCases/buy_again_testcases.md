# Buy Again Feature - QA Test Cases

## Overview
This document outlines the test cases for the "Buy Again" feature. It covers positive scenarios, negative scenarios, error handling, and transaction integrity.

## Pre-requisites
- A registered Customer account.
- Active products available in the database.
- A dummy delivery address.

---

## Test Scenario 1: Successful Repurchase of a Delivered Order
**Objective**: Verify that a customer can successfully use the Buy Again feature for an order that is marked as 'Delivered'.
**Pre-conditions**: Customer has an existing order with status 'Delivered'.
**Steps**:
1. Log in as the Customer.
2. Ensure the shopping cart is currently empty.
3. Call `POST /api/v1/orders/{order_id}/buy-again`.
**Expected Result**:
- API returns `200 OK`.
- Response contains `cart_total_items` matching the quantity of items in the original order.
- Response contains the products in the `added_items` array.
- `unavailable_items` array is empty.
- Fetching the Cart (`GET /api/v1/cart`) confirms the items are present.

---

## Test Scenario 2: Repurchase with Existing Cart Items (Quantity Merging)
**Objective**: Verify that if the user already has items in their cart, Buy Again merges quantities instead of creating duplicate cart rows.
**Pre-conditions**: Customer has an existing order with status 'Delivered' containing "Product A" (Quantity 1).
**Steps**:
1. Log in as the Customer.
2. Add 2 units of "Product A" to the cart manually.
3. Call `POST /api/v1/orders/{order_id}/buy-again` for the delivered order.
**Expected Result**:
- API returns `200 OK`.
- The cart should now have exactly ONE row for "Product A" with a total quantity of 3.

---

## Test Scenario 3: Repurchase an Order that is NOT Delivered
**Objective**: Verify that orders in 'Pending', 'Processing', or 'Cancelled' status cannot be repurchased.
**Pre-conditions**: Customer has an existing order with status 'Pending'.
**Steps**:
1. Call `POST /api/v1/orders/{order_id}/buy-again`.
**Expected Result**:
- API returns `400 Bad Request`.
- Error detail specifies: "Order is not eligible for Buy Again because it is not Delivered."

---

## Test Scenario 4: Repurchase an Order with Inactive Products
**Objective**: Verify that if a product from the original order is no longer active, it is skipped and marked as unavailable.
**Pre-conditions**: Customer has a delivered order with "Product A". "Product A" is now marked as 'Archived' in the database.
**Steps**:
1. Call `POST /api/v1/orders/{order_id}/buy-again`.
**Expected Result**:
- API returns `200 OK`.
- `added_items` array is empty.
- `unavailable_items` array contains "Product A" with reason: "Product is currently unavailable."
- Message states: "No products could be added to the cart."

---

## Test Scenario 5: Repurchase an Order with Deleted Products
**Objective**: Verify that if a product no longer exists in the database, it is properly caught.
**Pre-conditions**: Customer has a delivered order with "Product B". "Product B" has been completely deleted from the database.
**Steps**:
1. Call `POST /api/v1/orders/{order_id}/buy-again`.
**Expected Result**:
- API returns `200 OK`.
- `added_items` array is empty.
- `unavailable_items` array contains the product ID with reason: "Product no longer exists."

---

## Test Scenario 6: Repurchase an Order Exceeding Stock
**Objective**: Verify that if adding the order items to the cart exceeds the available product stock, it is handled gracefully.
**Pre-conditions**: Customer has a delivered order with "Product C" (Quantity: 5). The database stock for "Product C" is currently 2.
**Steps**:
1. Call `POST /api/v1/orders/{order_id}/buy-again`.
**Expected Result**:
- API returns `200 OK`.
- `added_items` array is empty.
- `unavailable_items` array contains "Product C" with reason: "Insufficient stock."

---

## Test Scenario 7: Unauthorized Access to Another User's Order
**Objective**: Ensure users cannot repurchase orders belonging to someone else.
**Pre-conditions**: Customer A has a delivered order. Customer B is logged in.
**Steps**:
1. Customer B calls `POST /api/v1/orders/{customer_a_order_id}/buy-again`.
**Expected Result**:
- API returns `403 Forbidden`.
- Error detail specifies: "Order belongs to another user."

---

## Test Scenario 8: Non-Existent Order
**Objective**: Handle invalid order IDs.
**Pre-conditions**: Logged in as a Customer.
**Steps**:
1. Call `POST /api/v1/orders/999999/buy-again`.
**Expected Result**:
- API returns `404 Not Found`.
- Error detail specifies: "Order not found."
