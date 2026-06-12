# Functional Requirements Document (FRD)
**Feature**: Product Ratings & Reviews
**Status**: Draft

## 1. Core Review Management (Customers)
* **Creation**: The system shall allow a customer to create a review with a rating (0.5 to 5.0 in increments of 0.5) and an optional text comment.
* **Validation**: The backend API shall verify that the requesting `user_id` has a corresponding `order_id` with `order_status = 'Delivered'` containing the requested `product_id`.
* **Idempotency**: The system shall reject duplicate review creations for the same `product_id` by the same `user_id`.
* **Modification**: Customers shall be able to edit their own reviews. Upon editing, the `is_edited` boolean flag shall be permanently set to `True`.
* **Deletion**: Customers shall be able to delete their own reviews. This will trigger a "soft delete" (changing `review_status` to `Deleted`).

## 2. Vendor Interaction
* **Reply Creation**: Vendors shall be able to add text to the `vendor_reply` field of a review attached to their products.
* **Restriction**: Vendors are limited to one reply per review. The vendor can edit their existing reply, but cannot create a thread of multiple replies.

## 3. Helpful Votes System
* **Voting**: Any authenticated user can upvote a review as "Helpful".
* **Abuse Prevention**: The system shall track votes in a `review_helpful_votes` table using a composite primary key (`review_id`, `user_id`) to mathematically prevent duplicate voting.
* **Toggling**: Sending the vote request a second time shall remove the user's vote.

## 4. Admin Moderation
* **Status Controls**: The system shall default all new reviews to `Published`. 
* **Overrides**: Admins shall have access to an endpoint to change a review's status to `Hidden` or `Deleted` based on community guidelines.

## 5. Automated Aggregation
* **Triggering**: Every time a review is successfully inserted, updated (rating changed), or deleted, the system shall recalculate the `average_rating` and `review_count` on the parent `products` row.
* **Scope**:
  - `average_rating` shall only be calculated from `Published` reviews.
  - `review_count` shall only count `Published` reviews.
  - `Hidden` and `Deleted` reviews must not affect product ratings or review counts.
