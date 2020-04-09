from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import config
from allocation.domain import model
from allocation.service import services, unit_of_work
from allocation.adapters import orm
from allocation.adapters import repository

orm.start_mappers()
app = Flask(__name__)


@app.route("/", methods=["GET"])
def default() -> tuple:
    return jsonify({"status": "on-line"}), 200


@app.route("/allocate", methods=["POST"])
def allocate_endpoint() -> tuple:
    # batches = repository.SqlAlchemyRepository(session).list()
    # line = model.OrderLine()
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.allocate(
            request.json["order_id"],
            request.json["sku"],
            request.json["qty"],
            uow=uow,
        )
    except (services.InvalidSku, model.OutOfStock) as ex:
        return jsonify({"message": ex.message}), 400
    return jsonify({"batchref": batchref}), 201


@app.route("/batch", methods=["POST"])
def post_endpoint() -> tuple:
    # session = get_session()
    # repo = repository.SqlAlchemyRepository(session)

    uow = unit_of_work.SqlAlchemyUnitOfWork()
    services.add_batch(
        ref=request.json["ref"],
        sku=request.json["sku"],
        qty=request.json["qty"],
        eta=request.json["eta"],
        uow=uow,
    )
    return jsonify({"status": "ok"}), 201
