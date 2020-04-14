# import redis
import redis
import json

from typing import Any
from allocation import config

r = redis.Redis(**config.get_redis_uri())


def serialize(message: Any) -> bytes:
    return json.dumps(message).encode("utf-8")


def deserialize(message: Any) -> dict:
    return json.loads(message)


def publish_message(channel: str, message: Any) -> None:
    # message = serialize(message)
    r.publish(channel, message)
