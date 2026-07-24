"""Saturated 2x2x2 factorial analysis of the spreadsheet ablation batch.

Primary model (per handoff): time ~ V * B * C with effect coding (-0.5, +0.5),
so main effects are averaged over the other two factors and interaction
coefficients have the direct factorial interpretation.  Uncertainty is a
10,000-resample stratified bootstrap (runs resampled independently within each
of the eight cells).  Interaction claims are judged against PRE-DECLARED
equivalence bounds; correlation is computed but explicitly secondary.

Pre-registered smallest effect sizes of interest (declared before looking at
the eight-cell results; see handoff):
  total completion time : +/- 5 s
  per-subtask time      : +/- 1 s

Fails loudly on: missing cells, fewer than the configured valid runs, duplicate task rows,
inconsistent factor manifests, nonnumeric durations, mixed/drifted source
hashes.

Outputs (under the batch root):
  factorial_effects.csv / factorial_effects.json
  task_interactions.csv
  cell_summary.csv
  w1_results.json
  mechanism_diagnostics.csv
  interaction_plot_VxB.png / .pdf
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

from ablation_2x2x2_common import (
    BATCH_ROOT, CELLS, N_RUNS, SUBTASKS, cell_label, check_sources_frozen,
    HUMAN_MEANS_CSV, HUMAN_WINDOWS_CSV, HUMAN_EXCLUDED_SUBJECTS,
    manifest_matches, load_seeds,
)

N_BOOT = 10_000
BOOT_SEED = 20260720
EQUIV_TOTAL_S = 5.0
EQUIV_TASK_S = 1.0

EFFECTS = ["V", "B", "C", "VxB", "VxC", "BxC", "VxBxC"]
OUTCOMES = ["total"] + [f"task{t}" for t in SUBTASKS]

CHECK_SOURCES_WORD = ["typed-text-check:word-immediate", "typed-text-check:word-final"]
CHECK_SOURCES_FKEY = ["typed-text-check:formula-keystroke",
                      "typed-text-check:learned-formula-keystroke"]
CHECK_SOURCE_FFINAL = "typed-text-check:formula-final"

# Optional, opt-in: replace the task-1 duration of every visual-search cell
# (V=1) with the run-matched value from a dedicated task-1 batch.  Unset by
# default, so archived analysis commands reproduce byte-identical results.
TASK1_OVERRIDE_DIR = os.environ.get("ABLATION_TASK1_OVERRIDE_DIR", "").strip()
# Optional: send outputs somewhere other than the batch root, so an override
# run never clobbers the primary analysis.
OUT_DIR = Path(os.environ.get("ABLATION_OUT_DIR", "").strip() or BATCH_ROOT)


def load_task1_override():
    """Return {run_index: task1_duration} from the override batch, or None."""
    if not TASK1_OVERRIDE_DIR:
        return None
    root = Path(TASK1_OVERRIDE_DIR)
    if not root.exists():
        raise SystemExit(f"Task-1 override dir missing: {root}")
    out = {}
    for run_dir in sorted(root.glob("run_*")):
        tt = pd.read_csv(run_dir / "task_times.csv")
        rows = tt[tt["task"] == 1]
        if len(rows) != 1:
            raise SystemExit(f"{run_dir}: expected exactly one task-1 row")
        dur = pd.to_numeric(rows["duration"], errors="coerce").iloc[0]
        if not np.isfinite(dur):
            raise SystemExit(f"{run_dir}: nonnumeric task-1 duration")
        manifest = json.loads((run_dir / "condition_manifest.json").read_text())
        if not manifest.get("visual_search"):
            raise SystemExit(f"{run_dir}: override batch must have visual search on")
        out[int(run_dir.name.split("_")[1])] = (float(dur), manifest.get("seed"))
    if len(out) < N_RUNS:
        raise SystemExit(
            f"Task-1 override: only {len(out)} runs (< {N_RUNS}) in {root}")
    return out


TASK1_OVERRIDE = load_task1_override()


# ---------------------------------------------------------------- loading

def load_cell(code: str, v: int, b: int, c: int, label: str, seeds: list[int]):
    """Return (matrix runs x 15 [total + 14 tasks], mechanism DataFrame)."""
    cell_dir = BATCH_ROOT / label
    if not cell_dir.exists():
        raise SystemExit(f"Missing cell folder: {cell_dir}")
    rows, mech_rows = [], []
    run_dirs = sorted(cell_dir.glob("run_*"))
    for run_dir in run_dirs:
        idx = int(run_dir.name.split("_")[1])
        tt = pd.read_csv(run_dir / "task_times.csv")
        counts = tt["task"].value_counts()
        if sorted(counts.index) != list(range(1, 15)) or (counts != 1).any():
            raise SystemExit(f"{run_dir}: duplicate/missing task rows")
        durations = pd.to_numeric(tt["duration"], errors="coerce")
        if not durations.notna().all():
            raise SystemExit(f"{run_dir}: nonnumeric durations")
        manifest = json.loads((run_dir / "condition_manifest.json").read_text())
        problems = manifest_matches(manifest, code, v, b, c)
        if problems:
            raise SystemExit(f"{run_dir}: inconsistent manifest: {problems}")
        if manifest.get("seed") != seeds[idx - 1]:
            raise SystemExit(f"{run_dir}: seed mismatch vs archived list")
        s = tt.set_index("task")["duration"]
        task_times = [float(s[t]) for t in SUBTASKS]
        if TASK1_OVERRIDE is not None and v == 1:
            if idx not in TASK1_OVERRIDE:
                raise SystemExit(f"{run_dir}: no task-1 override for run {idx}")
            dur, ov_seed = TASK1_OVERRIDE[idx]
            if ov_seed != seeds[idx - 1]:
                raise SystemExit(
                    f"run {idx}: task-1 override seed {ov_seed} != {seeds[idx - 1]}")
            task_times[SUBTASKS.index(1)] = dur
        rows.append([sum(task_times)] + task_times)

        shifts = pd.read_csv(run_dir / "attention_shifts.csv")
        src = shifts["source"].astype(str)
        kp = pd.read_csv(run_dir / "keypresses.csv")
        typed = kp["typed_key"].astype(str)
        post = json.loads((run_dir / "run_postcheck.json").read_text())
        mech_rows.append({
            "run": idx,
            "search_shifts": int(src.str.startswith("visual-search-request").sum()),
            "direct_location_shifts": int(
                src.str.contains("direct-known-object-location").sum()),
            "formula_lookbacks": int(
                (src == "look-back-to-formula-before-next-token").sum()),
            "check_word": int(src.isin(CHECK_SOURCES_WORD).sum()),
            "check_word_final": int((src == "typed-text-check:word-final").sum()),
            "check_formula_keystroke": int(src.isin(CHECK_SOURCES_FKEY).sum()),
            "check_formula_final": int((src == CHECK_SOURCE_FFINAL).sum()),
            "typos": int((typed != kp["expected_key"].astype(str)).sum()),
            "correction_deletes": int(typed.isin(["delete", "backspace"]).sum()),
            "keypresses": int(len(kp)),
            "final_direct_fallbacks": int(post.get("formula_final_direct_count", 0)),
            "checking_alive_at_end": bool(
                post.get("visual_error_checking_enabled_at_end", False)),
        })
    if len(rows) < N_RUNS:
        raise SystemExit(f"Cell {code}: only {len(rows)} valid runs (< {N_RUNS})")
    return np.array(rows), pd.DataFrame(mech_rows)


# ------------------------------------------------------- factorial machinery

def design_matrix() -> np.ndarray:
    """8x8 design matrix on cell means, effect coding +/-0.5, column order
    [intercept] + EFFECTS, row order = CELLS order."""
    X = np.zeros((8, 8))
    for i, (_code, v, b, c, _w) in enumerate(CELLS):
        xv, xb, xc = v - 0.5, b - 0.5, c - 0.5
        X[i] = [1.0, xv, xb, xc, xv * xb, xv * xc, xb * xc, xv * xb * xc]
    return X


def effects_from_cell_means(means: np.ndarray, Xinv: np.ndarray) -> np.ndarray:
    """means: (..., 8) cell means -> (..., 8) [intercept + 7 effects]."""
    return means @ Xinv.T


def simple_interaction_contrasts(mu: dict[str, np.ndarray]):
    """V x B contrast at each level of C (and the analogous pairs)."""
    return {
        "VxB_at_C0": mu["110"] - mu["100"] - mu["010"] + mu["000"],
        "VxB_at_C1": mu["111"] - mu["101"] - mu["011"] + mu["001"],
        "VxC_at_B0": mu["101"] - mu["100"] - mu["001"] + mu["000"],
        "VxC_at_B1": mu["111"] - mu["110"] - mu["011"] + mu["010"],
        "BxC_at_V0": mu["011"] - mu["010"] - mu["001"] + mu["000"],
        "BxC_at_V1": mu["111"] - mu["110"] - mu["101"] + mu["100"],
        "five_cell_residual_01coding":
            mu["111"] - mu["100"] - mu["010"] - mu["001"] + 2 * mu["000"],
    }


def holm(pvals: np.ndarray) -> np.ndarray:
    order = np.argsort(pvals)
    adj = np.empty_like(pvals)
    running = 0.0
    m = len(pvals)
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


# ---------------------------------------------------------------- human fit

def load_human():
    H, HSD = {}, {}
    with open(HUMAN_MEANS_CSV) as f:
        import csv as _csv
        for row in _csv.DictReader(f):
            t = int(row["Step"])
            H[t] = float(row["Average length time per task"])
            HSD[t] = float(row["standart deviation"])
    h_mean = np.array([H[t] for t in SUBTASKS])
    h_sd = np.array([HSD[t] for t in SUBTASKS])
    hw = pd.read_csv(HUMAN_WINDOWS_CSV)
    piv = hw.pivot_table(index="subject", columns="step_num", values="length_sec")
    piv = piv.drop(HUMAN_EXCLUDED_SUBJECTS, errors="ignore").dropna()
    h_matrix = piv[SUBTASKS].values
    return h_mean, h_sd, h_matrix


def human_fit(M: np.ndarray, h_mean, h_sd, h_matrix):
    task_m = M[:, 1:]
    sm = task_m.mean(0)
    diff = sm - h_mean
    tot = M[:, 0]
    w1_tasks = {f"task{t}": float(wasserstein_distance(h_matrix[:, i], task_m[:, i]))
                for i, t in enumerate(SUBTASKS)}
    return {
        "model_total_mean": float(tot.mean()),
        "model_total_sd": float(tot.std(ddof=1)),
        "human_total_mean": float(h_mean.sum()),
        "pct_dev_total": float(100 * (tot.mean() - h_mean.sum()) / h_mean.sum()),
        "rmse": float(np.sqrt((diff ** 2).mean())),
        "nrmse_human_sd": float(np.sqrt(((diff / h_sd) ** 2).mean())),
        "mae": float(np.abs(diff).mean()),
        "pearson_r_secondary": float(np.corrcoef(sm, h_mean)[0, 1]),
        "w1_total": float(wasserstein_distance(h_matrix.sum(1), tot)),
        "w1_tasks": w1_tasks,
        "w1_task_mean": float(np.mean(list(w1_tasks.values()))),
    }


# ---------------------------------------------------------------- plotting

def interaction_plot(mu_total: dict[str, np.ndarray], ci: dict, out_base: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Okabe-Ito colorblind-safe pair; identity also encoded by marker + linestyle.
    col_b0, col_b1 = "#0072B2", "#D55E00"
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), sharey=True)
    for ax, c in zip(axes, (0, 1)):
        for b, colr, mark, ls in ((0, col_b0, "o", "-"), (1, col_b1, "s", "--")):
            ys, los, his = [], [], []
            for v in (0, 1):
                code = f"{v}{b}{c}"
                ys.append(mu_total[code])
                lo, hi = ci[code]
                los.append(mu_total[code] - lo)
                his.append(hi - mu_total[code])
            ax.errorbar([0, 1], ys, yerr=[los, his], color=colr, marker=mark,
                        linestyle=ls, markersize=6, capsize=3, linewidth=1.6,
                        label=f"B={b}")
        ax.set_xticks([0, 1], ["V=0", "V=1"])
        ax.set_title(f"C={c}", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="0.9", linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Total completion time (s)")
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("V x B interaction at each level of C (cell means, 95% bootstrap CI)",
                 fontsize=10)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_base.with_suffix("." + ext), dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------- main

def main() -> None:
    check_sources_frozen()
    seeds = load_seeds()
    h_mean, h_sd, h_matrix = load_human()
    print(f"Human reference: {h_matrix.shape[0]} subjects x 14 tasks "
          f"(excluding {HUMAN_EXCLUDED_SUBJECTS}); mean total {h_mean.sum():.1f}s")

    cell_data, mech_data = {}, {}
    for code, v, b, c, wrapper in CELLS:
        label = cell_label(wrapper)
        M, mech = load_cell(code, v, b, c, label, seeds)
        cell_data[code] = M
        mech_data[code] = mech
        print(f"cell {code} ({label}): {M.shape[0]} runs, "
              f"total {M[:, 0].mean():.1f} +/- {M[:, 0].std(ddof=1):.1f}s")

    codes = [c for c, *_ in CELLS]
    X = design_matrix()
    Xinv = np.linalg.inv(X)

    # Observed cell means: (8, 15)
    obs_means = np.stack([cell_data[c].mean(0) for c in codes])
    obs_eff = effects_from_cell_means(obs_means.T, Xinv).T  # (8coef, 15)

    # Stratified bootstrap: resample runs within each cell.
    rng = np.random.default_rng(BOOT_SEED)
    boot_means = np.empty((8, N_BOOT, 15))
    for i, c in enumerate(codes):
        M = cell_data[c]
        idx = rng.integers(0, M.shape[0], size=(N_BOOT, M.shape[0]))
        boot_means[i] = M[idx].mean(axis=1)
    boot_eff = np.einsum("ke,ebo->kbo", Xinv, boot_means)  # (8coef, N_BOOT, 15)

    mu_obs = {c: obs_means[i] for i, c in enumerate(codes)}
    mu_boot = {c: boot_means[i] for i, c in enumerate(codes)}
    simple_obs = simple_interaction_contrasts(mu_obs)
    simple_boot = simple_interaction_contrasts(mu_boot)

    def summarize(name, obs_vec, boot_mat, outcome_idx, equiv):
        lo, hi = np.percentile(boot_mat[:, outcome_idx], [2.5, 97.5])
        lo90, hi90 = np.percentile(boot_mat[:, outcome_idx], [5.0, 95.0])
        v = boot_mat[:, outcome_idx]
        p = 2 * min((v >= 0).mean(), (v <= 0).mean())
        p = min(1.0, max(p, 2.0 / N_BOOT))
        return {
            "effect": name,
            "outcome": OUTCOMES[outcome_idx],
            "estimate_s": float(obs_vec[outcome_idx]),
            "ci95_lo": float(lo), "ci95_hi": float(hi),
            "ci90_lo": float(lo90), "ci90_hi": float(hi90),
            "boot_p": float(p),
            "equiv_bound_s": equiv,
            "ci95_within_equiv": bool(-equiv <= lo and hi <= equiv),
            "tost_equivalent_ci90": bool(-equiv <= lo90 and hi90 <= equiv),
        }

    effects_rows, task_rows = [], []
    for k, name in enumerate(EFFECTS, start=1):
        effects_rows.append(summarize(name, obs_eff[k], boot_eff[k], 0, EQUIV_TOTAL_S))
        for j in range(1, 15):
            task_rows.append(summarize(name, obs_eff[k], boot_eff[k], j, EQUIV_TASK_S))
    for name in simple_obs:
        effects_rows.append(summarize(name, simple_obs[name],
                                      simple_boot[name], 0, EQUIV_TOTAL_S))
        for j in range(1, 15):
            task_rows.append(summarize(name, simple_obs[name],
                                       simple_boot[name], j, EQUIV_TASK_S))

    # Holm across the 14 task-specific tests, within each effect family.
    task_df = pd.DataFrame(task_rows)
    task_df["holm_p"] = np.nan
    for name in task_df["effect"].unique():
        sel = task_df["effect"] == name
        task_df.loc[sel, "holm_p"] = holm(task_df.loc[sel, "boot_p"].values)

    effects_df = pd.DataFrame(effects_rows)
    effects_df.to_csv(OUT_DIR / "factorial_effects.csv", index=False)
    task_df.to_csv(OUT_DIR / "task_interactions.csv", index=False)
    (OUT_DIR / "factorial_effects.json").write_text(json.dumps({
        "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
        "equivalence_bounds_pre_registered": {
            "total_s": EQUIV_TOTAL_S, "per_task_s": EQUIV_TASK_S},
        "effect_coding": "-0.5/+0.5",
        "effects_total": effects_rows,
    }, indent=2) + "\n")

    # Cell summary + human fit + W1.
    fit_rows, w1_out = [], {}
    for code, _v, _b, _c, wrapper in CELLS:
        fit = human_fit(cell_data[code], h_mean, h_sd, h_matrix)
        w1_out[code] = {"w1_total": fit["w1_total"], "w1_tasks": fit["w1_tasks"],
                        "w1_task_mean": fit["w1_task_mean"]}
        fit_rows.append({"cell": code, "label": cell_label(wrapper),
                         **{k: v for k, v in fit.items() if k != "w1_tasks"}})
    cell_df = pd.DataFrame(fit_rows)
    cell_df.to_csv(OUT_DIR / "cell_summary.csv", index=False)
    (OUT_DIR / "w1_results.json").write_text(json.dumps({
        "human_subjects": int(h_matrix.shape[0]),
        "excluded_subjects": HUMAN_EXCLUDED_SUBJECTS,
        "cells": w1_out}, indent=2) + "\n")

    # Mechanism diagnostics: does each factor manipulate the intended process?
    mech_rows = []
    for code, v, b, c, wrapper in CELLS:
        m = mech_data[code]
        mech_rows.append({
            "cell": code, "V": v, "B": b, "C": c,
            **{col: float(m[col].mean())
               for col in ["search_shifts", "direct_location_shifts",
                           "formula_lookbacks", "check_word", "check_word_final",
                           "check_formula_keystroke", "check_formula_final",
                           "typos", "correction_deletes", "keypresses",
                           "final_direct_fallbacks"]},
            "checking_alive_all_runs": bool(m["checking_alive_at_end"].all() if c
                                            else True),
        })
    mech_df = pd.DataFrame(mech_rows)
    mech_df.to_csv(OUT_DIR / "mechanism_diagnostics.csv", index=False)

    # Interaction plot: V x B at each level of C.
    ci_total = {c: tuple(np.percentile(boot_means[i][:, 0], [2.5, 97.5]))
                for i, c in enumerate(codes)}
    interaction_plot({c: obs_means[i, 0] for i, c in enumerate(codes)},
                     ci_total, OUT_DIR / "interaction_plot_VxB")

    # Console digest.
    print("\n=== Saturated factorial, total completion time (effect coding +/-0.5) ===")
    for row in effects_rows:
        if row["outcome"] != "total":
            continue
        flag = ""
        if row["effect"] in ("VxB", "VxC", "BxC", "VxBxC"):
            if row["ci95_within_equiv"]:
                flag = "  [95% CI within +/-5s equivalence bounds]"
            elif row["boot_p"] < 0.05:
                flag = "  [interaction detected]"
            else:
                flag = "  [CI includes 0; NOT evidence of independence]"
        print(f"  {row['effect']:>26}: {row['estimate_s']:8.2f} s "
              f"[{row['ci95_lo']:7.2f}, {row['ci95_hi']:7.2f}]  p={row['boot_p']:.4f}{flag}")
    print("\n=== Human fit by cell (deviation metrics primary; r secondary) ===")
    print(cell_df[["cell", "label", "model_total_mean", "pct_dev_total", "rmse",
                   "nrmse_human_sd", "mae", "w1_total", "w1_task_mean",
                   "pearson_r_secondary"]].to_string(index=False))
    print("\n=== Mechanism diagnostics (per-run means) ===")
    print(mech_df.to_string(index=False))
    print(f"\nOutputs written under {OUT_DIR}")


if __name__ == "__main__":
    main()
