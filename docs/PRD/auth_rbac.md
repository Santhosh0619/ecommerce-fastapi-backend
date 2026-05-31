# Product Requirements Document (PRD): Authentication, RBAC, Profiles & Vendors

## 1. Overview
The goal of this feature is to provide a highly secure, scalable authentication system and Role-Based Access Control (RBAC) foundation, extending into user profile management and a vendor application workflow for the e-commerce backend. It follows a Domain-Driven Design approach.

## 2. Target Audience
- **Customers**: Need to register securely, log in, complete their profiles, and optionally apply to become vendors.
- **Vendors**: Approved customers who gain access to manage products.
- **Admins**: Need full control over roles, permissions, users, and reviewing/approving vendor applications.

## 3. Features & Requirements
### 3.1 Authentication & Seeding
- **Registration**: Users can create an account using their Name, Email, Phone Number, and Password. Email must be unique. The "Customer" role is assigned by default.
- **Login/Logout**: Secure JWT-based login with a Redis-backed blocklist for complete session invalidation.
- **Admin Seeding**: The system automatically ensures base roles (Admin, Customer, Vendor) and a Default Admin user exist upon application startup.

### 3.2 Role-Based Access Control (RBAC)
- The system supports mapping users to multiple roles and roles to multiple permissions.
- The system supports assigning explicit permissions directly to users.

### 3.3 User Profiles
- **Profile Completion**: Users can complete their profile (Bio, Address, Profile Picture) after registration. This data is strictly kept in a separate `user_profiles` table (1-to-1 relationship) to keep the authentication table lightweight.

### 3.4 Vendor Applications
- **Application Flow**: Customers can submit an application to upgrade their account to a Vendor.
- **Admin Review**: Admins can view pending applications and approve or reject them.
- **Audit Trail**: The system strictly tracks which admin reviewed the application, at what time, and records any rejection reasons.
- **Automatic Role Assignment**: Upon approval, the system automatically assigns the Vendor role to the user.

### 3.5 Security & Authorization
- **Endpoint Protection**: All administrative endpoints (role/permission management, user overrides, vendor application reviews) are strictly protected and require the `Admin` role.
- **Data Isolation**: A user can only view or edit their own profile, unless accessed by an Admin.
- **Token Exchange**: Users can securely exchange a valid Refresh Token for a new Access Token.

## 4. User Stories
- As a new user, I want to create an account and fill out my profile later.
- As a customer, I want to apply to become a vendor so I can sell my own products.
- As an admin, I want to review pending vendor applications and either approve them (automatically granting the vendor role) or reject them with a reason.
- As an admin, I want the system to automatically set up my initial account so I don't have to manually configure the database on the first run.
