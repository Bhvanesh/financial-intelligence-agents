import os
import redis
import logging
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(host = os.getenv("REDIS_HOST","localhost"), port = int(os.getenv("REDIS_PORT", 6379)),
                           db = int(os.getenv("REDIS_DB", 0)), decode_responses = True)


logger = logging.getLogger(__name__)

def is_rate_limited(ip: str, limit: int = 3, window:int = 60) -> tuple[bool,int]:
    """
    Checks if an IP has exceeded the rate limit.

    ip:     client IP address
    limit:  max requests allowed per window
    window: time window in seconds

    Returns:
        (is_limited, current_count)
        is_limited = True  → reject request
        is_limited = False → allow request
    """

    key = f"rate_limit:{ip}"
    try:
        count = redis_client.incr(key)
        if count==1:
            redis_client.expire(key,window)
        logger.info(f"Rate limit check | IP: {ip} | Count: {count}")
