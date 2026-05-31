import redis.asyncio as redis
from app.core.config import settings

# Create a global Redis connection pool for fast asynchronous caching and blocklisting
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
