# Product Requirements Document (PRD)

## 1. Feature Overview
The **Checkout Feature** enables users to review their pending orders prior to final payment processing. It consists of two major sub-systems:
1. **Address Management**: Allows users to manage multiple delivery locations (Home, Office).
2. **Checkout Preview Flow**: Generates a dynamic, non-persistent summary of the proposed order, providing an accurate financial breakdown and expected delivery timeline.

## 2. Target Audience
- **Customers**: Primary users who maintain personal addresses and perform checkouts.
- **Vendors**: Secondary users who may also act as buyers.

## 3. Scope
**In Scope:**
- CRUD operations for user addresses.
- Auto-fallback for default address selection.
- Dynamic calculation of delivery date ranges (processing + transit time).
- Subtotal, flat delivery fee calculation, and grand total generation.
- Support for "Buy Now" (single item bypass) and "Cart Checkout" (aggregated selected cart items).
- Strict validation rules ensuring the user has a valid address, valid cart, and available product stock.

**Out of Scope:**
- Actual payment processing gateways (Stripe, PayPal).
- Permanent Order table record creation (this occurs post-payment).
- Tax calculations.

## 4. Key Workflows
1. **Address Management**: A user can add a "Home" address and mark it as default. If deleted, the system assigns the most recently updated remaining address as the new default.
2. **Buy Now Checkout**: User clicks "Buy Now" on a specific product. The API dynamically calculates the price of that specific item + delivery fee without modifying their saved Cart.
3. **Cart Checkout**: User clicks "Checkout" in their Cart. The API gathers all items where `is_selected=True`, calculates the combined subtotal, adds the delivery fee, and computes expected delivery dates.
