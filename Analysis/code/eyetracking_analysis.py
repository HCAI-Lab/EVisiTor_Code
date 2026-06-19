import pandas as pd
import numpy as np
from pathlib import Path

# =========================
# User settings
# =========================
INPUT_DIR = Path("Human Data") / "Eye tracking data"
OUTPUT_DIR = Path("Human Data") / "eye_tracking_analysis"

SCORE_THRESHOLD = 0.01          # keep only detections with score >= this
MAX_INTERP_GAP_FRAMES = 0       # fill very short missing gaps only
SMOOTH_WINDOW = 0               # median smoothing window in samples

MIN_FIX_MS = 150                # minimum fixation duration
DISPERSION_PX = 100              # I-DT spatial threshold in pixels

MERGE_GAP_MS = 100               # merge nearby fixations if the gap is tiny
MERGE_DIST_PX = 100              # and the fixation centers are close

# =========================
# Load + preprocess
# =========================
def load_and_preprocess(csv_path):
    df = pd.read_csv(csv_path).copy()

    required = ["timestamp_sec", "found", "score", "cx", "cy"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.sort_values("timestamp_sec").reset_index(drop=True)

    # Estimate sampling rate
    dt = df["timestamp_sec"].diff().median()
    fps = 1.0 / dt if pd.notna(dt) and dt > 0 else np.nan
    print(f"Estimated sampling rate: {fps:.2f} Hz")

    # Mark bad samples
    good = (df["found"] == 1) & (df["score"] >= SCORE_THRESHOLD)

    df["x_raw"] = df["cx"]
    df["y_raw"] = df["cy"]

    df.loc[~good, ["cx", "cy"]] = np.nan

    # Interpolate only when a positive gap size is configured.
    if MAX_INTERP_GAP_FRAMES > 0:
        df["cx"] = df["cx"].interpolate(
            limit=MAX_INTERP_GAP_FRAMES, limit_direction="both"
        )
        df["cy"] = df["cy"].interpolate(
            limit=MAX_INTERP_GAP_FRAMES, limit_direction="both"
        )

    # Apply smoothing only when window > 1; otherwise keep raw coordinates.
    if SMOOTH_WINDOW > 1:
        df["x"] = df["cx"].rolling(SMOOTH_WINDOW, center=True, min_periods=1).median()
        df["y"] = df["cy"].rolling(SMOOTH_WINDOW, center=True, min_periods=1).median()
    else:
        df["x"] = df["cx"]
        df["y"] = df["cy"]

    df["valid"] = df["x"].notna() & df["y"].notna()

    return df


# =========================
# I-DT fixation detection
# =========================
def window_dispersion(x, y):
    return (np.nanmax(x) - np.nanmin(x)) + (np.nanmax(y) - np.nanmin(y))


def detect_fixations_idt(df, min_fix_ms=100, dispersion_px=50):
    min_fix_sec = min_fix_ms / 1000.0

    x = df["x"].to_numpy()
    y = df["y"].to_numpy()
    t = df["timestamp_sec"].to_numpy()
    valid = df["valid"].to_numpy()

    fixations = []
    i = 0
    n = len(df)

    while i < n:
        if not valid[i]:
            i += 1
            continue

        # Find minimum window that satisfies minimum duration
        j = i
        while j < n and (t[j] - t[i]) < min_fix_sec:
            if not valid[j]:
                break
            j += 1

        if j >= n:
            break

        if not valid[j]:
            i += 1
            continue

        # Check dispersion in the minimum window
        disp = window_dispersion(x[i:j+1], y[i:j+1])

        if disp <= dispersion_px:
            last_good = j
            k = j + 1

            # Expand while dispersion remains below threshold
            while k < n and valid[k]:
                disp_k = window_dispersion(x[i:k+1], y[i:k+1])
                if disp_k <= dispersion_px:
                    last_good = k
                    k += 1
                else:
                    break

            seg = df.iloc[i:last_good+1]

            fixations.append({
                "fixation_id": len(fixations) + 1,
                "start_index": int(seg.index[0]),
                "end_index": int(seg.index[-1]),
                "start_time_sec": float(seg["timestamp_sec"].iloc[0]),
                "end_time_sec": float(seg["timestamp_sec"].iloc[-1]),
                "duration_ms": float(
                    (seg["timestamp_sec"].iloc[-1] - seg["timestamp_sec"].iloc[0]) * 1000
                ),
                "x_px": float(seg["x"].median()),
                "y_px": float(seg["y"].median()),
                "n_samples": int(len(seg)),
                "mean_score": float(seg["score"].mean())
            })

            i = last_good + 1
        else:
            i += 1

    return pd.DataFrame(fixations)


# =========================
# Optional merge step
# =========================
def merge_close_fixations(fix_df, max_gap_ms=75, max_dist_px=50):
    if fix_df.empty:
        return fix_df.copy()

    merged = []
    current = fix_df.iloc[0].to_dict()

    for _, nxt in fix_df.iloc[1:].iterrows():
        gap_ms = (nxt["start_time_sec"] - current["end_time_sec"]) * 1000
        dist = np.sqrt((nxt["x_px"] - current["x_px"])**2 + (nxt["y_px"] - current["y_px"])**2)

        if gap_ms <= max_gap_ms and dist <= max_dist_px:
            total_samples = current["n_samples"] + nxt["n_samples"]

            current["end_index"] = int(nxt["end_index"])
            current["end_time_sec"] = float(nxt["end_time_sec"])
            current["duration_ms"] = (current["end_time_sec"] - current["start_time_sec"]) * 1000

            # weighted center update
            current["x_px"] = (
                current["x_px"] * current["n_samples"] + nxt["x_px"] * nxt["n_samples"]
            ) / total_samples
            current["y_px"] = (
                current["y_px"] * current["n_samples"] + nxt["y_px"] * nxt["n_samples"]
            ) / total_samples
            current["mean_score"] = (
                current["mean_score"] * current["n_samples"] + nxt["mean_score"] * nxt["n_samples"]
            ) / total_samples
            current["n_samples"] = int(total_samples)
        else:
            merged.append(current)
            current = nxt.to_dict()

    merged.append(current)

    out = pd.DataFrame(merged).reset_index(drop=True)
    out["fixation_id"] = np.arange(1, len(out) + 1)
    return out


# =========================
# Label each sample by fixation_id
# =========================
def label_samples(df, fix_df):
    df = df.copy()
    df["fixation_id"] = np.nan

    for _, row in fix_df.iterrows():
        start_idx = int(row["start_index"])
        end_idx = int(row["end_index"])
        df.loc[start_idx:end_idx, "fixation_id"] = int(row["fixation_id"])

    return df


def process_one_file(input_csv_path, output_dir):
    stem = input_csv_path.stem
    output_fixations_csv = output_dir / f"{stem}_fixations.csv"
    output_samples_csv = output_dir / f"{stem}_samples_labeled.csv"

    print(f"\nProcessing: {input_csv_path}")
    df = load_and_preprocess(input_csv_path)

    fix_df = detect_fixations_idt(
        df,
        min_fix_ms=MIN_FIX_MS,
        dispersion_px=DISPERSION_PX
    )

    fix_df = merge_close_fixations(
        fix_df,
        max_gap_ms=MERGE_GAP_MS,
        max_dist_px=MERGE_DIST_PX
    )

    labeled_df = label_samples(df, fix_df)

    fix_df.to_csv(output_fixations_csv, index=False)
    labeled_df.to_csv(output_samples_csv, index=False)

    print("Done.")
    print(f"Number of fixations: {len(fix_df)}")
    if len(fix_df) > 0:
        print("Fixation duration summary (ms):")
        print(fix_df["duration_ms"].describe())
    print(f"Saved: {output_fixations_csv}")
    print(f"Saved: {output_samples_csv}")


# =========================
# Run everything
# =========================
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / INPUT_DIR
    output_dir = base_dir / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    input_files = sorted(input_dir.glob("*.csv"))
    if not input_files:
        raise FileNotFoundError(f"No CSV files found in: {input_dir}")

    print(f"Found {len(input_files)} eye-tracking file(s) in: {input_dir}")
    print(f"Saving analysis outputs to: {output_dir}")

    for input_csv_path in input_files:
        process_one_file(input_csv_path, output_dir)

    print("\nAll files processed.")