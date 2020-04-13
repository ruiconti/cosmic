"Unit of Work Adapter"
# UoW represents a way to encapsulate transactions on a single unit.
# Doing so at a Service Domain layer, we do not need to worry
# about consistency issues because of concurrent transactions
# Rui Conti, Apr 2020
import abc

from typing import Callable, Generator

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

    def collect_events(self) -> None:
        pass

    def collect_new_events(self) -> Generator:
        """Unit of Work is responsible for connecting messages (commands and events)
        raised from Domain Layer to the Message Bus

        Message Bus calls this method to handle any new event that might have been
        raised after some command was ran"""
        for product in self.products.seen:
            while product._events:
                yield product._events.pop(0)

    # def publish_events(self) -> None:
    #     """Unit of Work is responsible for connecting events raised on Domain layer
    #     to the message bus to handle them"""
    #     for product in self.products.seen:
    #         while product.events:
    #             event = product.events.pop()
    #             message_bus.handle(event)

    def commit(self) -> None:
        """Every time a commit is made, we try to commit current database transaction"""
        self._commit()
        # self.publish_events()

    @abc.abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.products = repository.FakeProductRepository([])
        self.commited = False

    def _commit(self) -> None:
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

    def __exit__(self, *args):  # type: ignore
        super().__exit__(*args)
        self.session.close()

    def _commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
