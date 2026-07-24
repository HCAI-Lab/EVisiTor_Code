#!/usr/bin/env python3
"""Compare model task-completion times against the PSAI human demonstrations.

MODEL side: every live run writes csv_logs/task_times.csv inside its
live_runs/<Task>_<timestamp>/ folder; a data row exists ONLY if the model
finished the whole task (the row's `duration` is ACT-R simulated seconds).
This script pools all completed runs per task and reports n / mean / sd.

Because the model re-reads its instructions from a virtual panel (something
the human demonstrator never did), instruction-panel attention time is
computed per run from csv_logs/attention_shifts.csv (episodes where attention
is on a task<N>/subtask<N>_<M> location, ending at the next shift or at
start-typing) and subtracted: the reported "adj" time and the model/human
ratio are instruction-free. Raw and panel components are also reported.

HUMAN side: each task in task_specs.json carries the `unique_data_id` of the
PSAI demonstration it was templated from. The demonstration's timestamped
event stream is looked up first in the local candidate JSONs (they embed
`events` for some tasks) and then in the dataset clone's parquet shards
(G:\\computer-use-data-psai\\data). Human completion time is defined as
   last input event  -  first input event
where input events are click / press / release / scroll. The leading burst
of `app_opened` rows (process enumeration when recording starts) and the
trailing idle tail are thereby excluded. Each template has ONE demonstration,
so the human column is a single observation, not a mean.

Usage:
  python analyze_task_times.py                # table + model_vs_human_times.csv
  python analyze_task_times.py --runs-dir live_runs --out my.csv
"""

import argparse
import csv
import datetime
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PSAI_ROOT = r"G:\computer-use-data-psai"
LOCAL_EVENT_JSONS = [
    os.path.join(HERE, "..", "candidate_tasks_full.json"),
    os.path.join(HERE, "..", "new_candidate_tasks_full.json"),
]
INPUT_ACTIONS = {"click", "press", "release", "scroll"}

# Instruction-panel locations in attention_shifts.csv are named task<N> /
# subtask<N>_<M>_list; everything else is the real UI.
PANEL_LOCATION_RE = re.compile(r"^(task\d+|subtask\d+_\d+)")


def load_task_specs():
    with open(os.path.join(HERE, "task_specs.json"), encoding="utf-8") as f:
        specs = json.load(f)["tasks"]
    return {t["id"]: t for t in specs}


# ---------------------------------------------------------------------------
# Model times
# ---------------------------------------------------------------------------

def collect_attention_timelines(csv_logs_dir):
    """{(run_id, task): [(model_time, on_panel), ...]} from attention_shifts.csv.

    on_panel is True when visual attention is on the virtual instruction panel.
    start-typing rows inherit the last attended location's (possibly panel)
    name, but the model is typing into the real UI then — never panel time.
    """
    timelines = {}
    path = os.path.join(csv_logs_dir, "attention_shifts.csv")
    if not os.path.isfile(path):
        return timelines
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                t = float(row["model_time"])
            except (KeyError, ValueError):
                continue
            name = (row.get("location_name") or "").strip()
            on_panel = (bool(PANEL_LOCATION_RE.match(name))
                        and row.get("source") != "start-typing")
            timelines.setdefault((row["run_id"], row["task"]), []).append(
                (t, on_panel))
    for events in timelines.values():
        events.sort(key=lambda e: e[0])
    return timelines


def panel_time(events, start, end):
    """Seconds attention spent on the instruction panel within [start, end].

    Attention is on the panel from a panel-directed shift until the next
    shift; a trailing panel episode is capped at the task's end time.
    """
    total = 0.0
    for (t0, on_panel), (t1, _) in zip(events, events[1:]):
        if on_panel:
            total += max(0.0, min(t1, end) - max(t0, start))
    if events and events[-1][1]:
        total += max(0.0, end - max(events[-1][0], start))
    return total


