# Categories Test Cases

This document outlines the test scenarios automated in `tests/test_categories.py`.

## Scenario 1: Create Category Hierarchy
- **Objective**: Verify that root categories and subcategories can be created.
- **Pre-condition**: Logged in as Admin.
- **Steps**:
  1. POST `/api/v1/categories/` with name "Electronics". (Verify 201, gets `root_id`)
  2. POST `/api/v1/categories/` with name "Mobile" and `parent_category_id` = `root_id`. (Verify 201)
  3. POST `/api/v1/categories/` with name "Smartphones" and `parent_category_id` = `child_id`. (Verify 201)
- **Expected Result**: Hierarchy successfully created.

## Scenario 2: Prevent Duplicate Siblings (Case-Insensitive)
- **Objective**: Ensure sibling categories under the same parent cannot have identical or case-insensitive duplicate names.
- **Pre-condition**: Logged in as Admin. Root category "Fashion" exists. Subcategory "Shirts" exists.
- **Steps**:
  1. POST `/api/v1/categories/` with name "Shirts" under "Fashion". (Verify 409 Conflict)
  2. POST `/api/v1/categories/` with name "sHiRts" under "Fashion". (Verify 409 Conflict)
  3. POST `/api/v1/categories/` with name "Shirts" under a new root "Sports". (Verify 201 Created)
- **Expected Result**: Duplicates prevented, case-insensitive duplicates prevented, but same names under different parents allowed.

## Scenario 3: Prevent Circular Parent Assignment
- **Objective**: Verify that a category cannot be assigned itself or its descendant as a parent.
- **Pre-condition**: Logged in as Admin. Root "Home" and subcategory "Furniture" exist.
- **Steps**:
  1. PUT `/api/v1/categories/{root_id}` with `parent_category_id` = `root_id`. (Verify 400 Bad Request)
  2. PUT `/api/v1/categories/{root_id}` with `parent_category_id` = `child_id`. (Verify 400 Bad Request)
- **Expected Result**: Circular dependencies are blocked.

## Scenario 4: Prevent Deletion with Children
- **Objective**: Ensure a parent category cannot be deleted if it has subcategories.
- **Pre-condition**: Logged in as Admin. Root "Groceries" and subcategory "Fruits" exist.
- **Steps**:
  1. DELETE `/api/v1/categories/{root_id}`.
- **Expected Result**: 400 Bad Request (deletion blocked).

## Scenario 5: Role-Based Access Control (RBAC)
- **Objective**: Verify that only Admins can mutate categories, but all users can read them.
- **Pre-condition**: Active tokens for Customer, Vendor, and Admin.
- **Steps**:
  1. **Customer**: GET `/api/v1/categories/` (Verify 200). POST/PUT/DELETE (Verify 403 Forbidden).
  2. **Vendor**: GET `/api/v1/categories/` (Verify 200). POST/PUT/DELETE (Verify 403 Forbidden).
  3. **Admin**: GET `/api/v1/categories/` (Verify 200). POST `/api/v1/categories/` (Verify 201). PUT `/api/v1/categories/{id}` (Verify 200). DELETE `/api/v1/categories/{id}` (Verify 200).
- **Expected Result**: Strict RBAC enforcement correctly applied across all roles.
