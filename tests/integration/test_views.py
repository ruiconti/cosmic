from allocation.domain import events, commands
from allocation.service import unit_of_work, message_bus
from allocation import views

from tests import helpers


def create_and_allocate_batch(uow: unit_of_work.AbstractUnitOfWork) -> tuple:
    sku = helpers.random_sku()
    orderid = helpers.random_orderid()
    batchref = helpers.random_batchref()

    message_bus.handle(commands.CreateBatch(batchref, sku, 100, None), uow)
    message_bus.handle(commands.Allocate(orderid, sku, 30), uow)

    return batchref, orderid, sku


def test_view_all_allocations(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    create_and_allocate_batch(uow)

    allocations = views.all_allocations(uow)
    assert len(allocations) > 0


def test_view_specific_orderline(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    batchref, orderid, sku = create_and_allocate_batch(uow)

    [orderline] = views.allocations(orderid, uow)
    assert orderline["batchref"] == batchref
