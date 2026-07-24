"""Estimate human per-keystroke typing error rates for the Excel normalization task.

Splits every subject's keystroke stream into:
  - formula segments: first "=" through the following Enter (same convention as
    the existing Typing_Analysis_Report in ExcelDataAnalysis), and
  - word segments: out-of-formula typing runs that are mostly letters (the
    "subject" / "normalization-subject" filename and name entries),
matching the model's actual-word vs formula breakdown.

A keystroke error is not directly observable (we do not know the intended key),
so the rate is estimated from observed corrections:
  - episode rate  = correction episodes / content keystrokes   (primary; one
    run of consecutive Backspaces ~ one typo event, which matches how the
    model repairs each wrong keystroke)
  - deleted rate  = backspace presses / content keystrokes     (upper bound;
    delayed corrections delete correct collateral characters too)

Outputs (written next to this script under logs/human_error_analysis/):
  human_error_rates_by_subject.csv
  human_error_rates_summary.csv
Prints a summary table to stdout.
"""

import csv
import os
from collections import defaultdict

DATA_CANDIDATES = [
    r"G:/ExcelDataAnalysis/Human Data/key_analysis/key_down_events_dedup_updated.csv",
    r"G:/ExcelDataAnalysis/Human Data/key_analysis/key_down_events_dedup.csv",
]
HUMAN_TIME_CSV = r"G:/ExcelDataAnalysis/HumanCompletionTime.csv"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "logs", "human_error_analysis")

NAV_KEYS = {
    "shift", "ctrl", "alt", "caps lock", "home", "end", "insert",
    "page down", "page up", "left arrow", "right arrow", "up arrow",
    "down arrow", "escape", "tab", "windows", "menu", "f1", "f2", "f3",
    "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "delete",
}

NUMPAD_MAP = {
    "numpad multiply": "*", "numpad divide": "/", "numpad plus": "+",
    "numpad minus": "-", "numpad enter": "ENTER", "numpad decimal": ".",
}


def normalize_key(raw):
    """Return one of: 'ENTER', 'BACKSPACE', 'NAV', or a content character."""
    k = raw.strip().lower()
    if not k:
        return "NAV"
    if k == "enter":
        return "ENTER"
    if k == "backspace":
        return "BACKSPACE"
    if k in NAV_KEYS:
        return "NAV"
    if k.startswith("numpad ") or k.startswith("num pad "):
        tail = k.split()[-1]
        if tail.isdigit():
            return tail
        return NUMPAD_MAP.get(k, "NAV")
    if k in NUMPAD_MAP:
        return NUMPAD_MAP[k]
    if len(k) == 1:
        return k  # letters, digits, symbols
    if k == "space":
        return " "
    return "NAV"


def load_events(path):
    """Return {subject: [(time, key), ...]} sorted by file line order."""
    by_subject = defaultdict(list)
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            subject = os.path.splitext(os.path.basename(row["source_file"]))[0]
            key = normalize_key(row["key"])
            try:
                t = float(row["start_time_sec"])
            except (ValueError, KeyError):
                t = 0.0
            line = int(row.get("line_number", 0) or 0)
            by_subject[subject].append((line, t, key))
    for subject in by_subject:
        by_subject[subject].sort()
    return {s: [(t, k) for _line, t, k in evs] for s, evs in by_subject.items()}


def split_segments(events):
    """Split one subject's stream into formula and out-of-formula event lists.

    A formula segment runs from a '=' content key to the next ENTER
    (the '=' itself is included; the terminating ENTER is dropped).
    """
    formula_events, other_events = [], []
    in_formula = False
    for t, k in events:
        if k == "NAV":
            continue
        if in_formula:
            if k == "ENTER":
                in_formula = False
            else:
                formula_events.append((t, k))
        else:
            if k == "=":
                in_formula = True
                formula_events.append((t, k))
            elif k != "ENTER":
                other_events.append((t, k))
    return formula_events, other_events


def word_runs(other_events, gap=10.0, min_len=3, min_letter_frac=0.5):
    """Keep out-of-formula runs that look like word typing.

    Runs split on time gaps; a run qualifies when it has at least `min_len`
    content keys and at least `min_letter_frac` of them are letters, which
    captures the subject / normalization-subject entries and drops stray
    isolated presses.
    """
    runs, current = [], []
    last_t = None
    for t, k in other_events:
        if last_t is not None and t - last_t > gap and current:
            runs.append(current)
            current = []
        current.append((t, k))
        last_t = t
    if current:
        runs.append(current)

    kept = []
    for run in runs:
        content = [k for _t, k in run if k != "BACKSPACE"]
        if len(content) < min_len:
            continue
        letters = sum(1 for k in content if k.isalpha() or k == "-")
        if letters / len(content) >= min_letter_frac:
            kept.append(run)
    return kept


