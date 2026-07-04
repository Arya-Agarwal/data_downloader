import pandas as pd

from config import (
    N_WEEKS,
    STRIKE_STEP,
    INDEX_NAME,
    TRACKER_FILE
)

from core.logger import log
from core.utils.file_manager import (
    read_parquet
)
from core.tracker.tracker import (
    load_tracker
)


def get_spot_daily_file():
    tracker_df = load_tracker()

    result = tracker_df[
        (tracker_df["segment"] == "SPOT")
        &
        (tracker_df["timeframe"] == "day")
    ]

    if result.empty:
        raise Exception(
            "Spot daily data not found in tracker"
        )

    return result.iloc[0]["file_path"]


def round_down(
    value,
    step
):
    return int(
        (value // step) * step
    )


def round_up(
    value,
    step
):
    if value % step == 0:
        return int(value)

    return int(
        ((value // step) + 1) * step
    )


def get_recent_range():
    file_path = get_spot_daily_file()

    df = read_parquet(
        file_path
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    latest_date = df[
        "timestamp"
    ].max()

    cutoff_date = latest_date - pd.Timedelta(
        weeks=N_WEEKS
    )

    recent_df = df[
        df["timestamp"] >= cutoff_date
    ]

    range_low = recent_df[
        "low"
    ].min()

    range_high = recent_df[
        "high"
    ].max()

    log.info(
        f"{N_WEEKS} week range: "
        f"{range_low} → {range_high}"
    )

    return range_low, range_high


def generate_strikes():
    step = STRIKE_STEP[
        INDEX_NAME
    ]

    range_low, range_high = get_recent_range()

    start_strike = round_down(
        range_low,
        step
    )

    end_strike = round_up(
        range_high,
        step
    )

    strikes = list(
        range(
            start_strike,
            end_strike + step,
            step
        )
    )

    log.info(
        f"Generated {len(strikes)} strikes"
    )

    return strikes

def get_live_atm_strikes():
    file_path = get_spot_daily_file()

    df = read_parquet(
        file_path
    )

    latest_close = df.iloc[-1][
        "close"
    ]

    step = STRIKE_STEP[
        INDEX_NAME
    ]

    atm = round(
        latest_close / step
    ) * step

    strikes = [
        atm - step,
        atm,
        atm + step
    ]

    log.info(
        f"Live ATM strikes: {strikes}"
    )

    return strikes