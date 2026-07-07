from core.auth import (
    get_kite,
    get_kite_ticker
)

from core.logger import log

from core.live.instrument_lookup import (
    InstrumentLookup
)

from core.live.tick_router import (
    TickRouter
)
from core.live.tick_buffer import (
    TickBuffer
)

from core.live.tick_writer import (
    TickWriter
)
from core.live.subscription_manager import (
    SubscriptionManager
)


class LiveWebSocket:
    """
    Wrapper around KiteTicker.

    Responsibilities:
    - Create authenticated KiteTicker
    - Manage connection lifecycle
    - Register websocket callbacks

    Does NOT:
    - Subscribe instruments
    - Process ticks
    - Write files
    """

    def __init__(self):
        
        self.kite = get_kite()

        kite = self.kite

        self.instrument_lookup = (
            InstrumentLookup(
                kite
            )
        )

        self.tick_router = (
            TickRouter(
                self.instrument_lookup
            )
        )
        
        self.tick_buffer = TickBuffer()

        self.tick_writer = TickWriter(
            self.tick_buffer
        )

        self.tick_router.dispatcher.subscribe(
            "tick",
            self.tick_buffer.update
        )

        self.kws = get_kite_ticker()
        
        self.subscription_manager = (
            SubscriptionManager(
                kite,
                self.kws,
                self.instrument_lookup.df
            )
        )
        

        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error
        self.kws.on_ticks = self.on_ticks
        self.kws.on_reconnect = self.on_reconnect
        self.kws.on_noreconnect = self.on_noreconnect

    def connect(
        self,
        threaded=True
    ):
        log.info(
            "Starting Kite WebSocket..."
        )

        self.kws.connect(
            threaded=threaded
        )

    def disconnect(self):
        log.info(
            "Disconnecting Kite WebSocket..."
        )

        self.kws.close()

    def on_connect(
        self,
        ws,
        response
    ):
        log.info(
            "WebSocket connected."
        )

        self.subscription_manager.subscribe_initial()

    def on_close(
        self,
        ws,
        code,
        reason
    ):
        log.warning(
            f"WebSocket closed: "
            f"{code} | {reason}"
        )

    def on_error(
        self,
        ws,
        code,
        reason
    ):
        log.error(
            f"WebSocket error: "
            f"{code} | {reason}"
        )

    def on_reconnect(
        self,
        ws,
        attempts
    ):
        log.warning(
            f"Reconnect attempt: "
            f"{attempts}"
        )

    def on_noreconnect(
        self,
        ws
    ):
        log.error(
            "Maximum reconnect attempts reached."
        )

    def on_ticks(
        self,
        ws,
        ticks
    ):
        self.tick_router.process_ticks(
            ticks
        )
        
        for tick in ticks:

            if (
                tick["instrument_token"]
                == 256265
            ):

                self.subscription_manager.update_from_spot(
                    tick["last_price"]
                )

                break

        self.tick_writer.flush()