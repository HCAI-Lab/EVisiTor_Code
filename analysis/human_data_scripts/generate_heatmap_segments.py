from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Segment:
    subject: int
    start_frame: int
    end_frame: int


SEGMENTS: list[Segment] = [
    Segment(subject=2, start_frame=1400, end_frame=1656),
    Segment(subject=17, start_frame=2020, end_frame=2090),
    Segment(subject=18, start_frame=2458, end_frame=2619),
    Segment(subject=19, start_frame=3578, end_frame=3745),
]

SCORE_THRESHOLD = 0.01
KERNEL_SIZE = 121
KERNEL_SIGMA = 22.0
HEAT_ALPHA = 0.45
MIN_VISIBLE_HEAT_FRACTION = 0.08


def gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    axis = np.arange(size, dtype=np.float32) - (size - 1) / 2.0
    xx, yy = np.meshgrid(axis, axis)
    kernel = np.exp(-(xx * xx + yy * yy) / (2.0 * sigma * sigma))
    radius = (size - 1) / 2.0
    kernel[(xx * xx + yy * yy) > (radius * radius)] = 0.0
    return kernel.astype(np.float32)


def add_kernel(heat: np.ndarray, kernel: np.ndarray, x: float, y: float) -> None:
    h, w = heat.shape
    kh, kw = kernel.shape
    half_h = kh // 2
    half_w = kw // 2

    cx = int(round(x))
    cy = int(round(y))

    x0 = max(0, cx - half_w)
    y0 = max(0, cy - half_h)
    x1 = min(w, cx + half_w + 1)
    y1 = min(h, cy + half_h + 1)

    if x0 >= x1 or y0 >= y1:
        return

    kx0 = x0 - (cx - half_w)
    ky0 = y0 - (cy - half_h)
    kx1 = kx0 + (x1 - x0)
    ky1 = ky0 + (y1 - y0)

    heat[y0:y1, x0:x1] += kernel[ky0:ky1, kx0:kx1]


def colorize_heat(heat: np.ndarray) -> np.ndarray:
    max_val = float(heat.max())
    if max_val <= 0.0:
        return np.zeros((heat.shape[0], heat.shape[1], 3), dtype=np.uint8)

    min_visible_heat = max_val * MIN_VISIBLE_HEAT_FRACTION
    positive_mask = heat >= min_visible_heat
    norm = np.zeros_like(heat, dtype=np.uint8)
    norm[positive_mask] = np.clip((heat[positive_mask] / max_val) * 255.0, 0, 255).astype(np.uint8)

    heat_color = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    heat_color[~positive_mask] = 0
    return heat_color


def overlay_heat(frame: np.ndarray, heat_color: np.ndarray, alpha: float) -> np.ndarray:
    mask = np.any(heat_color > 0, axis=2)
    out = frame.copy()
    if np.any(mask):
        blended = cv2.addWeighted(frame, 1.0 - alpha, heat_color, alpha, 0.0)
        out[mask] = blended[mask]
    return out


def process_segment(base_dir: Path, out_dir: Path, segment: Segment, kernel: np.ndarray) -> tuple[Path, Path, Path]:
    subject_name = f"Subject{segment.subject}"
    video_path = base_dir / "HumanData_Video" / subject_name / f"{subject_name}.wmv"
    csv_path = base_dir / "Human Data" / "Eye tracking data" / f"{subject_name}_red_cross.csv"

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"Eye-tracking CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required_cols = {"frame_index", "found", "score", "cx", "cy"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {csv_path.name}: {sorted(missing)}")

    df = df[(df["frame_index"] >= segment.start_frame) & (df["frame_index"] <= segment.end_frame)]
    df = df[(df["found"] == 1) & (df["score"] >= SCORE_THRESHOLD)]
    grouped = df.groupby("frame_index")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    start = max(0, segment.start_frame)
    end = min(segment.end_frame, total_frames - 1)
    if end < start:
        cap.release()
        raise ValueError(f"Invalid frame range for {subject_name}: {segment.start_frame}-{segment.end_frame}")

    output_video = out_dir / f"{subject_name}_heatmap_{start}_{end}.mp4"
    output_last_overlay = out_dir / f"{subject_name}_heatmap_{start}_{end}_last_overlay.png"
    output_last_heat = out_dir / f"{subject_name}_heatmap_{start}_{end}_last_heatmap.png"

    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create output video: {output_video}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, float(start))

    heat = np.zeros((height, width), dtype=np.float32)
    last_overlay = None
    last_heat = None

    for frame_idx in range(start, end + 1):
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx in grouped.groups:
            rows = grouped.get_group(frame_idx)
            for _, row in rows.iterrows():
                x = float(row["cx"])
                y = float(row["cy"])
                if np.isfinite(x) and np.isfinite(y):
                    add_kernel(heat, kernel, x, y)

        heat_color = colorize_heat(heat)
        overlay = overlay_heat(frame, heat_color, HEAT_ALPHA)

        writer.write(overlay)
        last_overlay = overlay
        last_heat = heat_color

    cap.release()
    writer.release()

    if last_overlay is None or last_heat is None:
        raise RuntimeError(f"No frames rendered for {subject_name} segment {start}-{end}")

    cv2.imwrite(str(output_last_overlay), last_overlay)
    cv2.imwrite(str(output_last_heat), last_heat)

    return output_video, output_last_overlay, output_last_heat


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "HumanData_Video" / "heatmap_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    kernel = gaussian_kernel(KERNEL_SIZE, KERNEL_SIGMA)

    print(f"Saving outputs to: {out_dir}")
    for seg in SEGMENTS:
        print(f"Processing Subject{seg.subject}: frames {seg.start_frame}-{seg.end_frame}")
        out_video, out_overlay, out_heat = process_segment(base_dir, out_dir, seg, kernel)
        print(f"  video: {out_video}")
        print(f"  last overlay: {out_overlay}")
        print(f"  last heatmap: {out_heat}")

    print("Done.")


if __name__ == "__main__":
    main()
