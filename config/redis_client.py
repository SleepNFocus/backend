from __future__ import annotations

import redis
from django.conf import settings

client = redis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


# set_redis_key 함수는 key와 value를 받아들이며 반환값이 없는 함수입니다.
def set_redis_key(key: str, value: str) -> None:
    client.set(key, value)


# get_redis_key 함수는 key를 받아서 Redis에서 값을 가져오고, 문자열 또는 None을 반환합니다.
def get_redis_key(key: str) -> str | None:
    val = client.get(key)
    return val.decode("utf-8") if val else None
