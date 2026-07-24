"""Compare the typo-rate sweep of the Full-Realistic model against human data.

Reads every batch under Spreadsheet/logs/typo_sweep/rate_XXX/ (XXX = rate in
tenths of a percent), plus an optional human-calibrated batch, and produces:

  logs/typo_sweep_analysis/typo_sweep_summary.csv   per-rate aggregate numbers
  logs/typo_sweep_analysis/typo_sweep_summary.md    table incl. human reference
  logs/typo_sweep_analysis/typo_sweep_comparison.png  two-panel figure

Definitions (matched to analyze_human_error_rates.py):
  completion time  = max(end) - min(start) over task_times.csv, per run
  content keystroke = keypress row whose expected key is not shift/enter/delete
  realized error rate = mismatched (expected != typed) / content keystrokes
  formula bucket   = keystrokes inside a task-3..10 subtask window
  word bucket      = keystrokes inside (2,4), (12,2), (13,2), (14,4) windows
                     ((13,2) is "=today()", typed by the word mechanism in the
                     model; in the human segmentation it counts as a formula)
"""

import csv
import glob
import os
import re
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SWEEP_ROOT = os.path.join(HERE, "logs", "typo_sweep")
CALIBRATED_ROOT = os.path.join(HERE, "logs", "calibrated_full_realistic")
HUMAN_SUMMARY = os.path.join(HERE, "logs", "human_error_analysis",
                             "human_error_rates_summary.csv")
HUMAN_TIME_CSV = r"G:/ExcelDataAnalysis/HumanCompletionTime.csv"
OUT_DIR = os.path.join(HERE, "logs", "typo_sweep_analysis")

NON_CONTENT = {"shift", "enter", "return", "delete"}
WORD_SUBTASKS = {(2, 4), (12, 2), (13, 2), (14, 4)}

# Okabe-Ito: colorblind-safe, fixed assignment (entity -> hue, never cycled).
C_MODEL = "#0072B2"     # model completion time / formula series
C_WORD = "#E69F00"      # word series
C_HUMAN = "#555555"     # human reference ink
C_CALIB = "#D55E00"     # calibrated-point accent


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run_completion_time(run_dir):
    rows = read_csv_rows(os.path.join(run_dir, "task_times.csv"))
    if not rows:
        return None
    starts = [float(r["start_time"]) for r in rows if r["start_time"]]
    ends = [float(r["end_time"]) for r in rows if r["end_time"]]
    if len(rows) < 14 or not starts or not ends:
        return None  # incomplete run
    return max(ends) - min(starts)


def run_keystroke_stats(run_dir):
    """Return dict with content/error/backspace counts, overall and by bucket."""
    windows = []
    for r in read_csv_rows(os.path.join(run_dir, "subtask_times.csv")):
        try:
            windows.append((float(r["start_time"]), float(r["end_time"]),
                            int(r["task"]), int(r["subtask"])))
        except (ValueError, KeyError):
            continue

    def bucket_of(t):
        for start, end, task, subtask in windows:
            if start <= t <= end:
                if 3 <= task <= 10:
                    return "formula"
                if (task, subtask) in WORD_SUBTASKS:
                    return "word"
                return "other"
        return "other"

    stats = defaultdict(int)
    for r in read_csv_rows(os.path.join(run_dir, "keypresses.csv")):
        expected = (r["expected_key"] or "").strip().lower()
        typed = (r["typed_key"] or "").strip().lower()
        t = float(r["model_time"])
        if expected == "delete":
            stats["backspaces"] += 1
            continue
        if expected in NON_CONTENT:
            continue
        bucket = bucket_of(t)
        stats["content"] += 1
        stats[f"{bucket}_content"] += 1
        if expected != typed:
            stats["errors"] += 1
            stats[f"{bucket}_errors"] += 1
    return stats


