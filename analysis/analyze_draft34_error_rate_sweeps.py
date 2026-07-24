"""Analyze independent 0--5% word/formula typo-rate sweeps of the dated model."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get(
    "DRAFT34_ERROR_SWEEP_ROOT",
    HERE / "logs" / "draft34_20260721_error_rate_sweeps"))
HUMAN_CSV = Path(r"G:\ExcelDataAnalysis\HumanCompletionTime.csv")
N_REQUIRED = int(os.environ.get("ABLATION_N_RUNS", "142"))
N_BOOT = 5000
BOOT_SEED = 20260721
RATES = range(6)
# Wrapper folder inside each condition. Overridable so the visual-search-off
# sweep (Ablation_NoVisual_Rates) can reuse this analyzer unchanged.
LABEL = os.environ.get("DRAFT34_SWEEP_LABEL", "Ablation_Full_Realistic_Rates")


def human_means() -> np.ndarray:
    h = pd.read_csv(HUMAN_CSV).set_index("Step")
    return np.array([h.loc[t, "Average length time per task"]
                     for t in range(1, 15)], dtype=float)


def load_condition(kind: str, pct: int) -> tuple[np.ndarray, dict]:
    tag = f"{pct * 10:03d}"
    base = ROOT / f"{kind}_rate_{tag}" / LABEL
    rows, manifests = [], []
    for run in sorted(base.glob("run_*")):
        tt = pd.read_csv(run / "task_times.csv")
        counts = tt["task"].value_counts()
        if sorted(counts.index) != list(range(1, 15)) or (counts != 1).any():
            raise SystemExit(f"{run}: tasks are not exactly 1..14 once")
        s = tt.set_index("task")["duration"]
        rows.append([float(s[t]) for t in range(1, 15)])
        manifests.append(json.loads((run / "condition_manifest.json").read_text()))
    if len(rows) != N_REQUIRED:
        raise SystemExit(f"{base}: {len(rows)} runs, expected {N_REQUIRED}")
    first = manifests[0]
    for m in manifests[1:]:
        for key in ("formula_typo_rate", "word_typo_rate"):
            if not np.isclose(m[key], first[key]):
                raise SystemExit(f"{base}: mixed {key} values")
    expected_formula = pct / 100 if kind == "formula" else 0.034
    expected_word = pct / 100 if kind == "word" else 0.063
    if not np.isclose(first["formula_typo_rate"], expected_formula):
        raise SystemExit(
            f"{base}: formula rate {first['formula_typo_rate']} != {expected_formula}")
    if not np.isclose(first["word_typo_rate"], expected_word):
        raise SystemExit(
            f"{base}: word rate {first['word_typo_rate']} != {expected_word}")
    return np.asarray(rows), first


def metrics(matrix: np.ndarray, human: np.ndarray) -> tuple[float, float, float]:
    means = matrix.mean(axis=0)
    rmse = float(np.sqrt(np.mean((means - human) ** 2)))
    corr = float(np.corrcoef(means, human)[0, 1])
    total = float(means.sum())
    return rmse, corr, total


def main() -> None:
    human = human_means()
    rng = np.random.default_rng(BOOT_SEED)
    rows = []
    for kind in ("formula", "word"):
        for pct in RATES:
            matrix, manifest = load_condition(kind, pct)
            rmse, corr, total = metrics(matrix, human)
            idx = rng.integers(0, len(matrix), size=(N_BOOT, len(matrix)))
            boot_means = matrix[idx].mean(axis=1)
            boot_rmse = np.sqrt(np.mean((boot_means - human) ** 2, axis=1))
            boot_corr = np.array([np.corrcoef(x, human)[0, 1]
                                  for x in boot_means])
            rows.append({
                "sweep": kind,
                "varied_error_rate_pct": pct,
                "formula_error_rate_pct": 100 * manifest["formula_typo_rate"],
                "word_error_rate_pct": 100 * manifest["word_typo_rate"],
                "runs": len(matrix),
                "mean_total_s": total,
                "rmse_s": rmse,
                "rmse_ci95_lo": float(np.percentile(boot_rmse, 2.5)),
                "rmse_ci95_hi": float(np.percentile(boot_rmse, 97.5)),
                "pearson_r": corr,
                "r_ci95_lo": float(np.percentile(boot_corr, 2.5)),
                "r_ci95_hi": float(np.percentile(boot_corr, 97.5)),
            })
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "error_rate_fit_summary.csv", index=False)
    (ROOT / "error_rate_fit_summary.json").write_text(
        json.dumps({"power": 0.99, "cohens_d": 0.5,
                    "runs_per_condition": N_REQUIRED,
                    "bootstrap_resamples": N_BOOT,
                    "results": rows}, indent=2) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.4), sharey=True)
    colors = {"formula": "#0072B2", "word": "#D55E00"}
    for col, kind in enumerate(("formula", "word")):
        d = out[out.sweep == kind].sort_values("varied_error_rate_pct")
        x = d.varied_error_rate_pct.to_numpy()
        c = colors[kind]
        ax = axes[col]
        y = d["rmse_s"].to_numpy()
        ax.plot(x, y, color=c, marker="o", linewidth=1.8)
        ax.fill_between(x, d["rmse_ci95_lo"], d["rmse_ci95_hi"],
                        color=c, alpha=.18, linewidth=0)
        ax.grid(axis="y", color="0.9")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"Vary {kind} error rate")
        ax.set_xlabel(f"Nominal {kind} error rate (%)")
    axes[0].set_ylabel("RMSE (s)")
    fig.suptitle("Fit sensitivity: independent typing-error sweeps")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(ROOT / f"error_rate_rmse_correlation.{ext}", dpi=300)
    plt.close(fig)

    lines = [
        "# Error-rate sensitivity of the full realistic model", "",
        f"Each condition has {N_REQUIRED} runs (Ritter et al. 0.99 power, "
        "medium d=0.5). The non-varied rate remains at the full-model default.", "",
        "| Sweep | Rate | Formula rate | Word rate | Total (s) | RMSE (s) | r |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['sweep']} | {r['varied_error_rate_pct']:.0f}% | "
            f"{r['formula_error_rate_pct']:.1f}% | {r['word_error_rate_pct']:.1f}% | "
            f"{r['mean_total_s']:.2f} | {r['rmse_s']:.2f} | {r['pearson_r']:.3f} |")
    (ROOT / "error_rate_fit_summary.md").write_text("\n".join(lines) + "\n")
    print(out.to_string(index=False))
    print(f"\nWrote sweep analysis to {ROOT}")


if __name__ == "__main__":
    main()
