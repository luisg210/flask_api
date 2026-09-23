# API REST básica en Flask - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una API REST mínima en Flask con un patrón de app factory, 2 endpoints (`/` y `/health`) que devuelven texto plano, y tests con pytest.

**Architecture:** Paquete `app/` con `create_app()` en `__init__.py` que registra el blueprint `main` definido en `routes.py`. Los endpoints devuelven `Response(..., mimetype="text/plain")` porque Flask usa `text/html` por defecto. Los tests usan `app.test_client()` a través de un fixture en `conftest.py`.

**Tech Stack:** Python 3.14+, Flask, pytest, venv, git.

**Spec:** `docs/superpowers/specs/2026-09-22-flask-api-basica-design.md`

## Global Constraints

- Python 3.14+ (versión instalada en el sistema: 3.14.7).
- Dependencias exactas en `requirements.txt`: `Flask` y `pytest`.
- El paquete interno se llama `app` (no `flask_api`) para evitar colisión con Flask y porque la raíz ya se llama así.
- Endpoints fijos (método GET, status 200, Content-Type `text/plain`):
  - `GET /` → `Hola mundo`
  - `GET /health` → `ok`
- Arranque con `flask --app app run`.
- Raíz del proyecto: `F:\Luis\Python\flask_api` (Windows, PowerShell 5.1).

## Review Focus

- Ruta no definida (ej. `GET /nope`) → debe responder `404` (pinned en Task 2).
- Método no permitido (ej. `POST /`, `POST /health`) → debe responder `405` (pinned en Task 2).
- `Content-Type` debe ser `text/plain` y no `text/html`, en ambos endpoints (pinned en Task 2).

---

### Task 1: Scaffold del proyecto (git, venv, dependencias)

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`

**Interfaces:**
- Consumes: nada.
- Produces: repositorio git inicializado en la raíz, entorno virtual `.venv` con Flask y pytest instalados, `requirements.txt`. Tasks posteriores ejecutan pytest y flask desde `.venv`.

- [ ] **Step 1: Inicializar git (la carpeta no es un repo)**

Run:
```bash
git init
```
Expected: mensaje `Initialized empty Git repository`.

- [ ] **Step 2: Crear `.gitignore`**

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 3: Crear `requirements.txt`**

```
Flask
pytest
```

- [ ] **Step 4: Crear venv e instalar dependencias**

Run:
```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```
Expected: pip instala Flask y pytest sin errores.

- [ ] **Step 5: Verificar instalación**

Run: `.\.venv\Scripts\python -m flask --version`
Expected: imprime versión de Flask (ej. `Python 3.14.7 ... Flask 3.x.y`).

- [ ] **Step 6: Commit**

```bash
git add .gitignore requirements.txt
git commit -m "build: scaffold flask project with venv and deps"
```

### Task 2: App factory con los 2 endpoints (TDD)

**Files:**
- Create: `app/__init__.py`
- Create: `app/routes.py`
- Create: `conftest.py`
- Test: `tests/test_routes.py`

**Interfaces:**
- Consumes: nada de tareas anteriores (solo el entorno de Task 1).
- Produces:
  - `from app import create_app` → `callable() -> flask.Flask` con los blueprint registrados.
  - `from app.routes import bp` → `Blueprint("main", __name__)` con rutas `/` y `/health`.
  - Fixture de pytest `client` (definido en `conftest.py`): `flask.testing.FlaskClient` con `TESTING=True`. Tasks que descarguen pytest lo consumen por inyección: `def test_x(client):`.

- [ ] **Step 1: Escribir los tests (fallan)**

Create `conftest.py` en la raíz:

```python
import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
```

Create `tests/test_routes.py`:

```python
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


def test_unknown_route_returns_404(client):
    assert client.get("/nope").status_code == 404


def test_post_root_returns_405(client):
    assert client.post("/").status_code == 405


def test_post_health_returns_405(client):
    assert client.post("/health").status_code == 405
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app'` (o similar). `conftest.py` en la raíz hace que pytest añada la raíz al `sys.path`, así que el error confirma la ausencia de código, no un problema de importación.

- [ ] **Step 3: Implementación mínima**

Create `app/__init__.py`:

```python
from flask import Flask

from app.routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
```

Create `app/routes.py`:

```python
from flask import Blueprint, Response

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> Response:
    return Response("Hola mundo", mimetype="text/plain")


@bp.get("/health")
def health() -> Response:
    return Response("ok", mimetype="text/plain")
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 5 passed.

- [ ] **Step 5: Smoke test de arranque**

En una terminal aparte:
```bash
.\.venv\Scripts\flask --app app run
```

Luego, desde otra terminal:
```bash
Invoke-WebRequest http://127.0.0.1:5000/ -UseBasicParsing | Select-Object StatusCode, ContentType, Content
Invoke-WebRequest http://127.0.0.1:5000/health -UseBasicParsing | Select-Object StatusCode, ContentType, Content
```
Expected: ambas respuestas con `StatusCode: 200`, `ContentType: text/plain; charset=utf-8`, y content `Hola mundo` / `ok`. Detener el servidor (Ctrl+C).

- [ ] **Step 6: Commit**

```bash
git add app/ conftest.py tests/
git commit -m "feat: add app factory with hola mundo and health endpoints"
```