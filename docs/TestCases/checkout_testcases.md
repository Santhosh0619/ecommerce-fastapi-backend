# Checkout & Address Management Feature - Test Cases

This document outlines the test cases covering the Checkout feature and Address management system, validating all the core business logic, default address management, and checkout operations based on the Feature Requirements Document (FRD).

## Address Management

| Test Case ID | Scenario | Pre-Conditions | Test Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-ADDR-01** | First Address Auto-Default | User has no existing addresses. | 1. User submits a POST request to `/api/v1/addresses/` with `is_default=False`. | The created address automatically overrides the payload and is set as `is_default=True`. | Passed |
| **TC-ADDR-02** | Update Default Unsets Others | User has an existing default address. | 1. User submits a POST request to create a second address.<br>2. User submits a PUT request on the second address with `is_default=True`. | The second address becomes the default, and the first address is automatically updated to `is_default=False`. | Passed |
| **TC-ADDR-03** | Auto-Fallback on Delete Default | User has a default address (A) and a non-default address (B). | 1. User submits a DELETE request for address A. | Address A is deleted. Address B is automatically promoted to the new default (`is_default=True`). | Passed |
| **TC-ADDR-04** | Invalid Phone & Postal Code Block | User tries to create an address. | 1. User submits a POST request with short `postal_code` and malformed `phone_number`. | The API blocks the request due to Pydantic validation and returns a `422 Unprocessable Entity` error. | Passed |
| **TC-ADDR-05** | Unauthorized Address Access | User A attempts to view an address. | 1. User A submits a GET request with User B's `address_id` (or a non-existent ID). | The API blocks the request and returns a `404 Not Found` error. | Passed |
| **TC-ADDR-06** | Block Unsetting Default Address | User has an existing default address. | 1. User submits a PUT request to update the address, setting `is_default=False`. | The API blocks the request and returns a `400 Bad Request` with message: "Cannot unset the default address directly. Please set another address as default instead." | Passed |

---

## Checkout Feature

| Test Case ID | Scenario | Pre-Conditions | Test Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-CHK-01** | "Buy Now" Checkout Success | User selects a valid product. | 1. User submits a POST request to `/api/v1/checkout/preview` with `checkout_type="buy_now"`, a valid `address_id`, `product_id`, and `quantity=1`. | Returns a successful summary with the product subtotal + delivery fee correctly calculated. Expected delivery dates calculate business days accurately. | Passed |
| **TC-CHK-02** | "Buy Now" Missing Product Data | User selects "Buy Now". | 1. User submits a POST request with `checkout_type="buy_now"` but omits `product_id` and `quantity`. | The API blocks the request with a `422 Unprocessable Entity` or `400 Bad Request` validation error. | Passed |
| **TC-CHK-03** | "Cart" Checkout Success | User has selected items in the cart. | 1. User submits a POST request to `/api/v1/checkout/preview` with `checkout_type="cart"` and a valid `address_id`. | Returns a successful summary aggregating the line totals ONLY for cart items where `is_selected=True`, plus the delivery fee. | Passed |
| **TC-CHK-04** | "Cart" Rejects Extra Fields | User selects "Cart" checkout. | 1. User submits a POST request with `checkout_type="cart"` but incorrectly includes `product_id` or `quantity`. | The API actively blocks the request, enforcing polymorphic strictness, and returns a `422` or `400` validation error. | Passed |
| **TC-CHK-05** | Invalid Address Block | User attempts to checkout. | 1. User submits a POST request with an invalid `address_id` (does not belong to user, or does not exist). | The system instantly blocks the preview and returns a `400 Bad Request` with message: "A valid delivery address is required for checkout". | Passed |
| **TC-CHK-06** | Empty Cart Block | User has no items (or no selected items) in cart. | 1. User submits a POST request with `checkout_type="cart"`. | The API blocks the request and returns a `400 Bad Request` with message: "No items selected in cart for checkout" or "Cart is empty". | Passed |
| **TC-CHK-07** | Insufficient Stock Block | User attempts "Buy Now". | 1. User requests a quantity greater than the available `product_stock`. | The API blocks the transaction and returns a `400 Bad Request` indicating "insufficient stock" and listing the requested vs available amounts. | Passed |
| **TC-CHK-08** | Inactive/Archived Product Block | User attempts "Buy Now" for a deleted product. | 1. User requests a `product_id` whose status has transitioned to `Inactive` or `Archived`. | The API instantly blocks the transaction and returns a `400 Bad Request` stating the product is inactive and cannot be purchased. | Passed |
