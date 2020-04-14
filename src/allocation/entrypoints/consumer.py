import logging
import json

from allocation.domain import commands
from allocation.adapters import redis
from allocation.service import message_bus, unit_of_work


logger = logging.getLogger(__name__)


def handle_allocation_commands(message: bytes) -> None:
    data = json.loads(message)
    logger.info(f"Handling external msg {data}")
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    message_bus.handle(cmd, unit_of_work.SqlAlchemyUnitOfWork())


EXTERNAL_CHANNELS_HANDLERS = {"allocation-events": handle_allocation_commands}


def worker() -> None:
    pb = redis.r.pubsub(ignore_subscribe_messages=True)
    # We can map channels to specific handlers on the future
    pb.subscribe(EXTERNAL_CHANNELS_HANDLERS)
    while True:
        message = pb.get_message()
        channel = message["channel"].decode()
        handler = EXTERNAL_CHANNELS_HANDLERS[channel]
        handler(message)


if __name__ == "__main__":
    worker()
