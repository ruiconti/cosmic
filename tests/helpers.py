import uuid
import datetime


def random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def random_sku(name: str = "") -> str:
    return random_entity("sku", name)


def random_batchref(name: str = "") -> str:
    return random_entity("batch", name)


def random_orderid(name: str = "") -> str:
    return random_entity("order", name)


def random_entity(entity: str, name: str = "default") -> str:
    return f"{entity}-{name}-{random_suffix()}"


def tomorrow() -> datetime.date:
    return datetime.date.today() + datetime.timedelta(days=1)
