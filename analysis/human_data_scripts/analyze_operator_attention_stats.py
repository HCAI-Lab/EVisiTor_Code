from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent
DETAIL_INPUT = BASE_DIR / "attention_shift_outputs" / "formula_window_attention_shifts_by_subject_task.csv"
OUTPUT_PATH = BASE_DIR / "attention_shift_outputs" / "operator_formula_attention_shift_stats.csv"

OPERATOR_STEPS = {"Step 3", "Step 5", "Step 9"}
OPERATOR_GROUP = "Operator-heavy (* or /)"
NO_OPERATOR_GROUP = "No * or /"


def cohens_dz(diff: pd.Series) -> float:
    diff = diff.dropna()
    if len(diff) < 2:
        return np.nan
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd else np.nan


def paired_stats(subject_group: pd.DataFrame, metric: str, label: str) -> dict[str, object]:
    pivot = subject_group.pivot(index="subject", columns="group", values=metric).dropna()
    diff = pivot[OPERATOR_GROUP] - pivot[NO_OPERATOR_GROUP]
    return {
        "Comparison": label,
        "Paired subjects": len(pivot),
        "Operator-heavy mean": pivot[OPERATOR_GROUP].mean(),
        "No * or / mean": pivot[NO_OPERATOR_GROUP].mean(),
        "Mean diff operator-no-op": diff.mean(),
        "Paired t p": stats.ttest_rel(pivot[OPERATOR_GROUP], pivot[NO_OPERATOR_GROUP]).pvalue,
        "Wilcoxon p": stats.wilcoxon(pivot[OPERATOR_GROUP], pivot[NO_OPERATOR_GROUP]).pvalue,
        "Cohen dz": cohens_dz(diff),
        "Subjects operator > no-op": int((diff > 0).sum()),
    }


def build_stats() -> pd.DataFrame:
    detail = pd.read_csv(DETAIL_INPUT)
    detail = detail.copy()
    detail["group"] = np.where(detail["step"].isin(OPERATOR_STEPS), OPERATOR_GROUP, NO_OPERATOR_GROUP)

    subject_group = (
        detail.groupby(["subject", "group"], as_index=False)
        .agg(
            total_saccades=("all_fixation_to_fixation_saccades", "sum"),
            total_entries=("formula_entries", "sum"),
            total_duration_sec=("window_duration_sec", "sum"),
            total_fixations=("total_fixations", "sum"),
            saccades_per_task_window=("all_fixation_to_fixation_saccades", "mean"),
        )
    )
    subject_group["saccades_per_entry"] = subject_group["total_saccades"] / subject_group["total_entries"]
    subject_group["saccades_per_minute"] = subject_group["total_saccades"] / (
        subject_group["total_duration_sec"] / 60.0
    )
    subject_group["fixations_per_entry"] = subject_group["total_fixations"] / subject_group["total_entries"]

    return pd.DataFrame(
        [
            paired_stats(subject_group, "saccades_per_task_window", "Eye tracking: all saccades per task window"),
            paired_stats(subject_group, "saccades_per_entry", "Eye tracking: all saccades per formula entry"),
            paired_stats(subject_group, "saccades_per_minute", "Eye tracking: all saccades per minute"),
            paired_stats(subject_group, "fixations_per_entry", "Eye tracking: all fixations per formula entry"),
        ]
    )


def main() -> None:
    stats_df = build_stats()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(OUTPUT_PATH, index=False)
    print(stats_df.to_markdown(index=False))
    print(f"Saved stats: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
