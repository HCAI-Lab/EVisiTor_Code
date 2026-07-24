"""Smoke-test gate for the 2x2x2 factorial (2 runs per cell).

Verifies, per the handoff:
  V=0  zero visual-search events; direct/recalled location pathway used
  V=1  search events present
  B=0  zero formula instruction look-backs
  B=1  look-backs present
  C=0  zero typos, corrections, and check-driven attention shifts
  C=1  delivered typos and corrections, accumulated-entry perceptual chain
       alive at end of run, and zero direct-fallback final checks.  The dated
       7-21 model re-encodes the already attended editable field and therefore
       does not emit the older typed-text-check:* attention-shift labels.
plus: every run finished with tasks 1-14 exactly once, the run's
condition_manifest.json matches the requested factor levels and the July 20
configuration, and the archived seed was actually applied (run_id contains it).

Exit code 0 = gate passed; 1 = gate failed (details printed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from ablation_2x2x2_common import (
    BATCH_ROOT, CELLS, cell_label, load_seeds, manifest_matches,
)

SMOKE_RUNS = 2


def check_run(problems: list[str], tag: str, run_dir: Path,
              code: str, v: int, b: int, c: int, seed: int) -> None:
    def bad(msg: str) -> None:
        problems.append(f"[{tag}] {msg}")

    tt_path = run_dir / "task_times.csv"
    if not tt_path.exists():
        bad("task_times.csv missing")
        return
    tt = pd.read_csv(tt_path)
    counts = tt["task"].value_counts()
    if sorted(counts.index) != list(range(1, 15)) or (counts != 1).any():
        bad(f"tasks not exactly 1..14 once each: {dict(counts)}")
    if not pd.to_numeric(tt["duration"], errors="coerce").notna().all():
        bad("nonnumeric durations in task_times.csv")

    expected_files = {"task_times.csv", "subtask_times.csv", "keypresses.csv",
                      "attention_shifts.csv", "condition_manifest.json",
                      "run_postcheck.json"}
    extra = {p.name for p in run_dir.iterdir()} - expected_files
    if extra:
        bad(f"unexpected stale files in run dir: {sorted(extra)}")

    man_path = run_dir / "condition_manifest.json"
    if not man_path.exists():
        bad("condition_manifest.json missing")
        return
    manifest = json.loads(man_path.read_text())
    for prob in manifest_matches(manifest, code, v, b, c):
        bad(f"manifest mismatch — {prob}")
    if manifest.get("seed") != seed:
        bad(f"manifest seed {manifest.get('seed')} != archived seed {seed}")
    run_ids = tt["run_id"].astype(str).unique()
    if len(run_ids) != 1:
        bad(f"multiple run_ids in one run dir: {run_ids}")
    elif f"_s{seed}" not in run_ids[0] or f"cell{code}" not in run_ids[0]:
        bad(f"run_id {run_ids[0]!r} lacks cell{code}/seed {seed} tag")

    shifts = pd.read_csv(run_dir / "attention_shifts.csv")
    src = shifts["source"].astype(str)
    n_search = src.str.startswith("visual-search-request").sum()
    n_direct = src.str.contains("direct-known-object-location").sum()
    n_lookback = (src == "look-back-to-formula-before-next-token").sum()
    checks = src[src.str.startswith("typed-text-check")]
    n_check_word = checks.str.contains(":word-").sum()
    n_check_formula_key = checks.isin(
        ["typed-text-check:formula-keystroke",
         "typed-text-check:learned-formula-keystroke"]).sum()
    n_check_formula_final = (checks == "typed-text-check:formula-final").sum()

    kp = pd.read_csv(run_dir / "keypresses.csv")
    typed = kp["typed_key"].astype(str)
    expected = kp["expected_key"].astype(str)
    n_typos = (typed != expected).sum()
    n_deletes = typed.isin(["delete", "backspace"]).sum()

    if v == 0:
        if n_search:
            bad(f"V=0 but {n_search} visual-search events")
        if n_direct == 0:
            bad("V=0 but idealized direct-location pathway never used")
    else:
        if n_search == 0:
            bad("V=1 but zero visual-search events")

    if b == 0:
        if n_lookback:
            bad(f"B=0 but {n_lookback} formula look-backs")
    else:
        if n_lookback == 0:
            bad("B=1 but zero formula look-backs")

    post = json.loads((run_dir / "run_postcheck.json").read_text())
    if c == 0:
        if len(checks):
            bad(f"C=0 but {len(checks)} typed-text-check shifts")
        if n_typos:
            bad(f"C=0 but {n_typos} delivered typos")
        if n_deletes:
            bad(f"C=0 but {n_deletes} correction deletes")
    else:
        if n_typos == 0:
            bad("C=1 but zero delivered typos")
        if n_deletes == 0:
            bad("C=1 but zero correction keystrokes")
        if not post.get("visual_error_checking_enabled_at_end"):
            bad("C=1 but perceptual chain self-disabled during the run")
        if post.get("formula_final_direct_count", 0) != 0:
            bad(f"C=1 but {post.get('formula_final_direct_count')} direct-fallback final checks")

    print(f"  [{tag}] ok-ish: search={n_search} direct={n_direct} lookback={n_lookback} "
          f"checks(word={n_check_word},fkey={n_check_formula_key},ffinal={n_check_formula_final}) "
          f"typos={n_typos} deletes={n_deletes} "
          f"total={pd.to_numeric(tt['duration'], errors='coerce').sum():.1f}s")


def main() -> None:
    seeds = load_seeds()
    problems: list[str] = []
    for code, v, b, c, wrapper in CELLS:
        label = cell_label(wrapper)
        cell_root = BATCH_ROOT / "smoke" / f"s_{code}" / label
        summary_path = cell_root / "batch_summary.csv"
        if not summary_path.exists():
            problems.append(f"[{code}] batch_summary.csv missing under {cell_root}")
            continue
        summary = pd.read_csv(summary_path)
        finished = set(summary.loc[summary["status"] == "finished", "run_index"])
        print(f"Cell {code} ({label}):")
        for idx in range(1, SMOKE_RUNS + 1):
            tag = f"{code} run_{idx:03d}"
            if idx not in finished:
                status = summary.loc[summary["run_index"] == idx, "status"]
                problems.append(
                    f"[{tag}] not finished: "
                    f"{status.iloc[0] if len(status) else 'no summary row'}")
                continue
            check_run(problems, tag, cell_root / f"run_{idx:03d}",
                      code, v, b, c, seeds[idx - 1])

    print()
    if problems:
        print(f"SMOKE GATE FAILED — {len(problems)} problem(s):")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("SMOKE GATE PASSED: all 8 cells satisfy the factor diagnostics.")


if __name__ == "__main__":
    main()
