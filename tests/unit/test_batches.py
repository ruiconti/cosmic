# Tests BatchOrder's scope
# Expected behaviors on BatchOrder's methods and rules
# Rui Conti, Apr 2020
from datetime import date
from pytest import raises

from allocation.domain.model import OrderLine, BatchOrder, BatchIdempotency

# CHANGELOG
# 0.0.1 First notes
# 0.0.2 Maybe allocations are a service not part of an entity


def make_batch_and_line(sku: str, qty_batch: int, qty_line: int) -> tuple:
    return (
        BatchOrder("batch-ref", sku, qty=qty_batch, eta=date.today()),
        OrderLine("order-ref", sku, qty=qty_line),
    )


def test_allocating_order_to_batch_reduces_available_qty() -> None:
    batch = BatchOrder("batch-ref", "KALANCHOE-P11", qty=60, eta=date.today())
    order = OrderLine("order-ref", "KALANCHOE-P11", qty=12)

    batch.allocate(order)
    assert batch.available_quantity == 48


def test_deallocate_increases_available_qty() -> None:
    batch, order = make_batch_and_line("SOME-SKU", qty_batch=50, qty_line=10)

    batch.allocate(order)
    assert batch.available_quantity == 40
    batch.deallocate()
    assert batch.available_quantity == 50


def test_can_only_allocate_with_same_sku() -> None:
    batch = BatchOrder("bref-01", "CACTO SECO-P11", qty=19, eta=None)
    line = OrderLine("oline-03", "CACTO GRANDE", qty=2)
    assert batch.can_allocate(line) is False

    goat_line = OrderLine("oline-03", "CACTO SECO-P11", qty=2)
    assert batch.can_allocate(goat_line)
    # this should raise a specific return message


def test_can_allocate_if_available_greater_than_required() -> None:
    batch, order = make_batch_and_line(
        "ORQUIDEA-P15", qty_batch=12, qty_line=11
    )
    assert batch.can_allocate(order)
    batch.allocate(order)
    assert batch.available_quantity == 1


def test_cannot_allocate_if_available_smaller_than_required() -> None:
    batch, order = make_batch_and_line(
        "ORQUIDEA-P15", qty_batch=10, qty_line=11
    )
    assert batch.can_allocate(order) is False


def test_can_allocate_if_available_equal_to_required() -> None:
    batch, order = make_batch_and_line(
        "ORQUIDEA-P15", qty_batch=11, qty_line=11
    )
    assert batch.can_allocate(order) is True


def test_cannot_allocate_if_skus_do_not_match() -> None:
    batch = BatchOrder("b1", "ORQUIDEA-P12", 50, None)
    order = OrderLine("o1", "KALANCHOE-P06", 10)

    assert batch.can_allocate(order) is False


def test_allocation_is_idempotent() -> None:
    batch, order = make_batch_and_line(
        "CRISANTEMO-C21", qty_batch=8, qty_line=5
    )
    batch.allocate(order)

    with raises(BatchIdempotency):
        batch.allocate(order)

    assert batch.available_quantity == 3
