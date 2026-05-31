# Vendors Test Cases

## Scenario 1: Customer Applies to be a Vendor
- **Action**: Login as a Customer. Call `POST /api/v1/vendors/apply` with store details.
- **Expected Result**: 
  - Status Code `201 Created`
  - Application created with status `pending`. No manual `user_id` is required in the body because it is extracted from the JWT.

## Scenario 2: Customer tries to Review Applications
- **Action**: Customer calls `GET /api/v1/vendors/applications`.
- **Expected Result**:
  - Status Code `403 Forbidden`. Only Admins can view applications.

## Scenario 3: Admin Approves Vendor Application
- **Action**: Admin calls `PUT /api/v1/vendors/applications/{app_id}/status` with `status: "approved"`.
- **Expected Result**:
  - Status Code `200 OK`
  - Application status is updated to `approved`.
  - `reviewed_by` is set to the Admin's ID automatically.
  - The "Vendor" role is automatically assigned to the applying Customer.
