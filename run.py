from core.logger import log
from core.auth import get_kite
from core.instrument_master.manager import (
    load_instrument_master
)
from core.tracker.tracker import (
    initialize_tracker,
    mark_expired_contracts
)
from core.downloaders.spot_downloader import (
    download_spot
)
from core.downloaders.strike_selector import (
    generate_strikes
)
from core.downloaders.futures_downloader import (
    get_active_futures
)
from core.downloaders.futures_downloader import (
    download_futures
)
from core.downloaders.options_downloader import (
    get_active_options,
    filter_option_universe
)
from core.downloaders.options_downloader import (
    download_options
)
from core.scheduler import (
    start_scheduler
)


def main():
    log.info("Starting bot")

    kite = get_kite()

    profile = kite.profile()

    log.info(
        f"Logged in as: {profile['user_name']}"
    )

    instruments = load_instrument_master(
        kite
    )

    log.info(
        f"Instrument master loaded: {len(instruments)} rows"
    )

    initialize_tracker()

    mark_expired_contracts()

    start_scheduler(
        kite,
        instruments
    )


if __name__ == "__main__":
    main()