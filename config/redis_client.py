import redis
from django.conf import settings

client = redis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


def set_redis_key(key, value):
    client.set(key, value)


def get_redis_key(key):
    val = client.get(key)
    return val.decode("utf-8") if val else None
