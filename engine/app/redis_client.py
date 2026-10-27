import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# Azure Cache for Redis requires SSL (rediss://) and ignores self-signed cert checks
redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    ssl_cert_reqs=None
)