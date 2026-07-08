from pathlib import Path
from datetime import datetime

import pandas as pd


LIVE_ROOT = Path("data/live")


def summarize_file(file_path):
    try:
        df = pd.read_parquet(file_path)

        rows = len(df)

        if rows == 0:
            return {
                "rows": 0,
                "columns": [],
                "first": None,
                "last": None,
                "unique_ts": 0,
                "sample": "EMPTY"
            }

        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])

            first = ts.min()
            last = ts.max()
            unique_ts = ts.nunique()
        else:
            first = None
            last = None
            unique_ts = None

        sample = (
            df.iloc[0]
            .to_string()
        )

        return {
            "rows": rows,
            "columns": list(df.columns),
            "first": first,
            "last": last,
            "unique_ts": unique_ts,
            "sample": sample
        }

    except Exception as e:

        return {
            "error": str(e)
        }


def main():

    if not LIVE_ROOT.exists():
        print("Live folder not found.")
        return

    latest_day = sorted(
        LIVE_ROOT.iterdir()
    )[-1]

    report = []

    report.append("=" * 80)
    report.append("LIVE SESSION REPORT")
    report.append("=" * 80)
    report.append("")
    report.append(f"Folder : {latest_day}")
    report.append(
        f"Generated : {datetime.now()}"
    )
    report.append("")

    total_files = 0

    for segment_dir in sorted(latest_day.iterdir()):

        if not segment_dir.is_dir():
            continue

        report.append(
            "#" * 80
        )

        report.append(
            f"{segment_dir.name.upper()}"
        )

        report.append(
            "#" * 80
        )

        parquet_files = sorted(
            segment_dir.glob("*.parquet")
        )

        report.append(
            f"Files : {len(parquet_files)}"
        )

        report.append("")

        total_files += len(
            parquet_files
        )

        for file in parquet_files:

            info = summarize_file(
                file
            )

            report.append(
                "-" * 80
            )

            report.append(
                file.name
            )

            if "error" in info:

                report.append(
                    f"ERROR : {info['error']}"
                )

                report.append("")
                continue

            report.append(
                f"Rows                : {info['rows']}"
            )

            report.append(
                f"Columns             : {len(info['columns'])}"
            )

            report.append(
                f"Unique timestamps   : {info['unique_ts']}"
            )

            report.append(
                f"First timestamp     : {info['first']}"
            )

            report.append(
                f"Last timestamp      : {info['last']}"
            )

            report.append("")
            report.append(
                "Sample Row"
            )

            report.append(
                "-" * 20
            )

            report.append(
                info["sample"]
            )

            report.append("")

    report.append("=" * 80)
    report.append(
        f"Total files : {total_files}"
    )
    report.append("=" * 80)

    output_file = (
        latest_day
        / "live_session_report.txt"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(report)
        )

    print(
        f"\nReport written to:\n{output_file}"
    )


if __name__ == "__main__":
    main()