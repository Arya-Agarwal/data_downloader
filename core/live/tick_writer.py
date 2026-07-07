import pandas as pd

from core.logger import log


class TickWriter:

    def __init__(
        self,
        tick_buffer
    ):
        self.buffer = tick_buffer

    def flush(self):

        spot = len(self.buffer.spot)
        future = len(self.buffer.futures)
        option = len(self.buffer.options)

        if (
            spot == 0
            and future == 0
            and option == 0
        ):
            return

        log.info(
            f"Flushing "
            f"Spot={spot} "
            f"Future={future} "
            f"Option={option}"
        )

        #
        # Actual parquet writing
        # will come next.
        #

        self.buffer.clear()