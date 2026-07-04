from datetime import timedelta
import pandas as pd

def chunk_ranges(
    start_date,
    end_date,
    chunk_days
):
    chunks = []

    current = start_date

    while current < end_date:
        chunk_end = min(
            current + timedelta(days=chunk_days),
            end_date
        )

        chunks.append(
            (current, chunk_end)
        )

        current = chunk_end

    return chunks

def get_next_fetch_start(
    last_timestamp,
    timeframe_seconds
):
    ts = pd.to_datetime(
        last_timestamp
    )

    return ts