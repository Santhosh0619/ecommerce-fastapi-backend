from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.core.seeder import run_seeders

# Import our modular routers
from app.features.permissions.router import router as permissions_router
from app.features.roles.router import router as roles_router
from app.features.users.router import router as users_router
from app.features.auth.router import router as auth_router
from app.features.vendors.router import router as vendors_router
from app.features.categories.router import router as categories_router
from app.features.products.router import router as products_router
from app.features.cart.router import router as cart_router
from app.features.addresses.router import router as addresses_router
from app.features.checkout.router import router as checkout_router
from app.features.orders.router import router as orders_router
from app.features.payments.router import router as payments_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run on startup
    async with AsyncSessionLocal() as db:
        try:
            await run_seeders(db)
        except Exception as e:
            # Tables might not be created yet by alembic on the very first boot
            print(f"Skipping seeder (tables likely missing): {e}")
    yield
    # Run on shutdown

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Wire the routers into the main application under the /api/v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(roles_router, prefix=settings.API_V1_STR)
app.include_router(permissions_router, prefix=settings.API_V1_STR)
app.include_router(vendors_router, prefix=settings.API_V1_STR)
app.include_router(categories_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(cart_router, prefix=f"{settings.API_V1_STR}/cart", tags=["cart"])
app.include_router(addresses_router, prefix=f"{settings.API_V1_STR}/addresses", tags=["addresses"])
app.include_router(checkout_router, prefix=f"{settings.API_V1_STR}/checkout", tags=["checkout"])
app.include_router(orders_router, prefix=f"{settings.API_V1_STR}/orders", tags=["orders"])
app.include_router(payments_router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])

# Ensure upload directory exists
os.makedirs("uploads/products", exist_ok=True)
# Mount static files for images
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="static_uploads")

@app.get("/")
def root():
    return {"message": "Welcome to the E-Commerce API", "docs": "/docs"}
