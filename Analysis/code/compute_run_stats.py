#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class TaskWindow:
    task: int
    start_time: float
    end_time: float
    duration: float


def parse_float(value: str) -> float:
    return float(value.strip())


def sample_std(values: Sequence[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(variance)


def read_task_windows(task_times_path: str) -> List[TaskWindow]:
    windows: List[TaskWindow] = []
    with open(task_times_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"task", "start_time", "end_time", "duration"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {task_times_path}: {sorted(missing)}")

        for row in reader:
            try:
                windows.append(
                    TaskWindow(
                        task=int(float(row["task"])),
                        start_time=parse_float(row["start_time"]),
                        end_time=parse_float(row["end_time"]),
                        duration=parse_float(row["duration"]),
                    )
                )
            except (TypeError, ValueError):
                continue

    return windows


def read_keypress_times(keypresses_path: str) -> List[float]:
    times: List[float] = []
    with open(keypresses_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "model_time" not in (reader.fieldnames or []):
            raise ValueError(f"Missing model_time column in {keypresses_path}")

        for row in reader:
            try:
                times.append(parse_float(row["model_time"]))
            except (TypeError, ValueError):
                continue

    return times


def iter_run_dirs(base_dir: str) -> Iterable[str]:
    run_dirs = [
        os.path.join(base_dir, name)
        for name in os.listdir(base_dir)
        if name.startswith("run_") and os.path.isdir(os.path.join(base_dir, name))
    ]
    return sorted(run_dirs)


def summarize(values: Sequence[float]) -> Tuple[int, float, float]:
    n = len(values)
    if n == 0:
        return 0, float("nan"), float("nan")
    mean = sum(values) / n
    std = sample_std(values)
    return n, mean, std


def read_human_completion_times(human_csv_path: str) -> Dict[int, Tuple[float, float]]:
    """Return mapping task -> (human_mean, human_std)."""
    task_to_stats: Dict[int, Tuple[float, float]] = {}
    with open(human_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Step", "Average length time per task", "standart deviation"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {human_csv_path}: {sorted(missing)}")

        for row in reader:
            try:
                task = int(float(row["Step"]))
                human_mean = parse_float(row["Average length time per task"])
                human_std = parse_float(row["standart deviation"])
            except (TypeError, ValueError):
                continue
            task_to_stats[task] = (human_mean, human_std)

    return task_to_stats


def read_reference_completion_times(path: str) -> Dict[int, Tuple[float, float]]:
    """Read task summary stats from CSV or XLSX with common column names.

    Expected columns: Step, Average length time per task, standart deviation.
    """
    lower_path = path.lower()
    if lower_path.endswith(".csv"):
        return read_human_completion_times(path)

    if not (lower_path.endswith(".xlsx") or lower_path.endswith(".xls")):
        raise ValueError(f"Unsupported reference file format: {path}")

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas and openpyxl are required to read Excel references. "
            "Install with: pip install pandas openpyxl"
        ) from exc

    df = pd.read_excel(path)
    required = {"Step", "Average length time per task", "standart deviation"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    result: Dict[int, Tuple[float, float]] = {}
    for _, row in df.iterrows():
        try:
            task = int(float(row["Step"]))
            mean = float(row["Average length time per task"])
            std = float(row["standart deviation"])
        except (TypeError, ValueError):
            continue
        result[task] = (mean, std)

    return result


def compute_task_stats_from_run_dir(base_dir: str) -> Tuple[Dict[int, Tuple[float, float]], int, List[str]]:
    """Compute task mean/std from task_times.csv files in run_### directories."""
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Run directory not found: {base_dir}")

    durations_by_task: Dict[int, List[float]] = defaultdict(list)
    used_runs = 0
    skipped_runs: List[str] = []

    for run_dir in iter_run_dirs(base_dir):
        task_times_path = os.path.join(run_dir, "task_times.csv")
        if not os.path.exists(task_times_path):
            skipped_runs.append(os.path.basename(run_dir))
            continue

        try:
            task_windows = read_task_windows(task_times_path)
        except ValueError:
            skipped_runs.append(os.path.basename(run_dir))
            continue

        used_runs += 1
        for tw in task_windows:
            durations_by_task[tw.task].append(tw.duration)

    stats: Dict[int, Tuple[float, float]] = {}
    for task in sorted(durations_by_task):
        _, mean, std = summarize(durations_by_task[task])
        stats[task] = (mean, std)

    return stats, used_runs, skipped_runs


def save_grouped_completion_bar_plot(
    tasks: Sequence[int],
    new_means: Sequence[float],
    new_stds: Sequence[float],
    human_means: Sequence[float],
    human_stds: Sequence[float],
    third_means: Sequence[float],
    third_stds: Sequence[float],
    third_label: str,
    output_path: str,
    new_label: str = "Realistic Model",
    human_label: str = "Human baseline",
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for --save-plot. Install it with: pip install matplotlib"
        ) from exc

    x = list(range(len(tasks)))
    width = 0.26
    bar_styles = [
        {"color": "#f2f2f2", "edgecolor": "black", "hatch": "", "linewidth": 0.8},
        {"color": "#bdbdbd", "edgecolor": "black", "hatch": "///", "linewidth": 0.8},
        {"color": "#737373", "edgecolor": "black", "hatch": "xx", "linewidth": 0.8},
    ]
    error_kw = {"elinewidth": 1.0, "ecolor": "black", "capthick": 1.0}

    plt.figure(figsize=(13, 6.8))
    plt.bar(
        [i - width for i in x],
        new_means,
        width=width,
        yerr=new_stds,
        capsize=3,
        label=new_label,
        error_kw=error_kw,
        **bar_styles[0],
    )
    plt.bar(
        x,
        human_means,
        width=width,
        yerr=human_stds,
        capsize=3,
        label=human_label,
        error_kw=error_kw,
        **bar_styles[1],
    )
    plt.bar(
        [i + width for i in x],
        third_means,
        width=width,
        yerr=third_stds,
        capsize=3,
        label=third_label,
        error_kw=error_kw,
        **bar_styles[2],
    )

    plt.title(f"Completion Time by Subtask: {new_label} vs {human_label} vs {third_label}")
    plt.xlabel("Subtask")
    plt.ylabel("Time (seconds)")
    plt.xticks(x, [str(t) for t in tasks])
    plt.grid(axis="y", alpha=0.25, linestyle="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def save_overall_completion_bar_plot(
    new_mean: float,
    new_std: float,
    human_mean: float,
    human_std: float,
    third_mean: float,
    third_std: float,
    third_label: str,
    output_path: str,
    new_label: str = "Realistic Model",
    human_label: str = "Human baseline",
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for --save-plot. Install it with: pip install matplotlib"
        ) from exc

    labels = [new_label, human_label, third_label]
    means = [new_mean, human_mean, third_mean]
    stds = [new_std, human_std, third_std]
    x = list(range(len(labels)))
    colors = ["#f2f2f2", "#bdbdbd", "#737373"]
    hatches = ["", "///", "xx"]
    error_kw = {"elinewidth": 1.0, "ecolor": "black", "capthick": 1.0}

    plt.figure(figsize=(7.6, 5.8))
    bars = plt.bar(
        x,
        means,
        yerr=stds,
        capsize=5,
        color=colors,
        edgecolor="black",
        linewidth=0.8,
        error_kw=error_kw,
    )
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    plt.xticks(x, labels, rotation=12)
    plt.ylabel("Total completion time (seconds)")
    plt.title("Overall Completion Time Across 14 Tasks")
    plt.grid(axis="y", alpha=0.25, linestyle="--")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def save_statistical_summary_png(
    rows: Sequence[Tuple[str, str]],
    output_path: str,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for --save-plot. Install it with: pip install matplotlib"
        ) from exc

    fig, ax = plt.subplots(figsize=(10.5, 0.46 * (len(rows) + 2)))
    ax.axis("off")
    table = ax.table(cellText=[[k, v] for k, v in rows], colLabels=["Metric", "Value"], loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    plt.title("Completion-Time Statistical Summary", pad=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute mean and standard deviation of task durations and keypress counts across runs."
    )
    parser.add_argument(
        "--base-dir",
        default=os.path.join(os.getcwd(), "New_Error (3-5-2-TCP)"),
        help="Folder containing run_### directories (default: ./New_Error (3-5-2-TCP)).",
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        help="Write output CSV files into --output-dir.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.getcwd(), "New_Error (3-5-2-TCP)"),
        help="Output folder for CSV summaries when --save-csv is used.",
    )
    parser.add_argument(
        "--human-csv",
        default=None,
        help=(
            "Optional path to HumanCompletionTime.csv for model-vs-human task-time comparison. "
            "Expected columns: Step, Average length time per task, standart deviation."
        ),
    )
    parser.add_argument(
        "--perfect-model-dir",
        default=None,
        help=(
            "Optional folder containing Perfect_model run_### directories; if set, this is used as the "
            "third dataset in the three-way completion-time analysis."
        ),
    )
    parser.add_argument(
        "--og-model-xlsx",
        default=None,
        help=(
            "Optional path to OGModelCompletionTime.xlsx (or CSV with matching columns) for "
            "three-way completion-time analysis."
        ),
    )
    parser.add_argument(
        "--save-plot",
        action="store_true",
        help="Save a PNG error-bar plot for model-vs-human task-time comparison (requires --human-csv).",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.base_dir):
        raise FileNotFoundError(f"Base directory not found: {args.base_dir}")

    durations_by_task: Dict[int, List[float]] = defaultdict(list)
    keypress_count_per_run: List[float] = []
    keypress_count_by_task: Dict[int, List[float]] = defaultdict(list)
    used_runs = 0
    skipped_runs: List[str] = []

    for run_dir in iter_run_dirs(args.base_dir):
        task_times_path = os.path.join(run_dir, "task_times.csv")
        keypresses_path = os.path.join(run_dir, "keypresses.csv")

        if not (os.path.exists(task_times_path) and os.path.exists(keypresses_path)):
            skipped_runs.append(os.path.basename(run_dir))
            continue

        try:
            task_windows = read_task_windows(task_times_path)
            keypress_times = read_keypress_times(keypresses_path)
        except ValueError:
            skipped_runs.append(os.path.basename(run_dir))
            continue

        used_runs += 1
        keypress_count_per_run.append(float(len(keypress_times)))

        for tw in task_windows:
            durations_by_task[tw.task].append(tw.duration)
            count = sum(1 for t in keypress_times if tw.start_time <= t <= tw.end_time)
            keypress_count_by_task[tw.task].append(float(count))

    print(f"Runs included: {used_runs}")
    if skipped_runs:
        print(f"Runs skipped ({len(skipped_runs)}): {', '.join(skipped_runs)}")

    print("\nTask duration stats (seconds) by task")
    print("task,count,mean,std")
    task_duration_rows: List[Tuple[int, int, float, float]] = []
    for task in sorted(durations_by_task):
        n, mean, std = summarize(durations_by_task[task])
        task_duration_rows.append((task, n, mean, std))
        print(f"{task},{n},{mean:.6f},{std:.6f}")

    overall_n, overall_mean, overall_std = summarize(keypress_count_per_run)
    print("\nOverall keypress count per run")
    print("count,mean,std")
    print(f"{overall_n},{overall_mean:.6f},{overall_std:.6f}")

    print("\nKeypress count stats by task (keypresses per task per run)")
    print("task,count,mean,std")
    task_keypress_rows: List[Tuple[int, int, float, float]] = []
    for task in sorted(keypress_count_by_task):
        n, mean, std = summarize(keypress_count_by_task[task])
        task_keypress_rows.append((task, n, mean, std))
        print(f"{task},{n},{mean:.6f},{std:.6f}")

    if args.save_csv:
        os.makedirs(args.output_dir, exist_ok=True)

        task_duration_csv = os.path.join(args.output_dir, "task_duration_stats.csv")
        with open(task_duration_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["task", "count", "mean_duration", "std_duration"])
            writer.writerows(task_duration_rows)

        overall_keypress_csv = os.path.join(args.output_dir, "overall_keypress_stats.csv")
        with open(overall_keypress_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["count", "mean_keypresses_per_run", "std_keypresses_per_run"])
            writer.writerow([overall_n, overall_mean, overall_std])

        task_keypress_csv = os.path.join(args.output_dir, "task_keypress_stats.csv")
        with open(task_keypress_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["task", "count", "mean_keypresses", "std_keypresses"])
            writer.writerows(task_keypress_rows)

        print("\nSaved CSV files:")
        print(task_duration_csv)
        print(overall_keypress_csv)
        print(task_keypress_csv)

    if args.human_csv:
        if not os.path.exists(args.human_csv):
            raise FileNotFoundError(f"Human CSV not found: {args.human_csv}")

        human_stats = read_reference_completion_times(args.human_csv)
        comparison_rows: List[Tuple[int, int, float, float, float, float, float, float]] = []

        print("\nHuman vs model task completion time comparison")
        print(
            "task,count,model_mean,human_mean,mean_diff_sec,mean_diff_pct,"
            "model_std,human_std,std_diff_sec"
        )

        for task, n, model_mean, model_std in task_duration_rows:
            if task not in human_stats:
                continue
            human_mean, human_std = human_stats[task]
            mean_diff = model_mean - human_mean
            mean_diff_pct = (100.0 * mean_diff / human_mean) if human_mean != 0 else float("nan")
            std_diff = model_std - human_std
            comparison_rows.append(
                (
                    task,
                    n,
                    model_mean,
                    human_mean,
                    mean_diff,
                    mean_diff_pct,
                    model_std,
                    human_std,
                    std_diff,
                )
            )
            print(
                f"{task},{n},{model_mean:.6f},{human_mean:.6f},{mean_diff:+.6f},"
                f"{mean_diff_pct:+.2f},{model_std:.6f},{human_std:.6f},{std_diff:+.6f}"
            )

        if comparison_rows:
            model_total_mean = sum(r[2] for r in comparison_rows)
            human_total_mean = sum(r[3] for r in comparison_rows)
            total_diff = model_total_mean - human_total_mean
            total_diff_pct = (100.0 * total_diff / human_total_mean) if human_total_mean != 0 else float("nan")

            # Rough total SD estimate by root-sum-of-squares (assumes independence across tasks).
            model_total_std_approx = math.sqrt(sum((r[6] ** 2) for r in comparison_rows))
            human_total_std_approx = math.sqrt(sum((r[7] ** 2) for r in comparison_rows))

            print("\nOverall completion time comparison (sum across compared tasks)")
            print(f"model_total_mean_sec,{model_total_mean:.6f}")
            print(f"human_total_mean_sec,{human_total_mean:.6f}")
            print(f"mean_diff_sec,{total_diff:+.6f}")
            print(f"mean_diff_pct,{total_diff_pct:+.2f}")
            print(f"model_total_std_approx_sec,{model_total_std_approx:.6f}")
            print(f"human_total_std_approx_sec,{human_total_std_approx:.6f}")

            if args.save_csv:
                human_compare_csv = os.path.join(args.output_dir, "human_vs_model_task_time_comparison.csv")
                with open(human_compare_csv, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "task",
                            "count",
                            "model_mean_duration",
                            "human_mean_duration",
                            "mean_diff_sec",
                            "mean_diff_pct",
                            "model_std_duration",
                            "human_std_duration",
                            "std_diff_sec",
                        ]
                    )
                    writer.writerows(comparison_rows)

                print("\nSaved comparison CSV:")
                print(human_compare_csv)

        comparison_stats: Dict[int, Tuple[float, float]] | None = None
        comparison_label = ""
        comparison_key = ""

        if args.perfect_model_dir:
            comparison_stats, perfect_runs, perfect_skips = compute_task_stats_from_run_dir(args.perfect_model_dir)
            comparison_label = "Perfect Model"
            comparison_key = "perfect_model"
            print(f"\n{comparison_label} runs included: {perfect_runs}")
            if perfect_skips:
                print(f"{comparison_label} runs skipped ({len(perfect_skips)}): {', '.join(perfect_skips)}")
        elif args.og_model_xlsx:
            if not os.path.exists(args.og_model_xlsx):
                raise FileNotFoundError(f"OG model file not found: {args.og_model_xlsx}")
            comparison_stats = read_reference_completion_times(args.og_model_xlsx)
            comparison_label = "OG Model"
            comparison_key = "og_model"

        if comparison_stats:
            three_way_rows: List[
                Tuple[int, int, float, float, float, float, float, float, float, float, float]
            ] = []

            print(f"\nThree-way completion time comparison (New Error vs Human vs {comparison_label})")
            print(
                "task,count,new_mean,human_mean,comparison_mean,new_std,human_std,comparison_std,"
                "new_minus_human_sec,new_minus_comparison_sec,comparison_minus_human_sec"
            )

            for task, n, model_mean, model_std in task_duration_rows:
                if task not in human_stats or task not in comparison_stats:
                    continue
                human_mean, human_std = human_stats[task]
                comparison_mean, comparison_std = comparison_stats[task]
                new_minus_human = model_mean - human_mean
                new_minus_comparison = model_mean - comparison_mean
                comparison_minus_human = comparison_mean - human_mean

                row = (
                    task,
                    n,
                    model_mean,
                    human_mean,
                    comparison_mean,
                    model_std,
                    human_std,
                    comparison_std,
                    new_minus_human,
                    new_minus_comparison,
                    comparison_minus_human,
                )
                three_way_rows.append(row)
                print(
                    f"{task},{n},{model_mean:.6f},{human_mean:.6f},{comparison_mean:.6f},"
                    f"{model_std:.6f},{human_std:.6f},{comparison_std:.6f},"
                    f"{new_minus_human:+.6f},{new_minus_comparison:+.6f},{comparison_minus_human:+.6f}"
                )

            if three_way_rows:
                new_total_mean = sum(r[2] for r in three_way_rows)
                human_total_mean = sum(r[3] for r in three_way_rows)
                comparison_total_mean = sum(r[4] for r in three_way_rows)

                new_total_std = math.sqrt(sum((r[5] ** 2) for r in three_way_rows))
                human_total_std = math.sqrt(sum((r[6] ** 2) for r in three_way_rows))
                comparison_total_std = math.sqrt(sum((r[7] ** 2) for r in three_way_rows))

                print("\nOverall three-way completion time comparison (sum across compared tasks)")
                print(f"new_total_mean_sec,{new_total_mean:.6f}")
                print(f"human_total_mean_sec,{human_total_mean:.6f}")
                print(f"{comparison_key}_total_mean_sec,{comparison_total_mean:.6f}")
                print(f"new_minus_human_sec,{new_total_mean - human_total_mean:+.6f}")
                print(f"new_minus_{comparison_key}_sec,{new_total_mean - comparison_total_mean:+.6f}")
                print(f"{comparison_key}_minus_human_sec,{comparison_total_mean - human_total_mean:+.6f}")
                print(f"new_total_std_approx_sec,{new_total_std:.6f}")
                print(f"human_total_std_approx_sec,{human_total_std:.6f}")
                print(f"{comparison_key}_total_std_approx_sec,{comparison_total_std:.6f}")

                if args.save_csv:
                    three_way_csv = os.path.join(args.output_dir, f"completion_time_three_way_stats_{comparison_key}.csv")
                    with open(three_way_csv, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            [
                                "task",
                                "count",
                                "new_error_mean_duration",
                                "human_mean_duration",
                                f"{comparison_key}_mean_duration",
                                "new_error_std_duration",
                                "human_std_duration",
                                f"{comparison_key}_std_duration",
                                "new_minus_human_sec",
                                f"new_minus_{comparison_key}_sec",
                                f"{comparison_key}_minus_human_sec",
                            ]
                        )
                        writer.writerows(three_way_rows)

                    overall_csv = os.path.join(args.output_dir, f"completion_time_overall_stats_{comparison_key}.csv")
                    with open(overall_csv, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["metric", "value"])
                        writer.writerow(["new_total_mean_sec", new_total_mean])
                        writer.writerow(["human_total_mean_sec", human_total_mean])
                        writer.writerow([f"{comparison_key}_total_mean_sec", comparison_total_mean])
                        writer.writerow(["new_minus_human_sec", new_total_mean - human_total_mean])
                        writer.writerow([f"new_minus_{comparison_key}_sec", new_total_mean - comparison_total_mean])
                        writer.writerow([f"{comparison_key}_minus_human_sec", comparison_total_mean - human_total_mean])
                        writer.writerow(["new_total_std_approx_sec", new_total_std])
                        writer.writerow(["human_total_std_approx_sec", human_total_std])
                        writer.writerow([f"{comparison_key}_total_std_approx_sec", comparison_total_std])

                    print("\nSaved three-way statistical CSV files:")
                    print(three_way_csv)
                    print(overall_csv)

                if args.save_plot:
                    os.makedirs(args.output_dir, exist_ok=True)

                    tasks = [int(r[0]) for r in three_way_rows]
                    new_means = [float(r[2]) for r in three_way_rows]
                    human_means = [float(r[3]) for r in three_way_rows]
                    comparison_means = [float(r[4]) for r in three_way_rows]
                    new_stds = [float(r[5]) for r in three_way_rows]
                    human_stds = [float(r[6]) for r in three_way_rows]
                    comparison_stds = [float(r[7]) for r in three_way_rows]
                    new_plot_label = f"Realistic Model (N={used_runs})"
                    human_plot_label = "Human baseline (N=21)"
                    comparison_plot_label = comparison_label
                    if args.perfect_model_dir:
                        comparison_plot_label = f"{comparison_label} (N={perfect_runs})"

                    task_bar_plot = os.path.join(args.output_dir, f"completion_time_barplot_by_task_{comparison_key}.png")
                    save_grouped_completion_bar_plot(
                        tasks,
                        new_means,
                        new_stds,
                        human_means,
                        human_stds,
                        comparison_means,
                        comparison_stds,
                        comparison_plot_label,
                        task_bar_plot,
                        new_plot_label,
                        human_plot_label,
                    )

                    overall_bar_plot = os.path.join(args.output_dir, f"completion_time_barplot_overall_{comparison_key}.png")
                    save_overall_completion_bar_plot(
                        new_total_mean,
                        new_total_std,
                        human_total_mean,
                        human_total_std,
                        comparison_total_mean,
                        comparison_total_std,
                        comparison_plot_label,
                        overall_bar_plot,
                        new_plot_label,
                        human_plot_label,
                    )

                    summary_png = os.path.join(
                        args.output_dir,
                        f"completion_time_statistical_summary_{comparison_key}.png",
                    )
                    summary_rows = [
                        ("New Error total mean (sec)", f"{new_total_mean:.6f}"),
                        ("Human total mean (sec)", f"{human_total_mean:.6f}"),
                        (f"{comparison_label} total mean (sec)", f"{comparison_total_mean:.6f}"),
                        ("New - Human (sec)", f"{new_total_mean - human_total_mean:+.6f}"),
                        (f"New - {comparison_label} (sec)", f"{new_total_mean - comparison_total_mean:+.6f}"),
                        (f"{comparison_label} - Human (sec)", f"{comparison_total_mean - human_total_mean:+.6f}"),
                        ("New total SD approx (sec)", f"{new_total_std:.6f}"),
                        ("Human total SD approx (sec)", f"{human_total_std:.6f}"),
                        (f"{comparison_label} total SD approx (sec)", f"{comparison_total_std:.6f}"),
                    ]
                    save_statistical_summary_png(summary_rows, summary_png)

                    print("\nSaved three-way completion-time PNG files:")
                    print(task_bar_plot)
                    print(overall_bar_plot)
                    print(summary_png)

    elif args.save_plot:
        raise ValueError("--save-plot requires --human-csv")


if __name__ == "__main__":
    main()
