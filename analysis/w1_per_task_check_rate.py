"""Per-task Wasserstein-1 (W1) comparison of check-rate conditions.

Follows the published method of EVisiTor2026/revision_2026-07-17/
w1_participant_bootstrap.py exactly (same human file, same 21-complete-subject
analysis set, same participant/run resampling bootstrap), but reports
PER-TASK ΔW1 with bootstrap CIs/p-values for each pairwise comparison of
conditions, so we can say which condition statistically improves which tasks
rather than relying on aggregate RMSE/MAE.

Conditions:
  base     paper instant-check Full-Realistic 150-run batch
           (ablation_150_formula_latest, run_id 2026-07-07*)
  rate_040 final-check model, formula visual check probability 0.40
  rate_100 final-check model, formula visual check probability 1.00
           (both: Spreadsheet/logs/final_check_150_merged, run_id 2026-07*)

Output: printed tables + Spreadsheet/logs/final_check_150_merged/
w1_per_task.json
"""
import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

SUBTASKS = list(range(1, 15))
N_BOOT = 10_000
MERGED = Path(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"g:\ACT-RModels\Spreadsheet\logs")) / "final_check_150_merged"
BASE_LOGS = Path(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"g:\ACT-RModels\Spreadsheet\logs")) / "ablation_150_formula_latest"

# ---- human side (identical to w1_participant_bootstrap.py) -----------------
hw = pd.read_csv(str(Path(os.environ.get("EVISITOR_HUMAN_DATA_ROOT", r"G:\ExcelDataAnalysis"))
                     / "Human Data" / "eye_tracking_analysis"
                     / "task_time_windows_from_breakdown.csv"))
piv = hw.pivot_table(index="subject", columns="step_num", values="length_sec")
H = piv.drop(["Subject1", "Subject14"]).dropna().values
assert H.shape == (21, 14), H.shape


def runs_matrix(batch_dir, prefix):
    rows = []
    for run in sorted(Path(batch_dir).glob("run_*")):
        f = run / "task_times.csv"
        if not f.exists():
            continue
        tt = pd.read_csv(f)
        tt = tt[tt["run_id"].astype(str).str.startswith(prefix)]
        if tt.empty or tt["task"].nunique() < 14:
            continue
        s = tt.set_index("task")["duration"]
        rows.append([s[t] for t in SUBTASKS])
    return np.array(rows)


MERGED_PAPER = Path(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"g:\ACT-RModels\Spreadsheet\logs")) / "final_check_150_paper_merged"

CONDS = {
    "base": runs_matrix(BASE_LOGS / "Ablation_Full_Realistic", "2026-07-07"),
    "rate_040": runs_matrix(MERGED / "rate_040" / "Ablation_Full_Realistic",
                            "2026-07"),
    "rate_100": runs_matrix(MERGED / "rate_100" / "Ablation_Full_Realistic",
                            "2026-07"),
}
# paper-typo-rate variants (formula 3.4% / word 6.3%), when present
for tag in ("rate_040", "rate_100"):
    d = MERGED_PAPER / tag / "Ablation_Full_Realistic"
    if d.is_dir():
        CONDS[tag + "_paper"] = runs_matrix(d, "2026-07")
for name, M in CONDS.items():
    print(f"{name}: {M.shape[0]} runs")

# ---- point estimates -------------------------------------------------------
w1 = {name: np.array([wasserstein_distance(H[:, i], M[:, i])
                      for i in range(14)])
      for name, M in CONDS.items()}
w1_tot = {name: float(wasserstein_distance(H.sum(1), M.sum(1)))
          for name, M in CONDS.items()}

# ---- bootstrap: shared resamples across conditions -------------------------
rng = np.random.default_rng(20260720)
nH = H.shape[0]
boot = {name: np.empty((N_BOOT, 14)) for name in CONDS}
boot_tot = {name: np.empty(N_BOOT) for name in CONDS}
for b in range(N_BOOT):
    Hb = H[rng.integers(0, nH, nH)]
    for name, M in CONDS.items():
        Mb = M[rng.integers(0, M.shape[0], M.shape[0])]
        boot[name][b] = [wasserstein_distance(Hb[:, i], Mb[:, i])
                         for i in range(14)]
        boot_tot[name][b] = wasserstein_distance(Hb.sum(1), Mb.sum(1))


