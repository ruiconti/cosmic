"""Services layer"""
# These are not domain services
# Typical service functions
#   1. fetch objects from memory
#   2. make checks and asserts about the requests against current state
#   3. call domain service
#   4. alter (save/update/remove) state
# Rui Conti, Apr 2020
import datetime

from typing import Optional, List

# from allocation.adapters.repository import AbstractRepository
from allocation.domain import model
from allocation.service import unit_of_work


# Exceptions belong to where they are raised
class InvalidSku(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def is_valid_sku(sku: str, products: List[model.Product]) -> bool:
    return sku in {product.sku for product in products}


def is_allocated(batch: model.BatchOrder, order_id: str) -> bool:
    return order_id in batch


def allocate(
    order_id: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(order_id=order_id, sku=sku, qty=qty)
    with uow:
        product = uow.products.get(sku=sku)
        if not product:
            raise InvalidSku(f"Invalid sku {sku}")

        try:
            # batchref = model.allocate(line, batches)
            batchref = product.allocate(line)
        except model.BatchIdempotency:
            uow.rollback()
            return ""

        uow.commit()
        return batchref


def deallocate(sku: str, uow: unit_of_work.AbstractUnitOfWork) -> str:
    with uow:
        product = uow.products.get(sku)
        if not product:
            raise InvalidSku(f"Invalid sku {sku}")

        orderid = product.deallocate()
        uow.commit()
        return orderid


def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[datetime.date],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku=sku, batches=[])
            uow.products.add(product)

        batch = model.BatchOrder(ref, sku, qty, eta)
        product.batches.append(batch)
        uow.commit()
