import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


KEY_EVENT_RE = re.compile(r"^K\s+(.+)\s+([DU])$")
TYPING_SUBJECT_RE = re.compile(r"^Human Data/Typing Data/subject(\d+)\.csv$", re.IGNORECASE)


@dataclass
class FileStats:
    source_file: str
    total_rows: int = 0
    keyboard_events: int = 0
    raw_down_events: int = 0
    unique_key_presses: int = 0
    repeated_down_while_held: int = 0
    unmatched_up_events: int = 0
    keys_still_held_end: int = 0


def _read_rows(path: Path) -> List[List[str]]:
    encodings = ("utf-8-sig", "utf-8", "latin-1")
    last_error: Optional[Exception] = None

    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return list(csv.reader(f, delimiter="\t"))
        except Exception as exc:  # pragma: no cover - fallback path
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Unable to read file: {path}")


def _get_field(row: List[str], index: Optional[int]) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    return row[index].strip()


def _to_float(value: str) -> Optional[float]:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def process_file(path: Path, root: Path) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], FileStats]:
    rows = _read_rows(path)
    stats = FileStats(source_file=str(path.relative_to(root)).replace("\\", "/"))

    if len(rows) < 2:
        return [], [], stats

    header = [h.strip() for h in rows[1]]
    start_time_idx = header.index("Start Time") if "Start Time" in header else None
    utc_start_idx = header.index("UTC Start Time") if "UTC Start Time" in header else None
    number_idx = header.index("Number") if "Number" in header else None

    held_keys: Set[str] = set()
    raw_down_events: List[Dict[str, object]] = []
    dedup_down_events: List[Dict[str, object]] = []

    for line_number, row in enumerate(rows[2:], start=3):
        stats.total_rows += 1
        code = _get_field(row, 1)
        match = KEY_EVENT_RE.match(code)
        if not match:
            continue

        stats.keyboard_events += 1
        key_name, action = match.group(1), match.group(2)
        event_number = _get_field(row, number_idx)
        start_time_str = _get_field(row, start_time_idx)
        utc_start_str = _get_field(row, utc_start_idx)

        common_event = {
            "source_file": stats.source_file,
            "line_number": line_number,
            "event_number": event_number,
            "code": code,
            "key": key_name,
            "action": action,
            "start_time": start_time_str,
            "utc_start_time": utc_start_str,
            "start_time_sec": _to_float(start_time_str),
            "utc_start_time_sec": _to_float(utc_start_str),
        }

        if action == "D":
            stats.raw_down_events += 1
            is_repeat_while_held = key_name in held_keys
            if is_repeat_while_held:
                stats.repeated_down_while_held += 1
            raw_down_events.append(
                {
                    **common_event,
                    "is_repeat_while_held": is_repeat_while_held,
                }
            )

            if not is_repeat_while_held:
                held_keys.add(key_name)
                stats.unique_key_presses += 1
                dedup_down_events.append(common_event)

        elif action == "U":
            if key_name in held_keys:
                held_keys.remove(key_name)
            else:
                stats.unmatched_up_events += 1

    stats.keys_still_held_end = len(held_keys)
    return raw_down_events, dedup_down_events, stats


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_path = path
    try:
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        output_path = path.with_name(f"{path.stem}_updated{path.suffix}")
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Warning: {path.name} is locked. Wrote {output_path.name} instead.")


def _subject_number_from_source(source_file: str) -> Optional[int]:
    match = TYPING_SUBJECT_RE.match(source_file)
    if not match:
        return None
    return int(match.group(1))


