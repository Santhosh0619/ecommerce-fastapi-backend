from celery import Celery
from app.core.config import settings

# Import all models to ensure SQLAlchemy mapper registry is fully populated for Celery workers
from app.features.users.models import User, UserProfile, UserRole, UserPermission
from app.features.roles.models import Role
from app.features.permissions.models import Permission
from app.features.vendors.models import VendorApplication
from app.features.categories.models import Category
from app.features.products.models import Product, ProductImage
from app.features.cart.models import Cart, CartItem
from app.features.addresses.models import Address
from app.features.orders.models import Order, OrderItem
from app.features.payments.models import Payment
from app.features.notifications.models import Notification

celery_app = Celery(
    "ecommerce_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Automatically discover tasks in app modules
    imports=[
        "app.features.notifications.tasks"
    ]
)
