import os, glob, csv, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE=r"G:\ACT-RModels\Spreadsheet\logs\ablation_150_formula_latest"
NEW="2026-07-07"
OUT=r"G:\ACT-RModels\EVisiTor2026\regen_2026-07-07"

H={}; HSD={}
with open(r"G:\ExcelDataAnalysis\HumanCompletionTime.csv") as f:
    for r in csv.DictReader(f):
        t=int(r["Step"]); H[t]=float(r["Average length time per task"]); HSD[t]=float(r["standart deviation"])

CONDS=[("Perfect",'Ablation_Perfect',"no VS"),
       ("Correction Checking",'Ablation_Correction_Checking',"no VS"),
       ("Batched Formula Typing",'Ablation_Batched_Formula_Typing',"no VS"),
       ("Visual Search Only",'Ablation_Visual_Search_Only',"VS"),
       ("Full Realistic",'Ablation_Full_Realistic',"VS")]

def load(folder):
    rows=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        d={}; p=os.path.join(rd,"task_times.csv")
        if not os.path.exists(p): continue
        with open(p) as f:
            for r in csv.DictReader(f):
                if r["run_id"].startswith(NEW): d[int(r["task"])]=float(r["duration"])
        if len(d)==14: rows.append([d[i] for i in range(1,15)])
    return np.array(rows)   # (runs,14)

data={n:load(fo) for n,fo,_ in CONDS}

VS_TASKS=[1,2,11,14]
FORM_TASKS=[3,5,7,9]

def sd_on(M,tasks): return np.array([M[:,t-1].std(ddof=1) for t in tasks])

print("VISUAL-SEARCH TASKS (1,2,11,14): run-to-run SD (individual-differences replication)")
print("Human SD is between-participant SD; model SD is between-run SD.\n")
hdr=f"{'Condition':<24}{'VS?':>5}" + "".join(f"{'T'+str(t):>9}" for t in VS_TASKS) + f"{'avgSD':>9}{'%ofHumanSD':>12}"
print(hdr); print("-"*len(hdr))
Hvs=np.array([HSD[t] for t in VS_TASKS])
print(f"{'HUMAN (target)':<24}{'--':>5}"+"".join(f"{HSD[t]:>9.2f}" for t in VS_TASKS)+f"{Hvs.mean():>9.2f}{'100%':>12}")
print("-"*len(hdr))
rowsout=[]
for name,fo,vs in CONDS:
    sds=sd_on(data[name],VS_TASKS)
    frac=100*sds.mean()/Hvs.mean()
    print(f"{name:<24}{vs:>5}"+"".join(f"{s:>9.2f}" for s in sds)+f"{sds.mean():>9.2f}{frac:>11.1f}%")
    rowsout.append((name,vs,sds,sds.mean(),frac))

# contrast: same conditions on FORMULA tasks (variability there is NOT from visual search)
print("\nCONTROL — FORMULA TASKS (3,5,7,9): SD (visual search should add little here)")
Hf=np.array([HSD[t] for t in FORM_TASKS])
print(f"{'HUMAN':<24}{'--':>5}"+"".join(f"{HSD[t]:>9.2f}" for t in FORM_TASKS)+f"{Hf.mean():>9.2f}")
for name,fo,vs in CONDS:
    sds=sd_on(data[name],FORM_TASKS)
    print(f"{name:<24}{vs:>5}"+"".join(f"{s:>9.2f}" for s in sds)+f"{sds.mean():>9.2f}")

# aggregate: no-VS group vs VS group on visual-search tasks
noVS=[n for n,_,v in CONDS if v=="no VS"]
VS=[n for n,_,v in CONDS if v=="VS"]
noVS_sd=np.mean([sd_on(data[n],VS_TASKS).mean() for n in noVS])
VS_sd=np.mean([sd_on(data[n],VS_TASKS).mean() for n in VS])
print("\n"+"="*70)
print(f"On visual-search tasks (1,2,11,14):")
print(f"  Human between-participant SD (avg)      : {Hvs.mean():6.2f} s")
print(f"  Models WITHOUT visual search (avg SD)   : {noVS_sd:6.2f} s  ({100*noVS_sd/Hvs.mean():4.1f}% of human)")
print(f"  Models WITH your visual search (avg SD) : {VS_sd:6.2f} s  ({100*VS_sd/Hvs.mean():4.1f}% of human)")
print(f"  ==> visual search multiplies replicated variability by {VS_sd/noVS_sd:.0f}x")
print("="*70)

# ---- figure: grouped bars, per VS task, human vs no-VS(Perfect) vs VS(Full Realistic & VS-only) ----
fig,ax=plt.subplots(figsize=(9,5))
x=np.arange(len(VS_TASKS)); w=0.2
ax.bar(x-1.5*w,[HSD[t] for t in VS_TASKS],w,label="Human (between-subject)",color="#333")
ax.bar(x-0.5*w,[data["Perfect"][:,t-1].std(ddof=1) for t in VS_TASKS],w,label="Perfect (no VS)",color="#b0b0b0")
ax.bar(x+0.5*w,[data["Visual Search Only"][:,t-1].std(ddof=1) for t in VS_TASKS],w,label="Visual Search Only",color="#7fa8d0")
ax.bar(x+1.5*w,[data["Full Realistic"][:,t-1].std(ddof=1) for t in VS_TASKS],w,label="Full Realistic (VS)",color="#2c6fbb")
ax.set_xticks(x); ax.set_xticklabels([f"Task {t}" for t in VS_TASKS])
ax.set_ylabel("Completion-time SD (s)")
ax.set_title("Run-to-run variability on visual-search tasks: only visual search reproduces human spread")
ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(OUT,"Figure_VS_variability.png"),dpi=200); plt.close()
print(f"\nsaved {os.path.join(OUT,'Figure_VS_variability.png')}")
