import pandas as pd

from core.logger import log
from core.utils.file_manager import (
    read_parquet,
    atomic_write_parquet
)
from core.validators.data_validator import (
    validate_dataframe
)
from core.utils.helpers import (
    get_next_fetch_start
)
from core.utils.time_utils import (
    now_ist,
    to_ist,
    format_date,
    format_time,
    format_day
)
from core.tracker.tracker import (
    upsert_tracker_row
)


def append_incremental(
    file_path,
    tracker_row,
    new_df,
    timeframe
):
    if new_df.empty:
        log.info(
            "No new candles to append"
        )
        return

    existing_df = read_parquet(
        file_path
    )


    final_df = pd.concat(
        [
            existing_df,
            new_df
        ],
        ignore_index=True
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

    atomic_write_parquet(
        final_df,
        file_path
    )

    tracker_row["last_timestamp"] = str(
        final_df.iloc[-1]["timestamp"]
    )

    tracker_row["rows"] = len(
        final_df
    )

    tracker_row["last_downloaded_at"] = str(
        now_ist()
    )

    tracker_row["validation_status"] = validation["status"]
    
    tracker_row["has_historical_gaps"] = (
        validation["missing_candles"] > 0
    )

    tracker_row["is_tail_complete"] = True

    tracker_row["expected_last_timestamp"] = str(
        final_df.iloc[-1]["timestamp"]
    )

    tracker_row["last_validated_at"] = str(
        now_ist()
    )

    upsert_tracker_row(
        tracker_row
    )

    log.info(
        f"Incremental append complete: {file_path}"
    )