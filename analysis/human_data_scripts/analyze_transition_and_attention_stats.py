from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent
TYPING_DIR = BASE_DIR / "Human Data" / "Typing Data"
ATTENTION_DETAIL = BASE_DIR / "attention_shift_outputs" / "formula_window_attention_shifts_by_subject_task.csv"
OUTPUT_DIR = BASE_DIR / "attention_shift_outputs"
STATS_OUTPUT = OUTPUT_DIR / "task_complexity_transition_attention_stats.csv"

COMPLEX_STEPS = {"Step 3", "Step 5"}
SIMPLE_STEPS = {"Step 7", "Step 9"}

sys.path.insert(0, str(TYPING_DIR))
from typing_task_utils import (  # noqa: E402
    build_formula_rows,
    build_within_task_transition_rows,
    read_combined_subjects,
)


def fmt_p(value: float) -> str:
    if pd.isna(value):
        return "-"
    if value < 0.001:
        return "<0.001"
    return f"{value:.4f}"


def cohens_dz(diff: pd.Series) -> float:
    diff = diff.dropna()
    if len(diff) < 2:
        return np.nan
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd else np.nan


def paired_group_stats(subject_metric: pd.DataFrame, metric_col: str, label: str, unit: str) -> dict[str, object]:
    pivot = subject_metric.pivot(index="subject", columns="group", values=metric_col).dropna()
    if len(pivot) >= 2:
        diff = pivot["Complex Steps 3/5"] - pivot["Simpler Steps 7/9"]
        t_p = stats.ttest_rel(pivot["Complex Steps 3/5"], pivot["Simpler Steps 7/9"]).pvalue
        try:
            w_p = stats.wilcoxon(pivot["Complex Steps 3/5"], pivot["Simpler Steps 7/9"]).pvalue
        except ValueError:
            w_p = np.nan
    else:
        diff = pd.Series(dtype=float)
        t_p = np.nan
        w_p = np.nan

    return {
        "Comparison": label,
        "Unit": unit,
        "Paired subjects": len(pivot),
        "Complex mean": pivot["Complex Steps 3/5"].mean() if len(pivot) else np.nan,
        "Complex median": pivot["Complex Steps 3/5"].median() if len(pivot) else np.nan,
        "Simple mean": pivot["Simpler Steps 7/9"].mean() if len(pivot) else np.nan,
        "Simple median": pivot["Simpler Steps 7/9"].median() if len(pivot) else np.nan,
        "Mean diff complex-simple": diff.mean() if len(diff) else np.nan,
        "Paired t p": t_p,
        "Wilcoxon p": w_p,
        "Cohen dz": cohens_dz(diff),
        "Subjects complex > simple": int((diff > 0).sum()) if len(diff) else 0,
    }


def transition_stats() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = read_combined_subjects()
    formula_rows, _ = build_formula_rows(df)
    formula_rows = formula_rows.dropna(subset=["mean_iki"]).copy()
    transitions = build_within_task_transition_rows(formula_rows)
    transitions = transitions[transitions["step"].isin(COMPLEX_STEPS | SIMPLE_STEPS)].copy()
    transitions["group"] = np.where(
        transitions["step"].isin(COMPLEX_STEPS),
        "Complex Steps 3/5",
        "Simpler Steps 7/9",
    )

    subject_metric = (
        transitions.groupby(["subject", "group"], as_index=False)
        .agg(
            enter_to_next_s=("prev_enter_to_next_start_s", "mean"),
            last_char_to_next_s=("prev_last_text_to_next_first_text_s", "mean"),
            transitions=("prev_enter_to_next_start_s", "size"),
        )
    )

    rows = [
        paired_group_stats(subject_metric, "enter_to_next_s", "Transition pause: Enter to next =", "seconds"),
        paired_group_stats(subject_metric, "last_char_to_next_s", "Transition pause: last char to next =", "seconds"),
    ]
    return pd.DataFrame(rows), subject_metric


def attention_stats() -> tuple[pd.DataFrame, pd.DataFrame]:
    attention = pd.read_csv(ATTENTION_DETAIL)
    attention = attention[attention["step"].isin(COMPLEX_STEPS | SIMPLE_STEPS)].copy()
    attention["group"] = np.where(
        attention["step"].isin(COMPLEX_STEPS),
        "Complex Steps 3/5",
        "Simpler Steps 7/9",
    )
    subject_metric = (
        attention.groupby(["subject", "group"], as_index=False)
        .agg(
            attention_shifts=("attention_shifts_x_lt_800_to_x_gt_1000", "mean"),
            shifts_per_min=("shifts_per_min", "mean"),
            left_right_fixations_used=("left_right_fixations_used", "mean"),
        )
    )
    rows = [
        paired_group_stats(subject_metric, "attention_shifts", "Eye tracking: attention shifts per formula task", "shift count"),
        paired_group_stats(subject_metric, "shifts_per_min", "Eye tracking: attention shifts per minute", "shifts/min"),
    ]
    return pd.DataFrame(rows), subject_metric


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    transition_summary, transition_subject = transition_stats()
    attention_summary, attention_subject = attention_stats()
    summary = pd.concat([transition_summary, attention_summary], ignore_index=True)
    summary.to_csv(STATS_OUTPUT, index=False)

    display = summary.copy()
    for col in ["Complex mean", "Complex median", "Simple mean", "Simple median", "Mean diff complex-simple", "Cohen dz"]:
        display[col] = display[col].map(lambda x: "-" if pd.isna(x) else f"{x:.3f}")
    display["Paired t p"] = display["Paired t p"].map(fmt_p)
    display["Wilcoxon p"] = display["Wilcoxon p"].map(fmt_p)
    print(display.to_markdown(index=False))
    print(f"Saved stats: {STATS_OUTPUT}")


if __name__ == "__main__":
    main()
