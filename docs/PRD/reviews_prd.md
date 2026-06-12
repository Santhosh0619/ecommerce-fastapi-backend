# Product Requirements Document (PRD)
**Feature**: Product Ratings & Reviews
**Status**: Draft

## 1. Overview
The Product Ratings & Reviews feature allows customers to rate and leave feedback on products they have successfully purchased and received. This feature aims to build trust in the platform, help users make informed purchasing decisions, and allow vendors to engage with customer feedback.

## 2. Target Audience
* **Customers**: Can read reviews, write reviews for purchased products, edit their reviews, and upvote helpful reviews.
* **Vendors**: Can read reviews on their products and reply to customer feedback (once per review).
* **Admins**: Can moderate the platform by hiding or deleting reviews that violate community guidelines.

## 3. User Stories
* **As a Customer**, I want to see the average rating and reviews of a product so that I know its quality before buying.
* **As a Customer**, I want to leave a rating from 0.5 to 5.0 in increments of 0.5 and comment on a product I received so that I can share my experience.
* **As a Customer**, I want to mark another user's review as "Helpful" so that the best reviews bubble up to the top.
* **As a Vendor**, I want to reply to a review left on my product so that I can address concerns or thank the customer.
* **As an Admin**, I want to be able to hide offensive reviews so that the platform remains professional.

## 4. Key Constraints
* **Verified Purchase Only**: A user cannot review a product unless they have an order containing that product with the status `Delivered`.
* **One Review Per User**: A user can only write one review per product, regardless of how many times they purchased it.
* **Soft Deletes**: Reviews are never hard-deleted from the database to preserve historical integrity.
