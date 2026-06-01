# Categories Product Requirements Document (PRD)

## 1. Overview
The Categories feature provides the foundational structure for organizing products within the e-commerce platform. It enables grouping similar products and allows for hierarchical parent-child relationships (e.g., Electronics → Mobile → Vivo), making product discovery intuitive for users.

## 2. Goals
- Group related products for easier navigation and filtering.
- Support infinitely nested subcategories (hierarchical data).
- Ensure data consistency (no circular references, no case-insensitive duplicate siblings).
- Secure operations through role-based access control (RBAC).

## 3. Key Features
1. **Hierarchical Categorization**: Categories can have parents and children.
2. **Duplicate Prevention**: A single parent cannot have two identically named child categories (case-insensitive).
3. **Safe Deletion**: A category cannot be deleted if it has subcategories.
4. **RBAC**: 
   - Customers, Vendors, and Admins can view the category tree.
   - Only Admins can create, update, or delete categories.

## 4. Out of Scope
- Linking products to categories (will be handled in the subsequent Product feature).
- Bulk import/export of categories.
