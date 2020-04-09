# Rui Conti
import abc
from typing import List

from sqlalchemy.orm import Session

import allocation.domain.model as model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    # "is one of the only things that makes ABCs actually “work” in Python
    # Python will refuse to let you instantiate a class that does not implement
    # all the abstractmethods defined in its parent class"
    def add(self, batch: model.BatchOrder) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str) -> model.BatchOrder:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[model.BatchOrder]:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session
        super().__init__()

    def add(self, batch: model.BatchOrder) -> None:
        self.session.add(batch)

    def get(self, reference: str) -> model.BatchOrder:
        return (
            self.session.query(model.BatchOrder)
            .filter_by(reference=reference)
            .first()
        )

    def list(self) -> List[model.BatchOrder]:
        return self.session.query(model.BatchOrder).all()


class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch: model.BatchOrder) -> None:
        self._batches.add(batch)

    def get(self, reference: str) -> model.BatchOrder:
        return next(filter(lambda b: b.reference == reference, self._batches))

    def list(self) -> list:
        return list(self._batches)
