import signal
import sys

from core.logger import log

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)

from core.runtime.session_summary import (
    SessionSummary
)


class ShutdownManager:

    def __init__(
        self,
        websocket
    ):

        self.websocket = websocket

        self.metrics = RuntimeMetrics()

        self.summary = SessionSummary()

    def register(self):

        signal.signal(
            signal.SIGINT,
            self.shutdown
        )

        signal.signal(
            signal.SIGTERM,
            self.shutdown
        )

    def shutdown(
        self,
        signum,
        frame
    ):

        log.info(
            "Graceful shutdown initiated."
        )

        self.metrics.graceful_shutdown()

        try:

            self.websocket.tick_writer.flush()

        except Exception:

            log.exception(
                "Unable to flush tick buffer."
            )

        try:

            self.websocket.disconnect()

        except Exception:

            log.exception(
                "Unable to disconnect websocket."
            )

        self.summary.print_summary()

        sys.exit(0)