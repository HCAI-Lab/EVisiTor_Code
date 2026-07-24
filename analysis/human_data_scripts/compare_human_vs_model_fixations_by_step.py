from pathlib import Path
import re

import pandas as pd


HUMAN_COUNTS_CSV = (
    Path("Human Data")
    / "eye_tracking_analysis"
    / "fixation_side_counts_by_subject_by_step.csv"
)
MODEL_RUNS_DIR = Path("New_Error (3-5-2-TCP)")
OUTPUT_DIR = Path("Human Data") / "eye_tracking_analysis"

OUTPUT_HUMAN_STEP_CSV = OUTPUT_DIR / "human_fixation_counts_by_step_excl_subject1.csv"
OUTPUT_MODEL_STEP_CSV = OUTPUT_DIR / "model_attention_shift_counts_by_step.csv"
OUTPUT_MODEL_RUN_STEP_CSV = OUTPUT_DIR / "model_attention_shift_counts_by_step_by_run.csv"
OUTPUT_COMPARISON_CSV = OUTPUT_DIR / "comparison_human_vs_model_by_step.csv"

X_THRESHOLD = 960
EXCLUDED_SUBJECTS = {"Subject1"}


def parse_step_num(step_name):
    m = re.match(r"Step\s+(\d+)$", str(step_name).strip())
    return int(m.group(1)) if m else None


def load_human_step_counts(base_dir):
    csv_path = base_dir / HUMAN_COUNTS_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"Human summary not found: {csv_path}")

    df = pd.read_csv(csv_path)
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
        raise ValueError(f"Missing required human columns: {sorted(missing)}")

    df = df[~df["subject"].isin(EXCLUDED_SUBJECTS)].copy()
    df = df[df["step_name"].astype(str).str.startswith("Step ")].copy()
    df["step_num"] = df["step_name"].map(parse_step_num)
    df = df[df["step_num"].notna()].copy()

    per_subject = (
        df.groupby(["subject", "step_num", "step_name"], as_index=False)
        .agg(
            human_left=("fixations_x_lt_threshold", "sum"),
            human_right=("fixations_x_gt_threshold", "sum"),
            human_equal=("fixations_x_eq_threshold", "sum"),
            human_total=("total_fixations", "sum"),
        )
    )

    per_step = (
        per_subject.groupby(["step_num", "step_name"], as_index=False)
        .agg(
            n_human_subjects=("subject", "nunique"),
            human_left_total=("human_left", "sum"),
            human_right_total=("human_right", "sum"),
            human_equal_total=("human_equal", "sum"),
            human_total_fixations=("human_total", "sum"),
            human_left_mean_per_subject=("human_left", "mean"),
            human_right_mean_per_subject=("human_right", "mean"),
            human_total_mean_per_subject=("human_total", "mean"),
        )
        .sort_values("step_num")
        .reset_index(drop=True)
    )

    return per_subject, per_step


