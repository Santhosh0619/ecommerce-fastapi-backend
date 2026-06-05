# Non-Functional Requirements Document (NFR)

## 1. Security
- **Data Isolation**: All operations (Address fetching, updating, checkout processing) must be strictly isolated to the authenticated `user_id`. Attempting to pass an `address_id` belonging to another user must fail securely (`404 Not Found` or `403 Forbidden`).
- **RBAC**: Admins must be prohibited from using the Checkout and Address features. Only Customers and Vendors are permitted.

## 2. Performance
- **Dynamic Speed**: Since the checkout preview relies heavily on relational joins (Users -> Addresses, Users -> Carts -> Products), queries must utilize `selectinload` appropriately to avoid N+1 query performance degradation.
- **Stateless Checkout**: By keeping the checkout preview entirely dynamic and completely stateless, we prevent database bloat. The database won't fill up with "abandoned checkouts".

## 3. Reliability & Data Integrity
- **Real-Time Accuracy**: Pricing and stock availability must be fetched instantly from the source of truth (`products` table) at the exact millisecond the checkout is requested. Caching must be bypassed for this specific operation to prevent overselling.

## 4. Maintainability
- **Modularity**: The Address management logic must be fully uncoupled from the Checkout logic, residing in separate sub-modules (`app/features/addresses/` and `app/features/checkout/`).
- **Configurability**: The base Delivery Fee and Transit Time variables should be structured as constants or configuration variables so they can be easily manipulated without tearing down business logic.
