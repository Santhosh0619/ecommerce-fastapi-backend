# Review Feature - Test Cases

This document outlines the test cases for the Product Ratings and Reviews feature. 
All of these scenarios are also covered by automated tests in `tests/test_reviews.py`.

## 1. Review Creation
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-01 | Create review for a delivered product | Success (200 OK), review is created with Published status. |
| REV-02 | Create review for a product not ordered | Failure (403 Forbidden), error: "You can only review products you have purchased and received." |
| REV-03 | Create review for a product ordered but not delivered | Failure (403 Forbidden), error: "You can only review products you have purchased and received." |
| REV-04 | Create review with rating < 0.5 or > 5.0 | Failure (422 Unprocessable Entity), rating validation error. |

## 2. Duplicate Reviews
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-05 | Create a second review for the same product by the same user | Failure (400 Bad Request), error: "You have already reviewed this product." |

## 3. Update Review
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-06 | Update own review (rating and comment) | Success (200 OK), `is_edited` flag is set to True. |
| REV-07 | Update someone else's review | Failure (403 Forbidden). |

## 4. Delete / Soft Delete Review
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-08 | Delete own review | Success (200 OK), review status changes to Deleted (soft delete). |
| REV-09 | Delete someone else's review | Failure (403 Forbidden). |
| REV-10 | Admin deletes any review | Success (200 OK), review status changes to Deleted. |

## 5. Vendor Replies
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-11 | Vendor replies to a review on their own product | Success (200 OK), vendor reply and timestamp are saved. |
| REV-12 | Vendor replies to a review on another vendor's product | Failure (403 Forbidden), error indicating they don't own the product. |

## 6. Helpful Votes
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-13 | User upvotes a review | Success (200 OK), `helpful_votes` increments, `voted` = True. |
| REV-14 | User upvotes the same review again | Success (200 OK), vote is removed (toggled), `helpful_votes` decrements back to 0, `voted` = False. |

## 7. Admin Moderation
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-15 | Admin changes review status to Hidden | Success (200 OK), review no longer appears in public product review lists. |
| REV-16 | Admin changes review status back to Published | Success (200 OK), review reappears in public lists. |

## 8. Product Aggregations
| Test Case ID | Description | Expected Result |
|---|---|---|
| REV-17 | Fetch product details after adding a 5-star and 4-star review | Product's `average_rating` is 4.5, `review_count` is 2. |
