"""Summarize an ablation batch directory into a per-condition table.

Usage: python summarize_ablation.py <batch_root> [<out_csv>]
batch_root contains one dir per condition, each with run_XXX/{task_times,keypresses,attention_shifts}.csv
"""
import csv
import math
import sys
from pathlib import Path

ORDER = ["Ablation_Perfect",
         "Ablation_Correction_Checking",
         "Ablation_Visual_Search_Only",
         "Ablation_Batched_Formula_Typing",
         "Ablation_Full_Realistic"]


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def run_total(task_file):
    seen = {}
    with open(task_file, newline="") as fh:
        for row in csv.DictReader(fh):
            seen[int(row["task"])] = float(row["duration"])
    if len(seen) < 14:
        return None
    return sum(seen.values())


def count_rows(path):
    if not path.exists():
        return 0
    with open(path, newline="") as fh:
        return max(0, sum(1 for _ in fh) - 1)


def count_check_shifts(path):
    if not path.exists():
        return 0
    n = 0
    with open(path, newline="") as fh:
        for line in fh:
            if "typed-text-check" in line:
                n += 1
    return n


def main():
    root = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    rows = []
    for cond in ORDER:
        cdir = root / cond
        if not cdir.is_dir():
            continue
        totals, keys, atts, checks = [], [], [], []
        skipped = 0
        for rdir in sorted(cdir.glob("run_*")):
            t = run_total(rdir / "task_times.csv") if (rdir / "task_times.csv").exists() else None
            if t is None:
                skipped += 1
                continue
            totals.append(t)
            keys.append(count_rows(rdir / "keypresses.csv"))
            atts.append(count_rows(rdir / "attention_shifts.csv"))
            checks.append(count_check_shifts(rdir / "attention_shifts.csv"))
        if not totals:
            continue
        rows.append(dict(condition=cond, n=len(totals),
                         mean=round(mean(totals), 2), sd=round(sd(totals), 2),
                         median=round(median(totals), 2),
                         min=round(min(totals), 2), max=round(max(totals), 2),
                         mean_keypresses=round(mean(keys), 1),
                         mean_attentions=round(mean(atts), 1),
                         mean_check_shifts=round(mean(checks), 1),
                         skipped=skipped))
    w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    if out:
        with open(out, "w", newline="") as fh:
            ww = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            ww.writeheader()
            ww.writerows(rows)


if __name__ == "__main__":
    main()
