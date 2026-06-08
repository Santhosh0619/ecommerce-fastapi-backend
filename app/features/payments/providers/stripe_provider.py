import stripe
from decimal import Decimal
from typing import Dict, Any
from fastapi import HTTPException
from .base import PaymentProvider
from app.core.config import settings

class StripeProvider(PaymentProvider):
    def __init__(self):
        stripe.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
    async def create_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Stripe expects amount in cents
            amount_cents = int(amount * 100)
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata
            )
            return {
                "client_secret": intent.client_secret,
                "intent_id": intent.id
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    async def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            if event.type == 'payment_intent.succeeded':
                intent = event.data.object
                return {
                    "status": "success",
                    "intent_id": intent.id
                }
            elif event.type == 'payment_intent.payment_failed':
                intent = event.data.object
                return {
                    "status": "failed",
                    "intent_id": intent.id
                }
                
            return {"status": "ignored"}
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
