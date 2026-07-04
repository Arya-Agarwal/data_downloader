from pathlib import Path
import pandas as pd
import os
import time

def ensure_dir(path):
    Path(path).mkdir(
        parents=True,
        exist_ok=True
    )


def atomic_write_parquet(df, final_path):
    final_path = Path(final_path)

    temp_path = final_path.with_name(
        f"temp_{final_path.name}"
    )

    df.to_parquet(
        temp_path,
        index=False
    )

    for attempt in range(5):
        try:
            os.replace(
                temp_path,
                final_path
            )
            break

        except PermissionError:
            if attempt < 4:
                time.sleep(
                    0.5
                )
            else:
                raise

def read_parquet(path):
    return pd.read_parquet(path)


def file_exists(path):
    return Path(path).exists()