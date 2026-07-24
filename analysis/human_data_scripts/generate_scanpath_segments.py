from __future__ import annotations

from collections import deque
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
MAX_HISTORY_POINTS = 120
POINT_RADIUS = 5
LINE_THICKNESS = 2


def clamp_point(x: float, y: float, width: int, height: int) -> tuple[int, int] | None:
    if not np.isfinite(x) or not np.isfinite(y):
        return None
    xi = int(round(x))
    yi = int(round(y))
    if xi < 0 or yi < 0 or xi >= width or yi >= height:
        return None
    return xi, yi


def draw_scanpath_overlay(frame: np.ndarray, history: deque[tuple[int, int]]) -> np.ndarray:
    out = frame.copy()
    points = list(history)
    n = len(points)

    if n >= 2:
        for idx in range(1, n):
            p0 = points[idx - 1]
            p1 = points[idx]
            age = idx / (n - 1)
            # Blue-to-red gradient in BGR space for path aging.
            color = (
                int((1.0 - age) * 255),
                int(180 * age),
                int(age * 255),
            )
            cv2.line(out, p0, p1, color, LINE_THICKNESS, lineType=cv2.LINE_AA)

    if n > 0:
        for idx, p in enumerate(points[:-1]):
            age = (idx + 1) / max(1, n)
            radius = max(2, int(POINT_RADIUS * (0.4 + 0.6 * age)))
            cv2.circle(out, p, radius, (0, 220, 255), -1, lineType=cv2.LINE_AA)

        # Highlight most recent gaze point.
        cv2.circle(out, points[-1], POINT_RADIUS + 2, (0, 0, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(out, points[-1], POINT_RADIUS + 5, (255, 255, 255), 1, lineType=cv2.LINE_AA)

    return out


def process_segment(base_dir: Path, out_dir: Path, segment: Segment) -> tuple[Path, Path]:
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
    grouped = {int(k): g for k, g in df.groupby("frame_index")}

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

    output_video = out_dir / f"{subject_name}_scanpath_{start}_{end}.mp4"
    output_last = out_dir / f"{subject_name}_scanpath_{start}_{end}_last.png"

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

    history: deque[tuple[int, int]] = deque(maxlen=MAX_HISTORY_POINTS)
    last_frame = None

    for frame_idx in range(start, end + 1):
        ok, frame = cap.read()
        if not ok:
            break

        rows = grouped.get(frame_idx)
        if rows is not None and not rows.empty:
            # Use median of all valid detections in this frame.
            cx = float(rows["cx"].median())
            cy = float(rows["cy"].median())
            point = clamp_point(cx, cy, width, height)
            if point is not None:
                history.append(point)

        overlay = draw_scanpath_overlay(frame, history)
        writer.write(overlay)
        last_frame = overlay

    cap.release()
    writer.release()

    if last_frame is None:
        raise RuntimeError(f"No frames rendered for {subject_name} segment {start}-{end}")

    cv2.imwrite(str(output_last), last_frame)
    return output_video, output_last


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "HumanData_Video" / "scanpath_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving outputs to: {out_dir}")
    for seg in SEGMENTS:
        print(f"Processing Subject{seg.subject}: frames {seg.start_frame}-{seg.end_frame}")
        out_video, out_last = process_segment(base_dir, out_dir, seg)
        print(f"  video: {out_video}")
        print(f"  last frame: {out_last}")

    print("Done.")


if __name__ == "__main__":
    main()