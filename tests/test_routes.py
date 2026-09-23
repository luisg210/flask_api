from app import create_app


def test_root_returns_hola_mundo(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.data.decode() == "Hola mundo"
    assert resp.content_type == "text/plain; charset=utf-8"


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.data.decode() == "ok"
    assert resp.content_type == "text/plain; charset=utf-8"


def test_root_uses_greeting_from_env(monkeypatch):
    monkeypatch.setenv("GREETING", "Hola desde env")
    app = create_app()
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.data.decode() == "Hola desde env"


def test_unknown_route_returns_404(client):
    assert client.get("/nope").status_code == 404


def test_post_root_returns_405(client):
    assert client.post("/").status_code == 405


def test_post_health_returns_405(client):
    assert client.post("/health").status_code == 405