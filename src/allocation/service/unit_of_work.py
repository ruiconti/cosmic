"Unit of Work Adapter"
# UoW represents a way to encapsulate transactions on a single unit.
# Doing so at a Service Domain layer, we do not need to worry
# about consistency issues because of concurrent transactions
# Rui Conti, Apr 2020
import abc

from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy import orm

from allocation import config
from allocation.adapters import repository


DEFAULT_SESSION_FACTORY = orm.sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(), isolation_level="SERIALIZABLE",
    ),
    autoflush=False,
)


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractProductRepository

    def __enter__(self):  # type: ignore
        return self

    def __exit__(self, *args):  # type: ignore
        self.rollback()

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.products = repository.FakeProductRepository([])
        self.commited = False

    def commit(self) -> None:
        self.commited = True

    def rollback(self) -> None:
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: Callable = DEFAULT_SESSION_FACTORY):
        self.session_factory: Callable = session_factory

    def __enter__(self) -> AbstractUnitOfWork:
        self.session: orm.Session = self.session_factory()
        self.products = repository.SqlAlchemyProductRepository(self.session)
        return super().__enter__()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
