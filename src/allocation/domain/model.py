from dataclasses import dataclass
from datetime import date

from typing import Optional, List, Union


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


# @dataclass(unsafe_hash=True)
# class OrderLine:
#     order_id: str
#     sku: str
#     qty: int = 0


# from collections import namedtuple

# OrderLine = namedtuple("OrderLine", "order_id sku qty")
class OrderLine:
    def __init__(self, order_id: str, sku: str, qty: int):
        self.order_id = order_id
        self.sku = sku
        self.qty = qty

    def __repr__(self):
        return f"<OrderLine {self.order_id}>"

    def __eq__(self, other):
        if not isinstance(other, OrderLine):
            return False
        return self.order_id == other.order_id

    def __hash__(self):
        return hash(self.order_id)


# def __init__(self, ref: str, sku: str, qty: int):
#     self.order_id = ref
#     self.sku = sku
#     self.qty = qty


class BatchOrder:
    def __init__(
        self, ref: str, sku: str, qty: int, eta: Optional[date] = None
    ):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self.qty_purchase = qty
        self._allocations = set()

    def __repr__(self):
        return f"<BatchOrder {self.reference}>"

    def __eq__(self, other):
        if not isinstance(other, BatchOrder):
            return False
        return other.reference == self.reference

    def __hash__(self):
        "Defines the behavior of objects when adding them "
        "to sets or using as dict keys "
        "Further reading: https://hynek.me/articles/hashes-and-equality/"
        return hash(self.reference)

    def __gt__(self, other):
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
        # return True if ((cond_qty) and (cond_idem)) else False

    # def can_deallocate(self, order_id: str) -> Union[OrderLine, bool]:
    #     try:
    #         next(
    #             filter(lambda o: o.order_id == order_id, self._allocations)
    #         )
    #     except StopIteration:
    #         return False


def find_earliest_batch(batches: List[BatchOrder]) -> BatchOrder:
    dates = [batch.eta for batch in batches]
    idx_earliest = min([batch.eta for batch in batches])
    return batches[dates.index(idx_earliest)]


def find_stock_batch(batches: List[BatchOrder]) -> Optional[BatchOrder]:
    def ref_contains(batch: BatchOrder, substr: str) -> bool:
        return str(batch.reference).__contains__(substr)

    is_stock = lambda batch: ref_contains(batch, IN_STOCK)  # noqa: E731
    # is_shipment = lambda batch: ref_contains(batch, SHIPMENT)
    try:
        return next(filter(is_stock, batches))
    except StopIteration:
        return None


# def allocation_policy(batches: List[BatchOrder]) -> BatchOrder:
#     stock = find_stock_batch(batches)
#     if not stock:
#         return find_earliest_batch(batches)
#     return stock


def allocate(line: OrderLine, batches: List[BatchOrder]) -> str:
    # earliest = find_earliest_batch(batches)
    # while earliest:
    #     earliest.allocate(line)
    #     assert line in earliest._allocations
    #     batches.remove(earliest)
    #     earliest = find_earliest_batch(batches)
    # return earliest.reference
    try:
        # I can use sorted the way I want by defining __gt__
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for SKU {line.sku}")


def deallocate(batches: List[BatchOrder]) -> str:
    try:
        batch = next(
            b for b in sorted(batches, reverse=True) if b.can_deallocate()
        )
        return batch.deallocate().order_id
    except KeyError:
        raise OutOfStock(f"There are no stock left")
