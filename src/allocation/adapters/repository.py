# Rui Conti
import abc
from typing import List, Set

from sqlalchemy.orm import Session

from allocation.adapters import orm
from allocation.domain import model


class AbstractProductRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: Set[model.Product] = set()

    def add(self, product: model.Product) -> None:
        self.seen.add(product)
        self._add(product)

    def get(self, sku: str) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref: str) -> model.Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    # "is one of the only things that makes ABCs actually “work” in Python
    # Python will refuse to let you instantiate a class that does not implement
    # all the abstractmethods defined in its parent class"
    @abc.abstractmethod
    def _add(self, product: model.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, reference: str) -> model.BatchOrder:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_batchref(self, reference: str) -> model.BatchOrder:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[model.Product]:
        raise NotImplementedError


class SqlAlchemyProductRepository(AbstractProductRepository):
    def __init__(self, session: Session):
        self.session = session
        super().__init__()

    def _add(self, product: model.Product) -> None:
        self.session.add(product)

    # def get(self, reference: str) -> model.BatchOrder:
    #     return (
    #         self.session.query(model.BatchOrder)
    #         .filter_by(reference=reference)
    #         .first()
    #     )
    def _get(self, sku: str) -> model.Product:
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batchref(self, batchref: str) -> model.Product:
        return (
            self.session.query(model.Product)
            .join(model.BatchOrder)
            .filter(orm.batches.c.reference == batchref,)
            # READ: Tables' `c` attribute makes reference to joined table columns
            .first()
        )

    # join(model.BatchOrder)

    def list(self) -> List[model.Product]:
        return self.session.query(model.Product).all()


class FakeProductRepository(AbstractProductRepository):
    # def __init__(self, batches):
    #     self._batches = set(batches)
    def __init__(self, products):
        self._products = set(products)
        super().__init__()

    # def add(self, batch: model.BatchOrder) -> None:
    #     self._batches.add(batch)
    def _add(self, product: model.Product) -> None:
        self._products.add(product)

    # def get(self, reference: str) -> model.BatchOrder:
    #     return next(filter(lambda b: b.reference == reference, self._batches))
    def _get(self, sku: str) -> model.Product:
        try:
            return next(filter(lambda p: p.sku == sku, self._products))
        except StopIteration:
            return None

    def _get_by_batchref(self, batch_ref: str) -> model.Product:
        is_batchref_in = lambda product: batch_ref in [
            b.reference for b in product.batches
        ]
        try:
            return next(
                filter(lambda product: is_batchref_in(product), self._products)
            )
        except StopIteration:
            return None

    # def list(self) -> list:
    #     return list(self._batches)
    def list(self) -> list:
        return list(self._products)
