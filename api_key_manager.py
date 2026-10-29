import os
import secrets
import logging
import redis
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import APIKey

load_dotenv()

logger = logging.getLogger(__name__)

#--------------Redis connection

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    protocol=2 
)

def generate_api_key() -> str:
    """
    Generates a secure random API key.
    Format: sk-{32 hex characters}
    Example: sk-a3f8c2e1b4d7f9e2a1c3b5d8e9f0a2b4
    """
    return f"sk-{secrets.token_hex(32)}"

def validate_api_key(key: str, db: Session)-> APIKey | None:
    """
    Checks if API key exists and is active.
    Returns APIKey object if valid, None if invalid.
    """
    api_key = db.query(APIKey).filter(APIKey.key == key, APIKey.is_active == True).first()
    if not api_key:
        logger.warning(f"Invalid or inactive API key: {key[:8]}")
        return None
    return api_key

def is_rate_limited(api_key: str, limit: int=2, window:int=60) -> tuple[bool, int, int]:
    """
    Checks if an API key has exceeded the rate limit.

    api_key: the API key string
    limit:   max requests per window
    window:  time window in seconds

    Returns:
        (is_limited, current_count, ttl)
        is_limited = True  → reject request
        is_limited = False → allow request
        ttl = seconds until window resets
    """

    redis_key = f"rate_limit:{api_key[:8]}"

    try:
        count = redis_client.incr(redis_key)
        #rate_limit:sk-12345 = 3

        if count == 1:
            redis_client.expire(redis_key, window)
        ttl = redis_client.ttl(redis_key)

        if count > limit:
            logger.warning(
                        f"Rate limit exceeded | key: {api_key[:8]}... | "
                        f"retry in {ttl}s"
                    )
            return True, count, ttl

        #time to live

        logger.info(f"Rate limit | key: {api_key[:8]}... |" f"count: {count}/{limit} | ttl: {ttl}s")

        
        return False, count, ttl
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)} - failing open")
        return False, 0, 0



