import os, glob, csv, math
import numpy as np

BASE = r"G:\ACT-RModels\Spreadsheet\logs\ablation_150_formula_latest"
PREFIX = "2026-07-07"

CONDITIONS = {
    "Perfect": "Ablation_Perfect",
    "Visual Search Only": "Ablation_Visual_Search_Only",
    "Batched Formula Typing": "Ablation_Batched_Formula_Typing",
    "Correction Checking": "Ablation_Correction_Checking",
    "Full Realistic": "Ablation_Full_Realistic",
}

# ---- human ----
human_mean = {}
human_sd = {}
with open(r"G:\ExcelDataAnalysis\HumanCompletionTime.csv") as f:
    for row in csv.DictReader(f):
        t = int(row["Step"])
        human_mean[t] = float(row["Average length time per task"])
        human_sd[t] = float(row["standart deviation"])
H = np.array([human_mean[i] for i in range(1,15)])
HSD = np.array([human_sd[i] for i in range(1,15)])
H_total = H.sum()

def read_run_tasks(path):
    """return dict task->duration for the 2026-07-07 rows only"""
    d = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            if not row["run_id"].startswith(PREFIX):
                continue
            d[int(row["task"])] = float(row["duration"])
    return d

results = {}
for label, folder in CONDITIONS.items():
    run_dirs = sorted(glob.glob(os.path.join(BASE, folder, "run_*")))
    # per-task matrix: rows=runs, cols=task1..14
    rows = []
    for rd in run_dirs:
        tt = os.path.join(rd, "task_times.csv")
        if not os.path.exists(tt): continue
        d = read_run_tasks(tt)
        if len(d) < 14:   # incomplete new-batch run
            continue
        rows.append([d[i] for i in range(1,15)])
    M = np.array(rows)                       # (nruns, 14)
    nruns = M.shape[0]
    subtask_mean = M.mean(axis=0)
    subtask_sd = M.std(axis=0, ddof=1)
    totals = M.sum(axis=1)
    total_mean = totals.mean()
    total_sd = totals.std(ddof=1)
    diff = subtask_mean - H
    rmse = math.sqrt((diff**2).mean())
    norm_rmse = math.sqrt(((diff/HSD)**2).mean())
    r = np.corrcoef(subtask_mean, H)[0,1]
    results[label] = dict(
        n=nruns, subtask_mean=subtask_mean, subtask_sd=subtask_sd,
        total_mean=total_mean, total_sd=total_sd,
        rmse=rmse, norm_rmse=norm_rmse, r=r,
        model_sd_avg=subtask_sd.mean(),
        pct=100*(total_mean-H_total)/H_total,
        totals=totals,
    )

print(f"HUMAN total = {H_total:.1f} s  (avg subtask SD = {HSD.mean():.3f})\n")
print("="*95)
print(f"{'Condition':<24}{'N':>4}{'Total(s)':>13}{'vsHuman':>9}{'r':>8}{'RMSE':>8}{'nRMSE':>8}{'ModelSD':>9}")
print("="*95)
order = ["Perfect","Visual Search Only","Batched Formula Typing","Correction Checking","Full Realistic"]
for label in order:
    x = results[label]
    print(f"{label:<24}{x['n']:>4}{x['total_mean']:>8.1f}±{x['total_sd']:>4.1f}{x['pct']:>8.1f}%{x['r']:>8.3f}{x['rmse']:>8.2f}{x['norm_rmse']:>8.3f}{x['model_sd_avg']:>9.3f}")
print("="*95)

# ---- per-subtask table for Full Realistic and Perfect ----
for label in ["Full Realistic","Perfect"]:
    x = results[label]
    print(f"\n--- Per-subtask: {label} (N={x['n']}) ---")
    print(f"{'ST':>3}{'Hmean':>9}{'Hsd':>8}{'Mmean':>9}{'Msd':>8}{'Diff':>9}{'AbsErr':>8}{'Diff(SD)':>9}")
    tot_abs=0
    for i in range(14):
        d = x['subtask_mean'][i]-H[i]
        tot_abs += abs(d)
        print(f"{i+1:>3}{H[i]:>9.2f}{HSD[i]:>8.2f}{x['subtask_mean'][i]:>9.2f}{x['subtask_sd'][i]:>8.2f}{d:>9.2f}{abs(d):>8.2f}{d/HSD[i]:>9.2f}")
    print(f"    mean abs err = {tot_abs/14:.3f}")

# ---- save CSV ----
out = r"C:\Users\ITXPC\AppData\Local\Temp\claude\g--ACT-RModels\5ba9268e-db61-4a6f-88ba-ec4498fb8f2b\scratchpad\newbatch_summary.csv"
with open(out,"w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["condition","n","total_mean","total_sd","pct_vs_human","r","rmse","norm_rmse","model_sd_avg"])
    for label in order:
        x=results[label]
        w.writerow([label,x['n'],f"{x['total_mean']:.3f}",f"{x['total_sd']:.3f}",f"{x['pct']:.2f}",f"{x['r']:.4f}",f"{x['rmse']:.3f}",f"{x['norm_rmse']:.4f}",f"{x['model_sd_avg']:.3f}"])
print(f"\nsaved {out}")
