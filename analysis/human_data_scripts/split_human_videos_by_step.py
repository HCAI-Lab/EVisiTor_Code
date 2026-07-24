from __future__ import annotations

import argparse
import csv
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


BASE_DIR = Path(__file__).resolve().parent
VIDEO_ROOT = BASE_DIR / "HumanData_Video"
WINDOWS_CSV = BASE_DIR / "Human Data" / "eye_tracking_analysis" / "task_time_windows_from_breakdown.csv"
OUTPUT_ROOT = VIDEO_ROOT / "subtask_videos"
MANIFEST_CSV = OUTPUT_ROOT / "subtask_video_manifest.csv"

VIDEO_EXTENSIONS = [".wmv", ".mp4", ".mov", ".avi", ".mkv", ".m4v"]
SUBJECT_RE = re.compile(r"^Subject(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class StepWindow:
    subject: str
    step_num: int
    start_time_sec: float
    length_sec: float
    end_time_sec: float


@dataclass(frozen=True)
class VideoPart:
    part_num: int
    path: Path


@dataclass(frozen=True)
class SubjectVideo:
    subject: str
    subject_num: int
    parts: list[VideoPart]
    source_rank: tuple[int, int, str]


@dataclass(frozen=True)
class ResolvedPart:
    part_num: int
    path: Path
    start_time_sec: float
    duration_sec: float
    end_time_sec: float


@dataclass(frozen=True)
class ClipSegment:
    source: Path
    source_start_sec: float
    duration_sec: float


def parse_subject(value: str) -> int | None:
    match = SUBJECT_RE.match(value)
    if not match:
        return None
    return int(match.group(1))


def load_step_windows(path: Path) -> dict[str, list[StepWindow]]:
    if not path.exists():
        raise FileNotFoundError(f"Task-window CSV not found: {path}")

    windows: dict[str, list[StepWindow]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"subject", "step_num", "start_time_sec", "length_sec", "end_time_sec"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

        for row in reader:
            subject = row["subject"]
            windows.setdefault(subject, []).append(
                StepWindow(
                    subject=subject,
                    step_num=int(row["step_num"]),
                    start_time_sec=float(row["start_time_sec"]),
                    length_sec=float(row["length_sec"]),
                    end_time_sec=float(row["end_time_sec"]),
                )
            )

    for subject_windows in windows.values():
        subject_windows.sort(key=lambda item: item.step_num)

    return windows


def candidate_subject_dirs(include_nested: bool) -> list[Path]:
    dirs: list[Path] = []
    dirs.extend(path for path in VIDEO_ROOT.iterdir() if path.is_dir() and parse_subject(path.name) is not None)

    if include_nested:
        nested_root = VIDEO_ROOT / "Subjects-withoutVideo"
        if nested_root.exists():
            dirs.extend(path for path in nested_root.iterdir() if path.is_dir() and parse_subject(path.name) is not None)

    return dirs


def video_candidates_for_part(subject_dir: Path, subject_num: int, part_num: int) -> list[Path]:
    stem = f"Subject{subject_num}"
    if part_num > 1:
        stem = f"{stem}-{part_num}"
    return [subject_dir / f"{stem}{extension}" for extension in VIDEO_EXTENSIONS]


def find_video_part(subject_dir: Path, subject_num: int, part_num: int) -> tuple[int, Path] | None:
    for extension_rank, candidate in enumerate(video_candidates_for_part(subject_dir, subject_num, part_num)):
        if candidate.exists():
            return extension_rank, candidate
    return None


def discover_parts_in_dir(subject_dir: Path, subject_num: int) -> tuple[int, list[VideoPart]] | None:
    first = find_video_part(subject_dir, subject_num, part_num=1)
    if first is None:
        return None

    first_rank, first_path = first
    parts_by_num: dict[int, tuple[int, Path]] = {1: (first_rank, first_path)}
    continuation_re = re.compile(rf"^Subject{subject_num}-(\d+)\.([^.]+)$", re.IGNORECASE)

    for file_path in subject_dir.iterdir():
        if not file_path.is_file():
            continue

        match = continuation_re.match(file_path.name)
        if not match:
            continue

        part_num = int(match.group(1))
        extension = f".{match.group(2).lower()}"
        if extension not in VIDEO_EXTENSIONS:
            continue

        extension_rank = VIDEO_EXTENSIONS.index(extension)
        current = parts_by_num.get(part_num)
        if current is None or extension_rank < current[0]:
            parts_by_num[part_num] = (extension_rank, file_path)

    parts = [
        VideoPart(part_num=part_num, path=path)
        for part_num, (_extension_rank, path) in sorted(parts_by_num.items())
    ]
    return first_rank, parts


def discover_subject_videos(include_nested: bool) -> dict[str, SubjectVideo]:
    discovered: dict[str, SubjectVideo] = {}

    for subject_dir in candidate_subject_dirs(include_nested):
        subject_num = parse_subject(subject_dir.name)
        if subject_num is None:
            continue

        parts_info = discover_parts_in_dir(subject_dir, subject_num)
        if parts_info is None:
            continue

        first_rank, parts = parts_info
        subject = f"Subject{subject_num}"
        folder_rank = 0 if subject_dir.parent == VIDEO_ROOT else 1
        rank = (folder_rank, first_rank, str(parts[0].path).lower())
        current = discovered.get(subject)
        if current is None or rank < current.source_rank:
            discovered[subject] = SubjectVideo(subject, subject_num, parts, rank)

    return dict(sorted(discovered.items(), key=lambda item: item[1].subject_num))


def ffprobe_duration(video_path: Path) -> float | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    text = result.stdout.strip()
    if not text or text == "N/A":
        return None
    return float(text)


def split_clip(source: Path, output: Path, start_sec: float, duration_sec: float, force: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if force else "-n",
        "-ss",
        f"{start_sec:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration_sec:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def concat_file_line(path: Path) -> str:
    escaped = str(path).replace("\\", "/").replace("'", "'\\''")
    return f"file '{escaped}'\n"


def split_segments(segments: list[ClipSegment], output: Path, force: bool) -> None:
    if not segments:
        raise ValueError(f"No source segments supplied for {output}")

    if len(segments) == 1:
        segment = segments[0]
        split_clip(segment.source, output, segment.source_start_sec, segment.duration_sec, force)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f"{output.stem}_", dir=output.parent) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_outputs: list[Path] = []

        for index, segment in enumerate(segments, start=1):
            temp_output = temp_dir / f"part{index:02d}.mp4"
            split_clip(segment.source, temp_output, segment.source_start_sec, segment.duration_sec, force=True)
            temp_outputs.append(temp_output)

        concat_list = temp_dir / "concat.txt"
        concat_list.write_text("".join(concat_file_line(path) for path in temp_outputs), encoding="utf-8")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y" if force else "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(output),
        ]
        subprocess.run(cmd, check=True)


def resolve_video_parts(video: SubjectVideo) -> list[ResolvedPart]:
    resolved: list[ResolvedPart] = []
    current_start = 0.0

    for part in video.parts:
        duration = ffprobe_duration(part.path)
        if duration is None:
            raise ValueError(f"Could not determine duration for {part.path}")

        end_time = current_start + duration
        resolved.append(
            ResolvedPart(
                part_num=part.part_num,
                path=part.path,
                start_time_sec=current_start,
                duration_sec=duration,
                end_time_sec=end_time,
            )
        )
        current_start = end_time

    return resolved


def clip_segments_for_window(window: StepWindow, parts: list[ResolvedPart]) -> list[ClipSegment]:
    segments: list[ClipSegment] = []

    for part in parts:
        overlap_start = max(window.start_time_sec, part.start_time_sec)
        overlap_end = min(window.end_time_sec, part.end_time_sec)
        duration = overlap_end - overlap_start
        if duration <= 0.001:
            continue

        segments.append(
            ClipSegment(
                source=part.path,
                source_start_sec=overlap_start - part.start_time_sec,
                duration_sec=duration,
            )
        )

    return segments


def unique_source_text(paths: list[Path]) -> str:
    unique_paths = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        unique_paths.append(str(path.relative_to(BASE_DIR)))
        seen.add(path)
    return "; ".join(unique_paths)


def parse_subject_filter(values: list[str] | None) -> set[str] | None:
    if not values:
        return None

    subjects: set[str] = set()
    for value in values:
        for piece in value.split(","):
            piece = piece.strip()
            if not piece:
                continue
            if piece.lower().startswith("subject"):
                num = parse_subject(piece)
            else:
                num = int(piece)
            if num is None:
                raise ValueError(f"Could not parse subject filter: {piece}")
            subjects.add(f"Subject{num}")
    return subjects


def write_manifest(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "subject",
        "step_num",
        "source_video",
        "output_video",
        "start_time_sec",
        "length_sec",
        "end_time_sec",
        "video_duration_sec",
        "clip_duration_sec",
        "status",
        "message",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split HumanData_Video subject videos into per-step clips using task_time_windows_from_breakdown.csv."
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing step clips.")
    parser.add_argument("--dry-run", action="store_true", help="Create the manifest without running ffmpeg.")
    parser.add_argument(
        "--no-nested",
        action="store_true",
        help="Only scan top-level HumanData_Video/SubjectN folders.",
    )
    parser.add_argument(
        "--subjects",
        nargs="*",
        help="Optional subject filter, e.g. --subjects 1 2 17 or --subjects Subject1,Subject2.",
    )
    args = parser.parse_args()

    selected_subjects = parse_subject_filter(args.subjects)
    windows_by_subject = load_step_windows(WINDOWS_CSV)
    videos_by_subject = discover_subject_videos(include_nested=not args.no_nested)

    manifest_rows: list[dict[str, object]] = []
    processed = 0
    skipped = 0

    subjects = sorted(videos_by_subject, key=lambda value: int(value.replace("Subject", "")))
    for subject in subjects:
        if selected_subjects is not None and subject not in selected_subjects:
            continue

        video = videos_by_subject[subject]
        windows = windows_by_subject.get(subject, [])
        if not windows:
            print(f"Skipping {subject}: no task windows")
            continue

        try:
            resolved_parts = resolve_video_parts(video)
        except Exception as exc:
            resolved_parts = []
            video_duration = None
            probe_error = str(exc)
        else:
            video_duration = resolved_parts[-1].end_time_sec if resolved_parts else 0.0
            probe_error = ""

        source_text = unique_source_text([part.path for part in video.parts])
        print(f"{subject}: {source_text}")
        for window in windows:
            output = OUTPUT_ROOT / subject / f"{subject}_step{window.step_num:02d}.mp4"
            status = "created"
            message = ""
            segments = [] if probe_error else clip_segments_for_window(window, resolved_parts)
            clip_duration = sum(segment.duration_sec for segment in segments)

            if probe_error:
                status = "error"
                message = f"ffprobe failed: {probe_error}"
            elif not segments:
                status = "skipped"
                message = "start time is beyond source video duration"
                clip_duration = 0.0
            elif clip_duration < window.length_sec - 0.01:
                status = "truncated"
                message = "step window extends beyond source video duration"
            elif len(segments) > 1:
                message = f"used {len(segments)} source video parts"

            if status in {"created", "truncated"} and output.exists() and not args.force:
                status = "exists"
                message = "output already exists; use --force to overwrite"

            if args.dry_run and status in {"created", "truncated"}:
                status = "dry-run"
                message = "ffmpeg not run"

            if status in {"created", "truncated"}:
                try:
                    split_segments(segments, output, force=args.force)
                except subprocess.CalledProcessError as exc:
                    status = "error"
                    message = f"ffmpeg failed with exit code {exc.returncode}"

            if status in {"created", "truncated", "dry-run", "exists"}:
                processed += 1
            else:
                skipped += 1

            print(f"  step {window.step_num:02d}: {status} -> {output.name}")
            manifest_rows.append(
                {
                    "subject": subject,
                    "step_num": window.step_num,
                    "source_video": unique_source_text([segment.source for segment in segments])
                    if segments
                    else source_text,
                    "output_video": str(output.relative_to(BASE_DIR)),
                    "start_time_sec": f"{window.start_time_sec:.3f}",
                    "length_sec": f"{window.length_sec:.3f}",
                    "end_time_sec": f"{window.end_time_sec:.3f}",
                    "video_duration_sec": "" if video_duration is None else f"{video_duration:.3f}",
                    "clip_duration_sec": f"{clip_duration:.3f}",
                    "status": status,
                    "message": message,
                }
            )

    write_manifest(manifest_rows, MANIFEST_CSV)
    print(f"Manifest: {MANIFEST_CSV}")
    print(f"Clip rows handled: {processed}; skipped/errors: {skipped}")


if __name__ == "__main__":
    main()
