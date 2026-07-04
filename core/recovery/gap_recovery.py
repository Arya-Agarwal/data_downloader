import pandas as pd

from core.logger import log
from core.utils.file_manager import (
    read_parquet,
    atomic_write_parquet
)
from core.validators.data_validator import (
    validate_dataframe
)
from core.tracker.tracker import (
    load_tracker,
    upsert_tracker_row
)
from core.downloaders.spot_downloader import (
    fetch_historical_chunk
)
from core.downloaders.spot_downloader import (
    prepare_dataframe
)
from core.utils.time_utils import (
    now_ist
)
from core.validators.data_validator import (
    validate_dataframe,
    TIMEFRAME_MAP
)

from core.utils.market_utils import (
    get_expected_session_timestamps
)


def get_expected_delta(
    timeframe
):
    mapping = {
        "minute": "1min",
        "5minute": "5min",
        "15minute": "15min",
        "60minute": "60min",
        "day": "1D"
    }

    return mapping[
        timeframe
    ]


def find_missing_ranges(
    df,
    timeframe
):
    timestamps = pd.to_datetime(
        df["timestamp"],
        utc=True
    ).dt.tz_convert(
        "Asia/Kolkata"
    )

    timeframe_seconds = TIMEFRAME_MAP[
        timeframe
    ]

    grouped = {}

    for ts in timestamps:
        day = ts.date()

        if day not in grouped:
            grouped[day] = []

        grouped[day].append(ts)

    missing = []

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

        for ts in expected_range:
            if ts not in actual_set:
                missing.append(ts)

    if not missing:
        return []

    missing = sorted(missing)

    ranges = []
    start = missing[0]
    prev = missing[0]

    delta = pd.Timedelta(
        seconds=timeframe_seconds
    )

    for current in missing[1:]:
        if current != prev + delta:
            ranges.append(
                (
                    start,
                    prev
                )
            )
            start = current

        prev = current

    ranges.append(
        (
            start,
            prev
        )
    )

    return ranges

def recover_file_gaps(
    kite,
    tracker_row
):
    file_path = tracker_row[
        "file_path"
    ]

    timeframe = tracker_row[
        "timeframe"
    ]

    token = tracker_row[
        "instrument_token"
    ]

    df = read_parquet(
        file_path
    )
    
    current_validation = validate_dataframe(
        df,
        timeframe,
        file_path
    )
    
    if current_validation["status"] == "VALID":
        tracker_row[
            "validation_status"
        ] = "VALID"

        tracker_row[
            "last_validated_at"
        ] = str(
            now_ist()
        )

        upsert_tracker_row(
            tracker_row
        )

        log.info(
            f"Already valid, skipping recovery: {file_path}"
        )

        return

    ranges = find_missing_ranges(
        df,
        timeframe
    )

    if not ranges:
        tracker_row[
            "validation_status"
        ] = current_validation[
            "status"
        ]

        tracker_row[
            "last_validated_at"
        ] = str(
            now_ist()
        )

        tracker_row[
            "recovery_status"
        ] = (
            "NOT_REQUIRED"
            if current_validation[
                "status"
            ] == "VALID"
            else "FAILED"
        )

        upsert_tracker_row(
            tracker_row
        )

        log.info(
            f"No recoverable gaps found: {file_path}"
        )

        return

    recovered = []

    for start, end in ranges:
        log.info(
            f"Recovering gap: "
            f"{start} → {end}"
        )

        gap_df = fetch_historical_chunk(
            kite,
            token,
            timeframe,
            start,
            end
        )

        if not gap_df.empty:
            recovered.append(
                gap_df
            )

    if not recovered:
        tracker_row[
            "recovery_attempts"
        ] = (
            tracker_row.get(
                "recovery_attempts",
                0
            ) or 0
        ) + 1

        tracker_row[
            "last_recovery_attempt_at"
        ] = str(
            now_ist()
        )

        if tracker_row[
            "recovery_attempts"
        ] >= 3:
            tracker_row[
                "recovery_status"
            ] = "UNRECOVERABLE"

        else:
            tracker_row[
                "recovery_status"
            ] = "FAILED"

        upsert_tracker_row(
            tracker_row
        )

        log.warning(
            f"No gap data recovered: {file_path}"
        )

        return

    recovered_df = pd.concat(
        recovered,
        ignore_index=True
    )

    recovered_df = prepare_dataframe(
        recovered_df
    )

    final_df = pd.concat(
        [
            df,
            recovered_df
        ],
        ignore_index=True
    )

    final_df = final_df.drop_duplicates(
        subset=["timestamp"],
        keep="last"
    )

    final_df = final_df.sort_values(
        "timestamp"
    )

    validation = validate_dataframe(
        final_df,
        timeframe
    )

    atomic_write_parquet(
        final_df,
        file_path
    )

    tracker_row[
        "validation_status"
    ] = validation[
        "status"
    ]

    tracker_row[
        "first_timestamp"
    ] = str(
        final_df.iloc[0]["timestamp"]
    )

    tracker_row[
        "last_timestamp"
    ] = str(
        final_df.iloc[-1]["timestamp"]
    )

    tracker_row[
        "rows"
    ] = len(
        final_df
    )

    tracker_row[
        "last_validated_at"
    ] = str(
        now_ist()
    )

    tracker_row[
        "recovery_status"
    ] = (
        "RECOVERED"
        if validation["status"] == "VALID"
        else "FAILED"
    )

    upsert_tracker_row(
        tracker_row
    )

    log.info(
        f"Gap recovery complete: "
        f"{file_path}"
    )


def recover_all_gaps(
    kite
):
    tracker_df = load_tracker()

    gap_rows = tracker_df[
        (
            tracker_df["validation_status"] == "VALID_WITH_GAPS"
        )
        &
        (
            tracker_df["recovery_status"].fillna("NOT_REQUIRED") == "NOT_REQUIRED"
        )
    ]

    if gap_rows.empty:
        log.info(
            "No files need recovery"
        )
        return

    log.info(
        f"Gap recovery files: "
        f"{len(gap_rows)}"
    )

    for _, row in gap_rows.iterrows():
        recover_file_gaps(
            kite,
            row
        )