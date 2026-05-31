# Auth & User Profile Test Cases

## Scenario 1: Customer Registration & Default Role
- **Action**: Call `POST /api/v1/auth/register` with valid email and password.
- **Expected Result**: 
  - Status Code `201 Created`
  - User is successfully inserted into the fake database.
  - The `Customer` role is automatically mapped to this user in `user_roles`.

## Scenario 2: Login and Token Validation
- **Action**: Call `POST /api/v1/auth/login` using the credentials from Scenario 1.
- **Expected Result**:
  - Status Code `200 OK`
  - Returns `access_token` and `refresh_token`.

## Scenario 3: Token Refresh
- **Action**: Call `POST /api/v1/auth/refresh` passing the `refresh_token` from Scenario 2.
- **Expected Result**:
  - Status Code `200 OK`
  - Returns a brand new `access_token`.

## Scenario 4: User Profile Isolation (Data Privacy)
- **Action**: 
  - Create User A and User B. 
  - Login as User A.
  - Call `PUT /api/v1/users/{User_B_ID}/profile`.
- **Expected Result**:
  - Status Code `403 Forbidden`. A user cannot edit another user's profile.
- **Action**:
  - Call `PUT /api/v1/users/{User_A_ID}/profile`.
- **Expected Result**:
  - Status Code `200 OK`. A user can edit their own profile.
