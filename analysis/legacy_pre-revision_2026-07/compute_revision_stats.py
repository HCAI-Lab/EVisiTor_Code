"""Revision statistics for Draft23 (2026-07-14).

Part 1: Uncertainty quantification for the realistic-vs-perfect comparison
  (reviewer themes B: R1#9, R2#6, R3#2):
  - 10,000-resample percentile bootstrap over the 14 subtasks for r, RMSE,
    SD-normalized RMSE, mean |error|, and the realistic-perfect differences.
  - Paired Wilcoxon signed-rank test on per-subtask |error| (realistic vs
    perfect) + matched-pairs rank-biserial effect size.
  - Steiger's z test for the dependent correlations (secondary).

Part 2: Typo-rate sweep extension (reviewer theme C: R1#3, R2#7, R3#3):
  - Per nominal rate: pooled P(correction) over formula entries and
    per-subtask RMSE vs human means, computed from the raw sweep runs in
    Spreadsheet/logs/typo_sweep/rate_*/Ablation_Full_Realistic/run_*/.
  - Two-panel figure: RMSE vs rate, P(correction) vs rate (human 25.0% line).

Also re-verifies the ablation-batch Full-Realistic pooled P(correction) and
backspaces/run quoted in the paper (run_id filtered to 2026-07-07*).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(r"g:\ACT-RModels\EVisiTor2026\revision_2026-07-14")
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- Part 1
# Per-subtask values from regen_2026-07-07/regenerated_tables.txt (verified
# against Spreadsheet/logs/ablation_150_formula_latest, 2026-07-07 rows).
SUBTASKS = list(range(1, 15))
H_MEAN = np.array([25.02, 42.38, 117.09, 28.87, 111.85, 20.89, 105.02, 22.25,
                   108.51, 22.75, 61.46, 13.81, 13.15, 22.34])
H_SD = np.array([15.44, 18.38, 35.41, 16.31, 42.32, 7.91, 27.46, 8.72,
                 55.99, 8.98, 28.95, 11.63, 4.28, 7.01])
REAL = np.array([39.19, 22.78, 104.91, 19.32, 105.00, 19.54, 149.31, 18.83,
                 127.71, 19.68, 41.23, 9.38, 11.49, 21.77])
PERF = np.array([5.98, 11.95, 78.51, 14.60, 78.30, 15.00, 117.23, 14.43,
                 102.16, 15.23, 13.85, 8.55, 10.80, 19.84])

def metrics(model, hm, hs):
    err = model - hm
    r = np.corrcoef(model, hm)[0, 1]
    rmse = float(np.sqrt(np.mean(err ** 2)))
    nrmse = float(np.sqrt(np.mean((err / hs) ** 2)))
    mae = float(np.mean(np.abs(err)))
    return r, rmse, nrmse, mae

rng = np.random.default_rng(20260714)
N_BOOT = 10_000
n = len(SUBTASKS)

boot = {k: [] for k in ["r_real", "r_perf", "rmse_real", "rmse_perf",
                        "nrmse_real", "nrmse_perf", "mae_real", "mae_perf",
                        "d_rmse", "d_nrmse", "d_mae", "d_r"]}
for _ in range(N_BOOT):
    idx = rng.integers(0, n, n)
    hm, hs, re_, pe = H_MEAN[idx], H_SD[idx], REAL[idx], PERF[idx]
    if np.std(hm) == 0 or np.std(re_) == 0 or np.std(pe) == 0:
        continue
    rr, rmr, nrr, mar = metrics(re_, hm, hs)
    rp, rmp, nrp, map_ = metrics(pe, hm, hs)
    boot["r_real"].append(rr); boot["r_perf"].append(rp)
    boot["rmse_real"].append(rmr); boot["rmse_perf"].append(rmp)
    boot["nrmse_real"].append(nrr); boot["nrmse_perf"].append(nrp)
    boot["mae_real"].append(mar); boot["mae_perf"].append(map_)
    boot["d_rmse"].append(rmr - rmp); boot["d_nrmse"].append(nrr - nrp)
    boot["d_mae"].append(mar - map_); boot["d_r"].append(rr - rp)

def ci(v):
    a = np.asarray(v)
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))

point = {}
point["real"] = metrics(REAL, H_MEAN, H_SD)
point["perf"] = metrics(PERF, H_MEAN, H_SD)

report = {"n_boot_effective": len(boot["d_rmse"]), "point": point,
          "ci": {k: ci(v) for k, v in boot.items()}}

# Wilcoxon signed-rank on paired |errors|
abs_r = np.abs(REAL - H_MEAN)
abs_p = np.abs(PERF - H_MEAN)
w = stats.wilcoxon(abs_r, abs_p, alternative="two-sided", mode="exact")
diffs = abs_r - abs_p
n_pairs = np.sum(diffs != 0)
rank_sum_total = n_pairs * (n_pairs + 1) / 2
# matched-pairs rank-biserial: r = (W+ - W-) / total rank sum
ranks = stats.rankdata(np.abs(diffs[diffs != 0]))
w_plus = ranks[diffs[diffs != 0] > 0].sum()
w_minus = ranks[diffs[diffs != 0] < 0].sum()
rank_biserial = (w_plus - w_minus) / rank_sum_total
report["wilcoxon_abs_err"] = {
    "W": float(w.statistic), "p": float(w.pvalue),
    "n_pairs": int(n_pairs),
    "realistic_lower_on": int(np.sum(abs_r < abs_p)),
    "rank_biserial": float(rank_biserial),
    "median_abs_err_real": float(np.median(abs_r)),
    "median_abs_err_perf": float(np.median(abs_p)),
}

# Steiger's z for dependent correlations (both models vs same human vector)
r12 = np.corrcoef(REAL, H_MEAN)[0, 1]   # realistic vs human
r13 = np.corrcoef(PERF, H_MEAN)[0, 1]   # perfect vs human
r23 = np.corrcoef(REAL, PERF)[0, 1]     # realistic vs perfect
det = 1 - r12**2 - r13**2 - r23**2 + 2 * r12 * r13 * r23
rbar = (r12 + r13) / 2
t_num = (r12 - r13) * math.sqrt((n - 1) * (1 + r23))
t_den = math.sqrt(2 * det * (n - 1) / (n - 3) + rbar**2 * (1 - r23)**3)
t_stat = t_num / t_den
p_steiger = 2 * (1 - stats.t.cdf(abs(t_stat), df=n - 3))
report["steiger"] = {"r_realistic": float(r12), "r_perfect": float(r13),
                     "r_models": float(r23), "t": float(t_stat),
                     "df": n - 3, "p": float(p_steiger)}

# ---------------------------------------------------------------- Part 2
SWEEP = Path(r"g:\ACT-RModels\Spreadsheet\logs\typo_sweep")
CMD_KEYS = {"shift", "delete", "enter", "return", "escape", "tab"}

def formula_entries(kp):
    """Split a run's keypresses into formula-entry segments '=' .. enter."""
    segs, cur, in_seg = [], None, False
    for _, row in kp.iterrows():
        k = str(row["delivered_key"]).lower()
        exp = str(row["expected_key"]).lower()
        if not in_seg and exp == "=":
            in_seg, cur = True, {"n_del": 0}
        elif in_seg:
            if exp in ("enter", "return"):
                segs.append(cur); in_seg, cur = False, None
            elif exp == "delete" or k == "delete":
                cur["n_del"] += 1
    if in_seg and cur is not None:
        segs.append(cur)
    return segs