def row_belongs_to_folder(run_id, run_name):
    """True if a CSV row's run_id is the run this live_runs folder was made
    for. Early runner versions started from a csv_logs folder that already
    held rows from previous (possibly offline) sessions, so a folder's CSVs
    can contain stale run_ids — only the run started right after the folder's
    own timestamp is a live run of this folder."""
    fm = re.search(r"(\d{8})_(\d{6})$", run_name)
    rm = re.match(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", run_id)
    if not (fm and rm):
        return False
    folder_t = datetime.datetime.strptime("_".join(fm.groups()), "%Y%m%d_%H%M%S")
    run_t = datetime.datetime(*map(int, rm.groups()))
    return datetime.timedelta(seconds=-60) <= run_t - folder_t <= datetime.timedelta(hours=2)


def completed_run_rows(run_dir):
    """[(run_id, task, start, end, duration), ...] for the folder's own run."""
    path = os.path.join(run_dir, "csv_logs", "task_times.csv")
    run_name = os.path.basename(os.path.normpath(run_dir))
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row_belongs_to_folder(row.get("run_id", ""), run_name):
                continue
            try:
                rows.append((row["run_id"], row["task"],
                             float(row["start_time"]), float(row["end_time"]),
                             float(row["duration"])))
            except (KeyError, ValueError):
                continue
    return rows


def collect_model_times(runs_dir):
    """{task_id: [(duration, panel_seconds, run_name), ...]} from every
    completed live run. panel_seconds is instruction-panel attention time,
    computed from the run's attention_shifts.csv."""
    times = {}
    for run_dir in glob.glob(os.path.join(runs_dir, "*")):
        run_name = os.path.basename(run_dir)
        m = re.match(r"(W\d\d)_", run_name)
        if not m:
            continue
        task_id = m.group(1)
        rows = completed_run_rows(run_dir)
        if not rows:
            continue
        timelines = collect_attention_timelines(os.path.join(run_dir, "csv_logs"))
        for run_id, task, start, end, dur in rows:
            events = timelines.get((run_id, task), [])
            times.setdefault(task_id, []).append(
                (dur, panel_time(events, start, end), run_name))
    return times


# ---------------------------------------------------------------------------
# Human times
# ---------------------------------------------------------------------------

def _as_obj(v):
    """Parquet stores events/metadata as JSON strings; local JSONs vary."""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return None
    return v


def _record(events, metadata):
    events = _as_obj(events) or []
    meta = _as_obj(metadata) or {}
    return {"events": events,
            "screen_w": meta.get("screen_width"),
            "screen_h": meta.get("screen_height")}


def human_duration_from_events(events):
    inputs = [e for e in events if e.get("action") in INPUT_ACTIONS]
    if len(inputs) < 2:
        return None
    return inputs[-1]["time_stamp"] - inputs[0]["time_stamp"]


def collect_human_records(specs):
    """{task_id: {"events": [...], "screen_w": int|None, "screen_h": ...}}
    for every spec whose demonstration can be found locally (candidate JSONs)
    or in the PSAI parquet shards."""
    wanted = {t["unique_data_id"]: tid for tid, t in specs.items()}
    records = {}

    for path in LOCAL_EVENT_JSONS:
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                uid = item.get("unique_data_id")
                if uid in wanted and item.get("events"):
                    rec = _record(item["events"], item.get("metadata"))
                    if rec["events"]:
                        records[wanted[uid]] = rec

    missing = {uid: tid for uid, tid in wanted.items()
               if tid not in records}
    if missing:
        shard_glob = os.path.join(PSAI_ROOT, "data", "*.parquet")
        shards = sorted(glob.glob(shard_glob))
        if not shards:
            print(f"  note: {len(missing)} tasks need the PSAI clone "
                  f"({shard_glob}) which was not found", file=sys.stderr)
        else:
            import pandas as pd
            for shard in shards:
                if not missing:
                    break
                ids = pd.read_parquet(shard, columns=["unique_data_id"])
                hits = set(ids["unique_data_id"]) & set(missing)
                if not hits:
                    continue
                full = pd.read_parquet(
                    shard, columns=["unique_data_id", "events", "metadata"])
                for uid in hits:
                    row = full[full["unique_data_id"] == uid].iloc[0]
                    rec = _record(row["events"], row.get("metadata"))
                    if rec["events"]:
                        records[missing.pop(uid)] = rec
    return records


def collect_human_times(specs):
    """{task_id: duration_seconds}; see collect_human_records."""
    durations = {}
    for tid, rec in collect_human_records(specs).items():
        d = human_duration_from_events(rec["events"])
        if d is not None:
            durations[tid] = d
    return durations


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs-dir", default=os.path.join(HERE, "live_runs"))
    ap.add_argument("--out", default=os.path.join(HERE, "model_vs_human_times.csv"))
    args = ap.parse_args()

    specs = load_task_specs()
    model = collect_model_times(args.runs_dir)
    human = collect_human_times(specs)

    def fmt(v, width, prec=2):
        return f"{v:>{width}.{prec}f}" if v is not None else f"{'-':>{width}}"

    header = (f"{'task':<6} {'name':<32} {'n':>3} {'raw mean':>9} "
              f"{'panel':>6} {'adj mean':>9} {'adj sd':>7} {'human':>8} "
              f"{'adj/human':>10}")
    print(header)
    print("-" * len(header))
    rows = []
    for tid in sorted(specs):
        samples = model.get(tid, [])
        n = len(samples)
        raw = [d for d, _, _ in samples]
        adj = [d - p for d, p, _ in samples]
        raw_mean = statistics.mean(raw) if raw else None
        panel_mean = statistics.mean([p for _, p, _ in samples]) if samples else None
        adj_mean = statistics.mean(adj) if adj else None
        adj_sd = statistics.stdev(adj) if n > 1 else None
        h = human.get(tid)
        ratio = (adj_mean / h) if (adj_mean and h) else None
        print(f"{tid:<6} {specs[tid]['name']:<32} {n:>3} "
              f"{fmt(raw_mean, 9)} {fmt(panel_mean, 6)} {fmt(adj_mean, 9)} "
              f"{fmt(adj_sd, 7)} {fmt(h, 8)} {fmt(ratio, 10)}")
        rows.append({
            "task": tid, "name": specs[tid]["name"],
            "model_n": n,
            "model_raw_mean_s": round(raw_mean, 3) if raw_mean is not None else "",
            "model_panel_mean_s": round(panel_mean, 3) if panel_mean is not None else "",
            "model_adj_mean_s": round(adj_mean, 3) if adj_mean is not None else "",
            "model_adj_sd_s": round(adj_sd, 3) if adj_sd is not None else "",
            "human_s": round(h, 3) if h is not None else "",
            "adj_over_human": round(ratio, 3) if ratio is not None else "",
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwritten: {args.out}")
    print("model times are ACT-R simulated seconds pooled over completed "
          "live runs; human time is the single PSAI demonstration "
          "(first input -> last input).")
    print("'panel' is mean instruction-panel attention time (from "
          "attention_shifts.csv); 'adj' = raw - panel, the instruction-free "
          "time compared against the human, who had no panel to read.")


if __name__ == "__main__":
    main()
