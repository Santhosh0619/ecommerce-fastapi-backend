# Cart Feature: Product Requirements Document (PRD)

## 1. Objective
The goal of the Cart feature is to provide a seamless and intuitive shopping cart experience where users can add, manage, and prepare products for final checkout. It acts as the bridge between product discovery and purchasing.

## 2. Target Audience
- **Customers**: Primary users who browse products and add them to their cart.
- **Vendors**: Can act as shoppers and use the cart feature.
- **Admins**: Excluded from cart functionality as they are platform managers.

## 3. Core Features & Capabilities
1. **Add to Cart**: Users can seamlessly add any Active product to their cart. If they do not already have a cart, one is automatically created behind the scenes.
2. **Duplicate Handling**: Adding the same product again increases the quantity rather than creating duplicate line items.
3. **Quantity Management**: Users can explicitly update the quantity of items in their cart.
4. **Checkout Preparation**: Users can select or deselect specific items (`is_selected`), preparing exactly what they want to purchase in the current session.
5. **Dynamic Subtotals**: The cart automatically calculates the `selected_item_count` (the count of distinct selected cart items, not the sum of their quantities) and the total financial `selected_subtotal` in real-time.
6. **Stock Awareness**: If the actual product stock drops below the quantity a user has in their cart, the system flags the item with a `stock_warning` so the UI can notify the user before they attempt to checkout.
7. **Product Unavailability**: If a product in the cart becomes Inactive or Archived, it remains visible in the cart but is flagged as `product_unavailable = True` so the user understands why it cannot be purchased.

## 4. Out of Scope
- **Checkout & Payments**: Processing payments, reducing stock, and generating final orders are out of scope for this feature.
- **Guest Carts**: Carts require an authenticated user session. Unauthenticated guest carts are out of scope.
