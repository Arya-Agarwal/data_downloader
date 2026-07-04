import pandas as pd

from config import (
    INDEX_NAME,
    EXCHANGE,
    INDEX_FOLDER,
    INDICES_DIR,
    TIMEFRAMES,
    START_DATE
)

from core.logger import log
from core.utils.file_manager import (
    ensure_dir,
    atomic_write_parquet
)
from core.utils.helpers import (
    chunk_ranges,
    get_next_fetch_start
)
from core.utils.time_utils import (
    now_ist,
    to_ist
)
from core.validators.data_validator import (
    validate_dataframe
)
from core.tracker.tracker import (
    upsert_tracker_row,
    load_tracker
)
from core.downloaders.spot_downloader import (
    fetch_historical_chunk,
    prepare_dataframe
)
from core.downloaders.incremental import (
    append_incremental
)
from core.utils.market_utils import (
    is_file_complete_for_day,
    get_market_close_for_day
)


def get_futures_folder():
    path = (
        INDICES_DIR
        / INDEX_FOLDER
        / "futures"
    )

    ensure_dir(path)

    return path


def get_active_futures(
    instruments_df
):
    today = pd.Timestamp.today().date()

    futures_df = instruments_df[
        (instruments_df["segment"] == "NFO-FUT")
        &
        (instruments_df["name"] == "NIFTY")
    ].copy()

    futures_df["expiry"] = pd.to_datetime(
        futures_df["expiry"]
    )

    futures_df = futures_df[
        futures_df["expiry"].dt.date >= today
    ]

    futures_df = futures_df.sort_values(
        "expiry"
    )

    return futures_df.head(2)


def get_existing_future_tracker(
    token,
    timeframe
):
    tracker_df = load_tracker()

    result = tracker_df[
        (tracker_df["segment"] == "FUTURE")
        &
        (tracker_df["instrument_token"] == token)
        &
        (tracker_df["timeframe"] == timeframe)
    ]

    if result.empty:
        return None

    return result.iloc[0]


def get_futures_filename(
    expiry,
    timeframe,
    first_timestamp
):
    tf_folder = TIMEFRAMES[
        timeframe
    ]["folder"]

    expiry_str = pd.to_datetime(
        expiry
    ).strftime("%d%m%y")

    start_dt = pd.to_datetime(
        first_timestamp
    )

    return (
        f"{INDEX_FOLDER.upper()}_futures_"
        f"{expiry_str}_"
        f"{tf_folder}_"
        f"{start_dt.strftime('%y%m%d')}_"
        f"{start_dt.strftime('%H%M')}.parquet"
    )


def download_single_future(
    kite,
    future_row
):
    token = future_row[
        "instrument_token"
    ]

    expiry = future_row[
        "expiry"
    ]

    for timeframe in TIMEFRAMES:
        existing_tracker = get_existing_future_tracker(
            token,
            timeframe
        )

        if existing_tracker is not None:
            start_date = get_next_fetch_start(
                existing_tracker["last_timestamp"],
                TIMEFRAMES[timeframe]["seconds"]
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
            TIMEFRAMES[timeframe]["chunk_days"]
        )

        all_data = []

        for start, end in chunks:
            df = fetch_historical_chunk(
                kite,
                token,
                timeframe,
                start,
                end
            )

            if not df.empty:
                all_data.append(df)

        if not all_data:
            continue

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

        futures_folder = get_futures_folder()

        if existing_tracker is not None:
            file_path = existing_tracker[
                "file_path"
            ]

        else:
            file_name = get_futures_filename(
                expiry,
                timeframe,
                final_df.iloc[0]["timestamp"]
            )

            file_path = futures_folder / file_name

        tracker_row = {
            "instrument_name": INDEX_NAME,
            "exchange": EXCHANGE,
            "segment": "FUTURE",
            "instrument_token": token,
            "tradingsymbol": future_row["tradingsymbol"],
            "expiry": str(expiry),
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

        else:
            atomic_write_parquet(
                final_df,
                file_path
            )

            upsert_tracker_row(
                tracker_row
            )

        log.info(
            f"Future saved: {file_path}"
        )


def download_futures(
    kite,
    instruments_df
):
    active_futures = get_active_futures(
        instruments_df
    )

    for _, future_row in active_futures.iterrows():
        download_single_future(
            kite,
            future_row
        )
        
def download_eod_pending_futures(
    kite
):
    tracker_df = load_tracker()

    future_rows = tracker_df[
        (tracker_df["segment"] == "FUTURE")
        &
        (tracker_df["contract_status"] == "ACTIVE")
    ]

    if future_rows.empty:
        log.info(
            "No active future files"
        )
        return

    for _, row in future_rows.iterrows():
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
            f"EOD refreshing future: "
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