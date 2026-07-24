from __future__ import annotations

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
TYPING_DIR = BASE_DIR / "Human Data" / "Typing Data"
EYE_DIR = BASE_DIR / "Human Data" / "eye_tracking_analysis"
OUTPUT_DIR = BASE_DIR / "attention_shift_outputs"
DETAIL_OUTPUT = OUTPUT_DIR / "formula_window_attention_shifts_by_subject_task.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "formula_window_attention_shifts_by_task.csv"
TASK_WINDOWS_PATH = EYE_DIR / "task_time_windows_from_breakdown.csv"

LEFT_X_MAX = 800
RIGHT_X_MIN = 1000
FORMULA_TASKS = {3, 4, 5, 6, 7, 8, 9, 10, 13}


def build_formula_task_windows() -> pd.DataFrame:
    task_windows = pd.read_csv(TASK_WINDOWS_PATH)
    task_windows = task_windows[task_windows["step_num"].isin(FORMULA_TASKS)].copy()

    rows: list[dict[str, object]] = []
    for _, task_window in task_windows.iterrows():
        subject = str(task_window["subject"])
        subject_num_match = re.search(r"\d+", subject)
        if not subject_num_match:
            continue

        subject_num = int(subject_num_match.group())
        typing_path = TYPING_DIR / f"subject{subject_num}.csv"
        if not typing_path.exists():
            continue

        typing_rows = read_typing_subject_csv(typing_path)
        step_rows = typing_rows[
            (typing_rows["time_sec"] >= float(task_window["start_time_sec"]))
            & (typing_rows["time_sec"] <= float(task_window["end_time_sec"]))
        ].copy()

        keydowns = step_rows[step_rows["Code"].astype(str).str.endswith(" D")].copy()
        equals = keydowns[keydowns["Code"] == "K = D"]
        if equals.empty:
            continue

        start_time = float(equals["time_sec"].min())
        enters_after_start = keydowns[(keydowns["Code"] == "K Enter D") & (keydowns["time_sec"] >= start_time)]
        if enters_after_start.empty:
            continue

        end_time = float(enters_after_start["time_sec"].max())
        rows.append(
            {
                "subject": subject,
                "step_num": int(task_window["step_num"]),
                "step": task_window["step_name"],
                "task": step_task_label(int(task_window["step_num"])),
                "formula_entries": int(len(equals)),
                "formula_window_start_sec": start_time,
                "formula_window_end_sec": end_time,
                "task_window_start_sec": float(task_window["start_time_sec"]),
                "task_window_end_sec": float(task_window["end_time_sec"]),
            }
        )

    windows = pd.DataFrame(rows).sort_values(["subject", "step_num"]).reset_index(drop=True)
    windows["formula_window_duration_sec"] = (
        windows["formula_window_end_sec"] - windows["formula_window_start_sec"]
    )
    return windows


def read_typing_subject_csv(path: Path) -> pd.DataFrame:
    df = pd.DataFrame()
    for skiprows in (1, 0):
        for sep in ("\t", ","):
            candidate = pd.read_csv(path, skiprows=skiprows, sep=sep, engine="python")
            if "Code" in candidate.columns:
                df = candidate
                break
        if not df.empty:
            break
    time_col = "Time" if "Time" in df.columns else "Start Time"
    if "Code" not in df.columns or time_col not in df.columns:
        raise ValueError(f"Missing Code or time column in {path}")

    df = df.copy()
    df["Code"] = df["Code"].astype(str).str.strip()
    df["time_sec"] = pd.to_numeric(df[time_col], errors="coerce")
    return df.dropna(subset=["time_sec"])


def step_task_label(step_num: int) -> str:
    labels = {
        3: "Calculate frequency",
        4: "Calculate total frequency",
        5: "Calculate normalization",
        6: "Calculate total normalization",
        7: "Calculate length",
        8: "Calculate total length",
        9: "Calculate typed characters",
        10: "Calculate total typed characters",
        13: "Insert current date",
    }
    return labels.get(step_num, f"Step {step_num}")


def fixation_side(x: float) -> str | None:
    if pd.isna(x):
        return None
    if x < LEFT_X_MAX:
        return "left"
    if x > RIGHT_X_MIN:
        return "right"
    return None


def count_left_right_shifts(fixations: pd.DataFrame) -> tuple[int, int, int, int, int]:
    if fixations.empty:
        return 0, 0, 0, 0, 0

    sides = fixations["x_px"].map(fixation_side)
    left_count = int((sides == "left").sum())
    right_count = int((sides == "right").sum())
    middle_count = int(sides.isna().sum())
    side_sequence = [side for side in sides.tolist() if side in {"left", "right"}]
    shifts = sum(1 for previous, current in zip(side_sequence, side_sequence[1:]) if previous != current)
    return shifts, left_count, right_count, middle_count, len(side_sequence)


