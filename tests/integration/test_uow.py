# Tests Unit of Work Adapter
# Expected behavior of unique entrypoint to ProductRepository
# No testing of services' layer abstractions. Only UoW's abstractions
# Domain's imported to simulate Service Layer behavior
# Rui Conti, Apr 2020
from sqlalchemy.orm import Session  # type: ignore

from allocation.domain import model  # type: ignore
from allocation.service import unit_of_work  # type: ignore


def insert_batch(session: Session, ref: str, sku: str, qty: int) -> None:
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        dict(sku=sku, version=1),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, qty_purchase) VALUES (:ref, :sku, :qty)",
        dict(ref=ref, sku=sku, qty=qty),
    )


def get_allocated_batch_ref(session: Session, order_id: str, sku: str) -> str:
    [(ref, *rest)] = session.execute(
        "SELECT b.reference "
        "FROM allocations a "
        "INNER JOIN batches b ON a.batch_id = b.id "
        "INNER JOIN order_lines l ON a.id_orderline = l.id "
        "WHERE l.order_id = :order_id",
        dict(order_id=order_id),
    )
    return ref


def test_uow_can_retrieve_batch_and_allocate_it(sqlite_session_factory):
    session = sqlite_session_factory()
    sku_dummy = "ROSEIRA P15"
    batchref_dummy = "b1"
    insert_batch(
        session=session, ref=batchref_dummy, sku=sku_dummy, qty=120,
    )
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    # we are testing Unit of Work, not Services Layer
    with uow:
        product = uow.products.get(sku=sku_dummy)
        line = model.OrderLine(order_id="o1", sku=sku_dummy, qty=80)
        product.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(
        session=session, order_id="o1", sku=sku_dummy
    )
    assert batchref == batchref_dummy


def test_rollsback_uncommited_work_by_default(sqlite_session_factory):
    batchref = "bref-01"
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        insert_batch(uow.session, batchref, "ROLLZEIRA", 30)
    # on exit, UoW (should) execute session.rollback()

    new_session = sqlite_session_factory()
    rows = list(
        new_session.execute(
            "SELECT * FROM batches WHERE reference = :batchref",
            dict(batchref=batchref),
        )
    )
    assert rows == []