sweep_rows = []
for rate_dir in sorted(SWEEP.glob("rate_*")):
    rate = int(rate_dir.name.split("_")[1]) / 10.0  # rate_030 -> 3.0 %
    cond = rate_dir / "Ablation_Full_Realistic"
    per_task, entries, entries_bs, n_runs, bs_total = {}, 0, 0, 0, 0
    for run in sorted(cond.glob("run_*")):
        tt = pd.read_csv(run / "task_times.csv")
        # keep only 2026-07-07+ rows (append-gotcha hygiene)
        tt = tt[tt["run_id"].astype(str).str.startswith("2026-07")]
        if tt.empty or tt["task"].nunique() < 14:
            continue
        n_runs += 1
        for _, row in tt.iterrows():
            per_task.setdefault(int(row["task"]), []).append(row["duration"])
        kp = pd.read_csv(run / "keypresses.csv")
        kp = kp[kp["run_id"].astype(str).str.startswith("2026-07")]
        segs = formula_entries(kp)
        entries += len(segs)
        entries_bs += sum(1 for s in segs if s["n_del"] > 0)
        bs_total += int((kp["expected_key"].astype(str).str.lower() == "delete").sum())
    model_means = np.array([np.mean(per_task[t]) for t in SUBTASKS])
    err = model_means - H_MEAN
    sweep_rows.append({
        "nominal_pct": rate, "n_runs": n_runs,
        "total_time": float(model_means.sum()),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "nrmse": float(np.sqrt(np.mean((err / H_SD) ** 2))),
        "p_corr_pct": 100 * entries_bs / entries if entries else float("nan"),
        "entries": entries, "entries_with_bs": entries_bs,
        "backspaces_per_run": bs_total / n_runs if n_runs else float("nan"),
    })
