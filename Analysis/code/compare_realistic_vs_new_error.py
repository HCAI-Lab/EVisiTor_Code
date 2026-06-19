#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

from analyze_ablation_vs_human import (
    build_attention_outputs,
    build_completion_outputs,
    load_human_completion_times,
    load_human_fixation_steps,
    load_model_attention,
    load_model_completion,
    plot_attention_left_prop,
    plot_attention_summary,
    plot_attention_total,
    plot_completion_by_task,
    plot_completion_overall,
    plot_heatmap,
    set_common_style,
)


def winner_lower(df: pd.DataFrame, metric: str) -> str:
    return str(df.loc[df[metric].astype(float).idxmin(), "model_label"])


def winner_abs_lower(df: pd.DataFrame, metric: str) -> str:
    values = df[metric].astype(float).abs()
    return str(df.loc[values.idxmin(), "model_label"])


def build_metric_comparison(completion_overall: pd.DataFrame, attention_overall: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in completion_overall.iterrows():
        rows.extend(
            [
                {
                    "metric_group": "completion",
                    "metric": "overall_total_time_error_sec",
                    "model_label": row["model_label"],
                    "value": float(row["model_minus_human_sec"]),
                    "absolute_value": abs(float(row["model_minus_human_sec"])),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "completion",
                    "metric": "overall_total_time_error_pct",
                    "model_label": row["model_label"],
                    "value": float(row["model_minus_human_pct"]),
                    "absolute_value": abs(float(row["model_minus_human_pct"])),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "completion",
                    "metric": "mean_abs_task_pct_error",
                    "model_label": row["model_label"],
                    "value": float(row["mean_abs_task_pct_error"]),
                    "absolute_value": float(row["mean_abs_task_pct_error"]),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "completion",
                    "metric": "rmse_task_sec",
                    "model_label": row["model_label"],
                    "value": float(row["rmse_task_sec"]),
                    "absolute_value": float(row["rmse_task_sec"]),
                    "lower_is_better": True,
                },
            ]
        )

    for _, row in attention_overall.iterrows():
        rows.extend(
            [
                {
                    "metric_group": "attention",
                    "metric": "total_count_error_pct",
                    "model_label": row["model_label"],
                    "value": float(row["total_count_diff_pct"]),
                    "absolute_value": abs(float(row["total_count_diff_pct"])),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "attention",
                    "metric": "overall_left_share_error_pp",
                    "model_label": row["model_label"],
                    "value": float(row["left_prop_diff_pp"]),
                    "absolute_value": abs(float(row["left_prop_diff_pp"])),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "attention",
                    "metric": "step_left_share_mae_pp",
                    "model_label": row["model_label"],
                    "value": float(row["step_left_prop_mae_pp"]),
                    "absolute_value": float(row["step_left_prop_mae_pp"]),
                    "lower_is_better": True,
                },
                {
                    "metric_group": "attention",
                    "metric": "step_count_rmse",
                    "model_label": row["model_label"],
                    "value": float(row["step_total_rmse"]),
                    "absolute_value": float(row["step_total_rmse"]),
                    "lower_is_better": True,
                },
            ]
        )

    comparison = pd.DataFrame(rows)
    winners = (
        comparison.sort_values(["metric", "absolute_value"])
        .groupby("metric", as_index=False)
        .first()[["metric", "model_label"]]
        .rename(columns={"model_label": "winner"})
    )
    return comparison.merge(winners, on="metric", how="left")


def main() -> None:
    analysis_dir = Path(__file__).resolve().parent
    realistic_dir = analysis_dir / "ablation_25_formula_latest" / "Ablation_Full_Realistic"
    new_error_dir = analysis_dir / "New_Error (3-5-2-TCP)"
    output_dir = analysis_dir / "realistic_vs_new_error_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    human_completion = load_human_completion_times(analysis_dir / "HumanCompletionTime.csv")
    _, human_fixations_by_step = load_human_fixation_steps(
        analysis_dir / "Human Data" / "eye_tracking_analysis" / "fixation_side_counts_by_subject_by_step.csv"
    )

    model_dirs = [realistic_dir, new_error_dir]
    completion_df = pd.concat([load_model_completion(path) for path in model_dirs], ignore_index=True)
    attention_df = pd.concat([load_model_attention(path) for path in model_dirs], ignore_index=True)

    completion_by_task, completion_overall = build_completion_outputs(completion_df, human_completion)
    attention_by_step, attention_overall = build_attention_outputs(attention_df, human_fixations_by_step)
    metric_comparison = build_metric_comparison(completion_overall, attention_overall)

    completion_by_task.to_csv(output_dir / "completion_by_task_vs_human.csv", index=False)
    completion_overall.to_csv(output_dir / "completion_overall_vs_human.csv", index=False)
    attention_by_step.to_csv(output_dir / "attention_by_step_vs_human.csv", index=False)
    attention_overall.to_csv(output_dir / "attention_overall_vs_human.csv", index=False)
    metric_comparison.to_csv(output_dir / "metric_comparison.csv", index=False)

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

    print(f"Output directory: {output_dir}")
    print("\nCompletion metrics:")
    print(
        completion_overall[
            [
                "model_label",
                "run_count_min",
                "model_total_mean_sec",
                "human_total_mean_sec",
                "model_minus_human_sec",
                "model_minus_human_pct",
                "mean_abs_task_pct_error",
                "rmse_task_sec",
            ]
        ].to_string(index=False)
    )
    print("\nAttention/fixation metrics:")
    print(
        attention_overall[
            [
                "model_label",
                "run_count_min",
                "model_total_attention_mean_per_run",
                "human_total_fixations_mean_per_subject",
                "total_count_diff_pct",
                "left_prop_diff_pp",
                "step_left_prop_mae_pp",
                "step_total_rmse",
            ]
        ].to_string(index=False)
    )
    print("\nMetric winners by absolute error:")
    print(metric_comparison[["metric_group", "metric", "winner"]].drop_duplicates().to_string(index=False))


if __name__ == "__main__":
    main()
