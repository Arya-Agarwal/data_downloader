from pathlib import Path
import pandas as pd
import os
import time
import pyarrow as pa
import pyarrow.parquet as pq

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

def append_parquet(
    df,
    file_path
):
    file_path = Path(file_path)

    ensure_dir(
        file_path.parent
    )

    table = pa.Table.from_pandas(
        df,
        preserve_index=False
    )

    if not file_path.exists():

        writer = pq.ParquetWriter(
            file_path,
            table.schema
        )

        writer.write_table(
            table
        )

        writer.close()

        return

    existing = pd.read_parquet(
        file_path
    )

    combined = pd.concat(
        [
            existing,
            df
        ],
        ignore_index=True
    )

    atomic_write_parquet(
        combined,
        file_path
    )