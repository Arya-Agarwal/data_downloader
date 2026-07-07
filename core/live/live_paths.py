from pathlib import Path

from config import DATA_DIR

from core.utils.file_manager import (
    ensure_dir
)

from core.utils.time_utils import (
    get_today
)


def get_live_root():

    path = (
        DATA_DIR
        / "live"
        / str(get_today())
    )

    ensure_dir(path)

    return path


def get_segment_dir(
    segment
):

    path = (
        get_live_root()
        / segment
    )

    ensure_dir(path)

    return path


def get_parquet_file(
    segment,
    tradingsymbol
):

    return (
        get_segment_dir(segment)
        / f"{tradingsymbol}.parquet"
    )