from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.features.checkout import schemas, services

router = APIRouter(prefix="/checkout", tags=["Checkout"])

# Reusing the existing dependency logic if we exported it, but for simplicity we will just restrict to authenticated users
# and enforce RBAC via the allow_customer_vendor_address dependency, or we can just import it.
# Let's import allow_customer_vendor_address from addresses router.
from app.features.addresses.router import allow_customer_vendor_address

@router.post("/preview", response_model=schemas.CheckoutSummaryResponse)
async def preview_checkout(
    request: schemas.CheckoutPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    """
    Generates a dynamic checkout preview summary. 
    Validates cart contents, stock availability, and address validity.
    """
    return await services.process_checkout_preview(db, current_user.user_id, request)
