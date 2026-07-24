"""Analyze the formula-check-probability sweep (cell 011, tasks 1-10 run).

RMSE / MAE / Pearson r are computed over the SCORED tasks only (3-10 by
default); tasks 1-2 are executed to build workbook state and are excluded.
Reports the whole curve, not just the argmin, and flags whether the minimum is
distinguishable from neighbouring conditions -- a flat curve means the
parameter is weakly identified and no precise 'best' value should be quoted.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get(
    "CHECKPROB_SWEEP_ROOT",
    HERE / "logs" / "draft34_20260722_checkprob_sweep"))
LABEL = os.environ.get("CHECKPROB_LABEL", "Ablation_NoVisual_CheckProb")
HUMAN_CSV = Path(os.environ.get("EVISITOR_HUMAN_DATA_ROOT", r"G:\ExcelDataAnalysis")) / "HumanCompletionTime.csv"
N_REQUIRED = int(os.environ.get("ABLATION_N_RUNS", "142"))
SCORED = [int(t) for t in os.environ.get("CHECKPROB_SCORED_TASKS",
                                         "3,4,5,6,7,8,9,10").split(",")]
RAN_TASKS = list(range(1, 11))
N_BOOT = 5000
BOOT_SEED = 20260722
PROBS = [round(i / 10, 1) for i in range(11)]


def human_means() -> dict[int, float]:
    h = pd.read_csv(HUMAN_CSV).set_index("Step")
    return {t: float(h.loc[t, "Average length time per task"])
            for t in range(1, 15)}


def load_condition(prob: float) -> tuple[np.ndarray, dict]:
    tag = f"{int(round(prob * 100)):03d}"
    base = ROOT / f"check_prob_{tag}" / LABEL
    rows, manifests = [], []
    for run in sorted(base.glob("run_*")):
        tt = pd.read_csv(run / "task_times.csv")
        counts = tt["task"].value_counts()
        if sorted(counts.index) != RAN_TASKS or (counts != 1).any():
            raise SystemExit(f"{run}: tasks are not exactly {RAN_TASKS} once")
        s = tt.set_index("task")["duration"]
        rows.append([float(s[t]) for t in RAN_TASKS])
        manifests.append(json.loads((run / "condition_manifest.json").read_text()))
    if len(rows) != N_REQUIRED:
        raise SystemExit(f"{base}: {len(rows)} runs, expected {N_REQUIRED}")
    first = manifests[0]
    got = first.get("formula_visual_check_probability")
    if got is None or not np.isclose(got, prob):
        raise SystemExit(f"{base}: manifest check probability {got} != {prob}")
    for m in manifests[1:]:
        if not np.isclose(m["formula_visual_check_probability"], got):
            raise SystemExit(f"{base}: mixed check probabilities")
        if m.get("visual_search"):
            raise SystemExit(f"{base}: visual search should be off")
    return np.asarray(rows), first


def fit_metrics(matrix: np.ndarray, human: dict[int, float],
                tasks: list[int]) -> tuple[float, float, float]:
    idx = [RAN_TASKS.index(t) for t in tasks]
    model = matrix[:, idx].mean(axis=0)
    ref = np.array([human[t] for t in tasks])
    resid = model - ref
    rmse = float(np.sqrt((resid ** 2).mean()))
    mae = float(np.abs(resid).mean())
    r = float(np.corrcoef(model, ref)[0, 1]) if len(tasks) > 2 else float("nan")
    return rmse, mae, r


def main() -> None:
    human = human_means()
    rng = np.random.default_rng(BOOT_SEED)
    rows = []
    for prob in PROBS:
        matrix, manifest = load_condition(prob)
        rmse, mae, r = fit_metrics(matrix, human, SCORED)
        idx = [RAN_TASKS.index(t) for t in SCORED]
        ref = np.array([human[t] for t in SCORED])
        boots = np.empty(N_BOOT)
        for b in range(N_BOOT):
            pick = rng.integers(0, matrix.shape[0], matrix.shape[0])
            m = matrix[pick][:, idx].mean(axis=0)
            boots[b] = np.sqrt(((m - ref) ** 2).mean())
        rows.append({
            "check_probability": prob,
            "runs": matrix.shape[0],
            "scored_total_s": float(matrix[:, idx].sum(axis=1).mean()),
            "ran_total_s": float(matrix.sum(axis=1).mean()),
            "rmse_s": rmse,
            "rmse_ci95_lo": float(np.percentile(boots, 2.5)),
            "rmse_ci95_hi": float(np.percentile(boots, 97.5)),
            "mae_s": mae,
            "pearson_r": r,
            "formula_typo_rate": manifest["formula_typo_rate"],
            "word_typo_rate": manifest["word_typo_rate"],
        })
    df = pd.DataFrame(rows)
    best = df.loc[df["rmse_s"].idxmin()]

    # Which conditions are statistically indistinguishable from the winner?
    lo, hi = best["rmse_ci95_lo"], best["rmse_ci95_hi"]
    df["overlaps_best_ci"] = ~((df["rmse_ci95_lo"] > hi) | (df["rmse_ci95_hi"] < lo))
    tied = df.loc[df["overlaps_best_ci"], "check_probability"].tolist()

    df.to_csv(ROOT / "checkprob_fit_summary.csv", index=False)
    summary = {
        "scored_tasks": SCORED,
        "executed_tasks": RAN_TASKS,
        "unscored_state_building_tasks": [1, 2],
        "n_runs_per_condition": N_REQUIRED,
        "best_check_probability": float(best["check_probability"]),
        "best_rmse_s": float(best["rmse_s"]),
        "indistinguishable_from_best": tied,
        "rmse_range_s": [float(df["rmse_s"].min()), float(df["rmse_s"].max())],
        "a_priori_value": 0.40,
        "a_priori_rmse_s": float(df.loc[np.isclose(df["check_probability"], 0.4),
                                        "rmse_s"].iloc[0]),
        "note": ("Parameter selected on the same task means it is scored "
                 "against; not an out-of-sample fit."),
    }
    (ROOT / "checkprob_fit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")

    pd.set_option("display.width", 200)
    print(df[["check_probability", "runs", "scored_total_s", "rmse_s",
              "rmse_ci95_lo", "rmse_ci95_hi", "mae_s", "pearson_r",
              "overlaps_best_ci"]].to_string(index=False))
    print(f"\nScored tasks: {SCORED}  (tasks 1-2 run but excluded)")
    print(f"Best RMSE {best['rmse_s']:.3f} s at p={best['check_probability']}; "
          f"a priori p=0.40 gives {summary['a_priori_rmse_s']:.3f} s")
    print(f"RMSE spread across the whole grid: "
          f"{summary['rmse_range_s'][0]:.3f} - {summary['rmse_range_s'][1]:.3f} s")
    print(f"Indistinguishable from best (95% CI overlap): {tied}")
    print(f"\nWrote checkprob_fit_summary.csv / .json under {ROOT}")


if __name__ == "__main__":
    main()
