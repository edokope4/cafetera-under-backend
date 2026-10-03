from __future__ import annotations

import json
from datetime import datetime, timezone


def notification_text(payload: bytes, notify_code: int) -> str | None:
    """Devuelve el texto de la push si el mensaje es el aviso esperado."""
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    code = data.get("code")
    if code != notify_code and str(code).strip() != str(notify_code):
        return None
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return None
    return message.strip()


def ready_stamp(moment: datetime | None = None) -> str:
    """Hora UTC en la que el backend acepta el aviso de café listo."""
    current = moment or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc).replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z")


def turn_off_command(payload: bytes, notify_code: int) -> bytes | None:
    """Agrega action turn-off al aviso de café listo."""
    if notification_text(payload, notify_code) is None:
        return None
    data = json.loads(payload.decode("utf-8"))
    if data.get("action") == "turn-off":
        return None
    data["action"] = "turn-off"
    return json.dumps(data, ensure_ascii=False, separators=(", ", ": ")).encode("utf-8")