def collect_batch(batch_root):
    """Aggregate all run_* dirs under <batch_root>/Ablation_Full_Realistic/."""
    run_dirs = sorted(glob.glob(os.path.join(batch_root, "*", "run_*")))
    times, totals = [], defaultdict(int)
    for run_dir in run_dirs:
        if not os.path.exists(os.path.join(run_dir, "task_times.csv")):
            continue
        ct = run_completion_time(run_dir)
        if ct is None:
            continue
        times.append(ct)
        for key, value in run_keystroke_stats(run_dir).items():
            totals[key] += value
    if not times:
        return None
    n = len(times)
    result = {
        "n_runs": n,
        "time_mean": float(np.mean(times)),
        "time_sd": float(np.std(times, ddof=1)) if n > 1 else float("nan"),
        "err_overall": totals["errors"] / totals["content"] if totals["content"] else 0.0,
        "backspaces_per_run": totals["backspaces"] / n,
    }
    for bucket in ("formula", "word"):
        content = totals[f"{bucket}_content"]
        result[f"err_{bucket}"] = (totals[f"{bucket}_errors"] / content) if content else 0.0
    return result


def load_human_reference():
    ref = {}
    for r in read_csv_rows(HUMAN_SUMMARY):
        if r["metric"] == "episode_rate":
            ref[f"err_{r['bucket']}"] = float(r["pooled"])
            ref[f"err_{r['bucket']}_sd"] = float(r["sd"])
    steps = read_csv_rows(HUMAN_TIME_CSV)
    ref["time_mean"] = sum(float(r["Average length time per task"]) for r in steps)
    ref["time_sd"] = sum(float(r["standart deviation"]) ** 2 for r in steps) ** 0.5
    return ref


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    human = load_human_reference()

    sweep = []
    for rate_dir in sorted(glob.glob(os.path.join(SWEEP_ROOT, "rate_*"))):
        m = re.search(r"rate_(\d+)$", rate_dir)
        if not m:
            continue
        rate = int(m.group(1)) / 1000.0
        agg = collect_batch(rate_dir)
        if agg:
            agg["rate"] = rate
            sweep.append(agg)
    sweep.sort(key=lambda a: a["rate"])

    calibrated = collect_batch(CALIBRATED_ROOT) if os.path.isdir(CALIBRATED_ROOT) else None

    # ---- summary CSV + markdown ----
    fields = ["label", "rate", "n_runs", "time_mean", "time_sd",
              "time_err_pct", "err_overall", "err_formula", "err_word",
              "backspaces_per_run"]

    def as_row(label, rate, agg):
        return {
            "label": label, "rate": rate, "n_runs": agg["n_runs"],
            "time_mean": round(agg["time_mean"], 1),
            "time_sd": round(agg["time_sd"], 1),
            "time_err_pct": round(100 * (agg["time_mean"] - human["time_mean"])
                                  / human["time_mean"], 1),
            "err_overall": round(agg["err_overall"], 4),
            "err_formula": round(agg["err_formula"], 4),
            "err_word": round(agg["err_word"], 4),
            "backspaces_per_run": round(agg["backspaces_per_run"], 1),
        }

    rows = [as_row(f"{a['rate']:.0%} nominal", a["rate"], a) for a in sweep]
    if calibrated:
        rows.append(as_row("human-calibrated", None, calibrated))

    with open(os.path.join(OUT_DIR, "typo_sweep_summary.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    md = [
        "# Typo-rate sweep: Full-Realistic model vs human data",
        "",
        f"Human reference: completion time {human['time_mean']:.1f} s "
        f"(~{human['time_sd']:.0f} s SD across steps), per-keystroke error "
        f"(correction-episode) rate: formula {human['err_formula']:.1%}, "
        f"word {human['err_word']:.1%}.",
        "",
        "| Condition | Runs | Completion time (s) | vs human | Error rate overall | Formula | Word | Backspaces/run |",
        "|---|---|---|---|---|---|---|---|",
        (f"| **Human (n=19..22 subj)** | — | {human['time_mean']:.1f} | — | — | "
         f"{human['err_formula']:.1%} | {human['err_word']:.1%} | — |"),
    ]
    for r in rows:
        md.append(
            f"| {r['label']} | {r['n_runs']} | {r['time_mean']:.1f} ± {r['time_sd']:.1f} "
            f"| {r['time_err_pct']:+.1f}% | {r['err_overall']:.1%} "
            f"| {r['err_formula']:.1%} | {r['err_word']:.1%} "
            f"| {r['backspaces_per_run']:.1f} |")
    md += [
        "",
        "Notes: model error rates are *realized* rates (mismatched / content "
        "keystrokes) measured from keypresses.csv; the nominal rate is the "
        "per-keystroke injection probability. Human rates are observed "
        "correction episodes per content keystroke (uncorrected errors are "
        "not observable in the keystroke log), so both quantify "
        "corrected-error events per keystroke. The human-calibrated "
        "condition uses the rates measured from the participant data: "
        "formula 3.4%, word 6.3% per keystroke.",
    ]
    with open(os.path.join(OUT_DIR, "typo_sweep_summary.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    # ---- figure ----
    rates_pct = [100 * a["rate"] for a in sweep]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    # Panel A: completion time vs nominal rate
    ax1.axhline(human["time_mean"], color=C_HUMAN, ls="--", lw=1.5)
    ax1.annotate(f"human mean {human['time_mean']:.0f} s", ha="right",
                 xy=(0.98, human["time_mean"]), xycoords=("axes fraction", "data"),
                 xytext=(0, 5), textcoords="offset points",
                 color=C_HUMAN, fontsize=9)
    ax1.errorbar(rates_pct, [a["time_mean"] for a in sweep],
                 yerr=[a["time_sd"] for a in sweep], color=C_MODEL,
                 marker="o", ms=5, lw=2, capsize=3, label="model (mean ± SD)")
    if calibrated:
        ax1.errorbar([100 * 0.034], [calibrated["time_mean"]],
                     yerr=[calibrated["time_sd"]], color=C_CALIB, marker="D",
                     ms=7, lw=0, elinewidth=2, capsize=3,
                     label="human-calibrated rates")
    ax1.set_xlabel("Nominal per-keystroke typo rate (%)")
    ax1.set_ylabel("Task completion time (s)")
    ax1.set_title("Completion time vs typo rate")
    ax1.legend(frameon=False, fontsize=9, loc="upper left")

    # Panel B: realized error rates vs nominal, by bucket
    ax2.axhline(100 * human["err_formula"], color=C_MODEL, ls="--", lw=1.5)
    ax2.annotate(f"human formula {human['err_formula']:.1%}", ha="left",
                 xy=(0.02, 100 * human["err_formula"]),
                 xycoords=("axes fraction", "data"),
                 xytext=(0, 4), textcoords="offset points",
                 color=C_MODEL, fontsize=9)
    ax2.axhline(100 * human["err_word"], color=C_WORD, ls="--", lw=1.5)
    ax2.annotate(f"human word {human['err_word']:.1%}", ha="left",
                 xy=(0.02, 100 * human["err_word"]),
                 xycoords=("axes fraction", "data"),
                 xytext=(0, 4), textcoords="offset points",
                 color=C_WORD, fontsize=9)
    ax2.plot(rates_pct, [100 * a["err_formula"] for a in sweep], color=C_MODEL,
             marker="o", ms=5, lw=2, label="model formula (realized)")
    ax2.plot(rates_pct, [100 * a["err_word"] for a in sweep], color=C_WORD,
             marker="s", ms=5, lw=2, label="model word (realized)")
    if calibrated:
        ax2.plot([3.4], [100 * calibrated["err_formula"]], color=C_CALIB,
                 marker="D", ms=7, lw=0)
        ax2.plot([6.3], [100 * calibrated["err_word"]], color=C_CALIB,
                 marker="D", ms=7, lw=0, label="human-calibrated rates")
    ax2.set_xlabel("Nominal per-keystroke typo rate (%)")
    ax2.set_ylabel("Realized per-keystroke error rate (%)")
    ax2.set_title("Keystroke error rate vs typo rate")
    ax2.legend(frameon=False, fontsize=9, loc="upper left")

    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#dddddd", lw=0.6)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig_path = os.path.join(OUT_DIR, "typo_sweep_comparison.png")
    fig.savefig(fig_path, dpi=200)
    print("Wrote", os.path.join(OUT_DIR, "typo_sweep_summary.csv"))
    print("Wrote", os.path.join(OUT_DIR, "typo_sweep_summary.md"))
    print("Wrote", fig_path)
    print()
    with open(os.path.join(OUT_DIR, "typo_sweep_summary.md"), encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    main()
