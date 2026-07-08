import pandas as pd

from core.logger import log

from core.live.tick_formatter import (
    TickFormatter
)

from core.live.live_paths import (
    get_parquet_file
)

from core.utils.file_manager import (
    append_parquet
)
from core.runtime.runtime_metrics import (
    RuntimeMetrics
)

class TickWriter:

    def __init__(
        self,
        tick_buffer
    ):
        self.buffer = tick_buffer
        self.metrics = RuntimeMetrics()

    def flush(self):

        self._write_segment(
            self.buffer.spot,
            "spot"
        )

        self._write_segment(
            self.buffer.futures,
            "futures"
        )

        self._write_segment(
            self.buffer.options,
            "options"
        )

        self.buffer.clear()

    def _write_segment(
        self,
        segment_buffer,
        segment_name
    ):

        for (
            tradingsymbol,
            ticks
        ) in segment_buffer.items():

            if not ticks:
                continue

            rows = []

            for item in ticks:

                if (
                    isinstance(item, tuple)
                    and
                    len(item) == 2
                ):

                    tick, instrument = item

                else:

                    log.warning(
                        "Unexpected tick format."
                    )

                    continue

                rows.append(

                    TickFormatter.format(
                        tick,
                        instrument
                    )

                )

            if not rows:
                continue

            df = pd.DataFrame(
                rows
            )

            try:

                append_parquet(
                    df,
                    get_parquet_file(
                        segment_name,
                        tradingsymbol
                    )
                )

                self.metrics.rows_added(
                    len(df)
                )

                self.metrics.file_written()

            except Exception as e:

                log.exception(
                    f"Failed writing "
                    f"{tradingsymbol}: {e}"
                )

            # log.info(
            #     f"{tradingsymbol}: "
            #     f"{len(df)} ticks written."
            # )