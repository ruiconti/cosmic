from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Table, ForeignKey
from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import mapper, relationship, clear_mappers  # noqa: F401

from allocation.domain import model

metadata: MetaData = MetaData()

order_lines: Table = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", String(255)),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
)

products = Table(
    "products",
    metadata,
    # Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255), primary_key=True),
    Column("version_number", Integer, nullable=False, server_default="0"),
)

batches: Table = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    # Column("sku", String(255)),
    Column("sku", ForeignKey("products.sku")),
    Column("qty_purchase", Integer, nullable=False),
    Column("eta", DateTime, nullable=True),
    Column("created_at", DateTime),
)

# AssociationTable pattern
allocations: Table = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("id_orderline", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)


def start_mappers(engine: Optional[Engine] = None) -> None:
    if engine:
        real: MetaData = MetaData()
        real.reflect(bind=engine)
        if not real.tables.keys() == metadata.tables.keys():
            metadata.create_all(engine)

    mapper_lines = mapper(model.OrderLine, order_lines)  # noqa: F841
    mapper_batches = mapper(  # noqa: F841
        model.BatchOrder,  # associating this Base declaration
        batches,  # to this table
        properties={
            "_allocations": relationship(
                mapper_lines, secondary=allocations, collection_class=set,
            )
        },
    )
    mapper(
        model.Product,
        products,
        properties={"batches": relationship(mapper_batches)},
    )
    # mapper(model.Product, products, properties={
    #     "batches": relationship(mapper_batches)})
