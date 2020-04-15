import threading

from tenacity import Retrying, stop_after_delay  # type: ignore

from allocation.entrypoints.consumer import parse_encoded_message
from tests.e2e.test_api import post_stock
from tests.helpers import random_sku, random_batchref, random_orderid


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
