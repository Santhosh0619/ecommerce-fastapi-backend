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
from app.features.notifications.tasks import process_order_confirmation_task, send_email_notification_task
import typing


logger = logging.getLogger(__name__)

async def initiate_payment(db: AsyncSession, current_user: User, request: PaymentInitiateRequest) -> PaymentInitiateResponse:
    # 1. Fetch and Validate Order
    uid = typing.cast(int, current_user.user_id)
    order = await get_order_by_id(db, request.order_id, uid)
    if order.order_status != 'Pending':
        raise HTTPException(status_code=400, detail="Only Pending orders can be paid for.")
        
    # 2. Idempotency Check: Existing Pending Payment
    existing_payment = await crud.get_pending_payment_for_order(db, request.order_id)
    if existing_payment and existing_payment.payment_method == request.payment_method:
        logger.info(f"Idempotency hit for order {request.order_id}. Returning existing payment intent.")
        # Reconstruct response from DB
        client_secret = None
        if existing_payment.gateway_response:
            data = json.loads(str(existing_payment.gateway_response))
            client_secret = data.get("client_secret")
            
        return PaymentInitiateResponse(
            payment_id=typing.cast(int, existing_payment.payment_id),
            order_id=typing.cast(int, order.order_id),
            gateway_provider=typing.cast(str, existing_payment.gateway_provider),
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
            
            # Phase 4 hook: Trigger Background Notifications
            process_order_confirmation_task.delay(typing.cast(int, order.order_id))
            
            return PaymentInitiateResponse(
                payment_id=typing.cast(int, payment.payment_id),
                order_id=typing.cast(int, order.order_id),
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
            order_id=typing.cast(int, order.order_id),
            gateway_provider=settings.DEFAULT_PAYMENT_GATEWAY,
            payment_method=request.payment_method,
            payment_amount=order.total_amount,
            transaction_reference=str(intent_data.get("intent_id", "")),
            stripe_payment_intent_id=str(intent_data.get("intent_id", ""))
        )
        payment.gateway_response = json.dumps(intent_data)
        
        await db.commit()
        
        return PaymentInitiateResponse(
            payment_id=typing.cast(int, payment.payment_id),
            order_id=typing.cast(int, order.order_id),
            gateway_provider=settings.DEFAULT_PAYMENT_GATEWAY,
            client_secret=intent_data.get("client_secret"),
            message="Payment initiated successfully."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment Gateway Error: {str(e)}")

async def process_webhook(db: AsyncSession, payload: bytes, signature: str):
    logger.warning("process_webhook() entered")
    logger.warning(f"Signature received: {signature}")
    provider = get_provider()
    try:
        event = await provider.verify_webhook(payload, signature)
        logger.warning(f"Event from provider: {event}")
    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    intent_id = event.get("intent_id")
    status_evt = event.get("status")
    logger.warning(f"Extracted intent_id: {intent_id}")
    logger.warning(f"Extracted status: {status_evt}")
    
    if not intent_id or status_evt == "ignored":
        logger.warning("Event ignored because no intent_id was found or status is ignored")
        return {"message": "Event ignored."}
        
    payment = await crud.get_payment_by_intent(db, intent_id)
    logger.warning(f"Payment found={payment is not None}")
    if not payment:
        logger.error(f"Webhook received for unknown intent {intent_id}")
        return {"message": "Unknown intent."}
        
    logger.warning(f"Payment status={payment.payment_status}")
    if payment.payment_status == 'Success':
        logger.warning(f"Idempotency hit: Payment {payment.payment_id} already marked success.")
        return {"message": "Already processed."}
        
    if status_evt == "success":
        logger.warning("Entering success branch")
        try:
            order = await crud.confirm_order_transaction(db, payment)
            logger.warning("Before database commit")
            await db.commit()
            logger.warning("Database commit successful")
            
            # Phase 4 hook: Trigger Background Notifications here
            if order.order_status == 'Confirmed':
                process_order_confirmation_task.delay(typing.cast(int, order.order_id))
            
            # Phase 4: Trigger PAYMENT_SUCCESS notification (Database Only)
            from app.features.orders.models import Order
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            stmt = select(Order).options(selectinload(Order.user)).where(Order.order_id == payment.order_id)
            res = await db.execute(stmt)
            order_details = res.scalar_one_or_none()
            
            if order_details and order_details.user:
                send_email_notification_task.delay(
                    user_id=typing.cast(int, order_details.user.user_id),
                    notification_type="PAYMENT_SUCCESS",
                    title="Payment Successful",
                    message=f"Your payment for Order #{payment.order_id} was successful.",
                    metadata_json={"order_id": typing.cast(int, payment.order_id), "payment_id": typing.cast(int, payment.payment_id)},
                    email_required=False,
                    recipient_email=None,
                    idempotency_key=f"payment_success_{payment.payment_id}"
                )
                
            return {"message": "Payment verified and order confirmed."}
        except Exception as e:
            logger.error(f"Exception during success processing: {str(e)}")
            await db.rollback()
            logger.error(f"DB Error while processing webhook for payment {payment.payment_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal processing error")
    elif status_evt == "failed":
        logger.warning("Entering failed branch")
        try:
            await crud.mark_payment_failed(db, payment)
            logger.warning("Before database commit (failed payment)")
            await db.commit()
            logger.warning("Database commit successful (failed payment)")
            
            # Trigger PAYMENT_FAILED notification
            from app.features.orders.models import Order
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            stmt = select(Order).options(selectinload(Order.user)).where(Order.order_id == payment.order_id)
            res = await db.execute(stmt)
            order_details = res.scalar_one_or_none()
            
            if order_details and order_details.user:
                send_email_notification_task.delay(
                    user_id=typing.cast(int, order_details.user.user_id),
                    notification_type="PAYMENT_FAILED",
                    title=f"Payment Failed for Order #{payment.order_id}",
                    message=f"Your payment attempt for Order #{payment.order_id} failed. Please try again.",
                    metadata_json={"order_id": typing.cast(int, payment.order_id), "payment_id": typing.cast(int, payment.payment_id)},
                    email_required=True,
                    recipient_email=str(order_details.user.email),
                    idempotency_key=f"payment_failed_{payment.payment_id}"
                )
            
            return {"message": "Payment failed."}
        except Exception as e:
            logger.error(f"Exception during failure processing: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal processing error")
