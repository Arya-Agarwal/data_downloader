import pandas as pd

from kiteconnect import KiteTicker

from config import (
    LIVE_OPTION_EXPIRIES,
    LIVE_FUTURE_EXPIRIES
)

from core.logger import log

from core.live.strike_universe import (
    StrikeUniverse
)

from core.runtime.runtime_metrics import (
    RuntimeMetrics
)


class SubscriptionManager:

    def __init__(
        self,
        kite,
        websocket,
        instruments,
        today_low=None,
        today_high=None
    ):

        self.kite = kite

        self.websocket = websocket

        self.instruments = instruments

        self.metrics = RuntimeMetrics()

        self.universe = StrikeUniverse(
            today_low=today_low,
            today_high=today_high
        )

        self.subscribed_tokens = set()

        self.option_index = {}

        today = pd.Timestamp.now().normalize()

        #
        # -----------------------------
        # Options
        # -----------------------------
        #

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
        ].copy()

        option_df["expiry"] = pd.to_datetime(
            option_df["expiry"]
        )

        option_df = option_df[
            option_df["expiry"] >= today
        ]

        active_expiries = sorted(
            option_df["expiry"].unique()
        )[:LIVE_OPTION_EXPIRIES]

        option_df = option_df[
            option_df["expiry"].isin(
                active_expiries
            )
        ]

        log.info(
            "Option expiries : "
            +
            ", ".join(
                str(x.date())
                for x in active_expiries
            )
        )

        for _, row in option_df.iterrows():

            strike = int(
                row["strike"]
            )

            self.option_index.setdefault(
                strike,
                []
            ).append(
                int(
                    row[
                        "instrument_token"
                    ]
                )
            )

        #
        # -----------------------------
        # Futures
        # -----------------------------
        #

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
        ].copy()

        future_df["expiry"] = pd.to_datetime(
            future_df["expiry"]
        )

        future_df = future_df[
            future_df["expiry"] >= today
        ]

        future_df = future_df.sort_values(
            "expiry"
        ).head(
            LIVE_FUTURE_EXPIRIES
        )

        self.future_tokens = (
            future_df[
                "instrument_token"
            ]
            .astype(int)
            .tolist()
        )

        log.info(
            f"Future contracts : "
            f"{len(self.future_tokens)}"
        )

        #
        # Spot
        #

        self.spot_token = 256265

    def subscribe_initial(
        self
    ):

        log.info(
            "Subscribing initial strike universe."
        )

        self.subscribe_strikes(
            sorted(
                self.universe.current_universe
            )
        )

    def record_spot_price(
        self,
        ltp
    ):
        """
        Called on every spot tick.

        Only updates today's
        high / low.
        """

        self.universe.update_today_range(
            ltp
        )

    def expand_strike_universe(
        self
    ):
        """
        Called every 5 minutes
        by HealthMonitor.

        Expands strike universe
        if today's range has moved
        outside yesterday's range.
        """

        strikes, changed = (
            self.universe.expand_if_required()
        )

        if changed:

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

        #
        # Subscribe only new tokens
        #

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
            len(
                self.subscribed_tokens
            )
        )

        log.info(
            f"Subscribed "
            f"{len(tokens)} new instruments "
            f"(Total={len(self.subscribed_tokens)})"
        )