import time
from datetime import timedelta

from config import (
    MARKET_START_HOUR,
    MARKET_START_MINUTE,
    MARKET_END_HOUR,
    MARKET_END_MINUTE
)

from core.logger import log
from core.utils.time_utils import (
    now_ist
)
from core.downloaders.spot_downloader import (
    download_spot
)
from core.downloaders.futures_downloader import (
    download_futures
)
from core.downloaders.options_downloader import (
    download_options
)
from core.downloaders.strike_selector import (
    generate_strikes,
    get_live_atm_strikes
)
from core.recovery.gap_recovery import (
    recover_all_gaps
)
from core.downloaders.options_downloader import (
    download_eod_pending_options
)
from core.downloaders.spot_downloader import (
    download_eod_pending_spot
)

from core.downloaders.futures_downloader import (
    download_eod_pending_futures
)


def get_market_start():
    now = now_ist()

    return now.replace(
        hour=MARKET_START_HOUR,
        minute=MARKET_START_MINUTE,
        second=0,
        microsecond=0
    )


def get_market_end():
    now = now_ist()

    return now.replace(
        hour=MARKET_END_HOUR,
        minute=MARKET_END_MINUTE,
        second=0,
        microsecond=0
    )


def is_weekend():
    return now_ist().weekday() >= 5


def is_market_open():
    now = now_ist()

    return (
        get_market_start()
        <= now
        <= get_market_end()
    )


def get_next_market_open():
    now = now_ist()

    next_open = get_market_start()

    if now < next_open:
        return next_open

    next_open = next_open + timedelta(
        days=1
    )

    while next_open.weekday() >= 5:
        next_open += timedelta(
            days=1
        )

    return next_open


def sleep_until_market():
    next_open = get_next_market_open()

    sleep_seconds = (
        next_open - now_ist()
    ).total_seconds()

    log.info(
        f"Sleeping until market opens: "
        f"{next_open}"
    )

    time.sleep(
        max(
            sleep_seconds,
            0
        )
    )


def run_live_cycle(
    kite,
    instruments
):
    log.info(
        "Running live cycle"
    )

    download_spot(
        kite
    )

    download_futures(
        kite,
        instruments
    )

    live_strikes = get_live_atm_strikes()

    download_options(
        kite,
        instruments,
        live_strikes,
        allowed_timeframes=[
            "minute",
            "5minute"
        ]
    )
    
    
def run_end_of_day(
    kite,
    instruments
):
    log.info(
        "Running EOD pending option refresh"
    )

    download_eod_pending_spot(
        kite
    )

    download_eod_pending_futures(
        kite
    )

    download_eod_pending_options(
        kite
    )

    log.info(
        "Market closed. Bot shutting down."
    )


def start_scheduler(
    kite,
    instruments
):
    while True:
        if is_weekend():
            run_end_of_day(
                kite,
                instruments
            )
            break

        if not is_market_open():
            run_end_of_day(
                kite,
                instruments
            )
            break

        run_live_cycle(
            kite,
            instruments
        )

        log.info(
            "Sleeping 60 seconds"
        )

        time.sleep(60)