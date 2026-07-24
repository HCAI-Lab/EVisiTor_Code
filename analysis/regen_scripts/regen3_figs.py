import os, glob, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.join(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"G:\ACT-RModels\Spreadsheet\logs"), "ablation_150_formula_latest")
NEW = "2026-07-07"
OUT = os.environ.get("EVISITOR_OUTPUT_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "regen_output_2026-07-07"))
os.makedirs(OUT, exist_ok=True)

H={}; HSD={}
with open(os.path.join(os.environ.get("EVISITOR_HUMAN_DATA_ROOT", r"G:\ExcelDataAnalysis"), "HumanCompletionTime.csv")) as f:
    for row in csv.DictReader(f):
        t=int(row["Step"]); H[t]=float(row["Average length time per task"]); HSD[t]=float(row["standart deviation"])
H=np.array([H[i] for i in range(1,15)]); HSD=np.array([HSD[i] for i in range(1,15)]); Htot=H.sum()

CONDS=[("Perfect",'Ablation_Perfect'),("Visual Search Only",'Ablation_Visual_Search_Only'),
       ("Batched Formula Typing",'Ablation_Batched_Formula_Typing'),
       ("Correction Checking",'Ablation_Correction_Checking'),("Full Realistic",'Ablation_Full_Realistic')]

def load(folder,prefix=NEW):
    rows=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        d={}; p=os.path.join(rd,"task_times.csv")
        if not os.path.exists(p): continue
        with open(p) as f:
            for r in csv.DictReader(f):
                if r["run_id"].startswith(prefix): d[int(r["task"])]=float(r["duration"])
        if len(d)==14: rows.append([d[i] for i in range(1,15)])
    return np.array(rows)

data={name:load(folder) for name,folder in CONDS}

# ---------- Figure 10: ablation bars ----------
labels=["Perfect","Visual\nSearch","Batched\nFormula","Correction\nChecking","Full\nRealistic"]
totals=[data[n].sum(1).mean() for n,_ in CONDS]
sds=[data[n].sum(1).std(ddof=1) for n,_ in CONDS]
pct=[100*(t-Htot)/Htot for t in totals]
fig,ax=plt.subplots(figsize=(8,5))
colors=["#b0b0b0","#7fa8d0","#7fa8d0","#7fa8d0","#2c6fbb"]
bars=ax.bar(labels,totals,yerr=sds,capsize=5,color=colors,edgecolor="black",linewidth=0.6)
ax.axhline(Htot,ls="--",color="crimson",lw=1.5)
ax.text(4.35,Htot+4,f"Human {Htot:.1f} s",color="crimson",ha="right",fontsize=9)
for i,(t,p) in enumerate(zip(totals,pct)):
    ax.text(i,t+sds[i]+6,f"{t:.1f} s\n({p:+.1f}%)",ha="center",va="bottom",fontsize=8)
ax.set_ylabel("Completion time (s)"); ax.set_ylim(450,800)
ax.set_title("Ablation study: completion time by condition (150 runs each)")
plt.tight_layout(); plt.savefig(os.path.join(OUT,"Figure10_ablation.png"),dpi=200); plt.close()

# ---------- Figure 9: 14-subtask human vs realistic vs perfect ----------
R=data["Full Realistic"]; P=data["Perfect"]
Rm,Rs=R.mean(0),R.std(0,ddof=1); Pm,Ps=P.mean(0),P.std(0,ddof=1)
x=np.arange(1,15); w=0.27
fig,ax=plt.subplots(figsize=(11,5.5))
ax.bar(x-w,H,w,yerr=1.96*HSD/math.sqrt(21),capsize=3,label="Human (N=21)",color="#444")
ax.bar(x,Rm,w,yerr=1.96*Rs/math.sqrt(len(R)),capsize=3,label=f"Realistic (N={len(R)})",color="#2c6fbb")
ax.bar(x+w,Pm,w,yerr=1.96*Ps/math.sqrt(len(P)),capsize=3,label=f"Perfect (N={len(P)})",color="#b0b0b0")
ax.set_xticks(x); ax.set_xlabel("Subtask"); ax.set_ylabel("Completion time (s)")
ax.set_title("Mean completion time across 14 subtasks (95% CI)"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(OUT,"Figure9_subtasks.png"),dpi=200); plt.close()

# ---------- tables dump ----------
def metrics(M):
    sm=M.mean(0); diff=sm-H; tot=M.sum(1)
    return dict(r=np.corrcoef(sm,H)[0,1], rmse=math.sqrt((diff**2).mean()),
        nrmse=math.sqrt(((diff/HSD)**2).mean()), abserr=np.abs(diff).mean(),
        total=tot.mean(), totsd=tot.std(ddof=1), modsd=M.std(0,ddof=1).mean(),
        pct=100*(tot.mean()-Htot)/Htot, totdiff=tot.mean()-Htot)

lines=[]
lines.append(f"Human total = {Htot:.1f} s ; avg human subtask SD = {HSD.mean():.3f}\n")
lines.append("TABLE 7/8 (regenerated) — ablation, all 5 conditions, NEW batch vs human 715.4")
lines.append(f"{'Condition':<24}{'Time(s)':>13}{'vsHum':>8}{'r':>8}{'RMSE':>8}{'nRMSE':>8}{'AbsErr':>8}{'ModSD':>8}{'TotDiff':>9}")
for name,_ in CONDS:
    m=metrics(data[name])
    lines.append(f"{name:<24}{m['total']:>8.1f}±{m['totsd']:>4.1f}{m['pct']:>7.1f}%{m['r']:>8.3f}{m['rmse']:>8.2f}{m['nrmse']:>8.3f}{m['abserr']:>8.2f}{m['modsd']:>8.3f}{m['totdiff']:>9.1f}")

for name in ["Full Realistic","Perfect"]:
    M=data[name]; sm=M.mean(0); ss=M.std(0,ddof=1)
    lines.append(f"\nTABLE {'5' if name=='Full Realistic' else '6'} (regenerated) — {name} per-subtask")
    lines.append(f"{'ST':>3}{'Hmean':>9}{'Hsd':>8}{'Mmean':>9}{'Msd':>8}{'Diff':>9}{'AbsErr':>8}{'Diff(SD)':>9}")
    for i in range(14):
        d=sm[i]-H[i]
        lines.append(f"{i+1:>3}{H[i]:>9.2f}{HSD[i]:>8.2f}{sm[i]:>9.2f}{ss[i]:>8.2f}{d:>9.2f}{abs(d):>8.2f}{d/HSD[i]:>9.2f}")

txt="\n".join(lines)
with open(os.path.join(OUT,"regenerated_tables.txt"),"w") as f: f.write(txt)
print(txt)
print(f"\nFigures + tables written to {OUT}")
