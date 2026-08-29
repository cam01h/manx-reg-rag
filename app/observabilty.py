import logging
import logfire
from config import SEND_TO_LOGFIRE, SERVICE_NAME


def configure_logfire() -> None:
    logfire.configure(
        service_name=SERVICE_NAME,
        send_to_logfire=SEND_TO_LOGFIRE,
        console=False,
    )
    logfire.instrument_pydantic_ai()
    handler = logfire.LogfireLoggingHandler()
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
