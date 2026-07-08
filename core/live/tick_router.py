from core.logger import log


class TickRouter:
    """
    Routes incoming ticks.

    Responsibilities

    - Lookup instrument metadata
    - Update today's spot range
    - Forward ticks to TickBuffer

    Does NOT

    - Subscribe instruments
    - Expand strike universe
    """

    def __init__(
        self,
        instrument_lookup,
        tick_buffer,
        subscription_manager=None
    ):

        self.instrument_lookup = (
            instrument_lookup
        )

        self.tick_buffer = (
            tick_buffer
        )

        self.subscription_manager = (
            subscription_manager
        )

    def process_ticks(
        self,
        ticks
    ):

        for tick in ticks:

            metadata = self.instrument_lookup.get(
                tick["instrument_token"]
            )

            if metadata is None:
                continue

            if metadata["segment"] == "INDICES":

                if self.subscription_manager:

                    self.subscription_manager.record_spot_price(
                        tick["last_price"]
                    )

            self.tick_buffer.update(
                metadata,
                tick
            )

            # Uncomment for debugging
            #
            # log.debug(
            #     f"{metadata['tradingsymbol']} "
            #     f"{tick['last_price']}"
            # )