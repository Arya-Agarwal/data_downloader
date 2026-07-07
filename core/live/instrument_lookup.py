from core.instrument_master.manager import (
    load_instrument_master
)
from core.logger import log


class InstrumentLookup:
    """
    Fast instrument lookup.

    Loads the instrument master once and
    builds an in-memory dictionary keyed by
    instrument_token.

    Used by:

    - Tick Router
    - Subscription Manager
    - Option Chain
    - Live Tracker
    """

    def __init__(
        self,
        kite
    ):
        self.df = load_instrument_master(
            kite
        )

        df = self.df

        self.lookup = {}

        for _, row in df.iterrows():
            self.lookup[
                int(row["instrument_token"])
            ] = row.to_dict()

        log.info(
            f"Instrument lookup built: "
            f"{len(self.lookup)} instruments"
        )

    def get(
        self,
        instrument_token
    ):
        return self.lookup.get(
            int(instrument_token)
        )