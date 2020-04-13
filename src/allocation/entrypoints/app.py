from flask import Flask, jsonify, request

from allocation.domain import commands
from allocation.service import handlers, unit_of_work, message_bus
from allocation.adapters import orm

orm.start_mappers()
app = Flask(__name__)


@app.route("/", methods=["GET"])  # type: ignore
def default() -> tuple:
    return jsonify({"status": "on-line"}), 200


@app.route("/allocate", methods=["POST"])  # type: ignore
def allocate_endpoint() -> tuple:
    # batches = repository.SqlAlchemyRepository(session).list()
    # line = model.OrderLine()
    try:
        command = commands.Allocate(
            order_id=request.json["order_id"],
            sku=request.json["sku"],
            qty=request.json["qty"],
        )
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        message_bus.handle(command, uow)
    except handlers.InvalidSku as ex:
        return jsonify({"message": ex.message}), 400
    return jsonify({"status": "ok"}), 202


@app.route("/batch", methods=["POST"])  # type: ignore
def post_endpoint() -> tuple:
    # session = get_session()
    # repo = repository.SqlAlchemyRepository(session)

    command = commands.CreateBatch(
        ref=request.json["ref"],
        sku=request.json["sku"],
        qty=request.json["qty"],
        eta=request.json["eta"],
    )
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    message_bus.handle(command, uow)
    return jsonify({"status": "ok"}), 201
