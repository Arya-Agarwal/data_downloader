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

        self.step = STRIKE_STEP[
            INDEX_NAME
        ]

        self.day = None

        self.day_high = None
        self.day_low = None

        self.subscribed = set()

        self.previous_high = None
        self.previous_low = None

        self._load_previous_day()

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

        today = pd.Timestamp.now(
            tz="Asia/Kolkata"
        ).date()

        if self.day != today:

            self.day = today

            self.day_high = ltp
            self.day_low = ltp

            self.subscribed = (
                self._build_range(
                    self.previous_low,
                    self.previous_high
                )
            )

            log.info(
                f"Initial live universe : "
                f"{len(self.subscribed)} strikes"
            )

            return (
                self.subscribed,
                True
            )

        changed = False

        if ltp > self.day_high:
            self.day_high = ltp
            changed = True

        if ltp < self.day_low:
            self.day_low = ltp
            changed = True

        if not changed:
            return (
                set(),
                False
            )

        expanded = self._build_range(
            self.day_low,
            self.day_high
        )

        new = (
            expanded
            -
            self.subscribed
        )

        if new:

            self.subscribed |= new

            log.info(
                f"Universe expanded : "
                f"+{len(new)} strikes"
            )

        return (
            new,
            len(new) > 0
        )