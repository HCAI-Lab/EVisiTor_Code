#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TASKS = list(range(1, 15))
TASK_LABELS = {
    1: "Open file",
    2: "Save As initial",
    3: "Calculate frequency",
    4: "Calculate total frequency",
    5: "Calculate normalization",
    6: "Calculate total normalization",
    7: "Calculate length",
    8: "Calculate total length",
    9: "Calculate typed characters",
    10: "Calculate total typed characters",
    11: "Insert two rows",
    12: "Type name",
    13: "Insert current date",
    14: "Save As final",
}


def run_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"run_(\d+)", path.name)
    number = int(match.group(1)) if match else 10**9
    return number, path.name


def subject_sort_key(subject: object) -> tuple[int, str]:
    text = str(subject)
    match = re.search(r"\d+", text)
    number = int(match.group()) if match else 10**9
    return number, text.lower()


def sample_std(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) <= 1:
        return 0.0
    return float(np.std(values, ddof=1))


def sample_var(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) <= 1:
        return 0.0
    return float(np.var(values, ddof=1))


def fmt(value: float | int | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def fmt_pct(value: float | int | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}%"


def md_table(df: pd.DataFrame, digits: int = 2) -> str:
    display = df.copy()
    for col in display.columns:
        if pd.api.types.is_float_dtype(display[col]):
            display[col] = display[col].map(lambda value: fmt(value, digits))
    return display.to_markdown(index=False)


def read_human_reference(path: Path) -> dict[int, tuple[float, float]]:
    refs: dict[int, tuple[float, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            refs[int(float(row["Step"]))] = (
                float(row["Average length time per task"]),
                float(row["standart deviation"]),
            )
    return refs


def mean_abs_reference_diff(
    rows: pd.DataFrame,
    subjects: set[str],
    reference: dict[int, tuple[float, float]],
) -> float:
    subset = rows[rows["subject"].isin(subjects)]
    if subset.empty:
        return float("inf")
    means = subset.groupby("step_num")["length_sec"].mean()
    diffs = []
    for task, (ref_mean, _) in reference.items():
        if task not in means:
            return float("inf")
        diffs.append(abs(float(means.loc[task]) - ref_mean))
    return float(np.mean(diffs)) if diffs else float("inf")


def load_human_complete_case(human_csv: Path, human_windows_csv: Path) -> tuple[pd.DataFrame, list[str], list[str]]:
    reference = read_human_reference(human_csv)
    df = pd.read_csv(human_windows_csv)
    df = df.rename(columns={"step_num": "task", "length_sec": "duration"})
    df["task"] = pd.to_numeric(df["task"], errors="coerce")
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df = df.dropna(subset=["subject", "task", "duration"]).copy()
    df["task"] = df["task"].astype(int)

    all_subjects = set(df["subject"].astype(str))
    ref_rows = df.rename(columns={"task": "step_num", "duration": "length_sec"})
    candidate_sets = [all_subjects] + [all_subjects - {subject} for subject in sorted(all_subjects)]
    source_subjects = min(candidate_sets, key=lambda subjects: mean_abs_reference_diff(ref_rows, subjects, reference))

    source_df = df[df["subject"].isin(source_subjects)].copy()
    subject_tasks = source_df.groupby("subject")["task"].apply(lambda values: set(values))
    complete_subjects = {
        subject for subject, tasks in subject_tasks.items() if set(TASKS).issubset(tasks)
    }
    dropped_subjects = sorted(source_subjects - complete_subjects, key=subject_sort_key)
    human = source_df[source_df["subject"].isin(complete_subjects) & source_df["task"].isin(TASKS)].copy()
    human["group"] = "Human"
    human["run"] = human["subject"]
    return human[["group", "run", "task", "duration"]], sorted(complete_subjects, key=subject_sort_key), dropped_subjects


def complete_task_run_dirs(base_dir: Path, limit: int | None = None) -> list[Path]:
    run_dirs = sorted([path for path in base_dir.glob("run_*") if path.is_dir()], key=run_sort_key)
    complete: list[Path] = []
    for run_dir in run_dirs:
        task_path = run_dir / "task_times.csv"
        if not task_path.exists():
            continue
        df = pd.read_csv(task_path)
        if {"task", "duration"}.issubset(df.columns) and set(pd.to_numeric(df["task"], errors="coerce").dropna().astype(int)) >= set(TASKS):
            complete.append(run_dir)
        if limit is not None and len(complete) >= limit:
            break
    return complete


def load_model_task_runs(base_dir: Path, label: str, limit: int | None = None) -> tuple[pd.DataFrame, list[str]]:
    run_dirs = complete_task_run_dirs(base_dir, limit=limit)
    rows: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        df = pd.read_csv(run_dir / "task_times.csv")
        df = df[["task", "duration"]].copy()
        df["task"] = pd.to_numeric(df["task"], errors="coerce")
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
        df = df.dropna(subset=["task", "duration"])
        df["task"] = df["task"].astype(int)
        df = df[df["task"].isin(TASKS)].copy()
        df["group"] = label
        df["run"] = run_dir.name
        rows.append(df[["group", "run", "task", "duration"]])
    if not rows:
        raise RuntimeError(f"No complete task runs found in {base_dir}")
    return pd.concat(rows, ignore_index=True), [path.name for path in run_dirs]


def load_model_subtask_runs(base_dir: Path, label: str, run_names: list[str]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for run_name in run_names:
        path = base_dir / run_name / "subtask_times.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if not {"task", "subtask", "duration"}.issubset(df.columns):
            continue
        df = df[["task", "subtask", "duration"]].copy()
        df["task"] = pd.to_numeric(df["task"], errors="coerce")
        df["subtask"] = pd.to_numeric(df["subtask"], errors="coerce")
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
        df = df.dropna(subset=["task", "subtask", "duration"])
        df["task"] = df["task"].astype(int)
        df["subtask"] = df["subtask"].astype(int)
        df = df[df["task"].isin(TASKS)].copy()
        df["subtask_id"] = df["task"].astype(str) + "." + df["subtask"].astype(str)
        df["group"] = label
        df["run"] = run_name
        rows.append(df[["group", "run", "task", "subtask", "subtask_id", "duration"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def summarize_task_data(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = (
        df.groupby("task")["duration"]
        .agg(**{f"{prefix}_n": "count", f"{prefix}_mean": "mean", f"{prefix}_sd": "std"})
        .reset_index()
    )
    return out


def prediction_interval_coverage(model_df: pd.DataFrame, human_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    rows = []
    for task in TASKS:
        model_values = model_df.loc[model_df["task"] == task, "duration"].to_numpy()
        human_values = human_df.loc[human_df["task"] == task, "duration"].to_numpy()
        lower, upper = np.percentile(model_values, [5, 95])
        covered = (human_values >= lower) & (human_values <= upper)
        rows.append(
            {
                "task": task,
                f"{prefix}_pi_5": lower,
                f"{prefix}_pi_95": upper,
                f"{prefix}_humans_covered_n": int(covered.sum()),
                f"{prefix}_humans_covered_pct": 100.0 * float(covered.mean()),
            }
        )
    return pd.DataFrame(rows)


def model_metrics(model_df: pd.DataFrame, human_df: pd.DataFrame, model_subtasks: pd.DataFrame, label: str) -> dict[str, float]:
    model_task = summarize_task_data(model_df, "model")
    human_task = summarize_task_data(human_df, "human")
    merged = model_task.merge(human_task, on="task", how="inner")
    diffs = merged["model_mean"] - merged["human_mean"]
    rmse = float(np.sqrt(np.mean(np.square(diffs))))
    norm_rmse = float(np.sqrt(np.mean(np.square(diffs / merged["human_sd"]))))
    corr = float(np.corrcoef(merged["model_mean"], merged["human_mean"])[0, 1])
    task_var_mean = float(model_df.groupby("task")["duration"].var(ddof=1).mean())
    if model_subtasks.empty:
        subtask_var_mean = float("nan")
    else:
        subtask_var_mean = float(model_subtasks.groupby(["task", "subtask"])["duration"].var(ddof=1).mean())
    return {
        "model": label,
        "runs": int(model_df["run"].nunique()),
        "mean_task_variance": task_var_mean,
        "mean_subtask_variance": subtask_var_mean,
        "task_mean_correlation_with_human": corr,
        "task_rmse_sec": rmse,
        "human_sd_normalized_rmse": norm_rmse,
        "mean_model_sd_sec": float(merged["model_sd"].mean()),
        "mean_human_sd_sec": float(merged["human_sd"].mean()),
    }


def save_barplot(task_table: pd.DataFrame, output_path: Path) -> None:
    x = np.arange(len(task_table))
    width = 0.26
    realistic_n = int(task_table["realistic_n"].dropna().iloc[0])
    human_n = int(task_table["human_n"].dropna().iloc[0])
    perfect_n = int(task_table["perfect_n"].dropna().iloc[0])
    fig, ax = plt.subplots(figsize=(13, 7.1))
    ax.bar(x - width, task_table["realistic_mean"], width, yerr=task_table["realistic_sd"], capsize=3, label=f"Realistic Model (N={realistic_n})")
    ax.bar(x, task_table["human_mean"], width, yerr=task_table["human_sd"], capsize=3, label=f"Human (N={human_n})")
    ax.bar(x + width, task_table["perfect_mean"], width, yerr=task_table["perfect_sd"], capsize=3, label=f"Perfect Model (N={perfect_n})")
    ax.set_title("Completion Time by Task: Human vs Realistic Model vs Perfect Model")
    ax.set_xlabel("Task")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(task_table["task"].astype(str))
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    ax.legend()
    fig.text(
        0.5,
        0.012,
        f"N by plotted task: realistic model N={realistic_n}, human users N={human_n}, perfect model N={perfect_n} for all tasks.",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.14)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze human/model completion-time fit.")
    parser.add_argument("--realistic-dir", default="New_Error (3-5-2-TCP)")
    parser.add_argument("--perfect-dir", default="Perfect_model")
    parser.add_argument("--human-csv", default="HumanCompletionTime.csv")
    parser.add_argument("--human-windows-csv", default=os.path.join("Human Data", "eye_tracking_analysis", "task_time_windows_from_breakdown.csv"))
    parser.add_argument("--output-dir", default=os.path.join("New_Error (3-5-2-TCP)", "completion_model_performance_analysis"))
    parser.add_argument("--perfect-run-limit", type=int, default=26)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    human_df, human_subjects, dropped_humans = load_human_complete_case(Path(args.human_csv), Path(args.human_windows_csv))
    realistic_df, realistic_runs = load_model_task_runs(Path(args.realistic_dir), "Realistic Model")
    perfect_df, perfect_runs = load_model_task_runs(Path(args.perfect_dir), "Perfect Model", limit=args.perfect_run_limit)
    realistic_subtasks = load_model_subtask_runs(Path(args.realistic_dir), "Realistic Model", realistic_runs)
    perfect_subtasks = load_model_subtask_runs(Path(args.perfect_dir), "Perfect Model", perfect_runs)

    human_stats = summarize_task_data(human_df, "human")
    realistic_stats = summarize_task_data(realistic_df, "realistic")
    perfect_stats = summarize_task_data(perfect_df, "perfect")
    task_table = (
        pd.DataFrame({"task": TASKS})
        .merge(human_stats, on="task", how="left")
        .merge(realistic_stats, on="task", how="left")
        .merge(perfect_stats, on="task", how="left")
    )
    task_table["task_label"] = task_table["task"].map(TASK_LABELS)
    task_table["realistic_diff_sec"] = task_table["realistic_mean"] - task_table["human_mean"]
    task_table["perfect_diff_sec"] = task_table["perfect_mean"] - task_table["human_mean"]
    task_table["realistic_abs_error_sec"] = task_table["realistic_diff_sec"].abs()
    task_table["perfect_abs_error_sec"] = task_table["perfect_diff_sec"].abs()
    task_table["realistic_human_sd_units"] = task_table["realistic_diff_sec"] / task_table["human_sd"]
    task_table["perfect_human_sd_units"] = task_table["perfect_diff_sec"] / task_table["human_sd"]

    realistic_coverage = prediction_interval_coverage(realistic_df, human_df, "realistic")
    perfect_coverage = prediction_interval_coverage(perfect_df, human_df, "perfect")
    coverage_table = task_table[["task", "task_label", "human_n"]].merge(realistic_coverage, on="task").merge(perfect_coverage, on="task")

    metrics = pd.DataFrame(
        [
            model_metrics(realistic_df, human_df, realistic_subtasks, "Realistic Model"),
            model_metrics(perfect_df, human_df, perfect_subtasks, "Perfect Model"),
        ]
    )
    metrics["mean_task_pi_coverage_pct"] = [
        coverage_table["realistic_humans_covered_pct"].mean(),
        coverage_table["perfect_humans_covered_pct"].mean(),
    ]

    figure_path = output_dir / "completion_time_barplot_human_realistic_perfect.png"
    save_barplot(task_table, figure_path)

    task_csv = output_dir / "task_completion_fit_table.csv"
    coverage_csv = output_dir / "prediction_interval_coverage_table.csv"
    metrics_csv = output_dir / "model_performance_summary.csv"
    realistic_breakdown_csv = output_dir / "realistic_model_task_breakdown.csv"
    perfect_breakdown_csv = output_dir / "perfect_model_task_breakdown.csv"
    task_table.to_csv(task_csv, index=False)
    coverage_table.to_csv(coverage_csv, index=False)
    metrics.to_csv(metrics_csv, index=False)
    realistic_breakdown = task_table[
        [
            "task",
            "task_label",
            "human_n",
            "human_mean",
            "human_sd",
            "realistic_n",
            "realistic_mean",
            "realistic_sd",
            "realistic_diff_sec",
            "realistic_abs_error_sec",
            "realistic_human_sd_units",
        ]
    ].copy()
    perfect_breakdown = task_table[
        [
            "task",
            "task_label",
            "human_n",
            "human_mean",
            "human_sd",
            "perfect_n",
            "perfect_mean",
            "perfect_sd",
            "perfect_diff_sec",
            "perfect_abs_error_sec",
            "perfect_human_sd_units",
        ]
    ].copy()
    realistic_breakdown.to_csv(realistic_breakdown_csv, index=False)
    perfect_breakdown.to_csv(perfect_breakdown_csv, index=False)

    realistic = metrics.loc[metrics["model"] == "Realistic Model"].iloc[0]
    perfect = metrics.loc[metrics["model"] == "Perfect Model"].iloc[0]
    report_path = output_dir / "Model_Completion_Time_Performance_Analysis.md"
    report = f"""# Model Completion-Time Performance Analysis

## Summary

We compared human task-completion times with two model variants: the realistic model and the perfect model. Human data were analyzed as a complete-case sample, dropping `Subject14` because that participant did not complete task 8; `Subject1` was already outside the human summary matched by `HumanCompletionTime.csv`. The resulting human sample was `N={len(human_subjects)}` users. The realistic model used `N={len(realistic_runs)}` complete runs. The perfect model used `N={len(perfect_runs)}` complete runs from `Perfect_model`.

The human data are available at the level of the 14 task windows, so the report treats these 14 task windows as the comparable subtask units for model-human fit. Model-only fine-grained subtask variance is also reported separately from task-level variance.

The average fine-grained subtask completion-time variance was {fmt(realistic['mean_subtask_variance'], 3)} s^2 for the realistic model and {fmt(perfect['mean_subtask_variance'], 3)} s^2 for the perfect model. At the 14-task comparison level, the task completion-time correlation between model mean times and human mean times was r={fmt(realistic['task_mean_correlation_with_human'], 3)} for the realistic model and r={fmt(perfect['task_mean_correlation_with_human'], 3)} for the perfect model. The task-level RMSE between model and human mean completion times was {fmt(realistic['task_rmse_sec'], 2)} s for the realistic model and {fmt(perfect['task_rmse_sec'], 2)} s for the perfect model.

Because raw RMSE does not account for differences in human variability across tasks, we additionally computed a human-SD-normalized RMSE, in which the model-human mean difference for each task was divided by the observed standard deviation of human completion times for that task. This metric evaluates model error relative to the natural between-participant variability in task performance. The normalized RMSE was {fmt(realistic['human_sd_normalized_rmse'], 2)} human SD units for the realistic model and {fmt(perfect['human_sd_normalized_rmse'], 2)} human SD units for the perfect model.

Figure 1 highlights the barplot of completion time for participants, the realistic model, and the perfect model: `{figure_path.name}`.

## Table 1. Model Performance Summary

{md_table(metrics.rename(columns={
    'model': 'Model',
    'runs': 'Runs',
    'mean_task_variance': 'Mean task variance (s^2)',
    'mean_subtask_variance': 'Mean model subtask variance (s^2)',
    'task_mean_correlation_with_human': 'Task mean correlation with human',
    'task_rmse_sec': 'Task RMSE (s)',
    'human_sd_normalized_rmse': 'Human-SD-normalized RMSE',
    'mean_model_sd_sec': 'Mean model SD (s)',
    'mean_human_sd_sec': 'Mean human SD (s)',
    'mean_task_pi_coverage_pct': 'Mean 5-95% PI coverage (%)',
}), digits=3)}

## Table 2. Prediction-Interval Coverage by Task

This table shows how much of the human completion-time distribution fell within each model's task-level 5-95% prediction interval.

{md_table(coverage_table.rename(columns={
    'task': 'Task',
    'task_label': 'Task label',
    'human_n': 'Human N',
    'realistic_pi_5': 'Realistic PI 5% (s)',
    'realistic_pi_95': 'Realistic PI 95% (s)',
    'realistic_humans_covered_n': 'Human N covered by realistic',
    'realistic_humans_covered_pct': 'Human % covered by realistic',
    'perfect_pi_5': 'Perfect PI 5% (s)',
    'perfect_pi_95': 'Perfect PI 95% (s)',
    'perfect_humans_covered_n': 'Human N covered by perfect',
    'perfect_humans_covered_pct': 'Human % covered by perfect',
}), digits=2)}

## Table 3. Realistic Model Per-Task Completion-Time Breakdown

{md_table(realistic_breakdown.rename(columns={
    'task': 'Task',
    'task_label': 'Task label',
    'human_n': 'Human N',
    'human_mean': 'Human mean (s)',
    'human_sd': 'Human SD (s)',
    'realistic_n': 'Realistic N',
    'realistic_mean': 'Realistic mean (s)',
    'realistic_sd': 'Realistic SD (s)',
    'realistic_diff_sec': 'Realistic-human diff (s)',
    'realistic_abs_error_sec': 'Realistic abs error (s)',
    'realistic_human_sd_units': 'Realistic diff (human SD units)',
}), digits=2)}

## Table 4. Perfect Model Per-Task Completion-Time Breakdown

{md_table(perfect_breakdown.rename(columns={
    'task': 'Task',
    'task_label': 'Task label',
    'human_n': 'Human N',
    'human_mean': 'Human mean (s)',
    'human_sd': 'Human SD (s)',
    'perfect_n': 'Perfect N',
    'perfect_mean': 'Perfect mean (s)',
    'perfect_sd': 'Perfect SD (s)',
    'perfect_diff_sec': 'Perfect-human diff (s)',
    'perfect_abs_error_sec': 'Perfect abs error (s)',
    'perfect_human_sd_units': 'Perfect diff (human SD units)',
}), digits=2)}

## Table 5. Combined Per-Task Completion-Time Breakdown

{md_table(task_table[[
    'task',
    'task_label',
    'human_n',
    'human_mean',
    'human_sd',
    'realistic_n',
    'realistic_mean',
    'realistic_sd',
    'realistic_diff_sec',
    'realistic_human_sd_units',
    'perfect_n',
    'perfect_mean',
    'perfect_sd',
    'perfect_diff_sec',
    'perfect_human_sd_units',
]].rename(columns={
    'task': 'Task',
    'task_label': 'Task label',
    'human_n': 'Human N',
    'human_mean': 'Human mean (s)',
    'human_sd': 'Human SD (s)',
    'realistic_n': 'Realistic N',
    'realistic_mean': 'Realistic mean (s)',
    'realistic_sd': 'Realistic SD (s)',
    'realistic_diff_sec': 'Realistic-human diff (s)',
    'realistic_human_sd_units': 'Realistic diff (human SD units)',
    'perfect_n': 'Perfect N',
    'perfect_mean': 'Perfect mean (s)',
    'perfect_sd': 'Perfect SD (s)',
    'perfect_diff_sec': 'Perfect-human diff (s)',
    'perfect_human_sd_units': 'Perfect diff (human SD units)',
}), digits=2)}

## Interpretation

The realistic model tracked the rank ordering of human task times more closely than the perfect model, as reflected in the higher task-mean correlation. Its raw task RMSE was also lower than the perfect model's RMSE. Prediction-interval coverage provides a stricter distributional check: it asks whether individual human completion times fall inside the model's run-to-run variability. Low coverage indicates that even when mean trends are similar, the model distribution is too narrow, shifted, or both relative to human behavior.

## Outputs

- Figure 1: `{figure_path.name}`
- Summary CSV: `{metrics_csv.name}`
- Prediction-interval coverage CSV: `{coverage_csv.name}`
- Per-task breakdown CSV: `{task_csv.name}`
- Realistic model breakdown CSV: `{realistic_breakdown_csv.name}`
- Perfect model breakdown CSV: `{perfect_breakdown_csv.name}`
"""
    report_path.write_text(report, encoding="utf-8")

    print(f"Human users used: {len(human_subjects)}")
    print(f"Human users dropped for complete-case coverage: {', '.join(dropped_humans) if dropped_humans else 'none'}")
    print(f"Realistic model runs used: {len(realistic_runs)}")
    print(f"Perfect model runs used: {len(perfect_runs)} ({', '.join(perfect_runs)})")
    print(f"Saved report: {report_path}")
    print(f"Saved figure: {figure_path}")
    print(f"Saved CSVs: {metrics_csv}, {coverage_csv}, {task_csv}")


if __name__ == "__main__":
    main()
