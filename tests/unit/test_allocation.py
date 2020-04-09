from datetime import date, timedelta

from allocation.service import services, unit_of_work  # type: ignore
from allocation.domain.model import BatchOrder, OrderLine  # type: ignore
from allocation.adapters.repository import FakeRepository  # type: ignore

TOMORROW = date.today() + timedelta(days=1)
YESTERDAY = date.today() - timedelta(days=1)


# class FakeSession:
#     commited = False

#     def commit(self):
#         self.commited = True


def test_prefers_current_stock_batches_to_shipments() -> None:
    # batch_in_stock = BatchOrder("in-stock-ref", "KALANCHOE-P11", 100, eta=None)
    # batch_shipment = BatchOrder(
    #     "shipment-ref", "KALANCHOE-P11", 100, eta=TOMORROW
    # )
    # line = OrderLine("o-ref", "KALANCHOE-P11", 10)

    # session = FakeSession()
    # repo = FakeRepository([batch_in_stock, batch_shipment])
    # services.allocate(line, repo, session)
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch(
            "in-stock-ref", "KALANCHOE-P11", 100, eta=None, uow=uow
        )
        services.add_batch(
            "shipment-ref", "KALANCHOE-P11", 100, eta=TOMORROW, uow=uow
        )
        services.allocate("o-ref", "KALANCHOE-P11", 10, uow=uow)
        batch_in_stock = uow.batches.get("in-stock-ref")
        batch_shipment = uow.batches.get("shipment-ref")

        assert batch_in_stock.available_quantity == 90
        assert batch_shipment.available_quantity == 100

        # services.deallocate(repo, session)
        services.deallocate(uow)
        assert batch_in_stock.available_quantity == 100


def test_prefer_earlier_batches() -> None:
    # batch_today = BatchOrder(
    #     "shipment-ref02", "KALANCHOE-P11", 100, eta=date.today()
    # )
    # batch_yesterday = BatchOrder(
    #     "shipment-ref03", "KALANCHOE-P11", 100, eta=YESTERDAY
    # )
    # batch_tomorrow = BatchOrder(
    #     "shipment-ref04", "KALANCHOE-P11", 100, eta=TOMORROW
    # )
    # line = OrderLine("o-ref", "KALANCHOE-P11", 10)

    # session = FakeSession()
    # repo = FakeRepository([batch_today, batch_tomorrow, batch_yesterday])
    # services.allocate(line, repo, session)
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch(
            "shipment-ref02", "KALANCHOE-P11", 100, eta=date.today(), uow=uow
        )
        services.add_batch(
            "shipment-ref03", "KALANCHOE-P11", 100, eta=YESTERDAY, uow=uow
        )
        services.add_batch(
            "shipment-ref04", "KALANCHOE-P11", 100, eta=TOMORROW, uow=uow
        )

        services.allocate("o-ref", "KALANCHOE-P11", 10, uow=uow)
        batch_yesterday = uow.batches.get("shipment-ref03")
        batch_tomorrow = uow.batches.get("shipment-ref04")
        batch_today = uow.batches.get("shipment-ref02")

        assert batch_yesterday.available_quantity == 90
        assert batch_today.available_quantity == 100
        assert batch_tomorrow.available_quantity == 100
