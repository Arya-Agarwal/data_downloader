import pandas as pd
import time
from datetime import datetime

from config import (
    INDICES_DIR,
    INDEX_FOLDER,
    INDEX_NAME,
    EXCHANGE,
    SPOT_TOKEN,
    TIMEFRAMES,
    START_DATE
)

from core.logger import log
from core.utils.helpers import (
    chunk_ranges,
    get_next_fetch_start
)
from core.utils.file_manager import (
    ensure_dir,
    atomic_write_parquet,
    file_exists,
    read_parquet
)
from core.utils.time_utils import (
    to_ist,
    now_ist,
    format_date,
    format_time,
    format_day
)
from core.validators.data_validator import (
    validate_dataframe
)
from core.tracker.tracker import (
    upsert_tracker_row,
    load_tracker
)
from core.downloaders.incremental import (
    append_incremental
)
from core.utils.market_utils import (
    is_file_complete_for_day,
    get_market_close_for_day
)


def get_spot_folder():
    path = (
        INDICES_DIR
        / INDEX_FOLDER
        / "spot"
    )

    ensure_dir(path)

    return path


def get_spot_filename(
    timeframe,
    first_timestamp
):
    tf_folder = TIMEFRAMES[
        timeframe
    ]["folder"]

    dt = pd.to_datetime(
        first_timestamp
    )

    return (
        f"{INDEX_FOLDER.upper()}_spot_"
        f"{tf_folder}_"
        f"{dt.strftime('%y%m%d')}_"
        f"{dt.strftime('%H%M')}.parquet"
    )

def get_existing_spot_tracker(
    timeframe
):
    tracker_df = load_tracker()

    result = tracker_df[
        (tracker_df["segment"] == "SPOT")
        &
        (tracker_df["timeframe"] == timeframe)
        &
        (tracker_df["instrument_token"] == SPOT_TOKEN)
    ]

    if result.empty:
        return None

    return result.iloc[0]

def fetch_historical_chunk(
    kite,
    token,
    timeframe,
    start_date,
    end_date
):
    start_str = start_date.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    end_str = end_date.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for attempt in range(3):
        try:
            log.info(
                f"Fetching {timeframe} "
                f"{start_str} → {end_str}"
            )

            data = kite.historical_data(
                instrument_token=token,
                from_date=start_str,
                to_date=end_str,
                interval=timeframe,
                oi=True
            )

            return pd.DataFrame(data)

        except Exception as e:
            retry_wait = [
                300,
                600,
                900
            ][attempt]

            log.warning(
                f"Fetch failed ({attempt + 1}/3): {e}"
            )

            if attempt < 2:
                log.info(
                    f"Retrying in {retry_wait // 60} minutes..."
                )

                time.sleep(
                    retry_wait
                )

            else:
                log.error(
                    "Max retries reached. Stopping bot."
                )

                raise

