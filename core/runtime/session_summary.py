from core.logger import log

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)


class SessionSummary:

    def __init__(self):

        self.metrics = RuntimeMetrics()

    def print_summary(self):

        log.info(

            "\n"

            "========== SESSION SUMMARY ==========\n"

            f"Connected      : {self.metrics.connected}\n"

            f"Reconnects     : {self.metrics.reconnects}\n"

            f"Ticks          : {self.metrics.total_ticks}\n"

            f"Spot           : {self.metrics.spot_ticks}\n"

            f"Future         : {self.metrics.future_ticks}\n"

            f"Option         : {self.metrics.option_ticks}\n"

            f"Rows Written   : {self.metrics.rows_written}\n"

            f"Files Written  : {self.metrics.files_written}\n"

            f"Shutdown       : {self.metrics.shutdown}\n"

            "===================================="

        )