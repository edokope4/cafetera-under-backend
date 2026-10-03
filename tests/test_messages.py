import unittest
from pathlib import Path

from notifier.config import ConfigError, Settings
from datetime import datetime, timezone

from notifier.messages import notification_text, ready_stamp, turn_off_command


class NotificationTextTest(unittest.TestCase):
    def test_accepts_expected_code(self) -> None:
        payload = b'{"code": 4, "message": "Cafe listo"}'
        self.assertEqual(notification_text(payload, 4), "Cafe listo")

    def test_accepts_code_as_text(self) -> None:
        payload = b'{"code": "4", "message": " Cafe listo "}'
        self.assertEqual(notification_text(payload, 4), "Cafe listo")

    def test_ignores_other_codes(self) -> None:
        payload = b'{"code": 1, "message": "Encendida"}'
        self.assertIsNone(notification_text(payload, 4))

    def test_ignores_invalid_json(self) -> None:
        self.assertIsNone(notification_text(b"hacer", 4))
        self.assertIsNone(notification_text(b'{"code": 4}', 4))

    def test_accepts_ready_message_with_turn_off(self) -> None:
        payload = b'{"code": 4, "message": "Cafe listo", "action": "turn-off"}'
        self.assertEqual(notification_text(payload, 4), "Cafe listo")


class ReadyStampTest(unittest.TestCase):
    def test_formats_utc(self) -> None:
        moment = datetime(2026, 10, 3, 13, 5, tzinfo=timezone.utc)
        self.assertEqual(ready_stamp(moment), "2026-10-03T13:05:00Z")


class TurnOffCommandTest(unittest.TestCase):
    def test_adds_turn_off_to_ready_message(self) -> None:
        payload = b'{"code": 4, "message": "Cafe listo"}'
        self.assertEqual(
            turn_off_command(payload, 4),
            b'{"code": 4, "message": "Cafe listo", "action": "turn-off"}',
        )

    def test_does_not_repeat_turn_off(self) -> None:
        payload = b'{"code": 4, "message": "Cafe listo", "action": "turn-off"}'
        self.assertIsNone(turn_off_command(payload, 4))

    def test_ignores_other_messages(self) -> None:
        self.assertIsNone(turn_off_command(b'{"code": 1, "message": "Encendida"}', 4))


class SettingsTest(unittest.TestCase):
    def test_reads_environment(self) -> None:
        credentials = Path(__file__).with_name("firebase.json")
        credentials.write_text("{}", encoding="utf-8")
        self.addCleanup(credentials.unlink, missing_ok=True)
        settings = Settings.from_env(
            {
                "MQTT_HOST": "broker.local",
                "MQTT_PORT": "1883",
                "MQTT_TOPIC": "cafetera/status",
                "MQTT_TLS": "false",
                "NOTIFY_CODE": "4",
                "FCM_PROJECT_ID": "cafetera-app",
                "FCM_TOKEN": "token",
                "GOOGLE_APPLICATION_CREDENTIALS": str(credentials),
            }
        )
        self.assertEqual(settings.mqtt_host, "broker.local")
        self.assertEqual(settings.notify_code, 4)
        self.assertEqual(settings.mqtt_command_topic, "cafetera")
        self.assertFalse(settings.mqtt_tls)

    def test_requires_firebase_values(self) -> None:
        with self.assertRaises(ConfigError):
            Settings.from_env({"MQTT_HOST": "broker.local", "MQTT_TOPIC": "estado"})


if __name__ == "__main__":
    unittest.main()
