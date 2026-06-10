import logging
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.features.users.models import User
from app.features.auth.dependencies import get_current_user
from app.features.payments.schemas import PaymentInitiateRequest, PaymentInitiateResponse
from app.features.payments import services

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a payment for an order.
    Returns client_secret for frontend SDK if online, or auto-confirms if COD.
    """
    return await services.initiate_payment(db, current_user, request)

@router.post("/webhook")
async def payment_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint for gateway webhooks to notify payment success/failure.
    """
    logger.warning("===== STRIPE WEBHOOK RECEIVED =====")
    logger.warning(f"Headers: {dict(request.headers)}")
    payload = await request.body()
    logger.warning(
        f"Webhook payload: {payload[:500].decode(errors='ignore')}"
    )
    from app.core.config import settings
    from fastapi import HTTPException
    
    if stripe_signature:
        sig = stripe_signature
    elif settings.DEFAULT_PAYMENT_GATEWAY == "mock" and settings.ENVIRONMENT in ["development", "testing"]:
        sig = "mock_signature"
    else:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        
    return await services.process_webhook(db, payload, sig)

