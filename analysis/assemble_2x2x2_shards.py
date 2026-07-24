"""Assemble parallel shard outputs into final per-cell folders and validate them.

Reads  <root>/shards/s_<code>_*/<Label>/run_NNN   (and <root>/reruns/... if present)
Writes <root>/<Label>/run_NNN                     (global seed-index numbering)
plus   <root>/<Label>/assembly_report.json

A run is VALID iff:
  - its shard batch_summary.csv row says "finished";
  - task_times.csv exists with tasks 1..14 exactly once, numeric durations;
  - condition_manifest.json matches the cell's factor levels and July 20 config,
    and records the archived seed for its global index;
  - for C=1 cells: run_postcheck.json shows the perceptual chain alive at end
    and zero direct-fallback final checks.

Invalid runs are NOT copied silently: they are recorded in the assembly report
(with reasons) and left in place in the shard folder for inspection.  Rerun
shards (from run_2x2x2_batch.ps1 -Mode custom) may replace a failed global
index; a valid rerun of an index beats an invalid original, but two VALID
sources for one index abort assembly.

Exit 0 only if every cell ends with at least the configured number of valid runs.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

from ablation_2x2x2_common import (
    BATCH_ROOT, CELLS, N_RUNS, cell_label, check_sources_frozen, load_seeds,
    manifest_matches,
)


def validate_run(run_dir: Path, code: str, v: int, b: int, c: int,
                 seed: int) -> list[str]:
    problems = []
    tt_path = run_dir / "task_times.csv"
    if not tt_path.exists():
        return ["task_times.csv missing"]
    tt = pd.read_csv(tt_path)
    counts = tt["task"].value_counts()
    if sorted(counts.index) != list(range(1, 15)) or (counts != 1).any():
        problems.append("tasks not exactly 1..14 once each")
    if not pd.to_numeric(tt["duration"], errors="coerce").notna().all():
        problems.append("nonnumeric durations")
    man_path = run_dir / "condition_manifest.json"
    if not man_path.exists():
        problems.append("condition_manifest.json missing")
    else:
        manifest = json.loads(man_path.read_text())
        problems += manifest_matches(manifest, code, v, b, c)
        if manifest.get("seed") != seed:
            problems.append(f"seed {manifest.get('seed')} != archived {seed}")
    post_path = run_dir / "run_postcheck.json"
    if not post_path.exists():
        problems.append("run_postcheck.json missing")
    elif c:
        post = json.loads(post_path.read_text())
        if not post.get("visual_error_checking_enabled_at_end"):
            problems.append("perceptual chain self-disabled during run")
        if post.get("formula_final_direct_count", 0) != 0:
            problems.append(
                f"{post.get('formula_final_direct_count')} direct-fallback final checks")
    return problems


def main() -> None:
    check_sources_frozen()
    seeds = load_seeds()
    overall_ok = True

    for code, v, b, c, wrapper in CELLS:
        label = cell_label(wrapper)
        dest = BATCH_ROOT / label
        # candidate runs: {global_index: [(run_dir, finished, shard_name)]}
        candidates: dict[int, list[tuple[Path, bool, str]]] = {}
        shard_dirs = sorted((BATCH_ROOT / "shards").glob(f"s_{code}_*")) + \
            sorted((BATCH_ROOT / "reruns").glob(f"s_{code}_*")
                   if (BATCH_ROOT / "reruns").exists() else [])
        if not shard_dirs:
            print(f"[{code}] FAIL: no shard folders found")
            overall_ok = False
            continue
        for shard in shard_dirs:
            cell_dir = shard / label
            summary_path = cell_dir / "batch_summary.csv"
            finished = set()
            if summary_path.exists():
                s = pd.read_csv(summary_path)
                finished = set(s.loc[s["status"] == "finished", "run_index"])
            for run_dir in sorted(cell_dir.glob("run_*")):
                idx = int(run_dir.name.split("_")[1])
                candidates.setdefault(idx, []).append(
                    (run_dir, idx in finished, shard.name))

        assembled, failures = {}, {}
        for idx, sources in sorted(candidates.items()):
            valid = []
            for run_dir, finished_ok, shard_name in sources:
                problems = ([] if finished_ok else ["not marked finished"]) + \
                    validate_run(run_dir, code, v, b, c, seeds[idx - 1])
                if problems:
                    failures.setdefault(idx, []).append(
                        {"shard": shard_name, "run_dir": str(run_dir),
                         "problems": problems})
                else:
                    valid.append((run_dir, shard_name))
            if len(valid) > 1:
                raise SystemExit(
                    f"[{code}] run_{idx:03d}: {len(valid)} VALID sources "
                    f"({[s for _, s in valid]}) — ambiguous, aborting.")
            if valid:
                assembled[idx] = valid[0]

        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for idx, (run_dir, _shard) in sorted(assembled.items()):
            target = dest / f"run_{idx:03d}"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(run_dir, target)
            copied += 1

        report = {
            "cell": code,
            "label": label,
            "valid_runs": copied,
            "required_runs": N_RUNS,
            "valid_indices": sorted(assembled),
            "failed": {str(k): val for k, val in sorted(failures.items())},
            "missing_indices": [i for i in range(1, N_RUNS + 1)
                                if i not in assembled],
        }
        (dest / "assembly_report.json").write_text(
            json.dumps(report, indent=2) + "\n")
        status = "OK" if copied >= N_RUNS and not report["missing_indices"] else "FAIL"
        if status == "FAIL":
            overall_ok = False
        print(f"[{code}] {status}: {copied} valid runs assembled, "
              f"{len(failures)} run indices with failures, "
              f"missing {report['missing_indices'] or 'none'}")
        for idx, fails in sorted(failures.items()):
            for f in fails:
                print(f"    run_{idx:03d} ({f['shard']}): {'; '.join(f['problems'])}")

    if not overall_ok:
        print("\nASSEMBLY INCOMPLETE — rerun failed indices with, e.g.:")
        print("  .\\Spreadsheet\\run_2x2x2_batch.ps1 -Mode custom -Shards '<code>:<idx>:1'")
        sys.exit(1)
    print(f"\nAll 8 cells assembled with {N_RUNS} valid runs each.")


if __name__ == "__main__":
    main()
