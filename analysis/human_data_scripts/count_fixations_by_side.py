from pathlib import Path

import pandas as pd


INPUT_DIR = Path("Human Data") / "eye_tracking_analysis"
OUTPUT_CSV = INPUT_DIR / "fixation_side_counts_by_subject.csv"
X_THRESHOLD = 960


def extract_subject_name(fixation_file_stem):
    name = fixation_file_stem
    if name.endswith("_fixations"):
        name = name[: -len("_fixations")]

    if "_red_cross" in name:
        return name.split("_red_cross")[0]

    return name


def summarize_fixation_sides(input_dir, x_threshold):
    fixation_files = sorted(input_dir.glob("*_fixations.csv"))
    if not fixation_files:
        raise FileNotFoundError(f"No fixation files found in: {input_dir}")

    rows = []
    for file_path in fixation_files:
        df = pd.read_csv(file_path)
        if "x_px" not in df.columns:
            raise ValueError(f"Missing required column 'x_px' in {file_path}")

        subject = extract_subject_name(file_path.stem)
        left_count = int((df["x_px"] < x_threshold).sum())
        right_count = int((df["x_px"] > x_threshold).sum())
        equal_count = int((df["x_px"] == x_threshold).sum())

        rows.append(
            {
                "subject": subject,
                "x_threshold": x_threshold,
                "fixations_x_lt_threshold": left_count,
                "fixations_x_gt_threshold": right_count,
                "fixations_x_eq_threshold": equal_count,
                "total_fixations": int(len(df)),
                "source_file": file_path.name,
            }
        )

    summary_df = pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)
    return summary_df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / INPUT_DIR

    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    summary_df = summarize_fixation_sides(input_dir, X_THRESHOLD)
    summary_df.to_csv(base_dir / OUTPUT_CSV, index=False)

    print(f"Processed {len(summary_df)} subject file(s).")
    print(summary_df[["subject", "fixations_x_lt_threshold", "fixations_x_gt_threshold"]])
    print(f"Saved: {base_dir / OUTPUT_CSV}")