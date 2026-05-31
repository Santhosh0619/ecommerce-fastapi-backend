# Functional Requirements Document (FRD): Auth, RBAC, Profiles & Vendors

## 1. Authentication & RBAC
*(Previously implemented)*
- **Registration (`/auth/register`)**: Creates user and assigns default `Customer` role.
- **Login (`/auth/login`)**: Returns Access and Refresh JWTs.
- **Logout (`/auth/logout`)**: Blocklists token in Redis.

## 2. Token Refresh (`/auth/refresh`)
- **Inputs**: `refresh_token` in body.
- **Processing**:
  - Validates the Refresh Token signature and type.
  - Ensures the user exists.
- **Outputs**: HTTP 200 OK with new `access_token`.

## 3. Authorization Dependencies
- `get_current_user`: Extracts the user from the Bearer JWT.
- `RequireRole(allowed_roles)`: Requires `get_current_user` and checks `user_roles` mapping. Throws HTTP 403 if invalid.
- `require_self_or_admin`: Checks if `current_user.user_id == path_id` or `current_user` has `Admin` role. Throws HTTP 403 if invalid.

## 4. Default Admin Seeding
- **Event**: Application Startup (`@asynccontextmanager` Lifespan).
- **Processing**:
  - Automatically inserts `Admin`, `Customer`, and `Vendor` into the `roles` table if they do not exist.
  - Reads `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` from `.env`.
  - Creates the superuser in the `users` table and links them to the `Admin` role if the user does not exist.

## 3. User Profiles (`/users/{id}/profile`)
- **Table**: `user_profiles` (1-to-1 linked to `users`).
- **Endpoints**:
  - `PUT /users/{id}/profile`: Create or update profile details (full_name, bio, address, profile_picture_url).
  - `GET /users/{id}/profile`: Fetch the user's completed profile.
- **Processing**:
  - Ensure the user exists before updating. Upsert the profile record based on the `user_id`.

## 4. Vendor Applications (`/vendors/applications`)
- **Table**: `vendor_applications`.
- **Endpoints**:
  - `POST /vendors/apply`: 
    - **Inputs**: `store_name`, `business_details`.
    - **Processing**: Creates a pending application tied to the current user's ID.
  - `GET /vendors/applications`: 
    - **Processing**: Fetches all applications (Admin only).
  - `PUT /vendors/applications/{id}/status`:
    - **Inputs**: `status` (approved/rejected), `rejection_reason` (optional).
    - **Processing**: 
      1. Updates application status.
      2. Records the current Admin's `user_id` into the `reviewed_by` column.
      3. Sets `reviewed_at` to the current timestamp.
      4. If `approved`, automatically communicates with the `roles` module to assign the `Vendor` role to the applicant.
- **Outputs**: Standard HTTP JSON responses (200 OK, 201 Created) with updated application objects.
