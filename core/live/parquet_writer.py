from pathlib import Path

import pandas as pd

from core.logger import log
from core.utils.file_manager import (
    ensure_dir,
    atomic_write_parquet,
    read_parquet,
    file_exists
)


class ParquetWriter:

    def append(
        self,
        file_path,
        rows
    ):
        if not rows:
            return

        file_path = Path(file_path)

        ensure_dir(
            file_path.parent
        )

        new_df = pd.DataFrame(
            rows
        )

        if file_exists(
            file_path
        ):
            old_df = read_parquet(
                file_path
            )

            final_df = pd.concat(
                [
                    old_df,
                    new_df
                ],
                ignore_index=True
            )

        else:
            final_df = new_df

        atomic_write_parquet(
            final_df,
            file_path
        )

        log.info(
            f"Written {len(new_df)} rows -> {file_path}"
        )