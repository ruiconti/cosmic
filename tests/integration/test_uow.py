from typing import Optional

from datetime import date
from sqlalchemy import orm  # type: ignore

from allocation.domain import model  # type: ignore
from allocation.service import services, unit_of_work  # type: ignore

from tests import helpers


def insert_batch(
    session: orm.Session, ref: str, sku: str, qty: int, eta: Optional[date]
) -> None:
    session.execute(
        "INSERT INTO batches (reference, sku, qty_purchase, eta) VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(
    session: orm.Session, order_id: str, sku: str
) -> str:
    # [[batchref]] = session.excute(
    #     "SELECT b.reference FROM allocations AS a JOIN batches AS b ON a.batch_id = b.id WHERE a.id_orderline=:order_id",
    #     dict(order_id=order_id),
    # )
    # return batchref
    [(ref, *rest)] = session.execute(
        "SELECT b.reference "
        "FROM allocations a "
        "INNER JOIN batches b ON a.batch_id = b.id "
        "INNER JOIN order_lines l ON a.id_orderline = l.id "
        "WHERE l.order_id = :order_id",
        dict(order_id=order_id),
    )
    return ref


# @pytest.fixture.mark("session_factory")
def test_uow_can_retrieve_batch_and_allocate_it(postgres_session_factory):
    session = postgres_session_factory()
    sku_dummy = "ROSEIRA P15"
    batchref_dummy = "b1"
    insert_batch(
        session=session,
        ref=batchref_dummy,
        sku=sku_dummy,
        qty=120,
        eta=helpers.tomorrow(),
    )
    session.commit()

    # uow = unit_of_work.SqlAlchemyUnitOfWork(postgres_session_factory)
    # uow = unit_of_work.FakeUnitOfWork()
    uow = unit_of_work.SqlAlchemyUnitOfWork(postgres_session_factory)
    # batch = uow.batches.get(reference=batchref_dummy)
    # DISCLAIMER: we're not testing service layer here, using domain service instead
    # model.allocate(
    #     model.OrderLine(order_id="o1", sku=sku_dummy, qty=80),
    #     uow.batches.list(),
    # )
    services.allocate(order_id="o1", sku=sku_dummy, qty=80, uow=uow)

    # services.allocate("o1", sku_dummy, 80, uow)
    uow.commit()
    # services.allocate("o15", "ROSEIRA P17", 80, uow=uow)
    # batch = uow.batches.get(reference="b1")
    # line = model.OrderLine("o1", "ROSEIRA P17", 80)

    batchref = get_allocated_batch_ref(
        session=session, order_id="o1", sku=sku_dummy
    )
    assert batchref == batchref_dummy