def ci(v):
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def p_boot(v):
    return float(2 * min((v >= 0).mean(), (v <= 0).mean()))


PAIRS = [("rate_100", "rate_040"), ("rate_040", "base"), ("rate_100", "base")]
if "rate_040_paper" in CONDS:
    PAIRS += [
        ("rate_040_paper", "base"),        # same typo rates: isolates policy
        ("rate_100_paper", "base"),
        ("rate_100_paper", "rate_040_paper"),  # winner check, paper rates
        ("rate_040", "rate_040_paper"),    # isolates the typo-rate change
    ]
report = {"n_runs": {k: int(v.shape[0]) for k, v in CONDS.items()},
          "w1_per_task": {k: [round(float(x), 2) for x in v]
                          for k, v in w1.items()},
          "w1_total": w1_tot,
          "mean_w1": {k: float(v.mean()) for k, v in w1.items()},
          "pairs": {}}

for a, b in PAIRS:
    d = boot[a] - boot[b]           # ΔW1 per task, negative = a closer
    d_pt = w1[a] - w1[b]
    rows = []
    print(f"\n=== ΔW1 per task: {a} − {b}  (negative = {a} closer to human) ===")
    print(f"{'task':>4} {'W1('+a+')':>12} {'W1('+b+')':>12} {'ΔW1':>7} "
          f"{'CI95':>18} {'p':>7} {'sig':>4}")
    for i, t in enumerate(SUBTASKS):
        c = ci(d[:, i])
        p = p_boot(d[:, i])
        sig = ("*" if p < 0.05 else "") + ("*" if p < 0.01 else "")
        rows.append({"task": t, "w1_a": round(float(w1[a][i]), 2),
                     "w1_b": round(float(w1[b][i]), 2),
                     "d": round(float(d_pt[i]), 2),
                     "ci95": [round(x, 2) for x in c],
                     "p_boot": round(p, 4)})
        print(f"{t:>4} {w1[a][i]:>12.2f} {w1[b][i]:>12.2f} {d_pt[i]:>+7.2f} "
              f"[{c[0]:>+7.2f},{c[1]:>+7.2f}] {p:>7.4f} {sig:>4}")
    d_mean = d.mean(axis=1)
    d_tot = boot_tot[a] - boot_tot[b]
    sig_better = [r["task"] for r in rows if r["p_boot"] < 0.05 and r["d"] < 0]
    sig_worse = [r["task"] for r in rows if r["p_boot"] < 0.05 and r["d"] > 0]
    summary = {
        "per_task": rows,
        "tasks_sig_better_a": sig_better,
        "tasks_sig_worse_a": sig_worse,
        "closer_on_n_tasks": int((d_pt < 0).sum()),
        "mean_dW1": {"point": float(d_pt.mean()), "ci95": ci(d_mean),
                     "p_boot": p_boot(d_mean)},
        "total_dW1": {"point": float(w1_tot[a] - w1_tot[b]),
                      "ci95": ci(d_tot), "p_boot": p_boot(d_tot)},
    }
    report["pairs"][f"{a}_vs_{b}"] = summary
    print(f"  {a} closer on {summary['closer_on_n_tasks']}/14 tasks; "
          f"sig better on {sig_better}, sig worse on {sig_worse}")
    print(f"  mean ΔW1 {summary['mean_dW1']['point']:+.2f} "
          f"CI {summary['mean_dW1']['ci95']} p={summary['mean_dW1']['p_boot']:.4f}; "
          f"total ΔW1 {summary['total_dW1']['point']:+.2f} "
          f"CI {summary['total_dW1']['ci95']} p={summary['total_dW1']['p_boot']:.4f}")

with open(MERGED / "w1_per_task.json", "w") as f:
    json.dump(report, f, indent=1)
print(f"\nwritten: {MERGED / 'w1_per_task.json'}")
