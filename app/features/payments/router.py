from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.features.users.models import User
from app.core.security import get_current_active_user
from app.features.payments.schemas import PaymentInitiateRequest, PaymentInitiateResponse
from app.features.payments import services

router = APIRouter()

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request_data: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiate a payment for an order.
    Returns client_secret for frontend SDK if online, or auto-confirms if COD.
    """
    return await services.initiate_payment(db, current_user, request_data)

@router.post("/webhook")
async def payment_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint for gateway webhooks to notify payment success/failure.
    """
    payload = await request.body()
    # Mock signature fallback if Stripe signature is not provided during local testing
    sig = stripe_signature or "mock_signature"
    return await services.process_webhook(db, payload, sig)
