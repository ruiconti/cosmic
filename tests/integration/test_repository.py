# Tests Repository Adapter
# Expected behavior of interface to persistant storage
# No testing of services' layer abstractions. Only UoW's abstractions
# Domain's imported to simulate Service Layer behavior
# Rui Conti, Apr 2020
from sqlalchemy.orm import Session  # type: ignore

from allocation.domain import model  # type: ignore
from allocation.adapters import repository  # type: ignore


def test_get_by_batchref(sqlite_session: Session):
    repo = repository.SqlAlchemyProductRepository(sqlite_session)
    b1 = model.BatchOrder("b1", sku="SKU-01", qty=100, eta=None)
    b2 = model.BatchOrder("b2", sku="SKU-01", qty=50, eta=None)
    b3 = model.BatchOrder("b3", sku="SKU-02", qty=75, eta=None)
    p1 = model.Product("SKU-01", [b1, b2])
    p2 = model.Product("SKU-02", [b3])

    repo.add(p1)
    repo.add(p2)
    # we're not testing UoW so we need to commit :)
    sqlite_session.commit()

    assert repo.get_by_batchref("b1") == p1
    assert repo.get_by_batchref("b3") == p2
