from pathlib import Path

import pandas as pd

from config import (
    DATA_DIR
)
from core.utils.file_manager import (
    ensure_dir
)


class LiveFileManager:

    def __init__(self):
        self.base = (
            DATA_DIR
            / "live"
        )

    def get_file_path(
        self,
        instrument
    ):
        segment = instrument[
            "segment"
        ]

        today = pd.Timestamp.now().strftime(
            "%Y%m%d"
        )

        if segment == "INDICES":

            folder = (
                self.base
                / "spot"
            )

            filename = (
                f"{instrument['tradingsymbol']}_{today}.parquet"
            )

        elif segment == "NFO-FUT":

            expiry = pd.to_datetime(
                instrument["expiry"]
            ).strftime(
                "%d%m%y"
            )

            folder = (
                self.base
                / "futures"
                / expiry
            )

            filename = (
                f"{instrument['tradingsymbol']}_{today}.parquet"
            )

        elif segment == "NFO-OPT":

            expiry = pd.to_datetime(
                instrument["expiry"]
            ).strftime(
                "%d%m%y"
            )

            folder = (
                self.base
                / "options"
                / expiry
            )

            filename = (
                f"{instrument['tradingsymbol']}_{today}.parquet"
            )

        else:
            raise ValueError(
                f"Unknown segment {segment}"
            )

        ensure_dir(
            folder
        )

        return folder / filename