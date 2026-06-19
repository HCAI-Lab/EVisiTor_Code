from pathlib import Path
import re

import numpy as np
import pandas as pd


INPUT_DIR = Path("Human Data") / "eye_tracking_analysis"
OUTPUT_COUNTS_CSV = INPUT_DIR / "fixation_side_counts_by_subject_by_step.csv"
OUTPUT_WINDOWS_CSV = INPUT_DIR / "task_time_windows_from_breakdown.csv"
X_THRESHOLD = 960


RAW_STEP_ROWS = [
    "Step 1 4.768 24.227 6.312 19.85 10.835 45.306 7.107 13.817 11.236 23.843 14.258 21.447 14.561 18.572 11.142 69.595 19.739 34.7 12.639 30.427 4.071 12.062 3.668 9.607 5.046 19.898 6.406 31.329 5.891 44.388 5.982 13.972 9.054 12.309 14.013 16.115 8.88 46.846 3.803 6.555 3.553 13.695 8.189 30.579 4.965 15.586",
    "Step 2 28.995 26.806 26.162 28.306 56.141 73.607 20.924 37.842 35.079 68.381 35.705 55.702 33.133 43.681 80.737 52.489 54.439 43.951 43.066 47.229 16.133 14.805 13.275 19.413 24.944 21.564 37.735 62.132 50.279 20.612 19.954 21.624 21.363 26.368 30.128 56.254 55.726 67.87 10.358 33.873 17.248 50.804 38.768 61.056 20.551 24.72",
    "Step 3 55.801 101.151 54.468 120.089 129.748 204.883 58.766 109.994 103.46 160.19 91.407 75.784 76.814 145.609 133.226 112.521 98.39 119.937 90.295 168.098 30.938 71.994 32.688 79.221 46.508 94.832 99.867 120.752 70.891 104.374 41.578 118.091 47.731 91.228 86.382 157.833 123.596 68.909 44.231 80.56 68.052 152.878 99.824 105.359 45.271 112.89",
    "Step 4 156.952 21.522 174.557 25.773 334.631 39.514 168.76 52.388 263.65 29.912 167.191 20.655 222.423 23.206 245.747 29.035 218.327 33.875 258.393 21.378 102.932 11.114 111.909 17.365 141.34 16.598 220.619 35.711 175.265 40.663 159.669 87.282 138.959 27.365 244.215 28.287 192.505 15.545 124.791 17.687 220.93 17.03 205.183 23.276 158.161 21.506",
    "Step 5 178.474 142.052 200.33 140.623 374.145 147.174 221.148 106.802 293.562 189.564 187.846 79.608 245.629 120.821 274.782 115.013 252.202 109.095 279.771 122.15 114.046 90.339 129.274 62.247 157.938 93.855 256.33 244.892 215.928 86.068 246.951 49.451 166.324 76.688 272.502 110.688 208.05 83.402 142.478 117.145 237.96 123.451 228.459 97.187 179.667 94.517",
    "Step 6 320.526 14.668 340.953 25.014 521.319 33.236 327.95 15.697 483.126 44.063 267.454 13.488 366.45 19.159 389.795 18.66 361.297 21.632 401.921 28.565 204.385 12.877 191.521 11.867 251.793 15.632 501.222 29.588 301.996 27.301 296.402 21.784 243.012 16.706 383.19 15.221 291.452 20.25 259.623 10.823 361.411 21.517 325.646 18.894 274.184 17.539",
    "Step 7 335.194 82.498 365.967 109.175 554.555 114.921 343.647 85.111 527.189 181.355 280.942 115.269 385.609 83.249 408.455 128.293 382.929 133.514 430.486 146.789 217.262 89.379 203.388 81.312 267.425 91.077 530.81 121.688 329.297 121.96 318.186 93.404 259.718 87.12 398.411 91.913 311.702 97.322 270.446 71.693 382.928 118.669 344.54 85.675 291.723 61.467",
    "Step 8 417.692 18.045 475.142 29.717 669.476 22.203 428.758 19.073 708.544 29.979 396.211 11.063 468.858 20.429 536.748 28.637 516.443 19.936 577.275 16.397 306.641 39.841 284.7 12.354 358.502 13.07 NA NA 451.257 26.496 411.59 19.878 346.838 43.075 490.324 13.42 409.024 23.665 342.139 14.755 501.597 26.335 430.215 23.755 353.19 13.105",
    "Step 9 435.737 79.44 504.859 205.342 691.679 168.356 447.831 71.014 738.523 145.551 407.274 88.208 489.287 78.239 565.385 94.296 536.379 128.593 593.672 142.593 346.482 66.716 297.054 58.419 371.572 107.449 652.498 286.217 477.753 144.652 431.468 84.239 389.913 70.621 503.744 88.408 432.689 60.138 356.894 76.547 527.932 89.26 453.97 73.08 366.295 59.188",
    "Step 10 515.177 18.705 710.201 16.419 860.035 24.891 518.845 28.09 884.074 20.675 495.482 15.898 567.526 16.519 659.681 21.147 664.972 15.191 736.265 22.128 413.198 16.828 355.473 14.908 479.021 15.576 938.715 18.894 622.405 42.857 515.707 37.114 460.534 14.95 592.152 41.884 492.827 31.176 433.441 17.005 617.192 32.852 527.05 20.631 425.483 14.96",
    "Step 11 533.882 34.841 726.62 31.982 884.926 123.033 546.935 62.593 904.749 84.317 511.38 30.322 584.045 55.467 680.828 157.326 680.163 70.44 758.393 45.471 430.026 62.955 370.381 38.805 494.597 52.382 957.609 58.064 665.262 66.501 552.821 46.371 475.484 54.287 634.036 51.537 524.003 57.678 450.446 39.977 650.044 65.383 547.681 53.351 440.443 43.789",
    "Step 12 568.723 9.716 758.602 6.132 1007.959 9.133 609.528 19.54 989.066 17.084 541.702 16.123 639.512 17.619 838.154 11.729 750.603 14.451 803.864 17.145 492.981 1.449 409.186 5.697 546.979 9.351 1015.673 20.374 731.763 9.324 599.192 3.513 529.771 4.647 685.573 13.647 581.681 11.267 490.423 11.267 715.427 11.755 601.032 12.225 484.232 60.372",
    "Step 13 578.439 8.394 764.734 8.836 1017.092 18.124 629.068 9.452 1006.15 17.306 557.825 15.635 657.131 9.403 849.883 18.978 765.054 11.801 821.009 9.293 494.43 15.364 414.883 9.09 556.33 10.296 1036.047 16.295 741.087 15.233 602.705 13.985 534.418 24.003 699.22 10.942 592.948 7.166 501.69 10.885 727.182 9.711 613.257 10.645 544.604 16.804",
    "Step 14 586.833 16.191 773.57 23.792 1035.216 36.682 638.52 19.508 1023.456 28.969 573.46 22.144 666.534 21.947 868.861 18.066 776.855 28.261 830.302 42.527 509.794 15.353 423.973 20.392 566.626 15.035 1052.342 22.802 756.32 24.958 616.69 24.076 558.421 14.316 710.162 18.585 600.114 21.849 512.575 17.986 736.893 15.882 623.902 23.499 561.408 14.914",
]


