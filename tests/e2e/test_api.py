# Tests API's entrypoint
# Expected behaviors on API requests and responses exclusively
# No usage of domain, services nor any adaptor
# Rui Conti, Apr 2020
import threading
from typing import Any, List

from tenacity import Retrying, stop_after_delay  # type: ignore

from allocation.entrypoints.consumer import parse_encoded_message
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


# @pytest.mark.usefixtures("restart_api")
def test_unhappy_path_400_error_message(client_api) -> None:
    unknown_sku, order_id = random_sku(), random_orderid()
    data = {"order_id": order_id, "sku": unknown_sku, "qty": 35}

    # url = config.get_api_url()
    r = client_api.post(f"/allocate", json=data)
    assert r.status_code == 400
    assert r.json["message"] == f"Invalid sku {unknown_sku}"


def test_allocation_and_query_responsibility(client_api) -> None:
    sku = random_sku()
    earlybatch = random_batchref(str(1))
    post_stock(
        client_api, [(earlybatch, sku, 100, "2011-01-02")],
    )

    orderid = random_orderid()
    data = {"order_id": orderid, "sku": sku, "qty": 90}
    # url = config.get_api_url()
    r = client_api.post(f"/allocate", json=data)
    assert r.status_code == 202

    r = client_api.get(f"/allocations")
    assert r.json[-1] == {
        "id_orderline": orderid,
        "batchref": earlybatch,
        "sku": sku,
        "qty": 90,
    }

    r = client_api.get(f"/allocations/{orderid}")
    assert r.json[0] == {"batchref": earlybatch, "sku": sku, "qty": 90}


# @retry(stop=stop_after_delay(5))
def background_event_listening(pubsub, event_name) -> None:
    for attempt in Retrying(stop=stop_after_delay(5), reraise=True):
        with attempt:
            msg = pubsub.get_message()
            if msg:
                data = parse_encoded_message(msg)["data"]
                assert data["name"] == event_name


def test_events_emmited_to_external_bus(client_api, redis_log_events_pubsub):
    sku = random_sku()
    earlybatch = random_batchref(str(1))
    createbatch = lambda: background_event_listening(
        redis_log_events_pubsub, "BatchCreated"
    )
    thread_cb = threading.Thread(target=createbatch)
    allocate = lambda: background_event_listening(
        redis_log_events_pubsub, "Allocated"
    )
    thread_allocate = threading.Thread(target=allocate)

    thread_cb.start()
    post_stock(
        client_api, [(earlybatch, sku, 100, "2011-01-02")],
    )
    thread_cb.join()

    orderid = random_orderid()
    data = {"order_id": orderid, "sku": sku, "qty": 90}

    thread_allocate.start()
    client_api.post(f"/allocate", json=data)
    thread_allocate.join()
