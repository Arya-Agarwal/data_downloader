import pandas as pd

from config import (
    INDEX_NAME,
    STRIKE_STEP
)

from core.logger import log
from core.downloaders.strike_selector import (
    get_spot_daily_file
)
from core.utils.file_manager import (
    read_parquet
)


class StrikeUniverse:

    BUFFER = 250

    def __init__(self):

        self.margin = 250

        self.previous_low = None
        self.previous_high = None

        self.live_low = None
        self.live_high = None

        self.current_universe = set()

        self.step = STRIKE_STEP[
            INDEX_NAME
        ]

        self._load_previous_day()

        self.live_low = self.previous_low
        self.live_high = self.previous_high

        self.current_universe = self._build_range(
            self.previous_low,
            self.previous_high
        )

    def _load_previous_day(
        self
    ):
        df = read_parquet(
            get_spot_daily_file()
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        last = df.iloc[-1]

        self.previous_high = float(
            last["high"]
        )

        self.previous_low = float(
            last["low"]
        )

        log.info(
            f"Previous session "
            f"{self.previous_low} - "
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

        low -= self.BUFFER
        high += self.BUFFER

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
    
    def update(
        self,
        ltp
    ):

        changed = False

        if ltp < self.live_low:
            self.live_low = ltp
            changed = True

        if ltp > self.live_high:
            self.live_high = ltp
            changed = True

        if not changed:
            return (
                sorted(self.current_universe),
                False
            )

        new_range = self._build_range(
            min(
                self.previous_low,
                self.live_low
            ),
            max(
                self.previous_high,
                self.live_high
            )
        )

        added = (
            new_range
            -
            self.current_universe
        )

        if added:

            self.current_universe |= added

            log.info(
                f"Strike universe expanded by "
                f"{len(added)} strikes"
            )

            return (
                sorted(
                    self.current_universe
                ),
                True
            )

        return (
            sorted(
                self.current_universe
            ),
            False
        )