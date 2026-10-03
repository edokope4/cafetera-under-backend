import logging
import sys

from notifier.config import ConfigError, Settings
from notifier.fcm import FcmClient
from notifier.listener import run


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    try:
        settings = Settings.from_env()
    except ConfigError as error:
        logging.error("%s", error)
        sys.exit(1)
    fcm = FcmClient(
        project_id=settings.fcm_project_id,
        credentials_path=settings.google_credentials,
        token=settings.fcm_token,
        title=settings.notify_title,
    )
    run(settings, fcm)


if __name__ == "__main__":
    main()