def load_model_attention_counts(base_dir):
    runs_dir = base_dir / MODEL_RUNS_DIR
    if not runs_dir.exists():
        raise FileNotFoundError(f"Model runs folder not found: {runs_dir}")

    run_dirs = sorted([p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith("run_")])
    if not run_dirs:
        raise FileNotFoundError(f"No run_* folders found in: {runs_dir}")

    per_run_rows = []
    for run_dir in run_dirs:
        run_name = run_dir.name
        attention_path = run_dir / "attention_shifts.csv"
        if not attention_path.exists():
            continue

        df = pd.read_csv(attention_path)
        required = {"model_time", "task", "screen_x", "screen_y"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required model columns {sorted(missing)} in {attention_path}")

        # Remove duplicate rows that represent the same shift emitted by multiple logging sources.
        dedup_cols = ["model_time", "task", "subtask", "screen_x", "screen_y", "location_name"]
        dedup_cols = [c for c in dedup_cols if c in df.columns]
        df = df.drop_duplicates(subset=dedup_cols).copy()

        df["step_num"] = pd.to_numeric(df["task"], errors="coerce")
        df = df[df["step_num"].notna()].copy()
        df["step_num"] = df["step_num"].astype(int)
        df = df[df["step_num"].between(1, 14)].copy()

        df["step_name"] = "Step " + df["step_num"].astype(str)
        df["model_left"] = df["screen_x"] < X_THRESHOLD
        df["model_right"] = df["screen_x"] > X_THRESHOLD
        df["model_equal"] = df["screen_x"] == X_THRESHOLD

        grouped = (
            df.groupby(["step_num", "step_name"], as_index=False)
            .agg(
                model_left=("model_left", "sum"),
                model_right=("model_right", "sum"),
                model_equal=("model_equal", "sum"),
                model_total_attention_shifts=("screen_x", "size"),
            )
        )
        grouped["run"] = run_name
        per_run_rows.append(grouped)

    if not per_run_rows:
        raise RuntimeError("No model attention_shifts.csv files could be processed.")

    per_run = pd.concat(per_run_rows, ignore_index=True)
    per_run = per_run.sort_values(["run", "step_num"]).reset_index(drop=True)

    per_step = (
        per_run.groupby(["step_num", "step_name"], as_index=False)
        .agg(
            n_model_runs=("run", "nunique"),
            model_left_total=("model_left", "sum"),
            model_right_total=("model_right", "sum"),
            model_equal_total=("model_equal", "sum"),
            model_total_attention_shifts=("model_total_attention_shifts", "sum"),
            model_left_mean_per_run=("model_left", "mean"),
            model_right_mean_per_run=("model_right", "mean"),
            model_total_mean_per_run=("model_total_attention_shifts", "mean"),
        )
        .sort_values("step_num")
        .reset_index(drop=True)
    )

    return per_run, per_step


def build_comparison(human_per_step, model_per_step):
    cmp_df = pd.merge(
        human_per_step,
        model_per_step,
        on=["step_num", "step_name"],
        how="outer",
    ).sort_values("step_num").reset_index(drop=True)

    cmp_df["delta_left_mean_human_minus_model"] = (
        cmp_df["human_left_mean_per_subject"] - cmp_df["model_left_mean_per_run"]
    )
    cmp_df["delta_right_mean_human_minus_model"] = (
        cmp_df["human_right_mean_per_subject"] - cmp_df["model_right_mean_per_run"]
    )
    cmp_df["delta_total_mean_human_minus_model"] = (
        cmp_df["human_total_mean_per_subject"] - cmp_df["model_total_mean_per_run"]
    )

    return cmp_df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    human_per_subject_step, human_per_step = load_human_step_counts(base_dir)
    model_per_run_step, model_per_step = load_model_attention_counts(base_dir)
    comparison_df = build_comparison(human_per_step, model_per_step)

    human_per_step.to_csv(base_dir / OUTPUT_HUMAN_STEP_CSV, index=False)
    model_per_run_step.to_csv(base_dir / OUTPUT_MODEL_RUN_STEP_CSV, index=False)
    model_per_step.to_csv(base_dir / OUTPUT_MODEL_STEP_CSV, index=False)
    comparison_df.to_csv(base_dir / OUTPUT_COMPARISON_CSV, index=False)

    print(f"Excluded subjects: {sorted(EXCLUDED_SUBJECTS)}")
    print(f"X threshold for left/right split: {X_THRESHOLD}")
    print(f"Saved human by-step summary: {base_dir / OUTPUT_HUMAN_STEP_CSV}")
    print(f"Saved model by-run by-step summary: {base_dir / OUTPUT_MODEL_RUN_STEP_CSV}")
    print(f"Saved model by-step summary: {base_dir / OUTPUT_MODEL_STEP_CSV}")
    print(f"Saved human-vs-model comparison: {base_dir / OUTPUT_COMPARISON_CSV}")
    print(f"Model runs processed: {model_per_run_step['run'].nunique()}")
    print(f"Human subjects included: {human_per_subject_step['subject'].nunique()}")