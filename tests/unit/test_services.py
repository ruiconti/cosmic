from allocation.service import message_bus, unit_of_work  # type: ignore
from allocation.domain import events, commands  # type: ignore


def test_add_batch() -> None:
    sku = "KALANCHOE-P11"
    uow = unit_of_work.FakeUnitOfWork()
    create = commands.CreateBatch("b1", sku, 120, None)
    message_bus.handle(create, uow)
    assert uow.commited

    with uow:
        product = uow.products.get(sku)
        [batch] = product.batches
        assert batch.reference == "b1"


def test_allocation_reduces_available_qty() -> None:
    sku = "KALANCHOE-P11"
    uow = unit_of_work.FakeUnitOfWork()
    create = commands.CreateBatch("b1", sku, 120, None)
    message_bus.handle(create, uow)
    allocate = commands.Allocate("o1", sku, 100)
    message_bus.handle(allocate, uow)
    assert uow.commited

    with uow:
        product = uow.products.get(sku)
        [batch] = product.batches
        assert batch.available_quantity == 20

        assert batch.reference == "b1"
