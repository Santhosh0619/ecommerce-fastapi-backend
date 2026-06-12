from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.features.reviews.models import Review, ReviewHelpfulVote, ReviewStatus
from app.features.reviews.schemas import ReviewCreate, ReviewUpdate
from app.features.products.models import Product
from app.features.orders.models import Order, OrderItem
from app.features.users.models import User

async def get_review_by_id(db: AsyncSession, review_id: int) -> Optional[Review]:
    """
    Get review by review_id, eager loading the user and product.
    """
    result = await db.execute(
        select(Review)
        .options(joinedload(Review.user), joinedload(Review.product))
        .filter(Review.review_id == review_id)
    )
    return result.scalars().first()

async def get_user_review_for_product(db: AsyncSession, user_id: int, product_id: int) -> Optional[Review]:
    """
    Get user's review for a specific product if it exists.
    """
    result = await db.execute(
        select(Review)
        .filter(Review.user_id == user_id, Review.product_id == product_id)
    )
    return result.scalars().first()

async def verify_delivered_order_contains_product(db: AsyncSession, user_id: int, product_id: int, order_id: Optional[int] = None) -> Optional[int]:
    """
    Checks if user_id has an order with status 'Delivered' containing product_id.
    If order_id is provided, specifically validates that order.
    Returns the order_id if found, otherwise None.
    """
    query = select(Order.order_id).join(OrderItem, Order.order_id == OrderItem.order_id).where(
        Order.user_id == user_id,
        Order.order_status == 'Delivered',
        OrderItem.product_id == product_id
    )
    if order_id is not None:
        query = query.where(Order.order_id == order_id)
        
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none()

async def recalculate_product_rating_aggregates(db: AsyncSession, product_id: int):
    """
    Recalculates average_rating and review_count for a product based on Published reviews only.
    Updates the Product row under a pessimistic write lock.
    """
    # 1. Fetch count and average of Published reviews
    stats_result = await db.execute(
        select(
            func.count(Review.review_id).label("count"),
            func.avg(Review.rating).label("avg_rating")
        )
        .filter(
            Review.product_id == product_id,
            Review.review_status == ReviewStatus.Published
        )
    )
    stats = stats_result.first()
    count = int(getattr(stats, 'count', 0) or 0)
    avg_rating_raw = getattr(stats, 'avg_rating', None)
    avg_rating = round(float(avg_rating_raw), 2) if avg_rating_raw is not None else 0.00

    # 2. Lock the product row and update
    product_result = await db.execute(
        select(Product)
        .filter(Product.product_id == product_id)
        .with_for_update()
    )
    product = product_result.scalars().first()
    if product:
        product.average_rating = avg_rating
        product.review_count = count
        db.add(product)
        await db.flush()

async def create_review(db: AsyncSession, review_in: ReviewCreate, user_id: int, order_id: int) -> Review:
    """
    Create or reactivate/overwrite a soft-deleted review.
    """
    # Check for existing review (active or soft-deleted)
    existing_review = await get_user_review_for_product(db, user_id, review_in.product_id)
    
    if existing_review:
        if existing_review.review_status != ReviewStatus.Deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a review for this product. Please update your existing review."
            )
        else:
            # Re-use soft deleted review row
            existing_review.order_id = order_id  # type: ignore
            existing_review.rating = review_in.rating  # type: ignore
            existing_review.review_comment = review_in.review_comment  # type: ignore
            existing_review.review_status = ReviewStatus.Published  # type: ignore
            existing_review.is_edited = False  # type: ignore
            existing_review.helpful_votes = 0  # type: ignore
            existing_review.vendor_reply = None  # type: ignore
            existing_review.vendor_reply_at = None  # type: ignore
            db.add(existing_review)
            await db.flush()
            db_review = existing_review
    else:
        db_review = Review(
            product_id=review_in.product_id,
            user_id=user_id,
            order_id=order_id,
            rating=review_in.rating,
            review_comment=review_in.review_comment,
            is_edited=False,
            helpful_votes=0,
            review_status=ReviewStatus.Published
        )
        db.add(db_review)
        await db.flush()

    # Recalculate aggregates
    await recalculate_product_rating_aggregates(db, review_in.product_id)
    await db.commit()
    
    # Reload with relations
    review_id = getattr(db_review, 'review_id')
    return await get_review_by_id(db, review_id) # type: ignore

