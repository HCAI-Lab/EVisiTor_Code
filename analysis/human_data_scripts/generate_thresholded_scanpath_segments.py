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


@dataclass(frozen=True)
class FixationPoint:
    start_frame: int
    end_frame: int
    x: int
    y: int
    n_frames: int


SEGMENTS: list[Segment] = [
    Segment(subject=2, start_frame=1109, end_frame=1288),
    Segment(subject=11, start_frame=604, end_frame=759),
    Segment(subject=18, start_frame=2009, end_frame=2268),
    Segment(subject=19, start_frame=3329, end_frame=3436),
]

SCORE_THRESHOLD = 0.01
MIN_STABLE_FRAMES = 5
CLOSE_RADIUS_PX = 40.0
MAX_HISTORY_POINTS = 160
POINT_RADIUS = 12
LINE_THICKNESS = 1
NUMBER_FONT = cv2.FONT_HERSHEY_SIMPLEX
NUMBER_FONT_SCALE = 0.45
NUMBER_FONT_THICKNESS = 1


def clamp_point(x: float, y: float, width: int, height: int) -> tuple[int, int] | None:
    if not np.isfinite(x) or not np.isfinite(y):
        return None
    xi = int(round(x))
    yi = int(round(y))
    if xi < 0 or yi < 0 or xi >= width or yi >= height:
        return None
    return xi, yi


def cluster_center(cluster: list[tuple[int, float, float]]) -> tuple[float, float]:
    xs = [p[1] for p in cluster]
    ys = [p[2] for p in cluster]
    return float(np.median(xs)), float(np.median(ys))


def cluster_is_close(cluster: list[tuple[int, float, float]], x: float, y: float) -> bool:
    cx, cy = cluster_center(cluster)
    return float(np.hypot(x - cx, y - cy)) <= CLOSE_RADIUS_PX


def finalize_cluster(
    cluster: list[tuple[int, float, float]],
    width: int,
    height: int,
) -> FixationPoint | None:
    if len(cluster) < MIN_STABLE_FRAMES:
        return None

    x, y = cluster_center(cluster)
    point = clamp_point(x, y, width, height)
    if point is None:
        return None

    return FixationPoint(
        start_frame=int(cluster[0][0]),
        end_frame=int(cluster[-1][0]),
        x=point[0],
        y=point[1],
        n_frames=len(cluster),
    )


def find_thresholded_points(
    grouped: dict[int, pd.DataFrame],
    start: int,
    end: int,
    width: int,
    height: int,
) -> list[FixationPoint]:
    points: list[FixationPoint] = []
    cluster: list[tuple[int, float, float]] = []

    def close_current_cluster() -> None:
        nonlocal cluster
        fixation = finalize_cluster(cluster, width, height)
        if fixation is not None:
            points.append(fixation)
        cluster = []

    for frame_idx in range(start, end + 1):
        rows = grouped.get(frame_idx)
        if rows is None or rows.empty:
            close_current_cluster()
            continue

        x = float(rows["cx"].median())
        y = float(rows["cy"].median())
        if clamp_point(x, y, width, height) is None:
            close_current_cluster()
            continue

        if not cluster:
            cluster = [(frame_idx, x, y)]
            continue

        if cluster_is_close(cluster, x, y):
            cluster.append((frame_idx, x, y))
        else:
            close_current_cluster()
            cluster = [(frame_idx, x, y)]

    close_current_cluster()
    return points


def draw_numbered_dot(
    frame: np.ndarray,
    point: tuple[int, int],
    label: int,
    is_current: bool,
) -> None:
    text = str(label)
    radius = POINT_RADIUS + (2 if len(text) >= 3 else 0)
    fill_color = (0, 0, 255) if is_current else (0, 220, 255)
    outline_color = (255, 255, 255) if is_current else (20, 20, 20)
    text_color = (255, 255, 255) if is_current else (20, 20, 20)

    cv2.circle(frame, point, radius, fill_color, -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, point, radius + 2, outline_color, 1, lineType=cv2.LINE_AA)

    (text_width, text_height), baseline = cv2.getTextSize(
        text,
        NUMBER_FONT,
        NUMBER_FONT_SCALE,
        NUMBER_FONT_THICKNESS,
    )
    text_x = int(point[0] - text_width / 2)
    text_y = int(point[1] + (text_height - baseline) / 2)
    cv2.putText(
        frame,
        text,
        (text_x, text_y),
        NUMBER_FONT,
        NUMBER_FONT_SCALE,
        text_color,
        NUMBER_FONT_THICKNESS,
        lineType=cv2.LINE_AA,
    )