def prepare_dataframe(df):
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(
        df["date"]
    )

    df["timestamp"] = df[
        "timestamp"
    ].apply(to_ist)

    df["date_only"] = df[
        "timestamp"
    ].apply(format_date)

    df["time_only"] = df[
        "timestamp"
    ].apply(format_time)

    df["day_of_week"] = df[
        "timestamp"
    ].apply(format_day)

    df = df.drop(
        columns=["date"]
    )

    df = df.rename(
        columns={
            "date_only": "date",
            "time_only": "time"
        }
    )

    cols = [
        "timestamp",
        "date",
        "time",
        "day_of_week",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    if "oi" in df.columns:
        cols.append("oi")

    return df[cols]

def download_spot_timeframe(
    kite,
    timeframe
):
    chunk_days = TIMEFRAMES[
        timeframe
    ]["chunk_days"]

    existing_tracker = get_existing_spot_tracker(
        timeframe
    )

    if existing_tracker is not None:
        start_date = get_next_fetch_start(
            existing_tracker["last_timestamp"],
            TIMEFRAMES[timeframe]["seconds"]
        )

        log.info(
            f"Incremental mode for {timeframe} "
            f"from {start_date}"
        )

    else:
        start_date = to_ist(
            pd.to_datetime(
                START_DATE
            )
        )

    end_date = now_ist()

    chunks = chunk_ranges(
        start_date,
        end_date,
        chunk_days
    )

    all_data = []

    for start, end in chunks:
        df = fetch_historical_chunk(
            kite,
            SPOT_TOKEN,
            timeframe,
            start,
            end
        )

        if not df.empty:
            all_data.append(df)

    if not all_data:
        log.warning(
            f"No data fetched for {timeframe}"
        )
        return

    final_df = pd.concat(
        all_data,
        ignore_index=True
    )

    final_df = prepare_dataframe(
        final_df
    )

    final_df = final_df.drop_duplicates(
        subset=["timestamp"]
    )

    final_df = final_df.sort_values(
        "timestamp"
    )

    validation = validate_dataframe(
        final_df,
        timeframe
    )

    spot_folder = get_spot_folder()

    if existing_tracker is not None:
        file_path = existing_tracker["file_path"]

    else:
        file_name = get_spot_filename(
            timeframe,
            final_df.iloc[0]["timestamp"]
        )

        file_path = spot_folder / file_name
    
    tracker_row = {
        "instrument_name": INDEX_NAME,
        "exchange": EXCHANGE,
        "segment": "SPOT",
        "instrument_token": SPOT_TOKEN,
        "tradingsymbol": INDEX_NAME,
        "expiry": None,
        "strike": None,
        "option_type": None,
        "timeframe": timeframe,
        "file_path": str(file_path),
        "first_timestamp": str(
            final_df.iloc[0]["timestamp"]
        ),
        "last_timestamp": str(
            final_df.iloc[-1]["timestamp"]
        ),
        "rows": len(final_df),
        "last_downloaded_at": str(
            now_ist()
        ),
        "contract_status": "ACTIVE",
        "integrity_status": "OK",
        "validation_status": validation["status"],
        "has_historical_gaps": (
            validation["missing_candles"] > 0
        ),
        "is_tail_complete": True,
        "expected_last_timestamp": str(
            final_df.iloc[-1]["timestamp"]
        ),
        "last_validated_at": str(
            now_ist()
        ),
        "source_timezone": "Asia/Kolkata",
        "recovery_attempts": 0,
        "last_recovery_attempt_at": None,
        "recovery_status": "NOT_REQUIRED"
    }

    if existing_tracker is not None:
        append_incremental(
            file_path=file_path,
            tracker_row=tracker_row,
            new_df=final_df,
            timeframe=timeframe
        )

        return

    atomic_write_parquet(
        final_df,
        file_path
    )

    

    upsert_tracker_row(
        tracker_row
    )

    log.info(
        f"Spot saved: {file_path}"
    )


def download_spot(kite):
    for timeframe in TIMEFRAMES:
        download_spot_timeframe(
            kite,
            timeframe
        )

def download_eod_pending_spot(
    kite
):
    tracker_df = load_tracker()

    spot_rows = tracker_df[
        (tracker_df["segment"] == "SPOT")
        &
        (tracker_df["contract_status"] == "ACTIVE")
    ]

    if spot_rows.empty:
        log.info(
            "No active spot files"
        )
        return

    for _, row in spot_rows.iterrows():
        timeframe = row[
            "timeframe"
        ]

        timeframe_seconds = TIMEFRAMES[
            timeframe
        ]["seconds"]

        if timeframe == "day":
            continue

        if is_file_complete_for_day(
            row["last_timestamp"],
            timeframe_seconds
        ):
            continue

        log.info(
            f"EOD refreshing spot: "
            f"{row['tradingsymbol']}"
        )

        new_df = fetch_historical_chunk(
            kite,
            row["instrument_token"],
            timeframe,
            pd.to_datetime(
                row["last_timestamp"]
            ),
            get_market_close_for_day(
                row["last_timestamp"]
            )
        )

        if new_df.empty:
            continue

        new_df = prepare_dataframe(
            new_df
        )

        append_incremental(
            file_path=row["file_path"],
            tracker_row=row.to_dict(),
            new_df=new_df,
            timeframe=timeframe
        )
        
def get_today_high_low(kite):
    """
    Returns today's high and low from
    minute candles.

    Used to initialise the live strike
    universe when the bot starts after
    market open.
    """

    now = now_ist()

    start = now.replace(
        hour=9,
        minute=15,
        second=0,
        microsecond=0
    )

    if now <= start:
        return None, None

    df = fetch_historical_chunk(
        kite,
        SPOT_TOKEN,
        "minute",
        start,
        now
    )

    if df.empty:
        return None, None

    return (
        float(df["low"].min()),
        float(df["high"].max())
    )