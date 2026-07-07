from collections import defaultdict

from core.logger import log

from collections import defaultdict


class TickBuffer:

    def __init__(self):
        self.spot = defaultdict(list)
        self.futures = defaultdict(list)
        self.options = defaultdict(list)

    def update(
        self,
        instrument,
        tick
    ):
        segment = instrument["segment"]

        token = instrument[
            "instrument_token"
        ]

        if segment == "INDICES":
            self.spot[token].append(
                tick
            )

        elif segment == "NFO-FUT":
            self.futures[token].append(
                tick
            )

        elif segment == "NFO-OPT":
            self.options[token].append(
                tick
            )

    def clear(self):
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