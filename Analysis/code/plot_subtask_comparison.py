#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_subtask_data(base_dir: str, model_label: str) -> Tuple[pd.DataFrame, int, List[str]]:
    rows: List[pd.DataFrame] = []
    used_runs = 0
    skipped_runs: List[str] = []

    for name in sorted(os.listdir(base_dir)):
        if not name.startswith("run_"):
            continue

        run_dir = os.path.join(base_dir, name)
        if not os.path.isdir(run_dir):
            continue

        subtask_path = os.path.join(run_dir, "subtask_times.csv")
        if not os.path.exists(subtask_path):
            skipped_runs.append(name)
            continue

        try:
            df = pd.read_csv(subtask_path)
        except Exception:
            skipped_runs.append(name)
            continue

        required = {"task", "subtask", "duration"}
        if not required.issubset(df.columns):
            skipped_runs.append(name)
            continue

        df = df[["task", "subtask", "duration"]].copy()
        df["task"] = pd.to_numeric(df["task"], errors="coerce")
        df["subtask"] = pd.to_numeric(df["subtask"], errors="coerce")
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
        df = df.dropna(subset=["task", "subtask", "duration"])

        if df.empty:
            skipped_runs.append(name)
            continue

        df["task"] = df["task"].astype(int)
        df["subtask"] = df["subtask"].astype(int)
        df["run"] = name
        df["model"] = model_label
        rows.append(df)
        used_runs += 1

    if not rows:
        return pd.DataFrame(columns=["task", "subtask", "duration", "run", "model"]), used_runs, skipped_runs

    return pd.concat(rows, ignore_index=True), used_runs, skipped_runs


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare subtask times for New Error and Perfect model runs.")
    parser.add_argument("--new-dir", required=True, help="Directory containing New Error run_### folders")
    parser.add_argument("--perfect-dir", required=True, help="Directory containing Perfect model run_### folders")
    parser.add_argument("--output-dir", required=True, help="Directory to save CSV and PNG outputs")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    new_df, new_used, new_skipped = load_subtask_data(args.new_dir, "new_error")
    perfect_df, perfect_used, perfect_skipped = load_subtask_data(args.perfect_dir, "perfect_model")

    if new_df.empty or perfect_df.empty:
        raise RuntimeError("Subtask data could not be loaded for one or both model directories.")

    new_stats = (
        new_df.groupby(["task", "subtask"]) ["duration"]
        .agg(new_count="count", new_mean="mean", new_std="std")
        .reset_index()
    )
    perfect_stats = (
        perfect_df.groupby(["task", "subtask"]) ["duration"]
        .agg(perfect_count="count", perfect_mean="mean", perfect_std="std")
        .reset_index()
    )

    cmp = pd.merge(new_stats, perfect_stats, on=["task", "subtask"], how="outer").sort_values(["task", "subtask"])
    cmp["subtask_label"] = cmp.apply(lambda r: f"T{int(r['task'])}-S{int(r['subtask'])}", axis=1)
    cmp["mean_diff_sec_new_minus_perfect"] = cmp["new_mean"] - cmp["perfect_mean"]
    cmp["mean_diff_pct_vs_perfect"] = np.where(
        cmp["perfect_mean"].notna() & (cmp["perfect_mean"] != 0),
        100.0 * cmp["mean_diff_sec_new_minus_perfect"] / cmp["perfect_mean"],
        np.nan,
    )
    cmp["std_diff_sec_new_minus_perfect"] = cmp["new_std"] - cmp["perfect_std"]

    new_task_run = new_df.groupby(["run", "task"]) ["duration"].sum().reset_index()
    perfect_task_run = perfect_df.groupby(["run", "task"]) ["duration"].sum().reset_index()
    new_task_stats = (
        new_task_run.groupby("task") ["duration"]
        .agg(new_task_count="count", new_task_mean="mean", new_task_std="std")
        .reset_index()
    )
    perfect_task_stats = (
        perfect_task_run.groupby("task") ["duration"]
        .agg(perfect_task_count="count", perfect_task_mean="mean", perfect_task_std="std")
        .reset_index()
    )
    task_cmp = pd.merge(new_task_stats, perfect_task_stats, on="task", how="outer").sort_values("task")
    task_cmp["task_mean_diff_sec_new_minus_perfect"] = task_cmp["new_task_mean"] - task_cmp["perfect_task_mean"]

    overall_new = new_df.groupby("run") ["duration"].sum()
    overall_perfect = perfect_df.groupby("run") ["duration"].sum()
    overall_cmp = pd.DataFrame(
        {
            "model": ["new_error", "perfect_model"],
            "run_count": [overall_new.shape[0], overall_perfect.shape[0]],
            "mean_total_time_sec": [overall_new.mean(), overall_perfect.mean()],
            "std_total_time_sec": [overall_new.std(ddof=1), overall_perfect.std(ddof=1)],
        }
    )

    subtask_csv = os.path.join(args.output_dir, "subtask_time_comparison_new_vs_perfect.csv")
    task_csv = os.path.join(args.output_dir, "subtask_derived_task_time_comparison_new_vs_perfect.csv")
    overall_csv = os.path.join(args.output_dir, "subtask_overall_time_comparison_new_vs_perfect.csv")
    cmp.to_csv(subtask_csv, index=False)
    task_cmp.to_csv(task_csv, index=False)
    overall_cmp.to_csv(overall_csv, index=False)

    # Subtask-level grouped bar plot.
    x = np.arange(len(cmp))
    width = 0.42
    fig, ax = plt.subplots(figsize=(max(14, len(cmp) * 0.32), 7))
    ax.bar(x - width / 2, cmp["new_mean"], width, yerr=cmp["new_std"], capsize=2, label="New Error")
    ax.bar(x + width / 2, cmp["perfect_mean"], width, yerr=cmp["perfect_std"], capsize=2, label="Perfect Model")
    ax.set_title("Subtask Completion Time: New Error vs Perfect Model")
    ax.set_xlabel("Subtask (Task-Subtask)")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(cmp["subtask_label"], rotation=90)
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    ax.legend()
    fig.tight_layout()
    subtask_png = os.path.join(args.output_dir, "subtask_time_barplot_new_vs_perfect.png")
    fig.savefig(subtask_png, dpi=220)
    plt.close(fig)

    # Task-level grouped bar plot derived from subtasks.
    tx = np.arange(len(task_cmp))
    tfig, tax = plt.subplots(figsize=(12, 6.2))
    tax.bar(tx - width / 2, task_cmp["new_task_mean"], width, yerr=task_cmp["new_task_std"], capsize=3, label="New Error")
    tax.bar(tx + width / 2, task_cmp["perfect_task_mean"], width, yerr=task_cmp["perfect_task_std"], capsize=3, label="Perfect Model")
    tax.set_title("Task Completion Time (Derived from Subtasks): New Error vs Perfect Model")
    tax.set_xlabel("Task")
    tax.set_ylabel("Time (seconds)")
    tax.set_xticks(tx)
    tax.set_xticklabels([str(int(v)) for v in task_cmp["task"]])
    tax.grid(axis="y", alpha=0.25, linestyle="--")
    tax.legend()
    tfig.tight_layout()
    task_png = os.path.join(args.output_dir, "task_time_barplot_from_subtasks_new_vs_perfect.png")
    tfig.savefig(task_png, dpi=220)
    plt.close(tfig)

    # Overall bar plot.
    ox = np.arange(2)
    ofig, oax = plt.subplots(figsize=(7.2, 5.4))
    oax.bar(ox, overall_cmp["mean_total_time_sec"], yerr=overall_cmp["std_total_time_sec"], capsize=4)
    oax.set_xticks(ox)
    oax.set_xticklabels(["New Error", "Perfect Model"])
    oax.set_title("Overall Completion Time from Subtasks")
    oax.set_ylabel("Time (seconds)")
    oax.grid(axis="y", alpha=0.25, linestyle="--")
    ofig.tight_layout()
    overall_png = os.path.join(args.output_dir, "overall_time_barplot_from_subtasks_new_vs_perfect.png")
    ofig.savefig(overall_png, dpi=220)
    plt.close(ofig)

    print(f"New Error runs used: {new_used} (skipped {len(new_skipped)})")
    print(f"Perfect Model runs used: {perfect_used} (skipped {len(perfect_skipped)})")
    print("Saved CSV:")
    print(subtask_csv)
    print(task_csv)
    print(overall_csv)
    print("Saved PNG:")
    print(subtask_png)
    print(task_png)
    print(overall_png)


if __name__ == "__main__":
    main()
