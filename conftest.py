import pytest

from app import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("GREETING", "Hola mundo")
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()