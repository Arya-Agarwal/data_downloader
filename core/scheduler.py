import time

from datetime import timedelta

from config import (
    FORCE_MARKET_CLOSE,
    PREMARKET_UPDATE_HOUR,
    PREMARKET_UPDATE_MINUTE,
    PREMARKET_WAIT_HOUR,
    PREMARKET_WAIT_MINUTE,
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
    download_spot,
    download_eod_pending_spot
)

from core.downloaders.futures_downloader import (
    download_futures,
    download_eod_pending_futures
)

from core.downloaders.options_downloader import (
    download_options,
    download_eod_pending_options
)

from core.downloaders.strike_selector import (
    get_live_atm_strikes
)

from core.recovery.gap_recovery import (
    recover_all_gaps
)


def run_historical_download(
    kite,
    instruments
):

    log.info(
        "Running historical update."
    )

    download_spot(
        kite
    )

    download_futures(
        kite,
        instruments
    )

    strikes = (
        get_live_atm_strikes()
    )

    download_options(
        kite,
        instruments,
        strikes,
        allowed_timeframes=[
            "minute",
            "5minute"
        ]
    )


def run_gap_recovery(
    kite
):

    log.info(
        "Running gap recovery."
    )

    recover_all_gaps(
        kite
    )


def run_eod_refresh(
    kite
):

    log.info(
        "Running EOD refresh."
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


def market_open():

    now = now_ist()

    start = now.replace(
        hour=MARKET_START_HOUR,
        minute=MARKET_START_MINUTE,
        second=0,
        microsecond=0
    )

    end = now.replace(
        hour=MARKET_END_HOUR,
        minute=MARKET_END_MINUTE,
        second=0,
        microsecond=0
    )

    return start <= now <= end


def is_market_open():
    return market_open()


def wait_until_market_open():

    while not market_open():

        log.info(
            "Waiting for market open..."
        )

        time.sleep(30)


def wait_until_market_close():

    while market_open():

        time.sleep(5)


def start_scheduler(
    kite,
    instruments,
    websocket
):

    if FORCE_MARKET_CLOSE:

        log.warning(
            "FORCE_MARKET_CLOSE=True"
        )

        run_eod_refresh(
            kite
        )

        run_gap_recovery(
            kite
        )

        return

    now = now_ist()

    premarket_update = now.replace(
        hour=PREMARKET_UPDATE_HOUR,
        minute=PREMARKET_UPDATE_MINUTE,
        second=0,
        microsecond=0
    )

    premarket_wait = now.replace(
        hour=PREMARKET_WAIT_HOUR,
        minute=PREMARKET_WAIT_MINUTE,
        second=0,
        microsecond=0
    )

    market_start = now.replace(
        hour=MARKET_START_HOUR,
        minute=MARKET_START_MINUTE,
        second=0,
        microsecond=0
    )

    market_end = now.replace(
        hour=MARKET_END_HOUR,
        minute=MARKET_END_MINUTE,
        second=0,
        microsecond=0
    )

    if premarket_update <= now < premarket_wait:

        log.info(
            "Premarket update window."
        )

        run_historical_download(
            kite,
            instruments
        )

        run_gap_recovery(
            kite
        )

        wait_until_market_open()

    elif premarket_wait <= now < market_start:

        log.info(
            "Premarket waiting window."
        )

        wait_until_market_open()

    elif market_start <= now < market_end:

        log.info(
            "Market already open."
        )

    else:

        log.info(
            "Market closed."
        )

        run_eod_refresh(
            kite
        )

        run_gap_recovery(
            kite
        )

        return

    log.info(
        "Starting live session."
    )

    websocket.connect()

    try:

        wait_until_market_close()

    finally:

        log.info(
            "Stopping live session."
        )

        websocket.disconnect()

    log.info(
        "Running post market refresh."
    )

    run_eod_refresh(
        kite
    )

    run_gap_recovery(
        kite
    )

    log.info(
        "Bot completed successfully."
    )