def parse_time_breakdown(rows):
    subjects = [f"Subject{i}" for i in range(1, 24)]
    window_rows = []

    for line in rows:
        m = re.match(r"^Step\s+(\d+)\s+(.*)$", line.strip())
        if not m:
            raise ValueError(f"Could not parse row: {line}")

        step_num = int(m.group(1))
        tokens = re.findall(r"NA|-?\d+(?:\.\d+)?", m.group(2))
        if len(tokens) != 46:
            raise ValueError(
                f"Expected 46 values (23 start/length pairs) for Step {step_num}, got {len(tokens)}"
            )

        for i, subject in enumerate(subjects):
            start_tok = tokens[2 * i]
            length_tok = tokens[2 * i + 1]
            if start_tok == "NA" or length_tok == "NA":
                continue

            start_time = float(start_tok)
            length = float(length_tok)
            end_time = start_time + length

            window_rows.append(
                {
                    "subject": subject,
                    "step_num": step_num,
                    "step_name": f"Step {step_num}",
                    "start_time_sec": start_time,
                    "length_sec": length,
                    "end_time_sec": end_time,
                }
            )

    windows_df = pd.DataFrame(window_rows).sort_values(["subject", "step_num"]).reset_index(drop=True)
    return windows_df


def assign_step(mid_time, subject_windows):
    for _, row in subject_windows.iterrows():
        if row["start_time_sec"] <= mid_time < row["end_time_sec"]:
            return row["step_name"]
    return "Unassigned"


