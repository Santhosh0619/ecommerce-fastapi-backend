import uuid
from decimal import Decimal
from typing import Dict, Any
from .base import PaymentProvider

class MockProvider(PaymentProvider):
    async def create_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        intent_id = f"pi_mock_{uuid.uuid4().hex}"
        return {
            "client_secret": f"{intent_id}_secret_{uuid.uuid4().hex}",
            "intent_id": intent_id
        }
        
    async def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        # For mock, we'll assume the payload is JSON string and signature is a simple token
        import json
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            raise ValueError("Invalid payload")
            
        # Simple mock verification
        if signature != "mock_signature":
            raise ValueError("Invalid signature")
            
        return {
            "status": data.get("status", "success"),
            "intent_id": data.get("intent_id")
        }
