import pandas as pd

from config import (
    INDEX_NAME,
    STRIKE_STEP,
    LIVE_STRIKE_BUFFER
)

from core.logger import log

from core.downloaders.strike_selector import (
    get_spot_daily_file
)

from core.utils.file_manager import (
    read_parquet
)


class StrikeUniverse:

    def __init__(
        self,
        today_low=None,
        today_high=None
    ):

        self.step = STRIKE_STEP[
            INDEX_NAME
        ]

        self.buffer = LIVE_STRIKE_BUFFER

        self.previous_low = None
        self.previous_high = None

        self.today_low = None
        self.today_high = None

        self.current_universe = set()

        self._load_previous_day()

        self.today_low = (
            today_low
            if today_low is not None
            else self.previous_low
        )

        self.today_high = (
            today_high
            if today_high is not None
            else self.previous_high
        )

        self.current_universe = self._build_range(
            min(
                self.previous_low,
                self.today_low
            ),
            max(
                self.previous_high,
                self.today_high
            )
        )
        
        log.info(
            f"Initial strike universe : "
            f"{min(self.current_universe)} -> "
            f"{max(self.current_universe)} "
            f"({len(self.current_universe)} strikes)"
        )

    def _load_previous_day(self):

        df = read_parquet(
            get_spot_daily_file()
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        last = df.iloc[-1]

        self.previous_low = float(
            last["low"]
        )

        self.previous_high = float(
            last["high"]
        )

        log.info(
            f"Previous session : "
            f"{self.previous_low} -> "
            f"{self.previous_high}"
        )

    def _round_down(
        self,
        value
    ):
        return (
            int(value)
            //
            self.step
        ) * self.step

    def _round_up(
        self,
        value
    ):

        value = int(value)

        if value % self.step == 0:
            return value

        return (
            (
                value
                //
                self.step
            )
            + 1
        ) * self.step

    def _build_range(
        self,
        low,
        high
    ):

        low -= self.buffer
        high += self.buffer

        start = self._round_down(
            low
        )

        end = self._round_up(
            high
        )

        return set(
            range(
                start,
                end + self.step,
                self.step
            )
        )

    def update_today_range(
        self,
        ltp
    ):
        """
        Called on EVERY spot tick.

        Only stores today's high / low.
        No subscriptions.
        No expansion.
        """

        if ltp > self.today_high:
            self.today_high = ltp

        if ltp < self.today_low:
            self.today_low = ltp

    def expand_if_required(
        self
    ):
        """
        Called every 5 minutes.

        Expands ONLY.

        Never shrinks.
        """

        required_low = min(
            self.previous_low,
            self.today_low
        )

        required_high = max(
            self.previous_high,
            self.today_high
        )

        new_universe = self._build_range(
            required_low,
            required_high
        )

        added = (
            new_universe
            -
            self.current_universe
        )

        if not added:

            return (
                sorted(
                    self.current_universe
                ),
                False
            )

        self.current_universe |= added

        log.info(
            "Strike universe expanded : "
            f"{min(self.current_universe)} -> "
            f"{max(self.current_universe)} "
            f"Added={sorted(added)}"
        )

        return (
            sorted(
                self.current_universe
            ),
            True
        )