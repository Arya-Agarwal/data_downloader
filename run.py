from core.logger import log

from core.auth import (
    get_kite
)

from core.instrument_master.manager import (
    load_instrument_master
)

from core.tracker.tracker import (
    initialize_tracker,
    mark_expired_contracts
)

from core.live.websocket import (
    LiveWebSocket
)

from core.runtime.shutdown_manager import (
    ShutdownManager
)

from core.runtime.startup_validator import (
    StartupValidator
)

from core.scheduler import (
    start_scheduler
)


def main():

    log.info(
        "========== STARTING BOT =========="
    )

    kite = get_kite()

    profile = kite.profile()

    log.info(
        f"Logged in as: "
        f"{profile['user_name']}"
    )

    instruments = (
        load_instrument_master(
            kite
        )
    )

    log.info(
        f"Instrument master loaded: "
        f"{len(instruments)} rows"
    )

    initialize_tracker()

    mark_expired_contracts()

    StartupValidator().validate()

    websocket = LiveWebSocket()

    shutdown = ShutdownManager(
        websocket
    )

    shutdown.register()

    start_scheduler(
        kite,
        instruments,
        websocket
    )


if __name__ == "__main__":
    main()