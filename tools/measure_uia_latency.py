import argparse
import csv
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SPREADSHEET_DIR = ROOT_DIR / "Spreadsheet"

if str(SPREADSHEET_DIR) not in sys.path:
    sys.path.insert(0, str(SPREADSHEET_DIR))

import visual_v3  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Measure the UIA-to-visicons refresh path implemented by "
            "Spreadsheet/visual_v3.py."
        )
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of repeated visual refreshes to measure.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between repeated refreshes.",
    )
    parser.add_argument(
        "--app-title",
        action="append",
        dest="app_titles",
        help=(
            "Exact Excel window title to pass to visual_v3.py. "
            "May be supplied multiple times. Defaults to visual_v3.DEFAULT_APP_TITLES."
        ),
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=visual_v3.VISICONS_OUTPUT_PATH,
        help="visicons JSON path written by each measured refresh.",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=SPREADSHEET_DIR / "uia_latency_runs",
        help="Directory for timing summary CSV/JSON.",
    )
    return parser.parse_args()


def resolve_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def main():
    args = parse_args()

    app_titles = args.app_titles or visual_v3.DEFAULT_APP_TITLES
    output_path = resolve_path(args.output_path)
    summary_dir = resolve_path(args.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    elapsed_values = []

    print("Measuring Spreadsheet/visual_v3.py UIA refresh path")
    print("App titles:")
    for title in app_titles:
        print(f"  {title}")
    print(f"Visicons output: {output_path}")
    print()

    for run in range(1, args.runs + 1):
        started = time.perf_counter()
        visicons, snapshot_path = visual_v3.extract_ui_elements(
            app_titles,
            output_path=output_path,
        )
        elapsed_seconds = time.perf_counter() - started
        elapsed_values.append(elapsed_seconds)

        row = {
            "run": run,
            "elapsed_seconds": round(elapsed_seconds, 6),
            "visicons_count": len(visicons),
            "output_path": str(output_path),
            "snapshot_path": str(snapshot_path),
        }
        rows.append(row)

        print(
            f"Run {run}: {elapsed_seconds:.3f}s "
            f"({len(visicons)} visicons, snapshot {snapshot_path})"
        )

        if run < args.runs:
            time.sleep(args.delay)

    mean_seconds = statistics.mean(elapsed_values)
    sample_sd_seconds = statistics.stdev(elapsed_values) if len(elapsed_values) > 1 else 0.0
    population_sd_seconds = statistics.pstdev(elapsed_values)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = summary_dir / f"uia_visual_v3_latency_{timestamp}.csv"
    json_path = summary_dir / f"uia_visual_v3_latency_{timestamp}.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run",
                "elapsed_seconds",
                "visicons_count",
                "output_path",
                "snapshot_path",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "measurement_path": "Spreadsheet/visual_v3.py extract_ui_elements",
        "app_titles": app_titles,
        "runs": args.runs,
        "delay_seconds": args.delay,
        "output_path": str(output_path),
        "elapsed_seconds": [round(value, 6) for value in elapsed_values],
        "mean_seconds": round(mean_seconds, 6),
        "sample_sd_seconds": round(sample_sd_seconds, 6),
        "population_sd_seconds": round(population_sd_seconds, 6),
        "rows": rows,
        "summary_csv": str(csv_path),
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print()
    print("Elapsed seconds: " + ", ".join(f"{value:.3f}" for value in elapsed_values))
    print(f"Mean: {mean_seconds:.3f}s")
    print(f"Sample SD: {sample_sd_seconds:.3f}s")
    print(f"Population SD: {population_sd_seconds:.3f}s")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")


if __name__ == "__main__":
    main()
