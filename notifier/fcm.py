from __future__ import annotations

import logging

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from notifier.messages import ready_stamp

log = logging.getLogger(__name__)

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class FcmError(Exception):
    pass


class FcmClient:
    def __init__(self, project_id: str, credentials_path: str, token: str, title: str) -> None:
        self._project_id = project_id
        self._device_token = token
        self._title = title
        self._credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[FCM_SCOPE],
        )
        self._session = requests.Session()

    def send(self, body: str, code: int, ready_at: str | None = None) -> None:
        stamp = ready_at or ready_stamp()
        response = self._post(body, code, stamp)
        if response.status_code == 401:
            self._credentials.refresh(Request())
            response = self._post(body, code, stamp)
        if response.status_code >= 400:
            detail = response.text.replace("\n", " ")[:300]
            raise FcmError(f"FCM respondió {response.status_code}: {detail}")
        log.info("Notificación enviada, hora %s", stamp)

    def _post(self, body: str, code: int, ready_at: str) -> requests.Response:
        if not self._credentials.valid:
            self._credentials.refresh(Request())
        url = f"https://fcm.googleapis.com/v1/projects/{self._project_id}/messages:send"
        payload = {
            "message": {
                "token": self._device_token,
                "data": {
                    "code": str(code),
                    "title": self._title,
                    "message": body,
                    "ready_at": ready_at,
                },
                "android": {
                    "priority": "HIGH",
                },
            }
        }
        return self._session.post(
            url,
            headers={"Authorization": f"Bearer {self._credentials.token}"},
            json=payload,
            timeout=15,
        )
