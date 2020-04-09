from datetime import date

from sqlalchemy.orm import Session  # type: ignore

import allocation.adapters.repository as repository

import allocation.adapters.repository as repository  # type: ignoere
import allocation.domain.model as model  # type: ignore


def insert_order_line(postgres_session: Session) -> str:
    postgres_session.execute(
        "INSERT INTO order_lines (order_id, sku, qty)"
        ' VALUES ("order-01", "LIRIO-P15", 19)'
    )
    [[order_line_id]] = postgres_session.execute(
        "SELECT id FROM order_lines WHERE order_id:order_id " "AND sku=:sku",
        dict(order_id="order-01", sku="LIRIO-P15"),
    )
    return order_line_id


# DISCLAIMER: this is tested on "integration/test_uow.py"
# def test_repository_can_save_a_batch(postgres_session: Session) -> None:
#     repo = repository.SqlAlchemyRepository(postgres_session)
#     batch = model.BatchOrder("batch-ref-01", "BONSAI-P24", 150, eta=None)
#     repo.add(batch)
#     postgres_session.commit()
#     # We keep the .commit() outside of the repository and make it the responsibility of the caller.
#     # There are pros and cons for this

#     rows = list(
#         postgres_session.execute(
#             "SELECT batch_id, sku, qty_purchase, eta FROM batches"
#         )
#     )
#     assert rows == [("batch-ref-01", "BONSAI-P24", 150, None)]


def insert_batch(postgres_session: Session, ref: str) -> None:
    postgres_session.execute(
        "INSERT INTO batches (reference, sku, qty_purchase, eta, created_at)"
        ' VALUES (":ref", ":sku", ":qty_purchase", ":eta", :created_at)',
        dict(
            reference=ref,
            sku="LIRIO-P15",
            qty_purchase=50,
            eta=None,
            created_at=date.today(),
        ),
    )
    [[order_line_id]] = postgres_session.execute(
        "SELECT id FROM order_lines WHERE order_id:order_id " "AND sku=:sku",
        dict(order_id="order-01", sku="LIRIO-P15"),
    )
