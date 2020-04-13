"""Services layer"""
# These are not domain services
# Typical service functions
#   1. fetch objects from memory
#   2. make checks and asserts about the requests against current state
#   3. call domain service
#   4. alter (save/update/remove) state
# Rui Conti, Apr 2020
from typing import List

# from allocation.adapters.repository import AbstractRepository
from allocation.domain import events, commands, model
from allocation.service import unit_of_work


# Exceptions belong to where they are raised
class InvalidSku(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def send_out_of_stock_notification(event: events.OutOfStock) -> None:
    print(
        f"Sending notification because product {event.sku} has ran out of stock. "
        f"Allocation was tried at {event.when}"
    )
    pass


def log_to_sentry(event: events.Event) -> None:
    print(
        f"Logging to sentry the event {type(event)} that happened at {event.when}"
    )


def is_valid_sku(sku: str, products: List[model.Product]) -> bool:
    return sku in {product.sku for product in products}


def is_allocated(batch: model.BatchOrder, order_id: str) -> bool:
    return order_id in batch


def change_batch_qty(
    ref: str, qty: int, uow: unit_of_work.AbstractUnitOfWork
) -> None:
    pass


def allocate(
    command: commands.Allocate, uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    line = model.OrderLine(
        order_id=command.order_id, sku=command.sku, qty=command.qty
    )
    with uow:
        product = uow.products.get(sku=line.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")

        product.allocate(line)
        uow.commit()


def deallocate(
    command: commands.Deallocate, uow: unit_of_work.AbstractUnitOfWork
) -> None:
    with uow:
        product = uow.products.get(command.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {command.sku}")

        orderid = product.deallocate()
        uow.commit()
        return orderid


def add_batch(
    command: commands.CreateBatch, uow: unit_of_work.AbstractUnitOfWork,
) -> None:

    batch = model.BatchOrder(command.ref, command.sku, command.qty, command.eta)
    with uow:
        product = uow.products.get(sku=batch.sku)
        if product is None:
            product = model.Product(sku=batch.sku, batches=[])
            uow.products.add(product)

        product.add_batch(batch)
        uow.commit()
