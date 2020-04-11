from allocation.service import services, unit_of_work  # type: ignore


def test_returns_allocation() -> None:
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch("b1", "KALANCHOE-P11", 120, None, uow=uow)
        result = services.allocate("o1", "KALANCHOE-P11", 100, uow=uow)

        assert result == "b1"


def test_add_batch() -> None:
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch(
            "b1", "PALEMIRA ME", 30, eta=None, uow=uow,
        )

        assert uow.products.get_by_batchref("b1") is not None
        assert uow.commited
