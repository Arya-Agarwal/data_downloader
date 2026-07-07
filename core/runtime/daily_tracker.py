from core.logger import log

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)


class DailyTracker:

    def __init__(self):

        self.metrics = RuntimeMetrics()

    def report(self):

        log.info(

            "\n"

            "========== LIVE STATUS ==========\n"

            f"Connected      : {self.metrics.connected}\n"

            f"Reconnects     : {self.metrics.reconnects}\n"

            f"Total Ticks    : {self.metrics.total_ticks}\n"

            f"Spot Ticks     : {self.metrics.spot_ticks}\n"

            f"Future Ticks   : {self.metrics.future_ticks}\n"

            f"Option Ticks   : {self.metrics.option_ticks}\n"

            f"Rows Written   : {self.metrics.rows_written}\n"

            f"Files Written  : {self.metrics.files_written}\n"

            f"Subscriptions  : {self.metrics.subscribed}\n"

            f"Buffer Size    : {self.metrics.buffer_size}\n"

            f"Last Tick      : {self.metrics.last_tick}\n"

            "===============================\n"

        )