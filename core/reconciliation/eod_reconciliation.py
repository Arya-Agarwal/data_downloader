from core.logger import log

from core.tracker.tracker import (
    load_tracker,
    upsert_tracker_row
)

from core.utils.file_manager import (
    read_parquet,
    file_exists
)

from core.validators.data_validator import (
    validate_dataframe
)

from core.utils.time_utils import (
    now_ist
)


def run_eod_reconciliation():

    log.info(
        "========== EOD RECONCILIATION =========="
    )

    tracker = load_tracker()

    if tracker.empty:

        log.info(
            "Tracker is empty."
        )

        return

    validated = 0

    failed = 0

    for _, row in tracker.iterrows():

        file_path = row["file_path"]

        if not file_exists(
            file_path
        ):

            log.warning(
                f"Missing file: {file_path}"
            )

            continue

        try:

            df = read_parquet(
                file_path
            )

            result = validate_dataframe(
                df,
                row["timeframe"],
                file_path
            )

            row[
                "validation_status"
            ] = result[
                "status"
            ]

            row[
                "last_validated_at"
            ] = str(
                now_ist()
            )

            row[
                "rows"
            ] = len(df)

            row[
                "first_timestamp"
            ] = str(
                df.iloc[0]["timestamp"]
            )

            row[
                "last_timestamp"
            ] = str(
                df.iloc[-1]["timestamp"]
            )

            row[
                "has_historical_gaps"
            ] = (
                result["missing_candles"] > 0
            )

            upsert_tracker_row(
                row
            )

            validated += 1

        except Exception as e:

            failed += 1

            log.exception(
                f"Reconciliation failed for "
                f"{file_path}: {e}"
            )

    log.info(

        f"EOD reconciliation completed. "

        f"Validated={validated} "

        f"Failed={failed}"

    )