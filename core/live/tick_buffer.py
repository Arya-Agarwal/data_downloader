from collections import defaultdict

from core.logger import log

from collections import defaultdict
from core.runtime.runtime_metrics import (
    RuntimeMetrics
)

class TickBuffer:

    def __init__(self):
        self.spot = defaultdict(list)
        self.futures = defaultdict(list)
        self.options = defaultdict(list)
        self.metrics = RuntimeMetrics()
    
    def update(
        self,
        instrument,
        tick
    ):
        segment = instrument["segment"]

        symbol = instrument[
            "tradingsymbol"
        ]

        if segment == "INDICES":
            self.spot[symbol].append(
                (
                    tick,
                    instrument
                )
            )

        elif segment == "NFO-FUT":
            self.futures[symbol].append(
                (
                    tick,
                    instrument
                )
            )

        elif segment == "NFO-OPT":
            self.options[symbol].append(
                (
                    tick,
                    instrument
                )
            )
        
        self.metrics.tick_received(
            segment
        )

        self.metrics.update_buffer(
            self.counts()["spot"]
            +
            self.counts()["future"]
            +
            self.counts()["option"]
        )


    def clear(self):
        self.metrics.update_buffer(0)
        self.spot.clear()
        self.futures.clear()
        self.options.clear()

    def counts(self):
        return {
            "spot": sum(
                len(v)
                for v in self.spot.values()
            ),
            "future": sum(
                len(v)
                for v in self.futures.values()
            ),
            "option": sum(
                len(v)
                for v in self.options.values()
            )
        }

    def log_summary(self):
        c = self.counts()

        log.info(
            f"Tick Buffer | "
            f"Spot={c['spot']} "
            f"Future={c['future']} "
            f"Option={c['option']}"
        )