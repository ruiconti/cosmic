# Tests Product's scope
# Expected behaviors on Product's methods and rules
# Rui Conti, Apr 2020
from datetime import date, timedelta

from allocation.domain import events
from allocation.domain.model import BatchOrder, OrderLine, Product  # type: ignore

TOMORROW = date.today() + timedelta(days=1)
YESTERDAY = date.today() - timedelta(days=1)


def test_prefers_current_stock_batches_to_shipments() -> None:
    sku = "KALANCHOE-P11"
    batch_in_stock = BatchOrder("in-stock-ref", sku, 100, eta=None)
    batch_shipment = BatchOrder("shipment-ref", sku, 100, eta=TOMORROW)
    line = OrderLine("o-ref", sku, 10)
    product = Product(sku, [batch_in_stock, batch_shipment])

    product.allocate(line)

    assert batch_in_stock.available_quantity == 90
    assert batch_shipment.available_quantity == 100


def test_prefer_earlier_batches() -> None:
    sku = "KALANCHOE-P11"
    batch_today = BatchOrder("shipment-ref02", sku, 100, eta=date.today())
    batch_yesterday = BatchOrder("shipment-ref03", sku, 100, eta=YESTERDAY)
    batch_tomorrow = BatchOrder("shipment-ref04", sku, 100, eta=TOMORROW)
    line = OrderLine("o-ref", sku, 10)

    product = Product(sku, [batch_today, batch_yesterday, batch_tomorrow])
    product.allocate(line)

    assert batch_yesterday.available_quantity == 90
    assert batch_today.available_quantity == 100
    assert batch_tomorrow.available_quantity == 100


def test_version_number_increments() -> None:
    sku = "KALANCHOE-P11"
    batch_today = BatchOrder("shipment-ref02", sku, 100, eta=date.today())
    line = OrderLine("o-ref", sku, 10)

    product = Product(sku, [batch_today])
    assert product.version_number == 0
    product.allocate(line)
    assert product.version_number == 1
    product.deallocate()
    assert product.version_number == 2


def test_records_out_of_stock_event_if_cannot_allocate():
    sku = "KALANCHOE-EVENTO"
    batch = BatchOrder("b1", sku, 15, eta=TOMORROW)
    product = Product(sku, batches=[batch])

    product.allocate(OrderLine("o1", sku, 10))
    b2 = product.allocate(OrderLine("o2", sku, 20))

    assert product.latest_event == events.OutOfStock(sku=sku)
    assert b2 is None


def test_create_batch_emmits_events():
    sku = "KALANCHOE-EVENTO"
    batch = BatchOrder("b1", sku, 100, eta=TOMORROW)
    product = Product(sku, batches=[batch])

    product.add_batch(batch)
    assert type(product.latest_event) == events.BatchCreated


def test_allocation_emmits_events():
    sku = "KALANCHOE-EVENTO"
    batch = BatchOrder("b1", sku, 100, eta=TOMORROW)
    product = Product(sku, batches=[batch])
    line = OrderLine("o1", sku, qty=85)

    product.add_batch(batch)
    product.allocate(line)

    assert type(product.latest_event) == events.Allocated