report["sweep"] = sweep_rows

# --- ablation-batch Full Realistic: verify P(correction) & backspaces/run
AB = Path(r"g:\ACT-RModels\Spreadsheet\logs\ablation_150_formula_latest\Ablation_Full_Realistic")
entries, entries_bs, n_runs, bs_total = 0, 0, 0, 0
for run in sorted(AB.glob("run_*")):
    f = run / "keypresses.csv"
    if not f.exists():
        continue
    kp = pd.read_csv(f)
    kp = kp[kp["run_id"].astype(str).str.startswith("2026-07-07")]
    if kp.empty:
        continue
    n_runs += 1
    segs = formula_entries(kp)
    entries += len(segs)
    entries_bs += sum(1 for s in segs if s["n_del"] > 0)
    bs_total += int((kp["expected_key"].astype(str).str.lower() == "delete").sum())
report["ablation_full_realistic"] = {
    "n_runs": n_runs, "entries": entries, "entries_with_bs": entries_bs,
    "p_corr_pct": 100 * entries_bs / entries if entries else None,
    "backspaces_per_run": bs_total / n_runs if n_runs else None,
}

with open(OUT / "revision_stats.json", "w") as f:
    json.dump(report, f, indent=2)

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sw = pd.DataFrame(sweep_rows).sort_values("nominal_pct")
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
ax = axes[0]
ax.plot(sw["nominal_pct"], sw["rmse"], "o-", color="#1f77b4")
ax.axvspan(3.35, 6.28, color="#dddddd", alpha=0.5, zorder=0)
ax.set_xlabel("Nominal per-keystroke typo rate (%)")
ax.set_ylabel("Per-subtask RMSE vs human (s)")
ax.set_title("(a) Model-human RMSE")
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(sw["nominal_pct"], sw["p_corr_pct"], "s-", color="#d62728",
        label="Model P(correction)")
ax.axhline(25.0, ls="--", color="black", label="Human 25.0 %")
ax.axvspan(3.35, 6.28, color="#dddddd", alpha=0.5, zorder=0,
           label="Measured human rates")
ax.set_xlabel("Nominal per-keystroke typo rate (%)")
ax.set_ylabel("P(correction) over formula entries (%)")
ax.set_title("(b) Correction probability")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "Figure_sweep_rmse_pcorr.png", dpi=300)
print(json.dumps(report, indent=2)[:4000])
print("...\nSWEEP TABLE:")
print(sw.to_string(index=False))
