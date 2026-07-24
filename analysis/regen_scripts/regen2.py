import os, glob, csv, math
import numpy as np

BASE = r"G:\ACT-RModels\Spreadsheet\logs\ablation_150_formula_latest"
OLD, NEW = "2026-05-28", "2026-07-07"

# human
H={}; HSD={}
with open(r"G:\ExcelDataAnalysis\HumanCompletionTime.csv") as f:
    for row in csv.DictReader(f):
        t=int(row["Step"]); H[t]=float(row["Average length time per task"]); HSD[t]=float(row["standart deviation"])
H=np.array([H[i] for i in range(1,15)]); HSD=np.array([HSD[i] for i in range(1,15)]); Htot=H.sum()

def batch_metrics(folder, prefix):
    rows=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        d={}
        p=os.path.join(rd,"task_times.csv")
        if not os.path.exists(p): continue
        with open(p) as f:
            for r in csv.DictReader(f):
                if r["run_id"].startswith(prefix): d[int(r["task"])]=float(r["duration"])
        if len(d)==14: rows.append([d[i] for i in range(1,15)])
    M=np.array(rows); sm=M.mean(0); totals=M.sum(1)
    diff=sm-H
    return dict(n=len(rows), total=totals.mean(), total_sd=totals.std(ddof=1),
        pct=100*(totals.mean()-Htot)/Htot, r=np.corrcoef(sm,H)[0,1],
        rmse=math.sqrt((diff**2).mean()), nrmse=math.sqrt(((diff/HSD)**2).mean()),
        abserr=np.abs(diff).mean(), modsd=M.std(0,ddof=1).mean())

def typing_metrics(folder, prefix):
    """per-run typo count, backspace/correction count, realized content error rate,
       and P(correction)=fraction of formula entries containing >=1 backspace."""
    typos=[]; backs=[]; content=[]; pcorr=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        p=os.path.join(rd,"keypresses.csv")
        if not os.path.exists(p): continue
        seq=[]
        with open(p) as f:
            for r in csv.DictReader(f):
                if not r["run_id"].startswith(prefix): continue
                seq.append((r["expected_key"], r["typed_key"]))
        if not seq: continue
        t=sum(1 for e,ty in seq if e!=ty and e.lower()!="delete")
        b=sum(1 for e,ty in seq if e.lower()=="delete")
        c=sum(1 for e,ty in seq if e.lower() not in("delete","shift"))
        typos.append(t); backs.append(b); content.append(c)
        # formula-entry segmentation: '=' starts an entry; entry ends at next '='
        entries=[]; cur=None
        for e,ty in seq:
            if e=="=":
                if cur is not None: entries.append(cur)
                cur={"bs":0}
            if cur is not None and e.lower()=="delete": cur["bs"]+=1
        if cur is not None: entries.append(cur)
        if entries: pcorr.append(sum(1 for x in entries if x["bs"]>0)/len(entries))
    return dict(n=len(typos), typos=np.mean(typos), backs=np.mean(backs),
        err=100*np.mean(np.array(typos)/np.array(content)),
        pcorr=100*np.mean(pcorr) if pcorr else float('nan'))

print(f"HUMAN total={Htot:.1f}  (all model scored vs this identical human reference)\n")
print("SAME-REFERENCE MODEL FIT  (isolates the effect of the fixes+calibration)")
print("="*92)
print(f"{'':<22}{'Total(s)':>13}{'vsHuman':>9}{'r':>8}{'RMSE':>8}{'nRMSE':>8}{'AbsErr':>8}{'ModSD':>8}")
print("-"*92)
for name,folder in [("Full Realistic",'Ablation_Full_Realistic'),("Perfect",'Ablation_Perfect')]:
    for tag,pref in [("OLD 2026-05-28",OLD),("NEW 2026-07-07",NEW)]:
        x=batch_metrics(folder,pref)
        print(f"{name+' '+tag:<22}{x['total']:>8.1f}±{x['total_sd']:>4.1f}{x['pct']:>8.1f}%{x['r']:>8.3f}{x['rmse']:>8.2f}{x['nrmse']:>8.3f}{x['abserr']:>8.2f}{x['modsd']:>8.3f}")
    print("-"*92)

print("\nTYPING / CORRECTION  (Full Realistic)   human: P(corr)=25.0%, err formula 3.4% / word 6.3%")
print("="*72)
print(f"{'':<20}{'typos/run':>11}{'backsp/run':>12}{'realized err%':>15}{'P(corr)%':>10}")
for tag,pref in [("OLD 2026-05-28",OLD),("NEW 2026-07-07",NEW)]:
    t=typing_metrics('Ablation_Full_Realistic',pref)
    print(f"{tag:<20}{t['typos']:>11.1f}{t['backs']:>12.1f}{t['err']:>14.1f}%{t['pcorr']:>9.1f}%")
