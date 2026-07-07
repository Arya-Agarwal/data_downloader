from datetime import timedelta

from core.logger import log

from core.utils.time_utils import (
    now_ist
)

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)


class TickWatchdog:

    WARNING_SECONDS = 30

    ERROR_SECONDS = 60

    def __init__(self):

        self.metrics = RuntimeMetrics()

    def check(self):

        if self.metrics.last_tick is None:
            return

        delay = (

            now_ist()

            -

            self.metrics.last_tick

        ).total_seconds()

        if delay >= self.ERROR_SECONDS:

            log.error(

                f"No ticks received "

                f"for {int(delay)} sec."

            )

        elif delay >= self.WARNING_SECONDS:

            log.warning(

                f"No ticks received "

                f"for {int(delay)} sec."

            )