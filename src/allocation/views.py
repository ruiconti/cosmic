from typing import Dict, List

from allocation.service import unit_of_work


def all_allocations(uow: unit_of_work.AbstractUnitOfWork) -> List[Dict]:
    with uow:
        results = uow.session.execute(
            "SELECT id_orderline, batchref, sku, qty FROM allocations_view"
        )
    return [dict(r) for r in results]


def allocations(
    order_id: str, uow: unit_of_work.AbstractUnitOfWork
) -> List[Dict]:
    with uow:
        results = uow.session.execute(
            "SELECT batchref, sku, qty "
            "FROM allocations_view "
            "WHERE id_orderline = :order_id",
            dict(order_id=order_id),
        )
    return [dict(r) for r in results]
