from core.logger import log
from core.live.event_dispatcher import (
    EventDispatcher
)

class TickRouter:
    """
    Routes Zerodha ticks to the
    appropriate downstream pipeline.

    Responsibilities

    - Identify instrument type
    - Dispatch ticks

    Does NOT

    - Store data
    - Buffer ticks
    - Write parquet
    """

    def __init__(
        self,
        instrument_lookup,
        subscription_manager=None
    ):
        self.instrument_lookup = (
            instrument_lookup
        )
        
        self.subscription_manager = (
            subscription_manager
        )

        self.dispatcher = (
            EventDispatcher()
        )

    def process_ticks(
        self,
        ticks
    ):
        for tick in ticks:

            metadata = (
                self.instrument_lookup.get(
                    tick["instrument_token"]
                )
            )

            if metadata is None:
                continue

            segment = metadata["segment"]

            if segment == "INDICES":

                self.process_spot_tick(
                    tick,
                    metadata
                )

            elif segment == "NFO-FUT":

                self.process_future_tick(
                    tick,
                    metadata
                )

            elif segment == "NFO-OPT":

                self.process_option_tick(
                    tick,
                    metadata
                )

            self.dispatcher.publish(
                "tick",
                tick,
                metadata
            )
            
        
    def process_spot_tick(
        self,
        tick,
        metadata
    ):
        
        if self.subscription_manager:

            self.subscription_manager.update_from_spot(
                tick["last_price"]
            )
        
        log.debug(
            f"SPOT : "
            f"{metadata['tradingsymbol']}"
        )

    def process_future_tick(
        self,
        tick,
        metadata
    ):
        log.debug(
            f"FUTURE : "
            f"{metadata['tradingsymbol']}"
        )

    def process_option_tick(
        self,
        tick,
        metadata
    ):
        log.debug(
            f"OPTION : "
            f"{metadata['tradingsymbol']}"
        )