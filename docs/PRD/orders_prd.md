# Orders - Product Requirements Document (PRD)

## 1. Feature Name
Order Management

## 2. Target Audience
- **Customers:** To track their purchases, view order details, and check expected delivery dates.
- **Vendors:** To view which products were purchased by customers and prepare them for delivery.
- **Admins:** To oversee total system order flow.

## 3. Goals
- Securely persist the user's checkout data (products, prices, delivery address).
- Provide a robust state machine for an Order (Pending -> Confirmed -> Packed -> Out For Delivery -> Delivered).
- Link directly to the Payment Gateway to confirm a purchase.

## 4. Key Features
- **Order Initialization:** Order starts as `Pending` when a user attempts to checkout.
- **Stock Depletion Hook:** Once an order is `Confirmed`, reduce the corresponding product stock.
- **Order Retrieval:** Allow users to retrieve past orders and their status directly from the orders module.
- **Vendor Splitting:** Provide data to notify specific vendors when their products are ordered.
