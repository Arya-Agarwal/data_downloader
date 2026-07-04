from datetime import timedelta

import pandas as pd

from core.utils.time_utils import (
    to_ist
)


def get_market_close_for_day(ts):
    ts = pd.to_datetime(ts)

    ts = to_ist(ts)

    return ts.replace(
        hour=15,
        minute=30,
        second=0,
        microsecond=0
    )


def get_next_expected_timestamp(
    last_timestamp,
    timeframe_seconds
):
    ts = pd.to_datetime(
        last_timestamp
    )

    ts = to_ist(ts)

    return ts + timedelta(
        seconds=timeframe_seconds
    )

def is_file_complete_for_day(
    last_timestamp,
    timeframe_seconds
):
    ts = pd.to_datetime(
        last_timestamp
    )

    ts = to_ist(ts)

    market_close = get_market_close_for_day(
        ts
    )

    expected_last_candle = (
        market_close - timedelta(
            seconds=timeframe_seconds
        )
    )

    return (
        ts >= expected_last_candle
    )
    
def get_expected_session_timestamps(
    day,
    timeframe_seconds
):
    market_open = pd.Timestamp(
        f"{day} 09:15:00",
        tz="Asia/Kolkata"
    )

    market_close = pd.Timestamp(
        f"{day} 15:30:00",
        tz="Asia/Kolkata"
    )

    if timeframe_seconds == 86400:
        return [market_open.normalize()]

    expected_last = (
        market_close - timedelta(
            seconds=timeframe_seconds
        )
    )

    return pd.date_range(
        start=market_open,
        end=expected_last,
        freq=f"{timeframe_seconds}s"
    )
    
def get_expected_last_candle(day, timeframe_seconds):
    market_close = pd.Timestamp(
        f"{day} 15:30:00",
        tz="Asia/Kolkata"
    )

    return (
        market_close - timedelta(
            seconds=timeframe_seconds
        )
    )