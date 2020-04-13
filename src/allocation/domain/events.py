"Domain Events'"
# Events are a type of Value Objects: Immutable data scructures
# identifiable by their meta-attributes
# Semantics: Represents something that has happened
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


class Event:
    when: datetime = datetime.now()


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class Allocated(Event):
    order_id: str
    batch_ref: str
    sku: str
    qty: int


@dataclass
class Deallocated(Event):
    batch_ref: str
    order_id: str
    sku: str
    qty: int


@dataclass
class BatchCreated(Event):
    batch_ref: str
    sku: str
    qty: int
    eta: Optional[datetime]


@dataclass
class OrderAlreadyAllocated(Event):
    order_id: str


@dataclass
class AllocationsEmpty(Event):
    pass
