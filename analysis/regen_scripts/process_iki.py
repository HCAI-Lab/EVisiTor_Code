import os, glob, csv
import numpy as np

BASE=os.path.join(os.environ.get("EVISITOR_BATCH_LOGS_ROOT", r"G:\ACT-RModels\Spreadsheet\logs"), "ablation_150_formula_latest"); NEW="2026-07-07"
CMD={"shift","return","delete"}
CONDS=[("Perfect",'Ablation_Perfect'),("Correction Checking",'Ablation_Correction_Checking'),
       ("Visual Search Only",'Ablation_Visual_Search_Only'),("Batched Formula Typing",'Ablation_Batched_Formula_Typing'),
       ("Full Realistic",'Ablation_Full_Realistic')]

def per_run(folder):
    keys=[]; attn=[]; srch=[]; lb=[]; ikis=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        kp=os.path.join(rd,"keypresses.csv"); at=os.path.join(rd,"attention_shifts.csv")
        # keys + IKI
        seq=[]
        if os.path.exists(kp):
            with open(kp) as f:
                for r in csv.DictReader(f):
                    if r["run_id"].startswith(NEW): seq.append((float(r["model_time"]),r["expected_key"]))
        content=[(t,k) for t,k in seq if k.lower() not in CMD]
        keys.append(len(seq))
        # IKI: diffs between consecutive content keys, keep 0.05..3s (within-burst)
        d=[content[i][0]-content[i-1][0] for i in range(1,len(content))]
        d=[x for x in d if 0.05<=x<=3.0]
        if d: ikis.append(np.mean(d))
        # attention measures
        a=s=l=0
        if os.path.exists(at):
            with open(at) as f:
                for r in csv.DictReader(f):
                    if not r["run_id"].startswith(NEW): continue
                    a+=1; src=r["source"]
                    if src=="visual-search-request-succeeded": s+=1
                    elif src=="look-back-to-formula-before-next-token": l+=1
        attn.append(a); srch.append(s); lb.append(l)
    return dict(keys=np.mean(keys),attn=np.mean(attn),srch=np.mean(srch),lb=np.mean(lb),
                iki=np.mean(ikis), iki_sd=np.std(ikis,ddof=1))

print("TABLE 8 process measures (new batch means, N=150)   human IKI=0.70 s")
print(f"{'Condition':<24}{'Keys':>8}{'AttnShifts':>12}{'Search':>9}{'LookBk':>9}{'IKI(s)':>9}")
print("-"*72)
for name,fo in CONDS:
    x=per_run(fo)
    print(f"{name:<24}{x['keys']:>8.1f}{x['attn']:>12.1f}{x['srch']:>9.1f}{x['lb']:>9.1f}{x['iki']:>9.3f}")
