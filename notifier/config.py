from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(Exception):
    pass


def _required(env: Mapping[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise ConfigError(f"Falta la variable {key}")
    return value


def _command_topic(env: Mapping[str, str], status_topic: str) -> str:
    configured = env.get("MQTT_COMMAND_TOPIC", "").strip()
    if configured:
        return configured
    suffix = "/status"
    if status_topic.endswith(suffix):
        return status_topic[: -len(suffix)]
    return status_topic


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "si", "sí"}


@dataclass(frozen=True)
class Settings:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_tls: bool
    mqtt_topic: str
    mqtt_command_topic: str
    mqtt_qos: int
    mqtt_client_id: str
    notify_code: int
    notify_title: str
    fcm_project_id: str
    fcm_token: str
    google_credentials: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if env is None else env
        port_text = source.get("MQTT_PORT", "1883").strip() or "1883"
        qos_text = source.get("MQTT_QOS", "1").strip() or "1"
        code_text = source.get("NOTIFY_CODE", "4").strip() or "4"
        try:
            port = int(port_text)
            qos = int(qos_text)
            notify_code = int(code_text)
        except ValueError as error:
            raise ConfigError("MQTT_PORT, MQTT_QOS y NOTIFY_CODE deben ser números") from error
        if port < 1 or port > 65535:
            raise ConfigError("MQTT_PORT está fuera de rango")
        if qos not in (0, 1, 2):
            raise ConfigError("MQTT_QOS debe ser 0, 1 o 2")

        credentials = _required(source, "GOOGLE_APPLICATION_CREDENTIALS")
        if not os.path.isfile(credentials):
            raise ConfigError(f"No se encontró el archivo de credenciales: {credentials}")

        return cls(
            mqtt_host=_required(source, "MQTT_HOST"),
            mqtt_port=port,
            mqtt_username=source.get("MQTT_USERNAME", "").strip(),
            mqtt_password=source.get("MQTT_PASSWORD", ""),
            mqtt_tls=_bool(source.get("MQTT_TLS", "false")),
            mqtt_topic=(status_topic := _required(source, "MQTT_TOPIC")),
            mqtt_command_topic=_command_topic(source, status_topic),
            mqtt_qos=qos,
            mqtt_client_id=source.get("MQTT_CLIENT_ID", "cafetera-backend").strip() or "cafetera-backend",
            notify_code=notify_code,
            notify_title=source.get("NOTIFY_TITLE", "Cafetera").strip() or "Cafetera",
            fcm_project_id=_required(source, "FCM_PROJECT_ID"),
            fcm_token=_required(source, "FCM_TOKEN"),
            google_credentials=credentials,
        )
