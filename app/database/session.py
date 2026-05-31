from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from app.core.config import settings

# 1. Create the database engine
# The engine is the starting point for any SQLAlchemy application.
# It establishes the connection pool to the database.
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True, # Set to False in production. True helps debug SQL queries in terminal.
    future=True
)

# 2. Create a Session Factory
# When we need to talk to the database, we need a "Session".
# AsyncSessionLocal is a factory that spits out new AsyncSession objects.
# expire_on_commit=False ensures we can still access our Python objects after the transaction is closed.
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 3. Dependency Injection Function
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    This generator function yields a database session for every FastAPI request.
    It guarantees that the session is closed when the request finishes, preventing connection leaks.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
