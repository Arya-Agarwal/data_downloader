import json
from datetime import datetime
import pandas as pd

from config import (
    INSTRUMENT_MASTER_DIR,
    INSTRUMENT_MASTER_FILE,
    INSTRUMENT_MASTER_META
)

from core.logger import log
from core.utils.file_manager import (
    ensure_dir,
    atomic_write_parquet,
    file_exists,
    read_parquet
)
from core.utils.time_utils import get_today


def load_metadata():
    if not file_exists(INSTRUMENT_MASTER_META):
        return None

    with open(
        INSTRUMENT_MASTER_META,
        "r"
    ) as file:
        return json.load(file)


def save_metadata(row_count):
    metadata = {
        "last_refresh_date": str(get_today()),
        "row_count": row_count
    }

    with open(
        INSTRUMENT_MASTER_META,
        "w"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4
        )


def is_refresh_needed():
    metadata = load_metadata()

    if metadata is None:
        return True

    last_refresh = metadata["last_refresh_date"]

    return last_refresh < str(get_today())


def refresh_instrument_master(kite):
    log.info(
        "Refreshing instrument master"
    )

    ensure_dir(
        INSTRUMENT_MASTER_DIR
    )

    instruments = kite.instruments()

    df = pd.DataFrame(
        instruments
    )

    if "expiry" in df.columns:
        df["expiry"] = df["expiry"].astype(str)

    if "strike" in df.columns:
        df["strike"] = pd.to_numeric(
            df["strike"],
            errors="coerce"
        )

    if "instrument_token" in df.columns:
        df["instrument_token"] = pd.to_numeric(
            df["instrument_token"],
            errors="coerce"
        )

    if "lot_size" in df.columns:
        df["lot_size"] = pd.to_numeric(
            df["lot_size"],
            errors="coerce"
        )

    atomic_write_parquet(
        df,
        INSTRUMENT_MASTER_FILE
    )

    save_metadata(
        len(df)
    )

    log.info(
        f"Instrument master refreshed: {len(df)} rows"
    )

    return df


def load_instrument_master(kite):
    if (
        is_refresh_needed()
        or
        not file_exists(INSTRUMENT_MASTER_FILE)
    ):
        return refresh_instrument_master(
            kite
        )

    log.info(
        "Using cached instrument master"
    )

    return read_parquet(
        INSTRUMENT_MASTER_FILE
    )


def find_exact_instrument(
    df,
    tradingsymbol,
    exchange
):
    result = df[
        (df["tradingsymbol"] == tradingsymbol)
        &
        (df["exchange"] == exchange)
    ]

    if result.empty:
        log.error(
            f"Instrument not found: {exchange}:{tradingsymbol}"
        )
        return None

    return result.iloc[0]