def draw_scanpath_overlay(
    frame: np.ndarray,
    history: deque[tuple[int, int, int]],
    pending: list[tuple[int, FixationPoint]],
) -> np.ndarray:
    out = frame.copy()
    points = list(history)
    n = len(points)
    pending_labels = {label for label, _ in pending}

    if n >= 2:
        for idx in range(1, n):
            p0 = (points[idx - 1][0], points[idx - 1][1])
            p1 = (points[idx][0], points[idx][1])
            age = idx / (n - 1)
            color = (
                int((1.0 - age) * 255),
                int(180 * age),
                int(age * 255),
            )
            cv2.line(out, p0, p1, color, LINE_THICKNESS, lineType=cv2.LINE_AA)

    for x, y, label in points:
        is_current = label == points[-1][2]
        draw_numbered_dot(out, (x, y), label, is_current)

    for label, fixation in pending:
        if label in pending_labels:
            cv2.circle(
                out,
                (fixation.x, fixation.y),
                POINT_RADIUS + 7,
                (255, 255, 255),
                1,
                lineType=cv2.LINE_AA,
            )

    return out


def process_segment(base_dir: Path, out_dir: Path, segment: Segment) -> tuple[Path, Path, Path]:
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

    fixation_points = find_thresholded_points(grouped, start, end, width, height)
    points_by_end: dict[int, list[tuple[int, FixationPoint]]] = {p.end_frame: [] for p in fixation_points}
    for label, point in enumerate(fixation_points, start=1):
        points_by_end[point.end_frame].append((label, point))

    output_video = out_dir / f"{subject_name}_scanpath_threshold5_{start}_{end}.mp4"
    output_last = out_dir / f"{subject_name}_scanpath_threshold5_{start}_{end}_last.png"
    output_points = out_dir / f"{subject_name}_scanpath_threshold5_{start}_{end}_points.csv"

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

    history: deque[tuple[int, int, int]] = deque(maxlen=MAX_HISTORY_POINTS)
    last_frame = None

    for frame_idx in range(start, end + 1):
        ok, frame = cap.read()
        if not ok:
            break

        new_points = points_by_end.get(frame_idx, [])
        for label, point in new_points:
            history.append((point.x, point.y, label))

        overlay = draw_scanpath_overlay(frame, history, new_points)
        writer.write(overlay)
        last_frame = overlay

    cap.release()
    writer.release()

    if last_frame is None:
        raise RuntimeError(f"No frames rendered for {subject_name} segment {start}-{end}")

    cv2.imwrite(str(output_last), last_frame)
    pd.DataFrame(
        [
            {
                "subject": subject_name,
                "start_frame": p.start_frame,
                "end_frame": p.end_frame,
                "x": p.x,
                "y": p.y,
                "n_frames": p.n_frames,
                "min_stable_frames": MIN_STABLE_FRAMES,
                "close_radius_px": CLOSE_RADIUS_PX,
            }
            for p in fixation_points
        ]
    ).to_csv(output_points, index=False)

    return output_video, output_last, output_points


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "HumanData_Video" / "scanpath_threshold5_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving outputs to: {out_dir}")
    print(f"Using at least {MIN_STABLE_FRAMES} close frames within {CLOSE_RADIUS_PX:g}px.")
    for seg in SEGMENTS:
        print(f"Processing Subject{seg.subject}: frames {seg.start_frame}-{seg.end_frame}")
        out_video, out_last, out_points = process_segment(base_dir, out_dir, seg)
        print(f"  video: {out_video}")
        print(f"  last frame: {out_last}")
        print(f"  points: {out_points}")

    print("Done.")


if __name__ == "__main__":
    main()
