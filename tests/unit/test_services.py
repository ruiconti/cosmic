from typing import Callable

import pytest

from tests.helpers import tomorrow

from allocation.domain import model
from allocation.service import services, unit_of_work
from allocation.adapters import repository


# class FakeSession:
#     commited = False

#     def commit(self) -> None:
#         self.commited = True


def test_returns_allocation() -> None:
    # line = model.OrderLine("o1", "KALANCHOE-P11", 10)
    # batch = model.BatchOrder("b1", "KALANCHOE-P11", 20, None)

    # repo = repository.FakeRepository([batch])
    # result = services.allocate(line, repo, FakeSession())
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch("b1", "KALANCHOE-P11", 120, None, uow=uow)
        result = services.allocate("o1", "KALANCHOE-P11", 100, uow=uow)

        assert result == "b1"


# DISCLAIMER: commits are tested now on integration/test_uow.py
# def test_commits() -> None:
#     line = model.OrderLine("o1", "ROSA-FLORADA", 10)
#     batch = model.BatchOrder("b1", "ROSA-FLORADA", 90)

#     repo = repository.FakeRepository([batch])
#     session = FakeSession()
#     services.allocate(line, repo, session)

#     assert session.commited is True


def test_add_batch():
    # repo, session = repository.FakeRepository([]), FakeSession()
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch(
            # "b1", "PALMEIRA ME", 30, eta=None, repo=repo, session=session
            "b1",
            "PALEMIRA ME",
            30,
            eta=None,
            uow=uow,
        )

        assert uow.batches.get("b1") is not None
        assert uow.commited


def test_allocate_idempotent() -> None:
    # line = model.OrderLine("o1", "KALANCHOE-P11", 10)
    # batch = model.BatchOrder("b1", "KALANCHOE-P11", 20, None)

    # repo = repository.FakeRepository([batch])
    uow = unit_of_work.FakeUnitOfWork()
    with uow:
        services.add_batch("b1", "KALANCHOE-P11", 20, None, uow=uow)

        batchref = services.allocate("o1", "KALANCHOE-P11", 10, uow=uow)
        services.allocate("o1", "KALANCHOE-P11", 10, uow=uow)
        batch = uow.batches.get(batchref)

        assert batch.available_quantity == 10
