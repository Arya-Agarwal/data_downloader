from datetime import datetime


class TickFormatter:

    @staticmethod
    def format(
        tick,
        instrument
    ):

        depth = tick.get(
            "depth",
            {}
        )

        buy = depth.get(
            "buy",
            []
        )

        sell = depth.get(
            "sell",
            []
        )

        row = {

            "timestamp":
                tick.get(
                    "exchange_timestamp"
                )
                or
                datetime.now(),

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

            "average_price":
                tick.get(
                    "average_traded_price"
                ),

            "oi":
                tick.get(
                    "oi"
                ),

            "oi_day_high":
                tick.get(
                    "oi_day_high"
                ),

            "oi_day_low":
                tick.get(
                    "oi_day_low"
                ),

            "open":
                tick.get(
                    "ohlc",
                    {}
                ).get(
                    "open"
                ),

            "high":
                tick.get(
                    "ohlc",
                    {}
                ).get(
                    "high"
                ),

            "low":
                tick.get(
                    "ohlc",
                    {}
                ).get(
                    "low"
                ),

            "close":
                tick.get(
                    "ohlc",
                    {}
                ).get(
                    "close"
                )
        }

        for i in range(5):

            if i < len(buy):

                row[f"bid_{i+1}_price"] = buy[i]["price"]
                row[f"bid_{i+1}_qty"] = buy[i]["quantity"]
                row[f"bid_{i+1}_orders"] = buy[i]["orders"]

            else:

                row[f"bid_{i+1}_price"] = None
                row[f"bid_{i+1}_qty"] = None
                row[f"bid_{i+1}_orders"] = None

            if i < len(sell):

                row[f"ask_{i+1}_price"] = sell[i]["price"]
                row[f"ask_{i+1}_qty"] = sell[i]["quantity"]
                row[f"ask_{i+1}_orders"] = sell[i]["orders"]

            else:

                row[f"ask_{i+1}_price"] = None
                row[f"ask_{i+1}_qty"] = None
                row[f"ask_{i+1}_orders"] = None

        return row