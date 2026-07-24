import os, glob, csv, sys
import numpy as np

# ---- HUMAN: use their own util, their own definition ----
HUM_DIR = r"G:\ExcelDataAnalysis\Human Data\Typing Data"
sys.path.insert(0, HUM_DIR)
import typing_task_utils as U

df = U.read_combined_subjects()                 # key_down_events_dedup.csv
formula_rows, coverage = U.build_formula_rows(df)
hum_seg_iki = formula_rows["mean_iki"].dropna().to_numpy()
print("HUMAN formula-entry IKI (their def: '=' -> Enter, np.diff all keys, NO cutoff)")
print(f"  segments: {len(hum_seg_iki)}")
print(f"  mean of per-segment mean_iki : {hum_seg_iki.mean():.3f} s")
print(f"  median of per-segment mean_iki: {np.median(hum_seg_iki):.3f} s")
# subject-level mean then average (alt aggregation)
subj = formula_rows.groupby("subject")["mean_iki"].mean()
print(f"  mean over subjects           : {subj.mean():.3f} s  (n_subj={subj.size})")

# ---- MODEL: identical rule on keypresses.csv ('=' -> 'return', np.diff all keys, NO cutoff) ----
BASE=r"G:\ACT-RModels\Spreadsheet\logs\ablation_150_formula_latest"; NEW="2026-07-07"
def model_formula_iki(folder):
    seg_ikis=[]
    for rd in sorted(glob.glob(os.path.join(BASE,folder,"run_*"))):
        p=os.path.join(rd,"keypresses.csv")
        if not os.path.exists(p): continue
        seq_times=[]; active=False
        with open(p) as f:
            for r in csv.DictReader(f):
                if not r["run_id"].startswith(NEW): continue
                k=r["expected_key"].lower(); t=float(r["model_time"])
                if not active and k=="=":
                    active=True; seq_times=[t]
                elif active:
                    seq_times.append(t)
                    if k=="return":
                        if len(seq_times)>1:
                            seg_ikis.append(np.mean(np.diff(seq_times)))
                        active=False; seq_times=[]
    a=np.array(seg_ikis)
    return a

for name,folder in [("Full Realistic",'Ablation_Full_Realistic'),
                    ("Batched Formula Typing",'Ablation_Batched_Formula_Typing'),
                    ("Perfect",'Ablation_Perfect')]:
    a=model_formula_iki(folder)
    print(f"\nMODEL {name} formula-entry IKI (identical rule: '=' -> return, np.diff, NO cutoff)")
    print(f"  segments: {len(a)}")
    print(f"  mean of per-segment mean_iki : {a.mean():.3f} s")
    print(f"  median of per-segment mean_iki: {np.median(a):.3f} s")
