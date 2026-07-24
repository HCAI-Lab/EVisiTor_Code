import os, glob, csv
import numpy as np

BASE=os.path.join(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"G:\ACT-RModels\Spreadsheet\logs"), "ablation_150_formula_latest"); NEW="2026-07-07"
CMD={"shift","return","delete"}

def gaps(folder, include_bs=False):
    """collect all consecutive content-key gaps across runs"""
    allg=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        p=os.path.join(rd,"keypresses.csv")
        if not os.path.exists(p): continue
        seq=[]
        with open(p) as f:
            for r in csv.DictReader(f):
                if not r["run_id"].startswith(NEW): continue
                k=r["expected_key"]
                if include_bs:
                    if k.lower() in ("shift","return"): continue
                else:
                    if k.lower() in CMD: continue
                seq.append(float(r["model_time"]))
        allg += [seq[i]-seq[i-1] for i in range(1,len(seq)) if seq[i]-seq[i-1]>0]
    return np.array(allg)

for name,folder in [("Full Realistic",'Ablation_Full_Realistic'),("Perfect",'Ablation_Perfect')]:
    g=gaps(folder)
    print(f"\n=== {name} (content keys only) ===")
    print(f"  {'cap':>8}{'meanIKI':>10}{'medianIKI':>11}{'% kept':>9}")
    for cap in [1.0,1.5,2.0,3.0,5.0,10.0,1e9]:
        keep=g[g<=cap]
        lbl="none" if cap>1e8 else f"{cap:g}s"
        print(f"  {lbl:>8}{keep.mean():>10.3f}{np.median(keep):>11.3f}{100*len(keep)/len(g):>8.1f}%")
    print(f"  overall median (no cap) = {np.median(g):.3f} s ; n gaps = {len(g)}")
