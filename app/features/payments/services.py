import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import json

from app.features.payments import crud
from app.features.orders.crud import get_order_by_id
from app.features.payments.schemas import PaymentInitiateRequest, PaymentInitiateResponse
from app.features.payments.providers import get_provider
from app.features.users.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)

async def initiate_payment(db: AsyncSession, current_user: User, request: PaymentInitiateRequest) -> PaymentInitiateResponse:
    # 1. Fetch and Validate Order
    order = await get_order_by_id(db, request.order_id, current_user.user_id)
    if order.order_status != 'Pending':
        raise HTTPException(status_code=400, detail="Only Pending orders can be paid for.")
        
    # 2. Idempotency Check: Existing Pending Payment
    existing_payment = await crud.get_pending_payment_for_order(db, request.order_id)
    if existing_payment and existing_payment.payment_method == request.payment_method:
        logger.info(f"Idempotency hit for order {request.order_id}. Returning existing payment intent.")
        # Reconstruct response from DB
        client_secret = None
        if existing_payment.gateway_response:
            data = json.loads(existing_payment.gateway_response)
            client_secret = data.get("client_secret")
            
        return PaymentInitiateResponse(
            payment_id=existing_payment.payment_id,
            order_id=order.order_id,
            gateway_provider=existing_payment.gateway_provider,
            client_secret=client_secret,
            message="Resumed existing payment session."
        )

    # 3. Handle COD vs Online Payment
    if request.payment_method == 'COD':
        try:
            import uuid
            tx_ref = f"COD-{uuid.uuid4().hex}"
            payment = await crud.create_payment(
                db, 
                order_id=order.order_id,
                gateway_provider="none",
                payment_method="COD",
                payment_amount=order.total_amount,
                transaction_reference=tx_ref
            )
            # Instantly confirm order & deduct stock for COD, but payment remains Pending until delivery
            await crud.confirm_order_transaction(db, payment, mark_payment_success=False)
            await db.commit()
            return PaymentInitiateResponse(
                payment_id=payment.payment_id,
                order_id=order.order_id,
                gateway_provider="none",
                message="COD Order Confirmed successfully. Payment is Pending upon delivery."
            )
        except Exception as e:
            await db.rollback()
            raise e
            
    # Online Payment flow
    provider = get_provider()
    try:
        intent_data = await provider.create_intent(
            amount=order.total_amount,
            currency=settings.DEFAULT_CURRENCY, # Now standardized from backend .env config
            metadata={"order_id": order.order_id, "user_id": current_user.user_id}
        )
        
        payment = await crud.create_payment(
            db,
            order_id=order.order_id,
            gateway_provider=settings.DEFAULT_PAYMENT_GATEWAY,
            payment_method=request.payment_method,
            payment_amount=order.total_amount,
            transaction_reference=intent_data.get("intent_id"),
            stripe_payment_intent_id=intent_data.get("intent_id")
        )
        payment.gateway_response = json.dumps(intent_data)
        
        await db.commit()
        
        return PaymentInitiateResponse(
            payment_id=payment.payment_id,
            order_id=order.order_id,
            gateway_provider=settings.DEFAULT_PAYMENT_GATEWAY,
            client_secret=intent_data.get("client_secret"),
            message="Payment initiated successfully."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment Gateway Error: {str(e)}")

async def process_webhook(db: AsyncSession, payload: bytes, signature: str):
    provider = get_provider()
    try:
        event = await provider.verify_webhook(payload, signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    intent_id = event.get("intent_id")
    status_evt = event.get("status")
    
    if not intent_id or status_evt == "ignored":
        return {"message": "Event ignored."}
        
    payment = await crud.get_payment_by_intent(db, intent_id)
    if not payment:
        logger.error(f"Webhook received for unknown intent {intent_id}")
        return {"message": "Unknown intent."}
        
    if payment.payment_status == 'Success':
        logger.info(f"Idempotency hit: Payment {payment.payment_id} already marked success.")
        return {"message": "Already processed."}
        
    if status_evt == "success":
        try:
            order = await crud.confirm_order_transaction(db, payment)
            await db.commit()
            # Phase 4 hook: Trigger Background Notifications here
            return {"message": "Payment verified and order confirmed."}
        except Exception as e:
            await db.rollback()
            logger.error(f"DB Error while processing webhook for payment {payment.payment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal processing error")
    elif status_evt == "failed":
        await crud.mark_payment_failed(db, payment)
        await db.commit()
        return {"message": "Payment failed."}
