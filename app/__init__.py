import os

from dotenv import load_dotenv
from flask import Flask

from app.routes import bp


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config["GREETING"] = os.environ.get("GREETING", "Hola mundo")
    app.register_blueprint(bp)
    return app