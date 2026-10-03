# cafetera-under-backend — estado del desarrollo

Documento para retomar el trabajo. Actualizado el 3 de octubre de 2026.

Servicio que escucha el aviso de café listo, envía una notificación push al teléfono y publica la orden de apagado. Python 3.12, Eclipse Paho y la API HTTP v1 de FCM (`google-auth` y `requests`). No usa el SDK `firebase-admin`.

Repositorio: https://github.com/edokope4/cafetera-under-backend

Imagen publicada: `docker.io/edokope/cafetera-under-backend:latest`

## Qué hace

Se suscribe a `MQTT_TOPIC` (por defecto de ejemplo, `cl/kope/iot/cafetera/status`) con QoS 1. El identificador de cliente es `cafetera-backend` y la sesión no es limpia (`clean_session=False`), así que un aviso con QoS 1 que llegó mientras el servicio estaba caído se entrega al volver a arrancar.

Solo actúa si el cuerpo es JSON con `code` igual a `NOTIFY_CODE` (4) y `message` es un texto no vacío. Ejemplo:

```json
{"code": 4, "message": "Cafe listo"}
```

Entonces:

1. Envía a FCM un mensaje de datos, prioridad alta en Android, con `code`, `title`, `message` y `ready_at`. `ready_at` es la hora UTC en la que este servicio acepta el aviso, por ejemplo `2026-10-03T13:05:00Z`. No lleva bloque `notification`, para que la app Android lo reciba aunque esté en primer plano. La app muestra esa hora en la zona del teléfono.
2. Publica en el tópico de órdenes el mismo JSON más `"action": "turn-off"`:

```json
{"code": 4, "message": "Cafe listo", "action": "turn-off"}
```

El tópico de órdenes es `MQTT_COMMAND_TOPIC`. Si no está definido, se usa el tópico de estado sin el sufijo `/status`. Con el ejemplo, queda `cl/kope/iot/cafetera`.

Ese JSON completo también avisa. Si el mensaje que llega ya trae `"action": "turn-off"`, se envía la push y no se vuelve a publicar, para no repetir la orden.

`FCM_PROJECT_ID` es el id del proyecto de Firebase (`cafetera-android`), no el número de proyecto.

## Configuración

Copiar `.env.example` a `.env` y completar los valores. La cuenta de servicio va en `./secrets/firebase.json`. Ninguno de los dos archivos entra en la imagen Docker (`.dockerignore` excluye `.env` y `secrets`).

Variables de `.env.example`:

| Variable | Uso |
| --- | --- |
| `MQTT_HOST`, `MQTT_PORT` | Broker. Prueba: `test.mosquitto.org`, `1883`. |
| `MQTT_USERNAME`, `MQTT_PASSWORD` | Opcionales. |
| `MQTT_TLS` | `true` para TLS. |
| `MQTT_TOPIC` | Tópico de estado que se escucha. |
| `MQTT_COMMAND_TOPIC` | Tópico donde se publica `turn-off`. |
| `MQTT_QOS` | 0, 1 o 2. El ejemplo usa 1. |
| `MQTT_CLIENT_ID` | Por defecto `cafetera-backend`. |
| `NOTIFY_CODE` | Código que dispara el aviso. Ejemplo: 4. |
| `NOTIFY_TITLE` | Título del dato FCM. Ejemplo: Cafetera. |
| `FCM_PROJECT_ID` | Id del proyecto de Firebase. |
| `FCM_TOKEN` | Token del dispositivo. Sale de la app con `debug=true`. |
| `GOOGLE_APPLICATION_CREDENTIALS` | En el contenedor: `/run/secrets/firebase.json`. |

## Ejecutar

Con Docker Compose, en esta carpeta:

```powershell
docker compose up -d --build
docker compose logs -f notifier
```

El servicio se llama `notifier`, reinicia salvo que se detenga a mano y monta `./secrets/firebase.json` en solo lectura.

La imagen ya construida en Docker Hub no trae secretos. Para usarla hay que pasar el entorno y el archivo de la cuenta de servicio, igual que hace Compose.

Sin contenedor:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

En ese caso `GOOGLE_APPLICATION_CREDENTIALS` debe apuntar a un archivo que exista en el equipo.

Pruebas:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_messages
```

## Código

- `main.py` — lee la configuración y arranca el bucle.
- `notifier/config.py` — variables de entorno.
- `notifier/listener.py` — suscripción, aviso y publicación de `turn-off`.
- `notifier/messages.py` — reconoce el JSON y arma la orden.
- `notifier/fcm.py` — envía el mensaje de datos.
- `tests/test_messages.py` — el aviso, el `turn-off` y el mensaje que ya trae la orden.

## Pendiente

- `.env`, `.env-cafetera-under` y `secrets/firebase.json` no se versionan.
- Al recrear el contenedor, la sesión MQTT persistente puede entregar otra vez un «Cafe listo» en cola y el teléfono recibe el aviso de nuevo.
- El token de FCM es de un solo dispositivo. Cambiar de teléfono exige actualizar `FCM_TOKEN`.
