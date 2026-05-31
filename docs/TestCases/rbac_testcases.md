# Role-Based Access Control (RBAC) Test Cases

## Scenario 1: Standard Customer trying to access Admin Endpoints
- **Action**: Login as a standard Customer. Send a `GET` request to `/api/v1/roles/`.
- **Expected Result**: 
  - Status Code `403 Forbidden`
  - The `RequireRole(["Admin"])` dependency should intercept and block the request.

## Scenario 2: Admin accessing Admin Endpoints
- **Action**: Login as the System Admin (from the startup seeder). Send a `GET` request to `/api/v1/roles/`.
- **Expected Result**:
  - Status Code `200 OK`
  - The dependency verifies the "Admin" role in `user_roles` and allows the request.

## Scenario 3: Admin assigning roles to a user
- **Action**: Admin sends `POST /api/v1/users/{customer_id}/roles` with `{ "role_id": 2 }` (Vendor role).
- **Expected Result**:
  - Status Code `201 Created`
  - The user successfully receives the Vendor role.
