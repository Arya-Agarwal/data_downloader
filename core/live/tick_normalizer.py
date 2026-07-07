import pandas as pd


class TickNormalizer:

    @staticmethod
    def normalize(
        instrument,
        tick
    ):
        ohlc = tick.get(
            "ohlc",
            {}
        )

        return {
            "timestamp": pd.to_datetime(
                tick.get(
                    "exchange_timestamp"
                )
                or
                tick.get(
                    "timestamp"
                )
            ),

            "instrument_token":
                instrument[
                    "instrument_token"
                ],

            "tradingsymbol":
                instrument[
                    "tradingsymbol"
                ],

            "segment":
                instrument[
                    "segment"
                ],

            "exchange":
                instrument[
                    "exchange"
                ],

            "expiry":
                instrument.get(
                    "expiry"
                ),

            "strike":
                instrument.get(
                    "strike"
                ),

            "option_type":
                instrument.get(
                    "instrument_type"
                ),

            "ltp":
                tick.get(
                    "last_price"
                ),

            "ltq":
                tick.get(
                    "last_quantity"
                ),

            "volume":
                tick.get(
                    "volume_traded"
                ),

            "oi":
                tick.get(
                    "oi"
                ),

            "open":
                ohlc.get(
                    "open"
                ),

            "high":
                ohlc.get(
                    "high"
                ),

            "low":
                ohlc.get(
                    "low"
                ),

            "close":
                ohlc.get(
                    "close"
                )
        }