# Tests Unit of Work Adapter
# Expected behavior of unique entrypoint to ProductRepository
# No testing of services' layer abstractions. Only UoW's abstractions
# Domain's imported to simulate Service Layer behavior
# Rui Conti, Apr 2020
import time
import traceback
import threading

from pytest import raises  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from allocation.domain import model  # type: ignore
from allocation.service import unit_of_work  # type: ignore


def insert_batch(session: Session, ref: str, sku: str, qty: int) -> None:
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        dict(sku=sku, version=0),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, qty_purchase) VALUES (:ref, :sku, :qty)",
        dict(ref=ref, sku=sku, qty=qty),
    )


def remove_batch(session: Session, sku: str) -> None:

    [(batch_id,)] = list(
        session.execute(
            "SELECT id FROM batches WHERE sku = :sku", dict(sku=sku)
        )
    )

    orders = list(
        session.execute(
            "SELECT id_orderline FROM allocations WHERE batch_id = :batch_id",
            dict(batch_id=batch_id),
        )
    )
    orders = [car for cdr in orders for car in cdr]
    for order in orders:
        session.execute(
            "DELETE FROM allocations WHERE id_orderline = :order",
            dict(order=order),
        )
        session.execute(
            "DELETE FROM order_lines WHERE id = :order", dict(order=order)
        )

    session.execute("DELETE FROM batches WHERE sku=:sku", dict(sku=sku))
    session.commit()
    session.execute("DELETE FROM products WHERE sku=:sku", dict(sku=sku))
    session.commit()


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


def test_rollsback_on_exception_raised(sqlite_session_factory):
    class ASqlAlchemyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with raises(ASqlAlchemyException):
        with uow:
            insert_batch(uow.session, "bref-01", "ROLLZEIRA", 25)
            raise ASqlAlchemyException

    new_session = sqlite_session_factory()
    rows = list(new_session.execute("SELECT * FROM batches"))
    assert rows == []


def try_to_allocate(session_factory, order_id, sku, exceptions):
    line = model.OrderLine(order_id, sku, 10)
    with unit_of_work.SqlAlchemyUnitOfWork(session_factory) as uow:
        product = uow.products.get(sku=sku)
        product.allocate(line)
        time.sleep(0.5)
        try:
            uow.commit()  # this is where exception gets triggered
        except Exception as ex:
            uow.rollback()
            exceptions.append(ex)
            print(traceback.format_exc())


def test_allocations_to_same_version_number_fail(postgres_session_factory,):
    order_a, order_b = "orderid_01", "orderid_02"
    sku = "OLIVIA-P15"
    batchref = "bathref-01"

    session = postgres_session_factory()
    remove_batch(session, sku)
    insert_batch(session, batchref, sku, 15)
    session.commit()

    exceptions = []
    allocate_a = lambda: try_to_allocate(
        postgres_session_factory, order_a, sku, exceptions
    )
    allocate_b = lambda: try_to_allocate(
        postgres_session_factory, order_b, sku, exceptions
    )
    thread_a, thread_b = (
        threading.Thread(target=allocate_a),
        threading.Thread(target=allocate_b),
    )
    thread_a.start(), thread_b.start()
    # both threads will hold similar `version_numbers` of Product(OLIVIA-P11)
    # meaning that thread_b should fail
    thread_a.join(), thread_b.join()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku = :sku", dict(sku=sku)
    )

    assert version == 1
    assert len(exceptions) > 0

    orders = list(
        session.execute(
            "SELECT ol.order_id FROM allocations a "
            "JOIN order_lines ol ON a.id_orderline = ol.id "
            "WHERE ol.sku = :sku",
            dict(sku=sku,),
        )
    )
    print(orders)
    assert orders[0].order_id == "orderid_01"
