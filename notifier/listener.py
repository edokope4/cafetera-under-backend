from __future__ import annotations

import logging
import signal

import paho.mqtt.client as mqtt

from notifier.config import Settings
from notifier.fcm import FcmClient, FcmError
from notifier.messages import notification_text, turn_off_command

log = logging.getLogger(__name__)


def run(settings: Settings, fcm: FcmClient) -> None:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=settings.mqtt_client_id,
        protocol=mqtt.MQTTv311,
        clean_session=False,
        reconnect_on_failure=True,
    )
    client.reconnect_delay_set(1, 30)
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    if settings.mqtt_tls:
        client.tls_set()

    def on_connect(connected_client, _userdata, _flags, reason_code, _properties) -> None:
        if getattr(reason_code, "is_failure", reason_code not in (0, "Success")):
            log.error("El broker rechazó la conexión: %s", reason_code)
            return
        connected_client.subscribe(settings.mqtt_topic, qos=settings.mqtt_qos)
        log.info("Escuchando %s en %s:%s", settings.mqtt_topic, settings.mqtt_host, settings.mqtt_port)

    def on_message(mqtt_client, _userdata, message) -> None:
        text = notification_text(message.payload, settings.notify_code)
        if text is None:
            log.info("Mensaje ignorado en %s", message.topic)
            return
        log.info("Aviso recibido: %s", text)
        try:
            fcm.send(text, settings.notify_code)
        except FcmError:
            log.exception("No se pudo enviar la notificación")
        command = turn_off_command(message.payload, settings.notify_code)
        if command is None:
            log.info("El aviso ya incluye turn-off; no se vuelve a publicar")
            return
        published = mqtt_client.publish(
            settings.mqtt_command_topic,
            command,
            qos=settings.mqtt_qos,
        )
        if published.rc != mqtt.MQTT_ERR_SUCCESS:
            log.error("No se pudo publicar turn-off en %s", settings.mqtt_command_topic)
            return
        log.info("Orden publicada en %s: %s", settings.mqtt_command_topic, command.decode("utf-8"))

    def stop(_signum, _frame) -> None:
        log.info("Deteniendo")
        client.disconnect()

    client.on_connect = on_connect
    client.on_message = on_message
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    log.info("Conectando a %s:%s", settings.mqtt_host, settings.mqtt_port)
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=30)
    client.loop_forever(retry_first_connection=True)
