import pandas as pd

from config import TRACKER_FILE
from core.logger import log
from core.utils.file_manager import (
    file_exists,
    atomic_write_parquet,
    ensure_dir,
    read_parquet
)


TRACKER_COLUMNS = [
    "instrument_name",
    "exchange",
    "segment",
    "instrument_token",
    "tradingsymbol",
    "expiry",
    "strike",
    "option_type",
    "timeframe",
    "file_path",
    "first_timestamp",
    "last_timestamp",
    "rows",
    "last_downloaded_at",
    "contract_status",
    "integrity_status",
    "validation_status",
    "has_historical_gaps",
    "is_tail_complete",
    "expected_last_timestamp",
    "last_validated_at",
    "source_timezone",
    "recovery_attempts",
    "last_recovery_attempt_at",
    "recovery_status"
]


def initialize_tracker():
    ensure_dir(
        TRACKER_FILE.parent
    )

    if not file_exists(TRACKER_FILE):
        df = pd.DataFrame(
            columns=TRACKER_COLUMNS
        )

        atomic_write_parquet(
            df,
            TRACKER_FILE
        )

        log.info(
            "Tracker initialized"
        )


def load_tracker():
    initialize_tracker()

    return read_parquet(
        TRACKER_FILE
    )


def save_tracker(df):
    df = df.copy()
    
    atomic_write_parquet(
        df,
        TRACKER_FILE
    )


def upsert_tracker_row(row):
    df = load_tracker()

    match = (
        (df["instrument_token"] == row["instrument_token"])
        &
        (df["timeframe"] == row["timeframe"])
        &
        (df["file_path"] == row["file_path"])
    )

    if match.any():
        df.loc[
            match,
            TRACKER_COLUMNS
        ] = [
            row[col]
            for col in TRACKER_COLUMNS
        ]

        log.info(
            f"Tracker updated: {row['tradingsymbol']}"
        )

    else:
        df = pd.concat(
            [
                df,
                pd.DataFrame([row])
            ],
            ignore_index=True
        )

        log.info(
            f"Tracker inserted: {row['tradingsymbol']}"
        )

    save_tracker(df)


def get_tracker_rows(
    segment=None,
    contract_status=None
):
    df = load_tracker()

    if segment:
        df = df[
            df["segment"] == segment
        ]

    if contract_status:
        df = df[
            df["contract_status"] == contract_status
        ]

    return df


def mark_expired_contracts():
    df = load_tracker()

    if df.empty:
        return

    today = pd.Timestamp.today().date()

    for idx, row in df.iterrows():
        if pd.notna(row["expiry"]):
            try:
                expiry_date = pd.to_datetime(
                    row["expiry"]
                ).date()

                if today > expiry_date:
                    df.at[
                        idx,
                        "contract_status"
                    ] = "EXPIRED"

            except Exception:
                pass

    save_tracker(df)

    log.info(
        "Expired contract status updated"
    )