# Cart Feature: Functional Requirements Document (FRD)

## 1. Database Architecture

### `cart` Table
- **cart_id**: Primary Key
- **user_id**: Foreign Key to `users.user_id` (Unique - One user has exactly one cart)
- **created_at**: Timestamp
- **updated_at**: Timestamp

### `cart_items` Table
- **cart_item_id**: Primary Key
- **cart_id**: Foreign Key to `cart.cart_id`
- **product_id**: Foreign Key to `products.product_id`
- **quantity**: Integer
- **is_selected**: Boolean (Defaults to `True`)
- **created_at**: Timestamp
- **updated_at**: Timestamp
- **Constraints**: Unique combination of `(cart_id, product_id)`.

## 2. Business Rules & Logic

1. **Role-Based Access**:
   - `Customer` and `Vendor` roles can access their cart.
   - `Admin` roles attempting to use cart endpoints will receive a `403 Forbidden`.
   - Users can only view and modify their own carts.

2. **Add to Cart Rules**:
   - Product must have `product_status == "Active"`. (Inactive/Archived products are rejected).
   - Provided quantity must be `> 0`.
   - Provided quantity must be `<= product.product_stock`.
   - If the user has no cart, a `cart` row is automatically created.
   - If the product is already in the cart, the quantity is *increased* instead of failing the unique constraint. The new total quantity is validated against stock limits.

3. **Dynamic Calculations (On Retrieval)**:
   - `selected_item_count`: The count of distinct cart items where `is_selected = True` (e.g., Phone x 2 and Laptop x 1 = 2 items).
   - `selected_subtotal`: The sum of `(cart_item.quantity * product.product_price)` where `is_selected = True`.
   - **Stock Warning**: If `cart_item.quantity > product.product_stock`, attach a `stock_warning = True` flag to that specific item in the response payload. The quantity is *not* auto-modified in the database.
   - **Product Unavailability**: If the related product's status is no longer 'Active', attach a `product_unavailable = True` flag to the item response.

## 3. API Endpoints

1. **`GET /api/v1/cart/`**
   - **Response**: The cart, a list of cart items (joined with product details and primary image), `selected_item_count`, and `selected_subtotal`.

2. **`POST /api/v1/cart/items`**
   - **Payload**: `product_id`, `quantity`.
   - **Action**: Adds the product or increments existing quantity. 

3. **`PUT /api/v1/cart/items/{cart_item_id}`**
   - **Payload**: `quantity` (optional), `is_selected` (optional).
   - **Action**: Updates item state. Verifies stock bounds if `quantity` is being increased.

4. **`DELETE /api/v1/cart/items/{cart_item_id}`**
   - **Action**: Removes the specific item from the cart.

5. **`DELETE /api/v1/cart/`**
   - **Action**: Removes all `cart_items` from the cart (emptying it completely). The `cart` record itself is kept in the database to align with the One User → One Cart design.
