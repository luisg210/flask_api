from flask import Blueprint, Response

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> Response:
    return Response("Hola mundo", mimetype="text/plain")


@bp.get("/health")
def health() -> Response:
    return Response("ok", mimetype="text/plain")