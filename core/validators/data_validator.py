import pandas as pd

from core.logger import log

from core.utils.market_utils import (
    get_expected_session_timestamps
)
from config import GAP_DEBUG_FILE


TIMEFRAME_MAP = {
    "day": 86400,
    "60minute": 3600,
    "15minute": 900,
    "5minute": 300,
    "minute": 60
}


def check_blank_rows(df):
    blank_rows = df[
        df[
            ["open", "high", "low", "close"]
        ].isnull().any(axis=1)
    ]

    return len(blank_rows)


def check_monotonic(df):
    timestamps = pd.to_datetime(
        df["timestamp"]
    )

    return timestamps.is_monotonic_increasing

def write_gap_debug(
    file_path,
    timeframe,
    missing_timestamps
):
    if not missing_timestamps:
        return

    rows = []

    for ts in missing_timestamps:
        rows.append(
            {
                "file_path": file_path,
                "timeframe": timeframe,
                "missing_timestamp": str(ts)
            }
        )

    debug_df = pd.DataFrame(rows)

    if GAP_DEBUG_FILE.exists():
        existing = pd.read_csv(
            GAP_DEBUG_FILE
        )

        debug_df = pd.concat(
            [
                existing,
                debug_df
            ],
            ignore_index=True
        )

    debug_df = debug_df.drop_duplicates()

    debug_df.to_csv(
        GAP_DEBUG_FILE,
        index=False
    )

def check_missing_candles(
    df,
    timeframe,
    file_path=None
):
    if timeframe == "day":
        return 0

    timeframe_seconds = TIMEFRAME_MAP[
        timeframe
    ]

    timestamps = pd.to_datetime(
        df["timestamp"],
        utc=True
    ).dt.tz_convert(
        "Asia/Kolkata"
    )

    missing_count = 0
    missing_timestamps = []

    grouped = {}

    for ts in timestamps:
        day = ts.date()

        if day not in grouped:
            grouped[day] = []

        grouped[day].append(ts)

    for day, day_timestamps in grouped.items():
        actual_set = set(
            day_timestamps
        )

        expected_range = (
            get_expected_session_timestamps(
                day,
                timeframe_seconds
            )
        )

        actual_sorted = sorted(day_timestamps)

        if not actual_sorted:
            continue

        last_actual = actual_sorted[-1]

        for ts in expected_range:
            if ts > last_actual:
                continue

            if ts not in actual_set:
                missing_count += 1
                missing_timestamps.append(ts)
                
                
    if file_path:
        write_gap_debug(
            file_path,
            timeframe,
            missing_timestamps
        )
    

    return missing_count



def validate_dataframe(
    df,
    timeframe,
    file_path=None
):
    result = {
        "blank_rows": 0,
        "missing_candles": 0,
        "monotonic": True,
        "status": "VALID"
    }

    if df.empty:
        result["status"] = "EMPTY"
        return result

    result["blank_rows"] = check_blank_rows(
        df
    )

    result["missing_candles"] = check_missing_candles(
        df,
        timeframe,
        file_path
    )

    result["monotonic"] = check_monotonic(
        df
    )

    if result["blank_rows"] > 0:
        result["status"] = "HAS_BLANKS"

    elif result["missing_candles"] > 0:
        result["status"] = "VALID_WITH_GAPS"

    elif not result["monotonic"]:
        result["status"] = "TIMESTAMP_DISORDER"

    log.info(
        f"Validation complete: {result}"
    )

    return result