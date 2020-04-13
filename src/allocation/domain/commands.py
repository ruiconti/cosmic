"Command Events"
# Commands are also Value Objects represented by immutable
# data structures
# Semantics: Represents an imperative order to do something
# A command should modify a single aggregate and either succeed
# or fail in totality. Any other bookeeping, cleanup and notification
# happens with an Event
from dataclasses import dataclass
from datetime import date
from typing import Optional


class Command:
    pass


@dataclass
class Allocate(Command):
    order_id: str
    sku: str
    qty: int


@dataclass
class Deallocate(Command):
    sku: str


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date]


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
