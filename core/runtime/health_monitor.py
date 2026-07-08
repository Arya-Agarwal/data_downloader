import threading
import time

from config import (
    LIVE_UNIVERSE_UPDATE_SECONDS
)

from core.runtime.daily_tracker import (
    DailyTracker
)

from core.runtime.tick_watchdog import (
    TickWatchdog
)


class HealthMonitor:

    def __init__(
        self,
        subscription_manager,
        interval=1
    ):

        self.interval = interval

        self.subscription_manager = (
            subscription_manager
        )

        self.tracker = DailyTracker()

        self.watchdog = TickWatchdog()

        self.running = False

        self.thread = None

        now = time.time()

        self.last_status_report = now

        self.last_universe_update = now

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

            now = time.time()

            #
            # Run watchdog every second
            #
            self.watchdog.check()

            #
            # Print runtime summary every minute
            #
            if (
                now - self.last_status_report
                >= 60
            ):

                self.tracker.report()

                self.last_status_report = now

            #
            # Expand strike universe every
            # LIVE_UNIVERSE_UPDATE_SECONDS
            #
            if (
                now - self.last_universe_update
                >= LIVE_UNIVERSE_UPDATE_SECONDS
            ):

                try:

                    self.subscription_manager.expand_strike_universe()

                except Exception:

                    from core.logger import log

                    log.exception(
                        "Strike universe expansion failed."
                    )

                self.last_universe_update = now

            time.sleep(
                self.interval
            )