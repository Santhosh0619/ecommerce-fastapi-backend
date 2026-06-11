from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.features.reviews import crud, schemas
from app.features.reviews.models import Review, ReviewStatus
from app.features.users.models import User
from app.features.roles import crud as role_crud

def make_review_response(review: Review) -> schemas.ReviewResponse:
    """
    Helper to convert Review ORM object with joined user relationship to ReviewResponse.
    """
    res = schemas.ReviewResponse.model_validate(review)
    if review.user:
        res.user_name = review.user.user_name
    return res

async def create_review(db: AsyncSession, review_in: schemas.ReviewCreate, current_user: User) -> schemas.ReviewResponse:
    user_id: int = getattr(current_user, 'user_id')
    # 1. Verify delivered order contains this product
    order_id = await crud.verify_delivered_order_contains_product(
        db, 
        user_id=user_id, 
        product_id=review_in.product_id, 
        order_id=review_in.order_id
    )
    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only review products you have purchased and received (order status must be Delivered)."
        )
    
    # 2. Call CRUD creation
    db_review = await crud.create_review(db, review_in, user_id=user_id, order_id=order_id)
    return make_review_response(db_review)

async def update_review(db: AsyncSession, review_id: int, review_update: schemas.ReviewUpdate, current_user: User) -> schemas.ReviewResponse:
    user_id: int = getattr(current_user, 'user_id')
    db_review = await crud.get_review_by_id(db, review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
        
    if db_review.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own reviews."
        )
        
    if db_review.review_status == ReviewStatus.Deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a deleted review."
        )
        
    updated_review = await crud.update_review(db, db_review, review_update)
    return make_review_response(updated_review)

async def delete_review(db: AsyncSession, review_id: int, current_user: User) -> schemas.ReviewResponse:
    user_id: int = getattr(current_user, 'user_id')
    db_review = await crud.get_review_by_id(db, review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
        
    user_roles = await role_crud.get_user_roles_names(db, user_id)
    is_admin = "Admin" in user_roles
    
    if db_review.user_id != user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews."
        )
        
    deleted_review = await crud.delete_review_soft(db, db_review)
    return make_review_response(deleted_review)

async def toggle_helpful_vote(db: AsyncSession, review_id: int, current_user: User) -> bool:
    user_id: int = getattr(current_user, 'user_id')
    # Check if review exists and is published
    db_review = await crud.get_review_by_id(db, review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    if db_review.review_status != ReviewStatus.Published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only vote on published reviews."
        )
        
    return await crud.toggle_helpful_vote(db, review_id, user_id)

async def add_vendor_reply(db: AsyncSession, review_id: int, reply_in: schemas.VendorReplyCreate, current_user: User) -> schemas.ReviewResponse:
    user_id: int = getattr(current_user, 'user_id')
    db_review = await crud.get_review_by_id(db, review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
        
    # The product must belong to this vendor
    if getattr(db_review.product, 'vendor_id') != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reply to reviews on your own products."
        )
        
    if db_review.review_status == ReviewStatus.Deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reply to a deleted review."
        )
        
    updated_review = await crud.add_vendor_reply(db, db_review, reply_in.vendor_reply)
    return make_review_response(updated_review)

async def moderate_review_status(db: AsyncSession, review_id: int, status_update: schemas.AdminStatusUpdate) -> schemas.ReviewResponse:
    db_review = await crud.get_review_by_id(db, review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
        
    updated_review = await crud.update_review_status(db, db_review, status_update.status)
    return make_review_response(updated_review)

async def get_product_reviews(db: AsyncSession, product_id: int, skip: int = 0, limit: int = 100) -> List[schemas.ReviewResponse]:
    db_reviews = await crud.get_reviews_for_product(db, product_id, skip, limit)
    return [make_review_response(r) for r in db_reviews]
