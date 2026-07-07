import time

from core.logger import log

from core.scheduler import (
    is_market_open
)


class LiveScheduler:

    def __init__(
        self,
        websocket
    ):
        self.websocket = websocket

    def start(self):

        log.info(
            "Starting live websocket."
        )

        self.websocket.connect()

        try:

            while is_market_open():

                time.sleep(5)

        finally:

            log.info(
                "Stopping live websocket."
            )

            self.websocket.disconnect()