from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any

class PaymentProvider(ABC):
    @abstractmethod
    async def create_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Return a dict containing at minimum 'client_secret' and 'intent_id'"""
        pass
        
    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify webhook signature and return parsed event data containing 'intent_id' and 'status'"""
        pass