def extract_subject_from_filename(file_stem):
    base = file_stem.replace("_fixations", "")
    if "_red_cross" in base:
        base = base.split("_red_cross")[0]
    return base


def summarize_fixations_by_step(input_dir, windows_df, x_threshold):
    fixation_files = sorted(input_dir.glob("*_fixations.csv"))
    if not fixation_files:
        raise FileNotFoundError(f"No fixation files found in: {input_dir}")

    all_rows = []
    for file_path in fixation_files:
        subject = extract_subject_from_filename(file_path.stem)
        subject_windows = windows_df[windows_df["subject"] == subject].sort_values("step_num")
        if subject_windows.empty:
            print(f"Skipping {file_path.name}: no time windows for {subject}")
            continue

        fix_df = pd.read_csv(file_path)
        required_cols = {"start_time_sec", "end_time_sec", "x_px", "duration_ms"}
        missing = required_cols - set(fix_df.columns)
        if missing:
            raise ValueError(f"Missing required columns {sorted(missing)} in {file_path}")

        fix_df = fix_df.copy()
        fix_df["subject"] = subject
        fix_df["mid_time_sec"] = (fix_df["start_time_sec"] + fix_df["end_time_sec"]) / 2.0
        fix_df["step_name"] = fix_df["mid_time_sec"].apply(lambda t: assign_step(t, subject_windows))
        fix_df["is_left"] = fix_df["x_px"] < x_threshold
        fix_df["is_right"] = fix_df["x_px"] > x_threshold
        fix_df["is_equal"] = fix_df["x_px"] == x_threshold

        grouped = (
            fix_df.groupby(["subject", "step_name"], dropna=False)
            .agg(
                fixations_x_lt_threshold=("is_left", "sum"),
                fixations_x_gt_threshold=("is_right", "sum"),
                fixations_x_eq_threshold=("is_equal", "sum"),
                total_fixations=("x_px", "size"),
                total_fixation_duration_ms=("duration_ms", "sum"),
            )
            .reset_index()
        )

        grouped["x_threshold"] = x_threshold
        grouped["source_file"] = file_path.name

        all_rows.append(grouped)

    if not all_rows:
        return pd.DataFrame()

    out_df = pd.concat(all_rows, ignore_index=True)

    def step_order(step_name):
        m = re.match(r"Step\s+(\d+)$", str(step_name))
        return int(m.group(1)) if m else 999

    out_df["step_sort"] = out_df["step_name"].map(step_order)
    out_df = out_df.sort_values(["subject", "step_sort", "step_name"]).drop(columns=["step_sort"]).reset_index(drop=True)
    return out_df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / INPUT_DIR
    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    windows_df = parse_time_breakdown(RAW_STEP_ROWS)
    windows_df.to_csv(base_dir / OUTPUT_WINDOWS_CSV, index=False)

    summary_df = summarize_fixations_by_step(input_dir, windows_df, X_THRESHOLD)
    if summary_df.empty:
        raise RuntimeError("No summaries were produced. Check fixation files and subject names.")

    summary_df.to_csv(base_dir / OUTPUT_COUNTS_CSV, index=False)

    print(f"Saved task windows: {base_dir / OUTPUT_WINDOWS_CSV}")
    print(f"Saved fixation side counts by step: {base_dir / OUTPUT_COUNTS_CSV}")
    print(f"Rows written: {len(summary_df)}")