# Reproducing the EVisiTor results

This guide explains **exactly what can be reproduced from a clone, and what
requires resources that cannot be redistributed** (the ACT-R runtime,
IRB-restricted human data, a licensed third-party dataset, and paid LLM API
keys). Read the [reproduction matrix](#reproduction-matrix) first so you know
which parts apply to you.

For what each folder contains, see [`README.md`](README.md). This file is only
about *running* things.

> **The single most important setting** — to get the numbers in the paper you
> **must** select the reported model build. Its default is the *older* build,
> which does **not** implement the per-token formula check. See
> [The reproduction "trap"](#the-reproduction-trap) below. This is not optional.

---

## Reproduction matrix

| Result | Reproducible from a clone alone? | Also needs |
|---|---|---|
| **Model-source integrity** (the shipped models are the exact reported builds) | ✅ Yes | just `python` + `hashlib` — see [Verify integrity](#0-verify-model-source-integrity) |
| **Re-score the shipped raw LLM outputs** (generalization / parsing eval) | ✅ Yes | core Python deps |
| **Analysis tables/figures from shipped aggregates** (`analysis/batch_provenance/`) | ✅ Yes | core Python deps |
| **Run the ACT-R spreadsheet model** (smoke test, or regenerate a batch) | ⚠️ Partial | Windows, **ACT-R 7.x** (download), SBCL, Microsoft Excel |
| **Full factorial batch** (8 cells × 142 runs) + Appendix L sweeps | ⚠️ Partial | the above + hours of compute |
| **Model-vs-human comparison scripts** | ❌ No | IRB-restricted **human data** (request access) |
| **Re-run the LLM parsers from scratch** | ❌ No | your own **API keys** (billed) + the parsers are non-deterministic |
| **Windows generalization completion-time analysis** | ❌ No | the **Paradigm Shift AI** dataset (licensed) |

"Partial" = the code and provenance are here and will run once you supply the
external runtime/data; nothing about the pipeline is hidden.

---

## Prerequisites

Install only what your target row above needs.

1. **Python 3.10+** and the analysis dependencies:
   ```
   pip install -r requirements.txt
   ```
   (The live Windows bridge has its own pinned, Windows-only set in
   `bridge/VisiTor/requirements.txt`; install it only to drive the real Excel
   interface.)

2. **ACT-R 7.x** — *not bundled* (separately distributed). Download it from
   <https://github.com/asmaloney/ACT-R> (or the CMU distribution at
   <http://act-r.psy.cmu.edu/software/>) and either
   * unpack it to `<repo>\actr7.x\` (so `<repo>\actr7.x\load-act-r.lisp` exists), **or**
   * set `EVISITOR_ACTR_HOME` to the folder containing `load-act-r.lisp`.

3. **SBCL** (Steel Bank Common Lisp) on your `PATH` — the model runs under SBCL.

4. **Microsoft Excel + Windows** — the spreadsheet model drives a real Excel
   window through Windows UI Automation. The spreadsheet and live-interface runs
   are Windows-only. (Pure analysis / LLM re-scoring is cross-platform.)

5. **Human data** (optional) — IRB-restricted (protocol STUDY00012835),
   available on request per the paper's Data Availability statement. Point the
   analysis scripts at your copy with `EVISITOR_HUMAN_DATA_ROOT` (see below).

6. **Paradigm Shift AI dataset** (optional) — licensed separately; set
   `EVISITOR_PSAI_ROOT`. Tasks used here are identified by `unique_data_id` in
   `models/windows_tasks/`.

7. **LLM API keys** (optional, only to re-run the parsers) — read from
   `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`. None are stored in
   this repo.

---

## Environment variables

Paths are configurable so nothing is pinned to the authors' machine. Defaults
preserve the original values only so archived commands keep working; override
them for your environment.

| Variable | Used by | Purpose |
|---|---|---|
| `EVISITOR_ACTR_HOME` | `reproduce/*.ps1` | Folder containing `load-act-r.lisp` if ACT-R is not at `<repo>\actr7.x`. |
| `SPREADSHEET_ABLATION_BASE_MODEL` | Lisp model | **Selects the model build.** Set to `New_Error (3-5-2-TCP-7-21-2026).lisp` for the reported results. |
| `ABLATION_MODEL_SOURCE` | Python analysis | Base model the analysis *expects* (manifest validation). Match the above. |
| `ABLATION_CHECK_PROB` | Python analysis | Formula visual-check probability the manifest should show. Set `0.90` for the reported build. |
| `EVISITOR_MODELS_DIR` | Python analysis | Location of the `.lisp` model sources (default `models/spreadsheet_excel`). |
| `EVISITOR_HUMAN_DATA_ROOT` | analysis scripts | Root of your local human-data copy (default `G:\ExcelDataAnalysis`). |
| `EVISITOR_BATCH_LOGS_ROOT` | some analysis scripts | Root of raw per-run batch logs (regenerate, then point here). |
| `EVISITOR_PSAI_ROOT` | `analyze_task_times.py` | Root of the Paradigm Shift AI dataset. |
| `EVISITOR_OUTPUT_ROOT` | regen scripts | Where regenerated figures/CSVs are written (default: a repo-local folder). |

---

## 0. Verify model-source integrity

No runtime needed. Confirms the shipped models are byte-for-byte the builds that
produced the reported factorial:

```bash
cd models/spreadsheet_excel
python - <<'PY'
import json, hashlib, pathlib
h = json.load(open("../../analysis/batch_provenance/draft36_check090_factorial/source_hashes.json"))["hashes"]
bad = [f for f, x in h.items() if hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() != x]
print("MISMATCH:", bad) if bad else print(f"OK: all {len(h)} model sources match the freeze")
PY
```

## 1. Smoke test the model (recommended first run)

Once ACT-R is installed, from a PowerShell prompt at the repo root:

```powershell
pwsh reproduce/Run-Smoke-Test.ps1            # 3 runs of the Perfect cell (000)
pwsh reproduce/Run-Smoke-Test.ps1 -Cell 111 -Runs 3   # Full-Realistic cell
```

`Run-Smoke-Test.ps1` calls `reproduce/Setup-Layout.ps1`, which creates two
directory junctions at the repo root — `Spreadsheet\` → `models/spreadsheet_excel`
and `actr7.x\` → your ACT-R — so the **frozen** Lisp drivers (which load
`"actr7.x/load-act-r.lisp"` and `"Spreadsheet/Complete_error_model_tcp.lisp"`
relative to the working directory, using the original monorepo layout) resolve
without editing any hash-frozen source. Output lands in
`reproduce_output/smoke_cell<CELL>/batch_summary.csv`.

## 2. Regenerate a full batch

The reported factorial is 8 cells × 142 runs. The seed list and the source
freeze are shipped under `analysis/batch_provenance/draft36_check090_factorial/`.

* **Set the source freeze / seeds** (idempotent, refuses to overwrite):
  `python analysis/setup_2x2x2_batch.py`
* **Run each cell** with `models/spreadsheet_excel/Run_Ablation_2x2x2_Shard.lisp`
  (see the smoke script for the exact env vars, and `Run-Smoke-Test.ps1` as a
  template — raise `-Runs` to 142 and loop over all eight cells).
* **Assemble + analyze:** `python analysis/assemble_2x2x2_shards.py` then
  `python analysis/analyze_ablation_2x2x2.py`.

The **Appendix L** sweeps are launched by the parameterized scripts under
`analysis/batch_provenance/<batch>/run_*.ps1`; pass `-RepoRoot`/`-ActrHome` or
rely on their `$PSScriptRoot`-relative defaults.

## 3. Analysis only (no model runs)

The aggregate outputs behind Tables 4 and 7–9 and S11–S16 are already in
`analysis/batch_provenance/`. The analysis scripts read those directly. Scripts
that additionally need human data will raise a clear error until
`EVISITOR_HUMAN_DATA_ROOT` points at a real copy.

## 4. LLM parsing eval

The complete raw model outputs are shipped under `llm_parsing_eval/` (one JSON
per model × instruction variant × grounding condition) plus the gold workbook,
so you can **re-score** without any API access using the scripts in
`knowledge_acquisition/EnvironmentParsers/`. To **re-run** the parsers you need
your own API keys (billed) and results will differ run-to-run.

---

## The reproduction "trap"

The reusable ablation wrappers default to the **older** model build so archived
commands still validate. To reproduce the paper you must override two things:

* **Lisp side** — set `SPREADSHEET_ABLATION_BASE_MODEL="New_Error (3-5-2-TCP-7-21-2026).lisp"`.
  This build implements the per-token formula check (0.90) reported in the
  paper. The default fallback, `New_Error (3-5-2-TCP).lisp`, is the earlier
  build and will silently produce different numbers.
* **Python analysis side** — set `ABLATION_MODEL_SOURCE="New_Error (3-5-2-TCP-7-21-2026).lisp"`
  and `ABLATION_CHECK_PROB=0.90` so the manifest validator expects the values
  that were actually run.

The `reproduce/` scripts set the Lisp variable for you; the Python variables you
set in your shell before running the analysis.

---

## What is intentionally frozen (do not "fix")

* **`models/spreadsheet_excel/*.lisp`** — hash-frozen; editing them breaks the
  integrity guarantee in `README.md`. The `reproduce/` scripts bridge the layout
  around them rather than modifying them.
* **`analysis/batch_provenance/**/frozen_sources/`** — byte-exact snapshots of
  the scripts/sources as they were when each batch launched. They deliberately
  still contain the original machine paths; they are a record, not a runnable
  entry point. Use the parameterized copies one level up instead.
* **`llm_parsing_eval/*.log`, `*.json`** — raw run evidence; left verbatim.
