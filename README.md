# cafetera-under-backend

Servicio que escucha el aviso de café listo, envía una notificación al teléfono y, si hace falta, publica la orden de apagado.

Python 3.12, Eclipse Paho y la API HTTP v1 de FCM. No usa el SDK `firebase-admin`.

Imagen: [edokope/cafetera-under-backend](https://hub.docker.com/r/edokope/cafetera-under-backend)

## Piezas

| Pieza | Repositorio | Rol |
| --- | --- | --- |
| App Android | [cafetera](https://github.com/edokope4/cafetera) | Pide el café y muestra el ticket |
| Placa ESP8266 | [arduino-cafetera](https://github.com/edokope4/arduino-cafetera) | Parpadea 30 segundos y publica el café listo |
| Radar MQTT | [radar-mqtt](https://github.com/edokope4/radar-mqtt) | Cliente de Windows para escuchar y publicar |
| Este servicio | [cafetera-under-backend](https://github.com/edokope4/cafetera-under-backend) | Avisa al teléfono |

## MQTT

Broker de prueba: `broker.hivemq.com`, puerto 1883.

| Tópico | Mensaje | Qué hace este servicio |
| --- | --- | --- |
| `cl/kope/iot/cafetera/status` | `{"code": 4, "message": "Cafe listo", "action": "turn-off"}` | Envía la push y no vuelve a publicar, porque ya trae `turn-off` |
| `cl/kope/iot/cafetera/status` | `{"code": 4, "message": "Cafe listo"}` | Envía la push y publica la orden de apagado |
| `cl/kope/iot/cafetera` | `{"code": 4, "message": "Cafe listo", "action": "turn-off"}` | Destino de esa orden |

La push es un mensaje de datos de FCM, prioridad alta, sin bloque `notification`. Incluye `ready_at` en UTC, la hora en que este servicio acepta el aviso. La app la muestra en la zona del teléfono.

Un JSON con otro `code`, sin `message`, o que no es JSON, se ignora.

La suscripción usa QoS 1 y una sesión que no es limpia. Un aviso que llegó mientras el servicio estaba detenido puede entregarse al arrancar y el teléfono recibe otra notificación.

## Configuración

Copiar `.env.example` a `.env` y completar los valores. La cuenta de servicio de Firebase va en `secrets/firebase.json`. Esos archivos no se versionan y tampoco entran en la imagen Docker.

| Variable | Uso |
| --- | --- |
| `MQTT_HOST`, `MQTT_PORT` | Broker |
| `MQTT_USERNAME`, `MQTT_PASSWORD` | Opcionales |
| `MQTT_TLS` | `true` para TLS |
| `MQTT_TOPIC` | Tópico de estado. Ejemplo: `cl/kope/iot/cafetera/status` |
| `MQTT_COMMAND_TOPIC` | Tópico de la orden. Si se omite, se usa el de estado sin `/status` |
| `MQTT_QOS` | 0, 1 o 2 |
| `MQTT_CLIENT_ID` | Por defecto `cafetera-backend` |
| `NOTIFY_CODE` | Código que dispara el aviso. Ejemplo: 4 |
| `NOTIFY_TITLE` | Título del dato FCM |
| `FCM_PROJECT_ID` | Id del proyecto de Firebase, no el número |
| `FCM_TOKEN` | Token del teléfono. La app lo muestra con `debug=true` |
| `GOOGLE_APPLICATION_CREDENTIALS` | En el contenedor: `/run/secrets/firebase.json` |

## Ejecutar

Con Docker Compose:

```powershell
docker compose up -d --build
docker compose logs -f notifier
```

Para bajar la imagen ya publicada y arrancar el contenedor `cafeteraUnder`, los scripts están en `scripts/`. Leen `scripts/.env-cafetera-under` y montan `secrets/firebase.json`.

```bat
scripts\deployCafeteraUnder.bat
```

```bash
bash scripts/deployCafeteraUnder.sh
bash scripts/logsCafeteraUnder.sh
```

Sin contenedor:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Pruebas:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_messages
```

El detalle para retomar el trabajo está en [doc/desarrollo.md](doc/desarrollo.md).