def main() -> None:
    root = Path(__file__).resolve().parent
    data_root = root / "Human Data"
    output_dir = data_root / "key_analysis"

    csv_files = [
        p
        for p in sorted(data_root.rglob("*.csv"))
        if output_dir not in p.parents
    ]
    all_raw_down: List[Dict[str, object]] = []
    all_dedup_down: List[Dict[str, object]] = []
    all_stats: List[FileStats] = []

    for csv_file in csv_files:
        raw_events, dedup_events, stats = process_file(csv_file, root)
        all_raw_down.extend(raw_events)
        all_dedup_down.extend(dedup_events)
        all_stats.append(stats)

    raw_fields = [
        "source_file",
        "line_number",
        "event_number",
        "code",
        "key",
        "action",
        "start_time",
        "utc_start_time",
        "start_time_sec",
        "utc_start_time_sec",
        "is_repeat_while_held",
    ]
    dedup_fields = [
        "source_file",
        "line_number",
        "event_number",
        "code",
        "key",
        "action",
        "start_time",
        "utc_start_time",
        "start_time_sec",
        "utc_start_time_sec",
    ]
    summary_fields = [
        "source_file",
        "total_rows",
        "keyboard_events",
        "raw_down_events",
        "unique_key_presses",
        "repeated_down_while_held",
        "unmatched_up_events",
        "keys_still_held_end",
    ]

    write_csv(output_dir / "key_down_events_raw.csv", all_raw_down, raw_fields)
    write_csv(output_dir / "key_down_events_dedup.csv", all_dedup_down, dedup_fields)
    write_csv(
        output_dir / "keypress_summary_by_file.csv",
        [
            {
                "source_file": s.source_file,
                "total_rows": s.total_rows,
                "keyboard_events": s.keyboard_events,
                "raw_down_events": s.raw_down_events,
                "unique_key_presses": s.unique_key_presses,
                "repeated_down_while_held": s.repeated_down_while_held,
                "unmatched_up_events": s.unmatched_up_events,
                "keys_still_held_end": s.keys_still_held_end,
            }
            for s in all_stats
        ],
        summary_fields,
    )

    # Split deduplicated key presses into one file per typing subject.
    per_subject_events: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for event in all_dedup_down:
        subject_num = _subject_number_from_source(str(event.get("source_file", "")))
        if subject_num is not None:
            per_subject_events[subject_num].append(event)

    per_subject_dir = output_dir / "subjects_dedup"
    typing_subject_numbers = sorted(
        subject_num
        for subject_num in (
            _subject_number_from_source(stats.source_file) for stats in all_stats
        )
        if subject_num is not None
    )

    for subject_num in typing_subject_numbers:
        write_csv(
            per_subject_dir / f"subject{subject_num}_key_presses.csv",
            per_subject_events.get(subject_num, []),
            dedup_fields,
        )

    # Report each user's total key presses (deduplicated while held).
    subject_totals = []
    for stats in all_stats:
        subject_num = _subject_number_from_source(stats.source_file)
        if subject_num is None:
            continue
        subject_totals.append(
            {
                "subject": f"subject{subject_num}",
                "source_file": stats.source_file,
                "total_key_presses": stats.unique_key_presses,
                "raw_key_down_events": stats.raw_down_events,
                "repeated_down_while_held": stats.repeated_down_while_held,
            }
        )

    subject_totals.sort(key=lambda row: int(str(row["subject"]).replace("subject", "")))
    write_csv(
        output_dir / "key_presses_total_by_user.csv",
        subject_totals,
        [
            "subject",
            "source_file",
            "total_key_presses",
            "raw_key_down_events",
            "repeated_down_while_held",
        ],
    )

    total_raw = sum(s.raw_down_events for s in all_stats)
    total_unique = sum(s.unique_key_presses for s in all_stats)
    total_repeats = sum(s.repeated_down_while_held for s in all_stats)
    files_with_keyboard = sum(1 for s in all_stats if s.keyboard_events > 0)

    print("Analysis complete")
    print(f"CSV files scanned: {len(csv_files)}")
    print(f"Files with keyboard events: {files_with_keyboard}")
    print(f"Total key down events (raw): {total_raw}")
    print(f"Total key presses (dedup while held): {total_unique}")
    print(f"Repeated down events while held: {total_repeats}")
    print(f"Per-subject files written: {len(typing_subject_numbers)}")
    print(f"Output folder: {output_dir}")


if __name__ == "__main__":
    main()