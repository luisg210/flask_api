# Deploy de la API Flask en Debian (Gunicorn + Nginx + systemd)

Guía de despliegue completa para subir esta API (`app/`, factory `create_app()`)
a un servidor Linux **Debian** y servirla detrás de **Nginx** con **Gunicorn**
gestionado por **systemd**.

> **Importante:** `flask --app app run` usa el servidor de desarrollo de Flask.
> No es apto para producción: no escala y no está endurecido. Por eso usamos
> Gunicorn como servidor WSGI y Nginx como front HTTP.

---

## 0. Prerequisitos

- Servidor **Debian** (11/12/13) con acceso por SSH.
- Usuario con privilegios `sudo`.
- Puerto 80 accesible si vas a exponer HTTP directo (o 443 si añades HTTPS, sección 8).
- Esta guía asume que trabajas como tu usuario con `sudo`; los comandos con
  `#` se ejecutan con privilegios elevados (`sudo`).

Versiones objetivo:
- Python **3.11+** (el proyecto se desarrolló con 3.14, pero Gunicorn
  `23.x+` funciona con 3.11 en adelante).
- Gunicorn **23.x**, Nginx, systemd.

---

## 1. Preparar el sistema

Actualiza el sistema e instala lo que hace falta para el proyecto:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git curl build-essential
```

Comprueba la versión de Python:

```bash
python3 --version   # esperado: 3.11 o superior
```

---

## 2. Transferir el código

Elige una de las dos opciones.

### Opción A — clonar desde un repositorio git

```bash
sudo mkdir -p /opt/flask_api
sudo chown "$USER":"$USER" /opt/flask_api
git clone <URL_DEL_REPO> /opt/flask_api
```

### Opción B — copiar manualmente (scp)

Desde tu máquina local:

```bash
scp -r app requirements.txt .env.example usuario@SERVIDOR:/tmp/flask_api
```

Y dentro del servidor:

```bash
sudo mkdir -p /opt/flask_api
sudo cp -r /tmp/flask_api/* /opt/flask_api/
sudo rm -rf /tmp/flask_api
```

En ambos casos, verifica que la estructura quedó así:

```bash
ls -R /opt/flask_api
# ./app/__init__.py
# ./app/routes.py
# ./requirements.txt
# ...
```

---

## 3. Entorno virtual y dependencias

```bash
cd /opt/flask_api
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

> `requirements.txt` instala `Flask`, `python-dotenv` y `pytest`.
> Necesitamos además `gunicorn`; lo instalamos en el mismo venv:

```bash
.venv/bin/pip install gunicorn
```

Instala también systemd, Nginx y el soporte de Python del proyecto (ya
instalado en la sección 1, pero por si partes de una imagen mínima):

```bash
sudo apt install -y systemd nginx
```

---

## 4. Config de entorno (`.env`)

Crea el `.env` de producción a partir del ejemplo:

```bash
cd /opt/flask_api
cp .env.example .env
```

Edítalo con tu editor preferido (`nano .env`) y deja el valor que quieras
para `GREETING`. Asegúrate de que el usuario que ejecuta Gunicorn pueda
leerlo, pero no el resto del sistema:

```bash
sudo chown www-data:www-data .env
sudo chmod 0400 .env
```

> `python-dotenv` se carga dentro de `create_app()` (lo hace `load_dotenv()`
> en `app/__init__.py`), así que el `.env` se lee igual en los tests y en
> producción.

---

## 5. Probar Gunicorn manualmente

Antes de montar systemd, verifica que Gunicorn levanta la app. Lo lanzamos
en segundo plano y le damos un `curl`:

```bash
cd /opt/flask_api
.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 "app:create_app()" &
sleep 3
curl -i http://127.0.0.1:8000/
curl -i http://127.0.0.1:8000/health
```

Respuestas esperadas:

- `/` → `200`, `Content-Type: text/plain; charset=utf-8`, cuerpo `Hola mundo`.
- `/health` → `200`, cuerpo `ok`.

Detén Gunicorn antes de continuar:

```bash
kill %1
```

> `"app:create_app()"` invoca la factory, así que no hace falta
> `FLASK_APP`. Si tu `.env` define otro `GREETING`, el cuerpo de `/`
> será el del `.env`, no `Hola mundo`. Es lo esperado.

---

## 6. Servicio systemd

Crea la unidad:

```bash
sudo nano /etc/systemd/system/flask-api.service
```

Contenido:

```ini
[Unit]
Description=Flask API (gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/flask_api
EnvironmentFile=/opt/flask_api/.env
ExecStart=/opt/flask_api/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 "app:create_app()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> `--workers 2` es razonable para un VPS pequeño (regla práctica:
> `2 * CPUs + 1`, pero 2 basta para esta API). Nunca uses el dev server
> aquí.

Recarga systemd, arranca y marca el arranque automático:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now flask-api
```

Verifica:

```bash
sudo systemctl status flask-api --no-pager
curl -i http://127.0.0.1:8000/
```

Logs si algo no arranca:

```bash
sudo journalctl -u flask-api --no-pager -n 50
```

---

## 7. Nginx como proxy inverso

Los `permissions` del `.env` los fijamos en la sección 4; Nginx se encarga
de exponer el puerto 80 hacia `127.0.0.1:8000`.

Crea el site:

```bash
sudo nano /etc/nginx/sites-available/flask-api
```

Contenido:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> `server_name _;` responde a cualquier host. Si tienes dominio, ponlo
> aquí p. ej. `server_name api.midominio.com;`.

Activa el site y elimina el default si no lo necesitas:

```bash
sudo ln -s /etc/nginx/sites-available/flask-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Verificación final por el puerto 80:

```bash
curl -i http://127.0.0.1/
curl -i http://127.0.0.1/health
```

Desde fuera del servidor (en tu máquina local):

```bash
curl -i http://IP_DEL_SERVIDOR/
```

---

## 8. Firewall (ufw)

Solo abre lo imprescindible:

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

> `'Nginx Full'` abarca el 80 y el 443, listo para la sección de HTTPS.
> Si algo más necesita acceso (p. ej. puertos extra), ábrelos antes de
> `ufw enable` o el `enable` cortará tu sesión SSH de un modo brusco.

---

## 9. HTTPS con Let's Encrypt (opcional pero recomendado)

Si tienes un dominio apuntando a la IP, instala Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.midominio.com
```

Sigue las preguntas; Certbot edita el site de Nginx solo. Renovación
automática ya viene instalada por el paquete:

```bash
sudo certbot renew --dry-run
```

---

## 10. Actualizar la API

Cada vez que quieras desplegar una versión nueva:

```bash
cd /opt/flask_api
git pull                              # opción A (git)
# o copia de nuevo los archivos        # opción B (scp)
.venv/bin/pip install -r requirements.txt   # solo si cambió requirements
sudo systemctl restart flask-api
```

Verifica:

```bash
curl -i http://127.0.0.1/health
```

---

## 11. Troubleshooting

| Síntoma | Causa probable | Qué mirar |
| --- | --- | --- |
| `502 Bad Gateway` | Gunicorn caído | `sudo systemctl status flask-api`, `sudo journalctl -u flask-api -n 50` |
| Nginx no levanta | Config inválida | `sudo nginx -t` |
| `/` devuelve `Hola mundo` pese al `.env` | `.env` ilegible o ruta mal | `sudo -u www-data cat /opt/flask_api/.env`, `ls -l /opt/flask_api/.env` |
| Puerto 80 no responde fuera | ufw bloqueando | `sudo ufw status`, `sudo ufw allow 'Nginx Full'` |
| Gunicorn no encuentra el venv | Ejecutado como otro usuario | Comprobar `ExecStart` en la unidad: usa la ruta absoluta del venv |
| Changes no se ven tras `git pull` | Servicio no reiniciado | `sudo systemctl restart flask-api` |

---

## 12. Resumen de la arquitectura

```
Cliente ──HTTP/80──▶ Nginx (proxy inverso)
                        │ proxy_pass → 127.0.0.1:8000
                        ▼
                    Gunicorn (WSGI, 2 workers, systemd lo mantiene vivo)
                        │
                        ▼
                    Flask app (app:create_app), lee el .env con python-dotenv
```