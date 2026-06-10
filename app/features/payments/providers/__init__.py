from .base import PaymentProvider
from .stripe_provider import StripeProvider
from .mock_provider import MockProvider
from app.core.config import settings

def get_provider() -> PaymentProvider:
    if settings.DEFAULT_PAYMENT_GATEWAY.lower() == "stripe":
        return StripeProvider()
    elif settings.DEFAULT_PAYMENT_GATEWAY.lower() == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unsupported payment gateway: {settings.DEFAULT_PAYMENT_GATEWAY}")