def count_all_fixation_saccades(fixations: pd.DataFrame) -> int:
    if fixations.empty:
        return 0
    return max(int(len(fixations)) - 1, 0)


def analyze_subject_window(subject: str, windows: pd.DataFrame) -> list[dict[str, object]]:
    fixation_path = EYE_DIR / f"{subject}_red_cross_fixations.csv"
    if not fixation_path.exists():
        return []

    fixations = pd.read_csv(fixation_path)
    required = {"start_time_sec", "end_time_sec", "x_px", "duration_ms"}
    missing = required - set(fixations.columns)
    if missing:
        raise ValueError(f"Missing required columns {sorted(missing)} in {fixation_path}")

    fixations = fixations.copy()
    fixations["mid_time_sec"] = (fixations["start_time_sec"] + fixations["end_time_sec"]) / 2.0

    rows: list[dict[str, object]] = []
    for _, window in windows.iterrows():
        start = float(window["formula_window_start_sec"])
        end = float(window["formula_window_end_sec"])
        in_window = fixations[(fixations["mid_time_sec"] >= start) & (fixations["mid_time_sec"] <= end)].copy()
        in_window = in_window.sort_values("mid_time_sec")

        shifts, left_count, right_count, middle_count, side_fixation_count = count_left_right_shifts(in_window)
        all_saccades = count_all_fixation_saccades(in_window)
        duration_sec = float(window["formula_window_duration_sec"])
        rows.append(
            {
                "subject": subject,
                "step_num": int(window["step_num"]),
                "step": window["step"],
                "task": window["task"],
                "formula_entries": int(window["formula_entries"]),
                "window_start_sec": start,
                "window_end_sec": end,
                "window_duration_sec": duration_sec,
                "task_window_start_sec": float(window["task_window_start_sec"]),
                "task_window_end_sec": float(window["task_window_end_sec"]),
                "total_fixations": int(len(in_window)),
                "left_fixations_x_lt_800": left_count,
                "right_fixations_x_gt_1000": right_count,
                "middle_fixations_800_to_1000": middle_count,
                "left_right_fixations_used": side_fixation_count,
                "attention_shifts_x_lt_800_to_x_gt_1000": shifts,
                "all_fixation_to_fixation_saccades": all_saccades,
                "shifts_per_min": shifts / (duration_sec / 60.0) if duration_sec > 0 else np.nan,
                "all_saccades_per_min": all_saccades / (duration_sec / 60.0) if duration_sec > 0 else np.nan,
                "source_file": fixation_path.name,
            }
        )

    return rows


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame()

    summary = (
        detail.groupby(["step_num", "step", "task"], as_index=False)
        .agg(
            subjects=("subject", "nunique"),
            total_attention_shifts=("attention_shifts_x_lt_800_to_x_gt_1000", "sum"),
            mean_attention_shifts=("attention_shifts_x_lt_800_to_x_gt_1000", "mean"),
            median_attention_shifts=("attention_shifts_x_lt_800_to_x_gt_1000", "median"),
            total_all_saccades=("all_fixation_to_fixation_saccades", "sum"),
            mean_all_saccades=("all_fixation_to_fixation_saccades", "mean"),
            median_all_saccades=("all_fixation_to_fixation_saccades", "median"),
            total_left_fixations=("left_fixations_x_lt_800", "sum"),
            total_right_fixations=("right_fixations_x_gt_1000", "sum"),
            total_middle_fixations=("middle_fixations_800_to_1000", "sum"),
            total_fixations=("total_fixations", "sum"),
            mean_shifts_per_min=("shifts_per_min", "mean"),
            mean_all_saccades_per_min=("all_saccades_per_min", "mean"),
            mean_window_duration_sec=("window_duration_sec", "mean"),
        )
        .sort_values("step_num")
        .reset_index(drop=True)
    )
    return summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    windows = build_formula_task_windows()

    rows: list[dict[str, object]] = []
    for subject, subject_windows in windows.groupby("subject", sort=True):
        rows.extend(analyze_subject_window(subject, subject_windows))

    detail = pd.DataFrame(rows)
    if detail.empty:
        raise RuntimeError("No overlapping eye-tracking fixation files matched the formula task windows.")

    summary = build_summary(detail)
    detail.to_csv(DETAIL_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    print(f"Saved detail: {DETAIL_OUTPUT}")
    print(f"Saved summary: {SUMMARY_OUTPUT}")
    print(f"Subjects analyzed: {detail['subject'].nunique()}")
    print(f"Rows written: {len(detail)}")


if __name__ == "__main__":
    main()