def bucket_stats(events):
    """Count content keys, backspaces, and correction episodes."""
    content = bs = episodes = 0
    prev_bs = False
    for _t, k in events:
        if k == "BACKSPACE":
            bs += 1
            if not prev_bs:
                episodes += 1
            prev_bs = True
        else:
            content += 1
            prev_bs = False
    return content, bs, episodes


def mean_sd(values):
    n = len(values)
    if n == 0:
        return float("nan"), float("nan")
    m = sum(values) / n
    if n == 1:
        return m, float("nan")
    var = sum((v - m) ** 2 for v in values) / (n - 1)
    return m, var ** 0.5


def main():
    data_path = next((p for p in DATA_CANDIDATES if os.path.exists(p)), None)
    if data_path is None:
        raise SystemExit("No key_down_events csv found in ExcelDataAnalysis.")
    os.makedirs(OUT_DIR, exist_ok=True)

    subjects = load_events(data_path)
    rows = []
    for subject, events in sorted(subjects.items()):
        formula_events, other_events = split_segments(events)
        word_events = [ev for run in word_runs(other_events) for ev in run]
        f_content, f_bs, f_ep = bucket_stats(formula_events)
        w_content, w_bs, w_ep = bucket_stats(word_events)
        if f_content == 0 and w_content == 0:
            continue
        rows.append({
            "subject": subject,
            "formula_keys": f_content, "formula_backspaces": f_bs,
            "formula_episodes": f_ep,
            "formula_episode_rate": f_ep / f_content if f_content else None,
            "formula_deleted_rate": f_bs / f_content if f_content else None,
            "word_keys": w_content, "word_backspaces": w_bs,
            "word_episodes": w_ep,
            "word_episode_rate": w_ep / w_content if w_content else None,
            "word_deleted_rate": w_bs / w_content if w_content else None,
        })

    by_subject_path = os.path.join(OUT_DIR, "human_error_rates_by_subject.csv")
    with open(by_subject_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    for bucket in ("formula", "word"):
        for metric in ("episode_rate", "deleted_rate"):
            vals = [r[f"{bucket}_{metric}"] for r in rows
                    if r[f"{bucket}_{metric}"] is not None]
            m, sd = mean_sd(vals)
            pooled_num = sum(r[f"{bucket}_{'episodes' if metric == 'episode_rate' else 'backspaces'}"] for r in rows)
            pooled_den = sum(r[f"{bucket}_keys"] for r in rows)
            summary.append({
                "bucket": bucket, "metric": metric, "n_subjects": len(vals),
                "mean": round(m, 5), "sd": round(sd, 5),
                "pooled": round(pooled_num / pooled_den, 5) if pooled_den else None,
            })

    summary_path = os.path.join(OUT_DIR, "human_error_rates_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    total_keys = {
        "formula": sum(r["formula_keys"] for r in rows),
        "word": sum(r["word_keys"] for r in rows),
    }
    print(f"Data: {data_path}")
    print(f"Subjects with usable keystrokes: {len(rows)}")
    print(f"Total content keystrokes  formula={total_keys['formula']}  "
          f"word={total_keys['word']}")
    print()
    print(f"{'bucket':8} {'metric':14} {'n':>3} {'mean':>8} {'sd':>8} {'pooled':>8}")
    for s in summary:
        print(f"{s['bucket']:8} {s['metric']:14} {s['n_subjects']:>3} "
              f"{s['mean']:>8.4f} {s['sd']:>8.4f} {s['pooled']:>8.4f}")

    if os.path.exists(HUMAN_TIME_CSV):
        with open(HUMAN_TIME_CSV, newline="", encoding="utf-8-sig") as f:
            steps = list(csv.DictReader(f))
        mean_total = sum(float(r["Average length time per task"]) for r in steps)
        var_total = sum(float(r["standart deviation"]) ** 2 for r in steps)
        print(f"\nHuman completion time (sum of 14 step means): "
              f"{mean_total:.1f} s  (sd if steps independent ~{var_total ** 0.5:.1f} s)")

    print(f"\nWrote {by_subject_path}\nWrote {summary_path}")


if __name__ == "__main__":
    main()
