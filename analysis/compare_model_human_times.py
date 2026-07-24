"""Compare model per-task completion times against human data.

Usage: python compare_vischeck.py <batch_dir> [<batch_dir2> ...]
Each batch_dir contains run_XXX/task_times.csv (columns: run_id,task,start_time,end_time,duration).
Human data: G:/ExcelDataAnalysis/HumanCompletionTime.csv (Step, mean, sd) - 14 steps.
"""
import csv
import math
import sys
from pathlib import Path

HUMAN_CSV = Path(r"G:/ExcelDataAnalysis/HumanCompletionTime.csv")


def load_human():
    human = {}
    with open(HUMAN_CSV, newline="") as f:
        for row in csv.DictReader(f):
            step = int(row["Step"])
            human[step] = (float(row["Average length time per task"]),
                           float(row["standart deviation"]))
    return human


def load_batch(batch_dir):
    """Return {task: [durations across runs]} and [total per run]."""
    per_task = {}
    totals = []
    runs = sorted(Path(batch_dir).glob("run_*/task_times.csv"))
    for f in runs:
        total = 0.0
        seen = {}
        with open(f, newline="") as fh:
            for row in csv.DictReader(fh):
                t = int(row["task"])
                d = float(row["duration"])
                seen[t] = d  # keep last row per task if duplicated
        if len(seen) < 14:
            print(f"  WARNING: {f} has only {len(seen)} tasks - skipped")
            continue
        for t, d in seen.items():
            per_task.setdefault(t, []).append(d)
            total += d
        totals.append(total)
    return per_task, totals


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0


def pearson(a, b):
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den


def report(name, batch_dir, human):
    per_task, totals = load_batch(batch_dir)
    if not totals:
        print(f"{name}: no complete runs found in {batch_dir}")
        return None
    tasks = sorted(per_task)
    model_means = [mean(per_task[t]) for t in tasks]
    human_means = [human[t][0] for t in tasks]
    diffs = [m - h for m, h in zip(model_means, human_means)]
    r = pearson(model_means, human_means)
    rmse = math.sqrt(mean([d ** 2 for d in diffs]))
    mape = mean([abs(d) / h for d, h in zip(diffs, human_means)]) * 100
    # tasks within 1 human SD
    within = sum(1 for t, m in zip(tasks, model_means) if abs(m - human[t][0]) <= human[t][1])
    tot_h = sum(human_means)
    tot_m = mean(totals)
    print(f"\n=== {name} (n={len(totals)} runs) ===")
    print(f"{'task':>4} {'human':>8} {'hSD':>7} {'model':>8} {'mSD':>7} {'diff':>8} {'|z|':>5}")
    for t in tasks:
        hm, hs = human[t]
        mm, ms = mean(per_task[t]), sd(per_task[t])
        z = abs(mm - hm) / hs if hs else float("inf")
        print(f"{t:>4} {hm:>8.1f} {hs:>7.1f} {mm:>8.1f} {ms:>7.1f} {mm-hm:>+8.1f} {z:>5.2f}")
    print(f"total human={tot_h:.1f}s  model={tot_m:.1f}s ({(tot_m-tot_h)/tot_h*100:+.1f}%)  runSD={sd(totals):.1f}")
    print(f"r={r:.4f}  R2={r*r:.4f}  RMSE={rmse:.2f}s  MAPE={mape:.1f}%  tasks within 1 human SD: {within}/14")
    return dict(name=name, r=r, rmse=rmse, mape=mape, total=tot_m, n=len(totals))


def main():
    human = load_human()
    for arg in sys.argv[1:]:
        p = Path(arg)
        name = p.parent.name + "/" + p.name
        report(name, p, human)


if __name__ == "__main__":
    main()
