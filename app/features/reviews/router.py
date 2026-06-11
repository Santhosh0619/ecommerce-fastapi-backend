from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.features.auth.dependencies import get_current_user, RequireRole
from app.features.users.models import User
from app.features.reviews import schemas, services

router = APIRouter(tags=["Reviews"])

# Dependency instances
allow_customer = RequireRole(["Customer"])
allow_vendor = RequireRole(["Vendor"])
allow_admin = RequireRole(["Admin"])

@router.post("/reviews/", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_in: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer)
):
    """
    Submit a product rating & review.
    Requires that the customer has bought the product and the order status is 'Delivered'.
    """
    return await services.create_review(db, review_in, current_user)

@router.put("/reviews/{review_id}", response_model=schemas.ReviewResponse)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer)
):
    """
    Edit a review. Sets is_edited to True. Only review owner can edit.
    """
    return await services.update_review(db, review_id, review_update, current_user)

@router.delete("/reviews/{review_id}", response_model=schemas.ReviewResponse)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a review (changes status to Deleted). 
    Allowed for the review owner or Admin.
    """
    return await services.delete_review(db, review_id, current_user)

@router.post("/reviews/{review_id}/helpful")
async def toggle_helpful_vote(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upvote a review as helpful, or toggle to remove the vote.
    Allowed for any authenticated user.
    """
    voted = await services.toggle_helpful_vote(db, review_id, current_user)
    return {"voted": voted, "message": "Helpful vote added" if voted else "Helpful vote removed"}

@router.get("/products/{product_id}/reviews", response_model=List[schemas.ReviewResponse])
async def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Publicly retrieve Published reviews for a product with pagination.
    """
    return await services.get_product_reviews(db, product_id, skip, limit)

@router.post("/vendors/reviews/{review_id}/reply", response_model=schemas.ReviewResponse)
async def add_vendor_reply(
    review_id: int,
    reply_in: schemas.VendorReplyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_vendor)
):
    """
    Vendor reply to a product review.
    The vendor must own the product related to this review.
    Only one reply is allowed per review (subsequent replies will overwrite the existing one).
    """
    return await services.add_vendor_reply(db, review_id, reply_in, current_user)

@router.put("/admin/reviews/{review_id}/status", response_model=schemas.ReviewResponse)
async def moderate_review_status(
    review_id: int,
    status_update: schemas.AdminStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """
    Admin moderates a review by setting its status (Published, Hidden, Deleted).
    """
    return await services.moderate_review_status(db, review_id, status_update)
