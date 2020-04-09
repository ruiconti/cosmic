"""Services layer"""
# These are not domain services
# Typical service functions
#   1. fetch objects from memory
#   2. make checks and asserts about the requests against current state
#   3. call domain service
#   4. alter (save/update/remove) state
import datetime

from sqlalchemy.orm import Session
from typing import Optional, List

# from allocation.adapters.repository import AbstractRepository
from allocation.domain import model
from allocation.service import unit_of_work


# Exceptions belong to where they are raised
class InvalidSku(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# class NotAllocated(Exception):
#     def __init__(self, message: str):
#         super().__init__(message)


def is_valid_sku(sku: str, batches: List[model.BatchOrder]) -> bool:
    return sku in {batch.sku for batch in batches}


def is_allocated(batch: model.BatchOrder, order_id: str) -> bool:
    return order_id in batch


# def allocate(line: OrderLine, batches: List[BatchOrder]) -> None: TODO: v0.1
# def allocate(
#     line: model.OrderLine, repo: AbstractRepository, session: Session
# ) -> str: TODO: (v0.2)
#     batches = repo.list()
#     if not is_valid_sku(line.sku, batches):
#         raise InvalidSku(f"Invalid sku {line.sku}")

#     try:
#         batchref = model.allocate(
#             line, batches
#         )  # this may throw model Exceptions
#     except model.BatchIdempotency:
#         # This probably should be handled on API layer
#         return ""

#     session.commit()
#     return batchref
def allocate(
    order_id: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    with uow:
        line = model.OrderLine(order_id=order_id, sku=sku, qty=qty)
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")

        try:
            batchref = model.allocate(line, batches)
        except model.BatchIdempotency:
            uow.rollback()
            return ""

        uow.commit()
        return batchref


# def deallocate(repo: AbstractRepository, session: Session) -> str:
#     batches = repo.list()
#     # if not is_allocated(batch, order_id):
#     #     raise NotAllocated(
#     #         f"Order {order_id} is not allocated to Batch {batch_ref}"
#     #     )

#     orderid = model.deallocate(batches)  # this may throw model Exceptions
#     session.commit()
#     return orderid
def deallocate(uow: unit_of_work.AbstractUnitOfWork) -> str:
    with uow:
        batches = uow.batches.list()
        orderid = model.deallocate(batches)
        uow.commit()
        return orderid


# def add_batch(
#     ref: str,
#     sku: str,
#     qty: int,
#     eta: datetime.date,
#     repo: AbstractRepository,
#     session: Session,
# ) -> None:
#     repo.add(model.BatchOrder(ref, sku, qty, eta))
#     session.commit()
def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[datetime.date],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    batch = model.BatchOrder(ref, sku, qty, eta)
    with uow:
        uow.batches.add(batch)
        uow.commit()


# def deallocate(line: OrderLine, repo: AbstractRepository, session: Session):
#     batches = repo.list()
