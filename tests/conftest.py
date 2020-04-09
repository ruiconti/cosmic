import time
import requests
import pytest  # type: ignore

from pathlib import Path
from typing import Callable
from sqlalchemy import engine, create_engine, orm  # type: ignore
from tenacity import retry, stop_after_delay  # type: ignore


from allocation import config  # type: ignore
from allocation.entrypoints import app
from allocation.adapters.orm import start_mappers, clear_mappers, metadata  # type: ignore


pytest.register_assert_rewrite("tests.e2e.test_api")


@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up() -> requests.Response:
    return requests.get(config.get_api_url())


@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(eng: engine.Engine) -> engine.Connection:
    return eng.connect()


@pytest.fixture
def restart_api() -> None:
    (Path(__file__).parent / "../src/allocation/entrypoints/app.py").touch()
    # time.sleep(0.5)
    wait_for_webapp_to_come_up()


@pytest.fixture
def client_api() -> None:
    app.app.config["TESTING"] = True

    with app.app.test_client() as client:
        yield client


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


# Uses postgres_db as fixture as an Engine object
@pytest.fixture  # type: ignore
def postgres_session_factory(postgres_db: engine.Engine) -> None:
    clear_mappers()
    start_mappers(postgres_db)  # tear-up
    return orm.sessionmaker(bind=postgres_db)  # deliver to next fixture
    clear_mappers()  # tear-down


@pytest.fixture
def postgres_session(postgres_session_factory: Callable) -> None:
    return postgres_session_factory()
