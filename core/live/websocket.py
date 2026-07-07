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

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)

from core.runtime.health_monitor import (
    HealthMonitor
)
import time


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

        self.metrics = RuntimeMetrics()

        self.health_monitor = HealthMonitor()
         
        self.last_flush = time.time()

        self.flush_interval = 5        # seconds
        self.flush_threshold = 100     # ticks

        kite = self.kite

        self.instrument_lookup = (
            InstrumentLookup(
                kite
            )
        )

        self.tick_buffer = TickBuffer()

        self.tick_writer = TickWriter(
            self.tick_buffer
        )

        self.kws = get_kite_ticker()

        self.subscription_manager = (
            SubscriptionManager(
                kite,
                self.kws,
                self.instrument_lookup.df
            )
        )

        self.tick_router = (
            TickRouter(
                self.instrument_lookup,
                self.subscription_manager
            )
        )

        #
        # IMPORTANT
        # Connect TickRouter -> TickBuffer
        #
        self.tick_router.dispatcher.subscribe(
            "tick",
            self.tick_buffer.update
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

        self.health_monitor.stop()

        try:

            self.tick_writer.flush()

        except Exception:

            log.exception(
                "Unable to flush tick buffer."
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

        self.metrics.websocket_connected()

        self.health_monitor.start()

        self.subscription_manager.subscribe_initial()

    def on_close(
        self,
        ws,
        code,
        reason
    ):

        self.metrics.websocket_disconnected()

        self.health_monitor.stop()

        try:

            self.tick_writer.flush()

        except Exception:

            log.exception(
                "Final flush failed."
            )

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

        self.metrics.reconnect()

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

        total_buffered = (

            self.tick_buffer.counts()["spot"]

            +

            self.tick_buffer.counts()["future"]

            +

            self.tick_buffer.counts()["option"]

        )

        now = time.time()

        should_flush = (

            total_buffered >= self.flush_threshold

            or

            (
                now - self.last_flush
                >= self.flush_interval
            )

        )

        if should_flush:

            try:

                self.tick_writer.flush()

                self.last_flush = now

            except Exception:

                log.exception(
                    "Tick flush failed."
                )