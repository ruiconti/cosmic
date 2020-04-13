# Tests API's entrypoint
# Expected behaviors on API requests and responses exclusively
# No usage of domain, services nor any adaptor
# Rui Conti, Apr 2020
from typing import Any, List

from tests.helpers import random_sku, random_batchref, random_orderid

# CHANGELOG
# 0.0.10 Test e2e allocation service
# 0.0.11 Wait, we didn't verify if changes are commited to db
# 0.0.12 What if I try to allocate an SKU that's out of stock?
# 0.0.13 What if I try to allocate an SKU that has no stock?


def post_stock(client: Any, batches: List) -> None:
    for batch in batches:
        ref, sku, qty, eta = batch
        r = client.post(
            "/batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
        )
        assert r.status_code == 201


# @pytest.mark.usefixtures("restart_api")
def test_happy_path_201_allocated_batch(client_api) -> None:
    sku, other_sku = random_sku(), random_sku("other")

    earlybatch = random_batchref(str(1))
    laterbatch = random_batchref(str(2))
    otherbatch = random_batchref(str(3))
    post_stock(
        client_api,
        [
            (laterbatch, sku, 100, "2011-01-02"),
            (earlybatch, sku, 100, "2011-01-01"),
            (otherbatch, other_sku, 100, "2011-02-02"),
        ],
    )

    data = {"order_id": random_orderid(), "sku": sku, "qty": 90}
    # url = config.get_api_url()
    r = client_api.post(f"/allocate", json=data)
    assert r.status_code == 202
    # assert r.json["batchref"] == earlybatch


# @pytest.mark.usefixtures("restart_api")
def test_unhappy_path_400_error_message(client_api) -> None:
    unknown_sku, order_id = random_sku(), random_orderid()
    data = {"order_id": order_id, "sku": unknown_sku, "qty": 35}

    # url = config.get_api_url()
    r = client_api.post(f"/allocate", json=data)
    assert r.status_code == 400
    assert r.json["message"] == f"Invalid sku {unknown_sku}"
