#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


X_THRESHOLD = 960
EXCLUDED_SUBJECTS = {"Subject1"}
DEFAULT_ABLATION_DIR = Path("ablation_25_formula_latest")
DEFAULT_OUTPUT_DIRNAME = "analysis_outputs"


def clean_model_label(name: str) -> str:
    return name.replace("Ablation_", "").replace("_", " ")


def parse_step_num(step_name: object) -> int | None:
    match = re.match(r"Step\s+(\d+)$", str(step_name).strip())
    return int(match.group(1)) if match else None


def sample_std(values: Iterable[float]) -> float:
    series = pd.Series(list(values), dtype="float64").dropna()
    if len(series) <= 1:
        return 0.0
    return float(series.std(ddof=1))


def load_human_completion_times(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"Step", "Average length time per task", "standart deviation"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing human completion columns in {path}: {sorted(missing)}")

    out = df.rename(
        columns={
            "Step": "task",
            "Average length time per task": "human_mean_duration",
            "standart deviation": "human_std_duration",
        }
    )[["task", "human_mean_duration", "human_std_duration"]].copy()
    out["task"] = pd.to_numeric(out["task"], errors="coerce").astype("Int64")
    out["human_mean_duration"] = pd.to_numeric(out["human_mean_duration"], errors="coerce")
    out["human_std_duration"] = pd.to_numeric(out["human_std_duration"], errors="coerce")
    return out.dropna(subset=["task", "human_mean_duration"]).astype({"task": int})


def load_human_fixation_steps(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(path)
    required = {
        "subject",
        "step_name",
        "fixations_x_lt_threshold",
        "fixations_x_gt_threshold",
        "fixations_x_eq_threshold",
        "total_fixations",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing human fixation columns in {path}: {sorted(missing)}")

    df = df[~df["subject"].isin(EXCLUDED_SUBJECTS)].copy()
    df = df[df["step_name"].astype(str).str.startswith("Step ")].copy()
    df["step_num"] = df["step_name"].map(parse_step_num)
    df = df[df["step_num"].notna()].copy()
    df["step_num"] = df["step_num"].astype(int)

    per_subject = (
        df.groupby(["subject", "step_num"], as_index=False)
        .agg(
            human_left=("fixations_x_lt_threshold", "sum"),
            human_right=("fixations_x_gt_threshold", "sum"),
            human_equal=("fixations_x_eq_threshold", "sum"),
            human_total=("total_fixations", "sum"),
        )
        .sort_values(["subject", "step_num"])
    )

    per_step = (
        per_subject.groupby("step_num", as_index=False)
        .agg(
            n_human_subjects=("subject", "nunique"),
            human_left_mean=("human_left", "mean"),
            human_right_mean=("human_right", "mean"),
            human_equal_mean=("human_equal", "mean"),
            human_total_mean=("human_total", "mean"),
            human_left_std=("human_left", lambda s: sample_std(s)),
            human_right_std=("human_right", lambda s: sample_std(s)),
            human_total_std=("human_total", lambda s: sample_std(s)),
            human_left_total=("human_left", "sum"),
            human_right_total=("human_right", "sum"),
            human_total_fixations=("human_total", "sum"),
        )
        .sort_values("step_num")
    )
    per_step["step_name"] = "Step " + per_step["step_num"].astype(str)
    per_step["human_left_prop"] = np.where(
        per_step["human_left_mean"] + per_step["human_right_mean"] > 0,
        per_step["human_left_mean"] / (per_step["human_left_mean"] + per_step["human_right_mean"]),
        np.nan,
    )
    return per_subject, per_step


def iter_model_dirs(ablation_dir: Path) -> list[Path]:
    model_dirs = [p for p in ablation_dir.iterdir() if p.is_dir() and p.name.startswith("Ablation_")]
    return sorted(model_dirs, key=lambda p: p.name.lower())


def iter_run_dirs(model_dir: Path) -> list[Path]:
    return sorted([p for p in model_dir.iterdir() if p.is_dir() and p.name.startswith("run_")])


def load_model_completion(model_dir: Path) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for run_dir in iter_run_dirs(model_dir):
        path = run_dir / "task_times.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        required = {"task", "duration"}
        if not required.issubset(df.columns):
            continue
        df = df[["task", "duration"]].copy()
        df["task"] = pd.to_numeric(df["task"], errors="coerce")
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
        df = df.dropna(subset=["task", "duration"])
        if df.empty:
            continue
        df["task"] = df["task"].astype(int)
        df["run"] = run_dir.name
        df["model"] = model_dir.name
        df["model_label"] = clean_model_label(model_dir.name)
        rows.append(df)

    if not rows:
        return pd.DataFrame(columns=["model", "model_label", "run", "task", "duration"])
    return pd.concat(rows, ignore_index=True)


def load_model_attention(model_dir: Path) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for run_dir in iter_run_dirs(model_dir):
        path = run_dir / "attention_shifts.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        required = {"model_time", "task", "screen_x", "screen_y"}
        if not required.issubset(df.columns):
            continue

        dedup_cols = ["model_time", "task", "subtask", "screen_x", "screen_y", "location_name"]
        dedup_cols = [col for col in dedup_cols if col in df.columns]
        df = df.drop_duplicates(subset=dedup_cols).copy()
        df["step_num"] = pd.to_numeric(df["task"], errors="coerce")
        df = df[df["step_num"].notna()].copy()
        df["step_num"] = df["step_num"].astype(int)
        df = df[df["step_num"].between(1, 14)]
        if df.empty:
            continue

        df["model_left"] = df["screen_x"] < X_THRESHOLD
        df["model_right"] = df["screen_x"] > X_THRESHOLD
        df["model_equal"] = df["screen_x"] == X_THRESHOLD
        grouped = (
            df.groupby("step_num", as_index=False)
            .agg(
                model_left=("model_left", "sum"),
                model_right=("model_right", "sum"),
                model_equal=("model_equal", "sum"),
                model_total_attention_shifts=("screen_x", "size"),
            )
            .sort_values("step_num")
        )
        grouped["run"] = run_dir.name
        grouped["model"] = model_dir.name
        grouped["model_label"] = clean_model_label(model_dir.name)
        rows.append(grouped)

    if not rows:
        return pd.DataFrame(
            columns=[
                "model",
                "model_label",
                "run",
                "step_num",
                "model_left",
                "model_right",
                "model_equal",
                "model_total_attention_shifts",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def build_completion_outputs(model_task_df: pd.DataFrame, human_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    task_stats = (
        model_task_df.groupby(["model", "model_label", "task"], as_index=False)
        .agg(
            run_count=("run", "nunique"),
            model_mean_duration=("duration", "mean"),
            model_std_duration=("duration", lambda s: sample_std(s)),
        )
        .sort_values(["model_label", "task"])
    )
    by_task = pd.merge(task_stats, human_df, on="task", how="inner")
    by_task["mean_diff_sec"] = by_task["model_mean_duration"] - by_task["human_mean_duration"]
    by_task["mean_diff_pct"] = 100.0 * by_task["mean_diff_sec"] / by_task["human_mean_duration"]
    by_task["abs_mean_diff_sec"] = by_task["mean_diff_sec"].abs()
    by_task["abs_mean_diff_pct"] = by_task["mean_diff_pct"].abs()

    overall_rows = []
    for (model, model_label), group in by_task.groupby(["model", "model_label"], sort=False):
        model_total_mean = float(group["model_mean_duration"].sum())
        human_total_mean = float(group["human_mean_duration"].sum())
        model_total_std = math.sqrt(float((group["model_std_duration"] ** 2).sum()))
        human_total_std = math.sqrt(float((group["human_std_duration"] ** 2).sum()))
        diff = model_total_mean - human_total_mean
        overall_rows.append(
            {
                "model": model,
                "model_label": model_label,
                "task_count": int(group["task"].nunique()),
                "run_count_min": int(group["run_count"].min()),
                "run_count_max": int(group["run_count"].max()),
                "model_total_mean_sec": model_total_mean,
                "model_total_std_approx_sec": model_total_std,
                "human_total_mean_sec": human_total_mean,
                "human_total_std_approx_sec": human_total_std,
                "model_minus_human_sec": diff,
                "model_minus_human_pct": 100.0 * diff / human_total_mean,
                "mean_abs_task_error_sec": float(group["abs_mean_diff_sec"].mean()),
                "mean_abs_task_pct_error": float(group["abs_mean_diff_pct"].mean()),
                "rmse_task_sec": math.sqrt(float((group["mean_diff_sec"] ** 2).mean())),
            }
        )

    overall = pd.DataFrame(overall_rows).sort_values("mean_abs_task_pct_error").reset_index(drop=True)
    return by_task, overall


def build_attention_outputs(model_step_df: pd.DataFrame, human_step_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    step_stats = (
        model_step_df.groupby(["model", "model_label", "step_num"], as_index=False)
        .agg(
            n_model_runs=("run", "nunique"),
            model_left_mean=("model_left", "mean"),
            model_right_mean=("model_right", "mean"),
            model_equal_mean=("model_equal", "mean"),
            model_total_mean=("model_total_attention_shifts", "mean"),
            model_left_std=("model_left", lambda s: sample_std(s)),
            model_right_std=("model_right", lambda s: sample_std(s)),
            model_total_std=("model_total_attention_shifts", lambda s: sample_std(s)),
        )
        .sort_values(["model_label", "step_num"])
    )
    step_stats["model_left_prop"] = np.where(
        step_stats["model_left_mean"] + step_stats["model_right_mean"] > 0,
        step_stats["model_left_mean"] / (step_stats["model_left_mean"] + step_stats["model_right_mean"]),
        np.nan,
    )
    by_step = pd.merge(step_stats, human_step_df, on="step_num", how="inner")
    by_step["step_name"] = "Step " + by_step["step_num"].astype(str)
    by_step["total_mean_diff_model_minus_human"] = by_step["model_total_mean"] - by_step["human_total_mean"]
    by_step["total_mean_diff_pct"] = 100.0 * by_step["total_mean_diff_model_minus_human"] / by_step["human_total_mean"]
    by_step["left_prop_diff"] = by_step["model_left_prop"] - by_step["human_left_prop"]
    by_step["left_prop_diff_pp"] = 100.0 * by_step["left_prop_diff"]

    overall_rows = []
    for (model, model_label), group in by_step.groupby(["model", "model_label"], sort=False):
        model_left_total = float(group["model_left_mean"].sum())
        model_right_total = float(group["model_right_mean"].sum())
        human_left_total = float(group["human_left_mean"].sum())
        human_right_total = float(group["human_right_mean"].sum())
        model_total = float(group["model_total_mean"].sum())
        human_total = float(group["human_total_mean"].sum())
        model_left_prop = model_left_total / (model_left_total + model_right_total)
        human_left_prop = human_left_total / (human_left_total + human_right_total)
        overall_rows.append(
            {
                "model": model,
                "model_label": model_label,
                "step_count": int(group["step_num"].nunique()),
                "run_count_min": int(group["n_model_runs"].min()),
                "run_count_max": int(group["n_model_runs"].max()),
                "human_subjects": int(group["n_human_subjects"].max()),
                "model_total_attention_mean_per_run": model_total,
                "human_total_fixations_mean_per_subject": human_total,
                "total_count_diff_model_minus_human": model_total - human_total,
                "total_count_diff_pct": 100.0 * (model_total - human_total) / human_total,
                "model_left_prop": model_left_prop,
                "human_left_prop": human_left_prop,
                "left_prop_diff_pp": 100.0 * (model_left_prop - human_left_prop),
                "step_total_rmse": math.sqrt(float((group["total_mean_diff_model_minus_human"] ** 2).mean())),
                "step_left_prop_mae_pp": float(group["left_prop_diff_pp"].abs().mean()),
            }
        )

    overall = pd.DataFrame(overall_rows).sort_values("step_left_prop_mae_pp").reset_index(drop=True)
    return by_step, overall


def set_common_style() -> None:
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linestyle": "--",
            "font.size": 10,
        }
    )


def plot_completion_overall(overall: pd.DataFrame, output_path: Path) -> None:
    ordered = overall.sort_values("model_total_mean_sec")
    labels = ["Human"] + ordered["model_label"].tolist()
    means = [float(ordered["human_total_mean_sec"].iloc[0])] + ordered["model_total_mean_sec"].tolist()
    stds = [float(ordered["human_total_std_approx_sec"].iloc[0])] + ordered["model_total_std_approx_sec"].tolist()
    colors = ["#30343b"] + ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2"][: len(ordered)]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=stds, capsize=4, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("Total completion time (seconds)")
    ax.set_title("Overall Completion Time: Human vs Ablation Models")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_completion_by_task(by_task: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.4))
    human = by_task[["task", "human_mean_duration", "human_std_duration"]].drop_duplicates().sort_values("task")
    ax.errorbar(
        human["task"],
        human["human_mean_duration"],
        yerr=human["human_std_duration"],
        color="#30343b",
        linewidth=2.3,
        capsize=3,
        label="Human",
    )
    palette = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2"]
    for color, (label, group) in zip(palette, by_task.groupby("model_label", sort=True)):
        group = group.sort_values("task")
        ax.plot(group["task"], group["model_mean_duration"], marker="o", linewidth=1.8, color=color, label=label)
    ax.set_xticks(sorted(human["task"].unique()))
    ax.set_xlabel("Task")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Task Completion Time: Human vs Ablation Models")
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_heatmap(df: pd.DataFrame, value_col: str, title: str, cbar_label: str, output_path: Path) -> None:
    pivot = df.pivot(index="model_label", columns="task", values=value_col).sort_index()
    pivot = pivot.apply(pd.to_numeric, errors="coerce")
    fig, ax = plt.subplots(figsize=(13.2, 4.8))
    values = pivot.to_numpy(dtype=float)
    vmax = float(np.nanmax(np.abs(values)))
    image = ax.imshow(values, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns])
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Task")
    ax.set_title(title)
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_attention_total(by_step: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.4))
    human = by_step[["step_num", "human_total_mean", "human_total_std"]].drop_duplicates().sort_values("step_num")
    ax.errorbar(
        human["step_num"],
        human["human_total_mean"],
        yerr=human["human_total_std"],
        color="#30343b",
        linewidth=2.3,
        capsize=3,
        label="Human fixations",
    )
    palette = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2"]
    for color, (label, group) in zip(palette, by_step.groupby("model_label", sort=True)):
        group = group.sort_values("step_num")
        ax.plot(group["step_num"], group["model_total_mean"], marker="o", linewidth=1.8, color=color, label=label)
    ax.set_xticks(sorted(human["step_num"].unique()))
    ax.set_xlabel("Step")
    ax.set_ylabel("Count per subject/run")
    ax.set_title("Attention/Fixation Counts by Step: Human vs Ablation Models")
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_attention_left_prop(by_step: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    human = by_step[["step_num", "human_left_prop"]].drop_duplicates().sort_values("step_num")
    ax.plot(
        human["step_num"],
        100.0 * human["human_left_prop"],
        color="#30343b",
        linewidth=2.4,
        marker="o",
        label="Human",
    )
    palette = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2"]
    for color, (label, group) in zip(palette, by_step.groupby("model_label", sort=True)):
        group = group.sort_values("step_num")
        ax.plot(group["step_num"], 100.0 * group["model_left_prop"], marker="o", linewidth=1.8, color=color, label=label)
    ax.set_xticks(sorted(human["step_num"].unique()))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Step")
    ax.set_ylabel("Left-side share (%)")
    ax.set_title("Left/Right Attention Pattern: Human vs Ablation Models")
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_attention_summary(overall: pd.DataFrame, output_path: Path) -> None:
    ordered = overall.sort_values("step_left_prop_mae_pp")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
    colors = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2"][: len(ordered)]

    axes[0].barh(ordered["model_label"], ordered["step_left_prop_mae_pp"], color=colors)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Mean absolute left-share error (percentage points)")
    axes[0].set_title("Side Pattern Error")

    count_order = overall.sort_values("step_total_rmse")
    axes[1].barh(count_order["model_label"], count_order["step_total_rmse"], color=colors)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("RMSE of counts per step")
    axes[1].set_title("Count Pattern Error")

    fig.suptitle("Attention/Fixation Fit Summary")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare ablation model outputs against human timing and fixation summaries.")
    parser.add_argument("--ablation-dir", default=str(DEFAULT_ABLATION_DIR), help="Directory containing Ablation_* folders.")
    parser.add_argument("--human-completion", default="HumanCompletionTime.csv", help="Human task completion summary CSV.")
    parser.add_argument(
        "--human-fixations",
        default=str(Path("Human Data") / "eye_tracking_analysis" / "fixation_side_counts_by_subject_by_step.csv"),
        help="Human fixation side counts by subject and step.",
    )
    parser.add_argument("--output-dir", default=None, help="Output directory. Default: <ablation-dir>/analysis_outputs.")
    args = parser.parse_args()

    analysis_dir = Path(__file__).resolve().parent
    ablation_dir = (analysis_dir / args.ablation_dir).resolve()
    human_completion_path = (analysis_dir / args.human_completion).resolve()
    human_fixation_path = (analysis_dir / args.human_fixations).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else ablation_dir / DEFAULT_OUTPUT_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    if not ablation_dir.exists():
        raise FileNotFoundError(f"Ablation directory not found: {ablation_dir}")

    model_dirs = iter_model_dirs(ablation_dir)
    if not model_dirs:
        raise FileNotFoundError(f"No model folders found in {ablation_dir}")

    human_completion = load_human_completion_times(human_completion_path)
    _, human_fixations_by_step = load_human_fixation_steps(human_fixation_path)

    model_completion = pd.concat([load_model_completion(p) for p in model_dirs], ignore_index=True)
    model_attention = pd.concat([load_model_attention(p) for p in model_dirs], ignore_index=True)
    if model_completion.empty:
        raise RuntimeError("No task_times.csv data could be loaded from ablation folders.")
    if model_attention.empty:
        raise RuntimeError("No attention_shifts.csv data could be loaded from ablation folders.")

    completion_by_task, completion_overall = build_completion_outputs(model_completion, human_completion)
    attention_by_step, attention_overall = build_attention_outputs(model_attention, human_fixations_by_step)

    completion_by_task.to_csv(output_dir / "ablation_completion_by_task_vs_human.csv", index=False)
    completion_overall.to_csv(output_dir / "ablation_completion_overall_vs_human.csv", index=False)
    attention_by_step.to_csv(output_dir / "ablation_attention_by_step_vs_human.csv", index=False)
    attention_overall.to_csv(output_dir / "ablation_attention_overall_vs_human.csv", index=False)

    set_common_style()
    plot_completion_overall(completion_overall, output_dir / "completion_overall_vs_human.png")
    plot_completion_by_task(completion_by_task, output_dir / "completion_by_task_vs_human.png")
    plot_heatmap(
        completion_by_task,
        "mean_diff_pct",
        "Task Completion Difference from Human",
        "Model minus human (%)",
        output_dir / "completion_pct_diff_heatmap.png",
    )
    plot_attention_total(attention_by_step, output_dir / "attention_total_by_step_vs_human.png")
    plot_attention_left_prop(attention_by_step, output_dir / "attention_left_proportion_by_step.png")
    plot_attention_summary(attention_overall, output_dir / "attention_fit_summary.png")

    print(f"Models processed: {len(model_dirs)}")
    print(f"Output directory: {output_dir}")
    print("\nCompletion-time ranking by mean absolute task percent error:")
    print(completion_overall[["model_label", "mean_abs_task_pct_error", "model_minus_human_sec"]].to_string(index=False))
    print("\nAttention side-pattern ranking by left-share MAE:")
    print(attention_overall[["model_label", "step_left_prop_mae_pp", "step_total_rmse"]].to_string(index=False))


if __name__ == "__main__":
    main()
