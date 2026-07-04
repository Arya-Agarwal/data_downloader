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
from core.utils.market_utils import (
    is_file_complete_for_day,
    get_market_close_for_day
)
from core.downloaders.incremental import (
    append_incremental
)


def get_options_folder(
    expiry
):
    expiry_folder = pd.to_datetime(
        expiry
    ).strftime("%d%m%y")

    path = (
        INDICES_DIR
        / INDEX_FOLDER
        / "options"
        / expiry_folder
    )

    ensure_dir(path)

    return path


def get_active_options(
    instruments_df
):
    today = pd.Timestamp.today().date()

    options_df = instruments_df[
        (instruments_df["segment"] == "NFO-OPT")
        &
        (instruments_df["name"] == "NIFTY")
    ].copy()

    options_df["expiry"] = pd.to_datetime(
        options_df["expiry"]
    )

    options_df = options_df[
        options_df["expiry"].dt.date >= today
    ]

    unique_expiries = sorted(
        options_df["expiry"].unique()
    )

    selected_expiries = unique_expiries[:2]

    return options_df[
        options_df["expiry"].isin(
            selected_expiries
        )
    ]


def filter_option_universe(
    options_df,
    strikes
):
    return options_df[
        options_df["strike"].isin(
            strikes
        )
    ]


def get_existing_option_tracker(
    token,
    timeframe
):
    tracker_df = load_tracker()

    result = tracker_df[
        (tracker_df["segment"] == "OPTION")
        &
        (tracker_df["instrument_token"] == token)
        &
        (tracker_df["timeframe"] == timeframe)
    ]

    if result.empty:
        return None

    return result.iloc[0]


def get_option_filename(
    strike,
    option_type,
    expiry,
    first_timestamp,
    timeframe_folder
):
    expiry_str = pd.to_datetime(
        expiry
    ).strftime("%d%m%y")

    start_dt = pd.to_datetime(
        first_timestamp
    )

    return (
        f"{INDEX_FOLDER.upper()}_"
        f"{int(strike)}_"
        f"{option_type}_"
        f"{expiry_str}_"
        f"{start_dt.strftime('%y%m%d')}_"
        f"{start_dt.strftime('%H%M')}_"
        f"{timeframe_folder}.parquet"
    )


def download_single_option(
    kite,
    option_row,
    allowed_timeframes=None
):
    token = option_row[
        "instrument_token"
    ]

    expiry = option_row[
        "expiry"
    ]

    strike = option_row[
        "strike"
    ]

    option_type = option_row[
        "instrument_type"
    ]

    timeframes_to_run = (
        allowed_timeframes
        if allowed_timeframes
        else TIMEFRAMES.keys()
    )

    for timeframe in timeframes_to_run:
        
        existing_tracker = get_existing_option_tracker(
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

        options_folder = get_options_folder(
            expiry
        )

        if existing_tracker is not None:
            file_path = existing_tracker[
                "file_path"
            ]

        else:
            file_name = get_option_filename(
                strike,
                option_type,
                expiry,
                final_df.iloc[0]["timestamp"],
                TIMEFRAMES[timeframe]["folder"]
            )

            file_path = options_folder / file_name

        tracker_row = {
            "instrument_name": INDEX_NAME,
            "exchange": EXCHANGE,
            "segment": "OPTION",
            "instrument_token": token,
            "tradingsymbol": option_row["tradingsymbol"],
            "expiry": str(expiry),
            "strike": strike,
            "option_type": option_type,
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
            from core.downloaders.incremental import (
                append_incremental
            )

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
            f"Option saved: {file_path}"
        )


def download_options(
    kite,
    instruments_df,
    strikes,
    allowed_timeframes=None
):
    active_options = get_active_options(
        instruments_df
    )

    filtered_options = filter_option_universe(
        active_options,
        strikes
    )

    for _, option_row in filtered_options.iterrows():
        download_single_option(
            kite,
            option_row,
            allowed_timeframes
        )


def download_eod_pending_options(
    kite
):
    tracker_df = load_tracker()

    option_rows = tracker_df[
        (tracker_df["segment"] == "OPTION")
        &
        (tracker_df["contract_status"] == "ACTIVE")
    ]

    if option_rows.empty:
        log.info(
            "No active option files"
        )
        return

    for _, row in option_rows.iterrows():
        timeframe = row[
            "timeframe"
        ]

        timeframe_seconds = TIMEFRAMES[
            timeframe
        ]["seconds"]

        if is_file_complete_for_day(
            row["last_timestamp"],
            timeframe_seconds
        ):
            continue

        log.info(
            f"EOD refreshing: "
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