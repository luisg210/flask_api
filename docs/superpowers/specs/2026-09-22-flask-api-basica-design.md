# Diseño: API REST básica en Flask

Fecha: 2026-09-22
Estado: aprobado (diseño en chat)

## Propósito

Crear una API REST mínima en Flask con exactamente 2 endpoints que
devuelvan texto plano (`text/plain`). No hay base de datos, autenticación
ni lógica de negocio. Es una base sencilla para proyectos futuros.

## Endpoints

| Método | Ruta      | Respuesta (status, Content-Type, body) |
| ------ | --------- | --------------------------------------- |
| GET    | `/`       | `200`, `text/plain`, `GREETING` (default `Hola mundo`) |
| GET    | `/health` | `200`, `text/plain`, `ok`       |

No hay manejo especial de errores: los endpoints no dependen de estado
ni de recursos externos, así que se usa el manejo por defecto de Flask.
Cualquier ruta no definida devuelve `404` estándar.

## Estructura del proyecto

```
flask_api/                       # raíz del proyecto (reside en F:\Luis\Python\flask_api)
├── app/
│   ├── __init__.py              # create_app(): fábrica de la aplicación Flask
│   └── routes.py                # blueprint con los 2 endpoints
├── tests/
│   └── test_routes.py           # pruebas con pytest y app.test_client()
└── requirements.txt             # dependencias: Flask, python-dotenv, pytest
```

Decisión de naming: el paquete interno se llama `app` para evitar colisión
con el módulo `flask` y porque la carpeta raíz ya se llama `flask_api`.

## Componentes

### app/__init__.py

- Define `create_app()` (fábrica). Crea la instancia `Flask(__name__)`,
  registra el blueprint de `routes.py` y la devuelve.
- Flask CLI detecta esta fábrica automáticamente con `flask --app app run`,
  por lo que no se necesita script de arranque.

### app/routes.py

- Define `bp = Blueprint("main", __name__)`.
- `@bp.get("/")` → devuelve `current_app.config["GREETING"]`.
- `@bp.get("/health")` → devuelve `"ok"`.
- `create_app()` llama `load_dotenv()` y configura
  `GREETING = os.environ.get("GREETING", "Hola mundo")`.
- Flask usa `Content-Type: text/html` por defecto al devolver un string,
  así que cada respuesta se construye con `Response(..., mimetype="text/plain")`
  para garantizar `Content-Type: text/plain; charset=utf-8`.

## Pruebas

- pytest con `app.test_client()`.
- Casos:
  1. `GET /` → status `200`, body `"Hola mundo"`.
  2. `GET /health` → status `200`, body `"ok"`.
- Verificación de `Content-Type: text/plain` en ambos casos.

## Verificación / ejecución

1. Crear venv e instalar dependencias: `pip install -r requirements.txt`
   (dependencias: `Flask` y `pytest`).
2. Correr pruebas: `pytest`.
3. Arranque local: `flask --app app run`.

## Fuera de alcance

- Base de datos, autenticación, CORS, logging, despliegue.
- Endpoints adicionales más allá de los 2 definidos.
- Estructura empaquetable publicable (setup.py / pyproject).