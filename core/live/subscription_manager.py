import pandas as pd

from kiteconnect import KiteTicker

from core.logger import log

from core.live.strike_universe import (
    StrikeUniverse
)
from core.live.session.live_session import (
    LiveSession
)
from core.runtime.runtime_metrics import (
    RuntimeMetrics
)

class SubscriptionManager:

    def __init__(
        self,
        kite,
        websocket,
        instruments
    ):
        self.kite = kite
        
        self.metrics = RuntimeMetrics()
        
        self.session = LiveSession()

        self.websocket = websocket

        self.instruments = (
            instruments
        )

        self.universe = (
            StrikeUniverse()
        )

        self.subscribed_tokens = set()

        self.option_index = {}

        option_df = self.instruments[
            (
                self.instruments["segment"]
                == "NFO-OPT"
            )
            &
            (
                self.instruments["name"]
                == "NIFTY"
            )
        ]

        for _, row in option_df.iterrows():

            strike = int(
                row["strike"]
            )

            if strike not in self.option_index:
                self.option_index[
                    strike
                ] = []

            self.option_index[
                strike
            ].append(
                int(
                    row[
                        "instrument_token"
                    ]
                )
            )

        future_df = self.instruments[
            (
                self.instruments["segment"]
                == "NFO-FUT"
            )
            &
            (
                self.instruments["name"]
                == "NIFTY"
            )
        ].sort_values(
            "expiry"
        )

        self.future_tokens = (
            future_df[
                "instrument_token"
            ]
            .astype(int)
            .tolist()
        )

        self.spot_token = 256265

    def subscribe_initial(self):

        self.session.current_low = (
            self.universe.previous_low
        )

        self.session.current_high = (
            self.universe.previous_high
        )

        strikes, _ = (
            self.universe.update(
                self.universe.previous_low,
                self.universe.previous_high,
                self.universe.previous_low,
                self.universe.previous_high
            )
        )

        self.subscribe_strikes(
            strikes
        )
    
    
    def update_from_spot(
        self,
        ltp
    ):

        changed = self.session.update(
            ltp
        )

        if not changed:
            return

        live_low, live_high = (
            self.session.get_range()
        )

        strikes, universe_changed = (
            self.universe.update(
                self.universe.previous_low,
                self.universe.previous_high,
                live_low,
                live_high
            )
        )

        if universe_changed:

            self.subscribe_strikes(
                strikes
            )
    
    def subscribe_strikes(
        self,
        strikes
    ):

        tokens = []

        for strike in strikes:

            tokens.extend(
                self.option_index.get(
                    int(strike),
                    []
                )
            )

        tokens.extend(
            self.future_tokens
        )

        tokens.append(
            self.spot_token
        )

        tokens = list(
            set(tokens)
            -
            self.subscribed_tokens
        )

        if not tokens:
            return

        self.websocket.subscribe(
            tokens
        )

        self.websocket.set_mode(
            KiteTicker.MODE_FULL,
            tokens
        )

        self.subscribed_tokens.update(
            tokens
        )
        self.metrics.update_subscriptions(
            len(self.subscribed_tokens)
        )

        log.info(
            f"Subscribed "
            f"{len(tokens)} "
            f"instruments"
        )