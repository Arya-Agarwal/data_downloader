import pandas as pd
from pathlib import Path

TRACKER_PATH = r"C:\trading\data_downloader\data\tracker\tracker.parquet"
OUTPUT_PATH = r"C:\trading\data_downloader\data\tracker\schema_audit.csv"


def main():
    tracker = pd.read_parquet(
        TRACKER_PATH
    )

    output_rows = []

    for _, row in tracker.iterrows():
        file_path = row["file_path"]
        segment = row["segment"]

        try:
            df = pd.read_parquet(
                file_path
            )

            for col in df.columns:
                output_rows.append(
                    {
                        "file_name": Path(
                            file_path
                        ).name,
                        "segment": segment,
                        "column_name": col,
                        "dtype": str(
                            df[col].dtype
                        ),
                        "blank_count": int(
                            df[col].isnull().sum()
                        ),
                        "total_rows": len(df)
                    }
                )

        except Exception as e:
            output_rows.append(
                {
                    "file_name": Path(
                        file_path
                    ).name,
                    "segment": segment,
                    "column_name": "ERROR",
                    "dtype": None,
                    "blank_count": None,
                    "total_rows": None
                }
            )

            print(
                f"Failed: {file_path} -> {e}"
            )

    output_df = pd.DataFrame(
        output_rows
    )

    output_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"Schema audit saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()