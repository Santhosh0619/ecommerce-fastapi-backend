# Non-Functional Requirements Document (NFR)
**Feature**: Product Ratings & Reviews
**Status**: Draft

## 1. Performance & Scalability
* **Read Heavy Traffic**: Product listing and detail pages are read-heavy. The system shall **not** calculate average ratings on the fly via `GROUP BY` aggregations during page loads. Instead, the `average_rating` and `review_count` shall be cached directly on the `products` table.
* **Indexing**: The `reviews` table shall have optimized database indexes on `(product_id, review_status)` to quickly fetch active reviews for a product page.
* **Pagination**: The `GET /products/{id}/reviews` endpoint must implement pagination (limit/offset or cursor) to prevent memory exhaustion when a product has thousands of reviews.

## 2. Data Integrity
* **Soft Deletions**: Deleting a review shall never execute an SQL `DELETE` command. It shall execute an `UPDATE reviews SET review_status = 'Deleted'` to maintain referential integrity.
* **Concurrency**: The `review_helpful_votes` table composite key acts as a race-condition shield preventing concurrent API requests from logging multiple votes from the same user.
* **Atomic Aggregation**: Updating the product's average rating must be handled in an atomic transaction or via database triggers to prevent drift between the true average and the cached average.

## 3. Security
* **Authorization (IDOR Prevention)**: 
  - Users can only edit/delete reviews where `review.user_id == current_user.id`.
  - Vendors can only reply to reviews where `review.product.vendor_id == current_user.id`.
* **Input Validation**: The `rating` field must strictly validate boundaries (0.5 <= rating <= 5.0) and step increments. String inputs for `review_comment` should be sanitized to prevent XSS if rendered raw by a frontend.
