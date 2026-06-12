# Product Requirements Document (PRD): Buy Again Feature

## 1. Overview
The **Buy Again** feature enables customers to seamlessly repurchase items from their past orders. By leveraging the existing cart and checkout logic, the feature minimizes friction, ensuring users can quickly restock items they've purchased before.

## 2. Objectives
- Improve customer retention and increase Customer Lifetime Value (CLTV).
- Simplify the re-ordering process for recurring purchases.
- Maintain data integrity by enforcing current market prices and strict inventory checks.

## 3. Scope
**In-Scope:**
- Re-adding items from a historically **Delivered** order to the current active shopping cart.
- Merging quantities if the item already exists in the cart.
- Validating the product's active status and stock availability.
- Reflecting any price updates that occurred since the original purchase.

**Out-of-Scope:**
- Allowing "Buy Again" on Cancelled, Pending, or Returned orders.
- Directly skipping the Cart and checking out in one click (this feature explicitly deposits items into the cart to reuse existing validation).

## 4. User Stories
- **As a customer**, I want to click a "Buy Again" button on my past delivered order so that I can easily add those items back to my cart.
- **As a customer**, I want to be notified if an item's price has changed so I am aware of what I will be paying.
- **As a customer**, I want to be informed if an item I previously purchased is now out of stock or unavailable.

## 5. Key Business Rules
1. Only the owner of the order can trigger "Buy Again".
2. The order must have a status of exactly `Delivered`.
3. If an item has insufficient stock to meet the originally purchased quantity, it is completely skipped (no partial quantities).
4. Items that are added successfully must reflect the *current* product price, regardless of historical discounts or inflation.
5. If a product already exists in the customer's cart, Buy Again must merge quantities rather than creating duplicate cart entries.
