"Message Bus"
# A message bus is a simple mapper of Events to Handlers
# For a given event, what handler should I run?
from typing import List, Optional, Any, Union

from allocation.service import unit_of_work, handlers
from allocation.domain import events, commands

import logging


logger = logging.getLogger(__name__)


EVENTS_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.OrderAlreadyAllocated: [handlers.log_to_sentry],
    events.BatchCreated: [],
    events.Allocated: [],
    events.Deallocated: [],
}

COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.ChangeBatchQuantity: handlers.change_batch_qty,
    commands.CreateBatch: handlers.add_batch,
}

Message = Union[events.Event, commands.Command]


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    for handler in EVENTS_HANDLERS[type(event)]:
        try:
            logger.info("Handling event %s with handler %s", event, handler)
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception as ex:
            logger.exception("Exception handling event %s: %s", event, ex)
            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
) -> Optional[Any]:
    logger.info("Handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception as ex:
        logger.exception("Exception handling command %s: %s", command, ex)
        raise


# def handle(event: events.Event) -> None:
#     for handler in HANDLERS[type(event)]:
#         handler(event)
def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork) -> List:
    results: List = []
    queue: List[Message] = [message]
    # a Queue is used to handle events that might raise from executing
    # a command
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} is neither a Command nor an Event")
    return results
