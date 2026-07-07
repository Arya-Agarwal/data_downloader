import threading
import time

from core.runtime.daily_tracker import (
    DailyTracker
)

from core.runtime.tick_watchdog import (
    TickWatchdog
)


class HealthMonitor:

    def __init__(
        self,
        interval=60
    ):

        self.interval = interval

        self.tracker = DailyTracker()

        self.watchdog = TickWatchdog()

        self.running = False

        self.thread = None

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        self.running = False

    def run(self):

        while self.running:

            self.watchdog.check()

            self.tracker.report()

            time.sleep(
                self.interval
            )