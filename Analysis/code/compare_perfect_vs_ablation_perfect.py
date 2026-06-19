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
from compare_realistic_vs_new_error import build_metric_comparison


MODEL_LABELS = {
    "Perfect_model": "Original Perfect",
    "Ablation_Perfect": "Ablation Perfect",
}


def with_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["model_label"] = df["model"].map(MODEL_LABELS).fillna(df["model_label"])
    return df


def build_direct_completion_comparison(completion_by_task: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = ["task", "model_label", "run_count", "model_mean_duration", "model_std_duration"]
    wide = completion_by_task[cols].pivot(index="task", columns="model_label")
    out = pd.DataFrame(
        {
            "task": wide.index,
            "original_perfect_mean_duration": wide[("model_mean_duration", "Original Perfect")].values,
            "ablation_perfect_mean_duration": wide[("model_mean_duration", "Ablation Perfect")].values,
            "original_perfect_std_duration": wide[("model_std_duration", "Original Perfect")].values,
            "ablation_perfect_std_duration": wide[("model_std_duration", "Ablation Perfect")].values,
            "original_perfect_run_count": wide[("run_count", "Original Perfect")].values,
            "ablation_perfect_run_count": wide[("run_count", "Ablation Perfect")].values,
        }
    )
    out["ablation_minus_original_sec"] = (
        out["ablation_perfect_mean_duration"] - out["original_perfect_mean_duration"]
    )
    out["ablation_minus_original_pct"] = (
        100.0 * out["ablation_minus_original_sec"] / out["original_perfect_mean_duration"]
    )
    overall = pd.DataFrame(
        [
            {
                "original_perfect_total_mean_sec": out["original_perfect_mean_duration"].sum(),
                "ablation_perfect_total_mean_sec": out["ablation_perfect_mean_duration"].sum(),
                "ablation_minus_original_sec": out["ablation_minus_original_sec"].sum(),
                "ablation_minus_original_pct": 100.0
                * out["ablation_minus_original_sec"].sum()
                / out["original_perfect_mean_duration"].sum(),
                "mean_abs_task_difference_sec": out["ablation_minus_original_sec"].abs().mean(),
            }
        ]
    )
    return out, overall


def build_direct_attention_comparison(attention_by_step: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = [
        "step_num",
        "model_label",
        "n_model_runs",
        "model_total_mean",
        "model_left_prop",
        "model_left_mean",
        "model_right_mean",
    ]
    wide = attention_by_step[cols].pivot(index="step_num", columns="model_label")
    out = pd.DataFrame(
        {
            "step_num": wide.index,
            "original_perfect_total_attention": wide[("model_total_mean", "Original Perfect")].values,
            "ablation_perfect_total_attention": wide[("model_total_mean", "Ablation Perfect")].values,
            "original_perfect_left_prop": wide[("model_left_prop", "Original Perfect")].values,
            "ablation_perfect_left_prop": wide[("model_left_prop", "Ablation Perfect")].values,
            "original_perfect_run_count": wide[("n_model_runs", "Original Perfect")].values,
            "ablation_perfect_run_count": wide[("n_model_runs", "Ablation Perfect")].values,
        }
    )
    out["attention_count_ablation_minus_original"] = (
        out["ablation_perfect_total_attention"] - out["original_perfect_total_attention"]
    )
    out["left_prop_ablation_minus_original_pp"] = (
        100.0 * (out["ablation_perfect_left_prop"] - out["original_perfect_left_prop"])
    )
    overall = pd.DataFrame(
        [
            {
                "original_perfect_total_attention_mean": out["original_perfect_total_attention"].sum(),
                "ablation_perfect_total_attention_mean": out["ablation_perfect_total_attention"].sum(),
                "attention_count_ablation_minus_original": out[
                    "attention_count_ablation_minus_original"
                ].sum(),
                "attention_count_ablation_minus_original_pct": 100.0
                * out["attention_count_ablation_minus_original"].sum()
                / out["original_perfect_total_attention"].sum(),
                "mean_abs_step_attention_difference": out[
                    "attention_count_ablation_minus_original"
                ].abs().mean(),
                "mean_abs_left_prop_difference_pp": out["left_prop_ablation_minus_original_pp"].abs().mean(),
            }
        ]
    )
    return out, overall


def main() -> None:
    analysis_dir = Path(__file__).resolve().parent
    original_dir = analysis_dir / "Perfect_model"
    ablation_dir = analysis_dir / "ablation_25_formula_latest" / "Ablation_Perfect"
    output_dir = analysis_dir / "perfect_vs_ablation_perfect_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    human_completion = load_human_completion_times(analysis_dir / "HumanCompletionTime.csv")
    _, human_fixations_by_step = load_human_fixation_steps(
        analysis_dir / "Human Data" / "eye_tracking_analysis" / "fixation_side_counts_by_subject_by_step.csv"
    )

    completion_df = pd.concat(
        [load_model_completion(original_dir), load_model_completion(ablation_dir)],
        ignore_index=True,
    )
    attention_df = pd.concat(
        [load_model_attention(original_dir), load_model_attention(ablation_dir)],
        ignore_index=True,
    )
    completion_df = with_labels(completion_df)
    attention_df = with_labels(attention_df)

    completion_by_task, completion_overall = build_completion_outputs(completion_df, human_completion)
    attention_by_step, attention_overall = build_attention_outputs(attention_df, human_fixations_by_step)
    metric_comparison = build_metric_comparison(completion_overall, attention_overall)
    direct_completion_by_task, direct_completion_overall = build_direct_completion_comparison(completion_by_task)
    direct_attention_by_step, direct_attention_overall = build_direct_attention_comparison(attention_by_step)

    completion_by_task.to_csv(output_dir / "completion_by_task_vs_human.csv", index=False)
    completion_overall.to_csv(output_dir / "completion_overall_vs_human.csv", index=False)
    attention_by_step.to_csv(output_dir / "attention_by_step_vs_human.csv", index=False)
    attention_overall.to_csv(output_dir / "attention_overall_vs_human.csv", index=False)
    metric_comparison.to_csv(output_dir / "metric_comparison.csv", index=False)
    direct_completion_by_task.to_csv(output_dir / "direct_completion_by_task.csv", index=False)
    direct_completion_overall.to_csv(output_dir / "direct_completion_overall.csv", index=False)
    direct_attention_by_step.to_csv(output_dir / "direct_attention_by_step.csv", index=False)
    direct_attention_overall.to_csv(output_dir / "direct_attention_overall.csv", index=False)

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
    print("\nDirect model-to-model completion delta:")
    print(direct_completion_overall.to_string(index=False))
    print("\nDirect model-to-model attention delta:")
    print(direct_attention_overall.to_string(index=False))
    print("\nMetric winners by absolute error:")
    print(metric_comparison[["metric_group", "metric", "winner"]].drop_duplicates().to_string(index=False))


if __name__ == "__main__":
    main()
