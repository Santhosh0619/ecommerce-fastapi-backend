import asyncio
import logging
import json
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery_app
from app.database.session import AsyncSessionLocal
from app.core.mail import send_email
from app.features.users.models import User, UserRole, UserProfile
from app.features.roles.models import Role
from app.features.orders.models import Order, OrderItem
from app.features.products.models import Product
from .models import Notification, NotificationType, DeliveryStatus
from .templates import generate_email_html

logger = logging.getLogger(__name__)

async def _process_notification_async(
    user_id: int, 
    notification_type: str,
    title: str,
    message: str,
    metadata_json: Optional[Dict[str, Any]],
    email_required: bool,
    recipient_email: Optional[str],
    idempotency_key: Optional[str]
):
    async with AsyncSessionLocal() as db:
        if idempotency_key:
            stmt = select(Notification).where(Notification.idempotency_key == idempotency_key)
            result = await db.execute(stmt)
            if result.scalars().first():
                logger.info(f"Duplicate notification aborted for idempotency_key: {idempotency_key}")
                return

        new_notification = Notification(
            notification_type=NotificationType[notification_type],
            user_id=user_id,
            title=title,
            message=message,
            metadata_json=metadata_json,
            is_read=False,
            delivery_status=DeliveryStatus.PENDING,
            idempotency_key=idempotency_key
        )
        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)
        
        if email_required and recipient_email:
            try:
                html_body = generate_email_html(title, message)
                await send_email(subject=title, recipients=[recipient_email], body=html_body)
                new_notification.delivery_status = DeliveryStatus.SENT
                await db.commit()
            except Exception as e:
                new_notification.delivery_status = DeliveryStatus.FAILED
                await db.commit()
                raise e
        else:
            new_notification.delivery_status = DeliveryStatus.SENT
            await db.commit()

async def _create_admin_alert_async(failed_task_name: str, error_msg: str):
    async with AsyncSessionLocal() as db:
        stmt = (
            select(User)
            .join(UserRole, UserRole.user_id == User.user_id)
            .join(Role, Role.role_id == UserRole.role_id)
            .where(Role.role_name == "Admin")
        )
        result = await db.execute(stmt)
        admins = result.scalars().all()
        
        for admin in admins:
            alert = Notification(
                notification_type=NotificationType.ADMIN_ALERT,
                user_id=admin.user_id,
                title="System Alert: Task Failed & Retries Exhausted",
                message=f"Task {failed_task_name} permanently failed. Error: {error_msg}",
                is_read=False,
                delivery_status=DeliveryStatus.PENDING
            )
            db.add(alert)
        await db.commit()
        
        for admin in admins:
            if admin.email:
                try:
                    html_body = generate_email_html("CRITICAL: Admin Alert", f"Task {failed_task_name} permanently failed.<br/>Error: {error_msg}")
                    await send_email(subject="CRITICAL: Admin Alert", recipients=[admin.email], body=html_body)
                except Exception as e:
                    logger.error(f"Failed to send ADMIN_ALERT email to {admin.email}: {e}")

@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_email_notification_task(
    self, 
    user_id: int, 
    notification_type: str,
    title: str,
    message: str,
    metadata_json: Optional[Dict[str, Any]] = None,
    email_required: bool = False,
    recipient_email: Optional[str] = None,
    idempotency_key: Optional[str] = None
):
    try:
        asyncio.run(_process_notification_async(
            user_id, notification_type, title, message, metadata_json, email_required, recipient_email, idempotency_key
        ))
    except Exception as exc:
        logger.error(f"Notification Task Failed: {exc}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"Notification Task exhausted all retries! Alerting Admins.")
            asyncio.run(_create_admin_alert_async(self.name, str(exc)))
        raise exc

async def _process_order_confirmation_async(order_id: int):
    async with AsyncSessionLocal() as db:
        # Load Order, Items, Product, Customer
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user),
                selectinload(Order.address),
                selectinload(Order.payments)
            )
            .where(Order.order_id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            logger.error(f"Order {order_id} not found for confirmation notifications.")
            return

        # 1. Customer ORDER_CONFIRMED Notification
        items_list_str = "\n".join([f"- {item.product.product_name} x {item.quantity} (${item.product_price})" for item in order.items])
        
        addr = order.address
        shipping_address = f"{addr.street_address}, {addr.city}, {addr.state} {addr.postal_code}, {addr.country}" if addr else "N/A"
        tx_id = order.payments[0].transaction_reference if order.payments else "N/A"
        
        customer_message = f"Your order #{order.order_number} has been confirmed.\n\nShipping Address:\n{shipping_address}\n\nPayment Transaction ID: {tx_id}\n\nItems:\n{items_list_str}\n\nTotal Amount: ${order.total_amount}\nExpected Delivery: {order.expected_delivery_date}"
        
        await _process_notification_async(
            user_id=order.user_id,
            notification_type="ORDER_CONFIRMED",
            title=f"Order Confirmed: {order.order_number}",
            message=customer_message,
            metadata_json={"order_id": order.order_id, "order_number": order.order_number},
            email_required=True,
            recipient_email=order.user.email,
            idempotency_key=f"order_confirmed_customer_{order.order_id}"
        )

        # 2. Vendor Privacy Logic: Group products by vendor_id
        vendor_items_map = {}
        for item in order.items:
            vid = item.product.vendor_id
            if vid not in vendor_items_map:
                vendor_items_map[vid] = []
            vendor_items_map[vid].append(item)
            
        # Send NEW_VENDOR_ORDER to each distinct vendor
        for vendor_id, v_items in vendor_items_map.items():
            # Get vendor email
            vendor_stmt = select(User).where(User.user_id == vendor_id)
            v_res = await db.execute(vendor_stmt)
            vendor = v_res.scalar_one_or_none()
            if not vendor:
                continue
                
            v_items_str = "\n".join([f"- {i.product.product_name} x {i.quantity}" for i in v_items])
            v_message = f"You have a new order (Part of Order #{order.order_number})!\n\nCustomer Shipping Address:\n{shipping_address}\n\nProducts:\n{v_items_str}\n\nPlease prepare these items for shipment."
            
            await _process_notification_async(
                user_id=vendor.user_id,
                notification_type="NEW_VENDOR_ORDER",
                title=f"New Order Received: #{order.order_number}",
                message=v_message,
                metadata_json={"order_id": order.order_id, "order_number": order.order_number},
                email_required=True,
                recipient_email=vendor.email,
                idempotency_key=f"new_vendor_order_{order.order_id}_{vendor_id}"
            )

@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def process_order_confirmation_task(self, order_id: int):
    try:
        asyncio.run(_process_order_confirmation_async(order_id))
    except Exception as exc:
        logger.error(f"Process Order Confirmation Task Failed: {exc}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"Process Order Confirmation Task exhausted all retries! Alerting Admins.")
            asyncio.run(_create_admin_alert_async(self.name, str(exc)))
        raise exc
