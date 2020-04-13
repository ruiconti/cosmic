"Domain Layer"
# Single place where business logic lies on code-base
# Expected behaviors are mapped to
#   Entities: Identifiable changing abstractions,
#   Value Objects: Immutable attribute-identifiable abstractions,
#   Services: Abstractions that are better represented by an action and
#   Aggregates: Single entry-point to a domain and represents a unit
#       of business transactions and services
# Cleanest layer and no extenral dependencies are made
# Rui Conti, Apr 2020
from datetime import date

from typing import Optional, List

from allocation.domain import events

IN_STOCK = "in-stock"
SHIPMENT = "shipment"


class OutOfStock(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BatchIdempotency(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# from collections import namedtuple

# OrderLine = namedtuple("OrderLine", "order_id sku qty")
class OrderLine:
    def __init__(self, order_id: str, sku: str, qty: int):
        self.order_id = order_id
        self.sku = sku
        self.qty = qty

    def __repr__(self) -> str:
        return f"<OrderLine {self.order_id}>"

    def __eq__(self, other) -> bool:  # type: ignore
        if not isinstance(other, OrderLine):
            return False
        return self.order_id == other.order_id

    def __hash__(self) -> int:
        return hash(self.order_id)


class BatchOrder:
    def __init__(
        self, ref: str, sku: str, qty: int, eta: Optional[date] = None
    ):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self.qty_purchase = qty
        self._allocations: set = set()

    def __repr__(self) -> str:
        return f"<BatchOrder {self.reference}>"

    def __eq__(self, other):  # type: ignore
        if not isinstance(other, BatchOrder):
            return False
        return other.reference == self.reference

    def __hash__(self) -> int:
        "Defines the behavior of objects when adding them "
        "to sets or using as dict keys "
        "Further reading: https://hynek.me/articles/hashes-and-equality/"
        return hash(self.reference)

    def __gt__(self, other) -> bool:  # type: ignore
        """Conditions that make (self >= other) == True
        Meaning that self is equal or greather than the other (in any sense you wish)

        For what states of `other` that `self` BatchOrder should be
        considered greater than `other`

        If you think of ordering OrderBatches in a list
        `[a b c d e]` that will be iterated ascendingly on a given priority,
        `__gt__` defines what makes `elementof(list)` LESS prioritized"""
        if self.eta is None:
            return False
        if other.eta is None:
            return True

        return self.eta > other.eta

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self.qty_purchase - self.allocated_quantity

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self) -> OrderLine:
        return self._allocations.pop()

    def can_deallocate(self) -> bool:
        return len(self._allocations) > 0

    def can_allocate(self, line: OrderLine) -> bool:
        # Maybe expose those conditions to Exceptions?
        cond_qty = line.qty <= self.available_quantity
        cond_idem = line not in self._allocations
        cond_sku = line.sku == self.sku
        if not cond_idem:
            raise BatchIdempotency(
                f"Order {line.order_id} already in Batch {self.reference}"
            )

        return all([cond_qty, cond_idem, cond_sku])


class Product:
    def __init__(
        self, sku: str, batches: List[BatchOrder], version_number: int = 0,
    ):
        self.sku: str = sku
        self.batches: List[BatchOrder] = batches
        self.version_number: int = version_number
        self._events: List[events.Event] = []
        # whenever we make a change to an instance of Product, we
        # increment version_number

    @property
    def latest_event(self) -> Optional[events.Event]:
        try:
            return self._events[-1]
        except IndexError:
            return None

    def add_batch(self, batch: BatchOrder) -> None:
        self.batches.append(batch)
        self._events.append(
            events.BatchCreated(
                batch.reference, batch.sku, batch.qty_purchase, batch.eta
            )
        )

    def allocate(self, line: OrderLine) -> None:
        try:
            # I can use sorted the way I want by defining __gt__
            batch = next(
                b for b in sorted(self.batches) if b.can_allocate(line)
            )
            batch.allocate(line)
            self._events.append(
                events.Allocated(
                    order_id=line.order_id,
                    batch_ref=batch.reference,
                    sku=line.sku,
                    qty=line.qty,
                )
            )
            self.version_number += 1  # here
            # return batch.reference
        except StopIteration:
            # raise OutOfStock(f"Out of stock for SKU {line.sku}")
            self._events.append(events.OutOfStock(sku=line.sku))
        except BatchIdempotency:
            self._events.append(
                events.OrderAlreadyAllocated(order_id=line.order_id)
            )
        # return None

    def deallocate(self) -> None:
        try:
            batch = next(
                b
                for b in sorted(self.batches, reverse=True)
                if b.can_deallocate()
            )
            line = batch.deallocate()
            self._events.append(
                events.Deallocated(
                    batch_ref=batch.reference,
                    order_id=line.order_id,
                    sku=line.sku,
                    qty=line.qty,
                )
            )
            self.version_number += 1
        except KeyError:
            self._events.append(events.AllocationsEmpty())
            # return None
            # raise OutOfStock(f"There are no stock left")
