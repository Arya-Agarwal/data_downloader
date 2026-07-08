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

from core.downloaders.spot_downloader import (
    get_today_high_low
)

import time


class LiveWebSocket:
    """
    Wrapper around KiteTicker.

    Responsibilities

    - Manage websocket lifecycle
    - Route ticks
    - Flush tick buffer

    Strike universe expansion is handled
    by HealthMonitor.
    """

    def __init__(self):

        self.kite = get_kite()

        self.metrics = RuntimeMetrics()

        self.last_flush = time.time()

        self.flush_interval = 5

        self.flush_threshold = 100

        kite = self.kite

        #
        # Initialize today's range from
        # historical minute candles.
        #
        today_low, today_high = (
            get_today_high_low(
                kite
            )
        )

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

        #
        # Subscription manager
        #
        self.subscription_manager = (
            SubscriptionManager(
                kite,
                self.kws,
                self.instrument_lookup.df,
                today_low=today_low,
                today_high=today_high
            )
        )

        #
        # Health monitor depends on
        # SubscriptionManager.
        #
        self.health_monitor = (
            HealthMonitor(
                self.subscription_manager
            )
        )

        self.tick_router = (
            TickRouter(
                self.instrument_lookup,
                self.tick_buffer,
                self.subscription_manager
            )
        )

        #
        # WebSocket callbacks
        #
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

        self.subscription_manager.subscribe_initial()

        self.health_monitor.start()

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