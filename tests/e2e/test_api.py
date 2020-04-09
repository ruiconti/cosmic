from typing import Any, Callable, List

import pytest  # type: ignore
import requests
from datetime import date

from allocation import config
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
    assert r.status_code == 201
    assert r.json["batchref"] == earlybatch


# @pytest.mark.usefixtures("restart_api")
def test_unhappy_path_400_error_message(client_api) -> None:
    unknown_sku, order_id = random_sku(), random_orderid()
    data = {"order_id": order_id, "sku": unknown_sku, "qty": 35}

    # url = config.get_api_url()
    r = client_api.post(f"/allocate", json=data)
    assert r.status_code == 400
    assert r.json["message"] == f"Invalid sku {unknown_sku}"


# # @pytest.mark.usefixtures("restart_api")
# def test_allocations_are_persisted(restart_api, add_stock: Callable) -> None:
#     sku = random_sku()
#     batch1, batch2 = random_batchref(str(1)), random_batchref(str(2))
#     order1, order2 = random_orderid(str(1)), random_orderid(str(2))

#     add_stock(
#         [(batch1, sku, 10, "2011-01-01"), (batch2, sku, 10, "2011-01-02")]
#     )
#     line1 = {"orderid": order1, "sku": sku, "qty": 10}
#     line2 = {"orderid": order2, "sku": sku, "qty": 10}
#     url = config.get_api_url()

#     # first order uses up all stock in batch 1
#     r = requests.post(f"{url}/allocate", json=line1)
#     assert r.status_code == 201
#     assert r.json()["batchref"] == batch1

#     # second order should go to batch2
#     r = requests.post(f"{url}/allocate", json=line2)
#     assert r.status_code == 201
#     assert r.json()["batchref"] == batch2


# # @pytest.mark.usefixtures("restartapi")
# def test_400_out_of_stock(restart_api: Callable, add_stock: Callable) -> None:
#     sku, small_batch, large_order = (
#         random_sku(),
#         random_batchref(),
#         random_orderid(),
#     )

#     add_stock([(small_batch, sku, 5, "2011-01-01")])

#     data = {"orderid": large_order, "sku": sku, "qty": 15}

#     # try to allocate an order that exceeds stock
#     url = config.get_api_url()
#     r = requests.post(f"{url}/allocate", json=data)
#     assert r.status_code == 400
#     assert r.json()["message"] == f"Out of stock for sku {sku}"


# # @pytest.mark.usefixtures("restartapi")
# def test_400_invalid_sku(add_stock: Callable) -> None:
#     unknown_sku, orderid = random_sku(), random_orderid()

#     data = {"orderid": orderid, "sku": unknown_sku, "qty": 5}

#     # try to allocate an order that has no sku in stock
#     url = config.get_api_url()
#     r = requests.post(f"{url}/allocate", json=data)
#     assert r.status_code == 400
#     assert r.json()["message"] == f"Invalid sku {unknown_sku}"