async def update_review(db: AsyncSession, db_review: Review, review_update: ReviewUpdate) -> Review:
    """
    Update an existing review.
    """
    if review_update.rating is not None:
        db_review.rating = review_update.rating  # type: ignore
    if review_update.review_comment is not None:
        db_review.review_comment = review_update.review_comment  # type: ignore
        
    db_review.is_edited = True  # type: ignore
    db.add(db_review)
    await db.flush()
    
    # Recalculate aggregates
    await recalculate_product_rating_aggregates(db, getattr(db_review, 'product_id'))
    await db.commit()
    
    review_id = getattr(db_review, 'review_id')
    return await get_review_by_id(db, review_id) # type: ignore

async def delete_review_soft(db: AsyncSession, db_review: Review) -> Review:
    """
    Soft delete a review by setting status to Deleted.
    """
    db_review.review_status = ReviewStatus.Deleted  # type: ignore
    db.add(db_review)
    await db.flush()
    
    # Recalculate aggregates
    await recalculate_product_rating_aggregates(db, getattr(db_review, 'product_id'))
    await db.commit()
    
    review_id = getattr(db_review, 'review_id')
    return await get_review_by_id(db, review_id) # type: ignore

async def update_review_status(db: AsyncSession, db_review: Review, new_status: ReviewStatus) -> Review:
    """
    Moderator update status of a review.
    """
    db_review.review_status = new_status  # type: ignore
    db.add(db_review)
    await db.flush()
    
    # Recalculate aggregates
    await recalculate_product_rating_aggregates(db, getattr(db_review, 'product_id'))
    await db.commit()
    
    review_id = getattr(db_review, 'review_id')
    return await get_review_by_id(db, review_id) # type: ignore

async def get_reviews_for_product(db: AsyncSession, product_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
    """
    Retrieve Published reviews for a product with pagination. Eager loads user.
    """
    query = (
        select(Review)
        .options(joinedload(Review.user))
        .filter(
            Review.product_id == product_id,
            Review.review_status == ReviewStatus.Published
        )
        .order_by(desc(Review.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def toggle_helpful_vote(db: AsyncSession, review_id: int, user_id: int) -> bool:
    """
    Toggles a helpful vote for a review by a user.
    Returns True if vote was added, False if removed.
    Updates the cached helpful_votes count on the Review under row lock.
    """
    # 1. Lock review row FIRST to serialize concurrent vote toggles
    review_query = select(Review).filter(Review.review_id == review_id).with_for_update()
    review_result = await db.execute(review_query)
    db_review = review_result.scalars().first()
    
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # 2. Check if vote exists (now serialized under the review lock)
    vote_query = select(ReviewHelpfulVote).filter(
        ReviewHelpfulVote.review_id == review_id,
        ReviewHelpfulVote.user_id == user_id
    )
    vote_result = await db.execute(vote_query)
    vote = vote_result.scalars().first()
        
    is_voted = False
    if vote:
        # Remove vote
        await db.delete(vote)
        current_votes = getattr(db_review, 'helpful_votes', 0)
        db_review.helpful_votes = max(0, current_votes - 1)  # type: ignore
    else:
        # Add vote
        new_vote = ReviewHelpfulVote(review_id=review_id, user_id=user_id)
        db.add(new_vote)
        current_votes = getattr(db_review, 'helpful_votes', 0)
        db_review.helpful_votes = current_votes + 1  # type: ignore
        is_voted = True
        
    db.add(db_review)
    await db.commit()
    return is_voted

async def add_vendor_reply(db: AsyncSession, db_review: Review, reply_text: str) -> Review:
    """
    Sets vendor reply on a review.
    """
    db_review.vendor_reply = reply_text  # type: ignore
    db_review.vendor_reply_at = func.now()  # type: ignore
    db.add(db_review)
    await db.commit()
    
    review_id = getattr(db_review, 'review_id')
    return await get_review_by_id(db, review_id) # type: ignore
