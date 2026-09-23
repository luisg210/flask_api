from flask import Blueprint, Response, current_app

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> Response:
    return Response(current_app.config["GREETING"], mimetype="text/plain")


@bp.get("/health")
def health() -> Response:
    return Response("ok", mimetype="text/plain")