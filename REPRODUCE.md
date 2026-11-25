# Reproducing the EVisiTor results

This guide explains **exactly what can be reproduced from a clone, and what
requires resources that cannot be redistributed** (the ACT-R runtime,
IRB-restricted human data, a licensed third-party dataset, and paid LLM API
keys). Read the [reproduction matrix](#reproduction-matrix) first so you know
which parts apply to you.

For what each folder contains, see [`README.md`](README.md). This file is only
about *running* things.

> The reported factorial uses the July 21 model, a formula-check probability of
> 0.90 in checking cells, and 142 runs per cell. Set the
> [environment variables](#environment-variables) before regenerating or
> analyzing this batch.

---

## Reproduction matrix

| Result | Reproducible from a clone alone? | Also needs |
|---|---|---|
| **Model-source integrity** (the shipped models are the exact reported builds) | ✅ Yes | just `python` + `hashlib` — see [Verify integrity](#0-verify-model-source-integrity) |
| **Re-score the shipped raw LLM outputs** (generalization / parsing eval) | ✅ Yes | core Python deps |
| **Inspect the published aggregate values** for Tables 4, 7–9, and S11–S16 | ✅ Yes | Open the CSV or JSON files in `analysis/batch_provenance/`. |
| **Recompute factorial tables and the interaction plot** | ❌ No | An assembled batch with per-run files for all eight cells, the authorized human CSVs, and the analysis dependencies. |
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

3. **SBCL** (Steel Bank Common Lisp) on your `PATH`. Initialize Quicklisp in
   SBCL so the model can load `inferior-shell`, `usocket`, and `cl-json`.

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
| `FORMULA_CHECK_PROB` | Lisp model | Per-token formula-check probability in checking cells. Defaults to `0.40`. Set to `0.90` for the reported factorial. |
| `ABLATION_MODEL_SOURCE` | Python analysis | Base model to verify against the source hashes. Match `SPREADSHEET_ABLATION_BASE_MODEL`. |
| `ABLATION_CHECK_PROB` | Python analysis | Formula-check probability to expect in checking-cell manifests. Defaults to `0.40`. Set to `0.90` for the reported factorial. |
| `ABLATION_N_RUNS` | Python batch scripts | Runs per cell. Defaults to `150`. Set to `142` for the reported factorial. |
| `ABLATION_BATCH_ROOT` | Python batch scripts | Batch directory containing the seeds, source hashes, and run folders. Defaults to `analysis/logs/ablation_2x2x2_150_july20_correct_typo_rates` under the repository root. |
| `ABLATION_OUT_DIR` | Factorial analysis | Optional existing output directory for regenerated CSVs, JSON, and plots. Defaults to `ABLATION_BATCH_ROOT`. |
| `EVISITOR_MODELS_DIR` | Python analysis | Location of the `.lisp` model sources (default `models/spreadsheet_excel`). |
| `EVISITOR_HUMAN_DATA_ROOT` | analysis scripts | Root of your local human-data copy (default `G:\ExcelDataAnalysis`). |
| `EVISITOR_BATCH_LOGS_ROOT` | some analysis scripts | Root of raw per-run batch logs (regenerate, then point here). |
| `EVISITOR_PSAI_ROOT` | `analyze_task_times.py` | Root of the Paradigm Shift AI dataset. |
| `EVISITOR_OUTPUT_ROOT` | regen scripts | Where regenerated figures/CSVs are written (default: a repo-local folder). |

---

## 0. Verify model-source integrity

From the repository root, use Python to compare the shipped files with their
archived SHA-256 hashes. This checks 15 model sources for the reported
factorial and 10 frozen sources for the draft34 check-probability sweep.

```sh
python reproduce/verify_integrity.py
```

## 1. Smoke test the model (recommended first run)

Once ACT-R is installed, from a PowerShell prompt at the repo root:

```powershell
$env:FORMULA_CHECK_PROB = '0.90'
pwsh reproduce/Run-Smoke-Test.ps1            # 3 runs of the Perfect cell (000)
pwsh reproduce/Run-Smoke-Test.ps1 -Cell 111 -Runs 3   # Full-Realistic cell
```

`Run-Smoke-Test.ps1` calls `reproduce/Setup-Layout.ps1`, which creates two
directory junctions at the repo root — `Spreadsheet\` → `models/spreadsheet_excel`
and `actr7.x\` → your ACT-R — so the **frozen** Lisp drivers (which load
`"actr7.x/load-act-r.lisp"` and `"Spreadsheet/Complete_error_model_tcp.lisp"`
relative to the working directory, using the original monorepo layout) resolve
without editing any hash-frozen source. Each cell writes its summary under its
wrapper name. For example, the second command writes
`reproduce_output/smoke_cell111/Ablation_Full_Realistic/batch_summary.csv`.

For typo substitutions, the model looks for
`../MSR Spelling Correction Data/motor_model.json` relative to the loaded
`fucntion_new_tcp.lisp`. A clone uses the built-in QWERTY fallback. If you
want to replay a batch that used a custom substitution table, supply the
same table at that path.

## 2. Regenerate a full batch

The reported factorial has eight cells with 142 runs each. After verifying the
sources in section 0, open PowerShell at the repository root. Create a new batch
directory and copy in the archived freeze and seed list (142 primary seeds and
50 reserves).

```powershell
$env:ABLATION_BATCH_ROOT = Join-Path $PWD 'reproduce_output/factorial_142'
if (Test-Path $env:ABLATION_BATCH_ROOT) { throw 'Choose a new batch directory.' }
New-Item -ItemType Directory -Path $env:ABLATION_BATCH_ROOT | Out-Null
$freeze = 'analysis/batch_provenance/draft36_check090_factorial'
Copy-Item "$freeze/seed_list.txt", "$freeze/source_hashes.json" -Destination $env:ABLATION_BATCH_ROOT
```

In the same shell, generate a single shard for each cell. The Lisp driver uses
`BATCH_ROOT` for one shard. The Python assembler uses `ABLATION_BATCH_ROOT`
for the entire experiment.

```powershell
./reproduce/Setup-Layout.ps1
$env:SPREADSHEET_ABLATION_BASE_MODEL = 'New_Error (3-5-2-TCP-7-21-2026).lisp'
$env:FORMULA_CHECK_PROB = '0.90'
$env:ABLATION_MODEL_SOURCE = $env:SPREADSHEET_ABLATION_BASE_MODEL
$env:ABLATION_CHECK_PROB = $env:FORMULA_CHECK_PROB
$env:ABLATION_N_RUNS = '142'
$env:SEED_FILE = Join-Path $env:ABLATION_BATCH_ROOT 'seed_list.txt'
$env:SEED_START = '1'
$env:SEED_COUNT = $env:ABLATION_N_RUNS
$env:ACTR_RECOMPILE = '1'
$wrappers = [ordered]@{
    '000' = 'Ablation_Perfect.lisp'
    '100' = 'Ablation_Visual_Search_Only.lisp'
    '010' = 'Ablation_Batched_Formula_Typing.lisp'
    '001' = 'Ablation_Correction_Checking.lisp'
    '110' = 'Ablation_Visual_Plus_Batched.lisp'
    '101' = 'Ablation_Visual_Plus_Checking.lisp'
    '011' = 'Ablation_Batched_Plus_Checking.lisp'
    '111' = 'Ablation_Full_Realistic.lisp'
}
foreach ($code in $wrappers.Keys) {
    $env:CELL_CODE = $code
    $env:CELL_SOURCE = $wrappers[$code]
    $shard = Join-Path $env:ABLATION_BATCH_ROOT "shards/s_${code}_1"
    $env:BATCH_ROOT = $shard.Replace('\', '/') + '/'
    sbcl --dynamic-space-size 4096 --noinform --non-interactive --load Spreadsheet/Run_Ablation_2x2x2_Shard.lisp
    if ($LASTEXITCODE -ne 0) { throw "Shard failed for cell $code" }
}
python analysis/assemble_2x2x2_shards.py
```

The assembler reads `shards/s_<code>_*/<wrapper-name>/run_NNN/` inside the
batch and validates each run against the archived seeds and cell settings.
After it reports success for all eight cells, the assembled runs are under
`<wrapper-name>/run_NNN/` at the batch root. Continue with section 3.

The **Appendix L** sweeps are launched by the parameterized scripts under
`analysis/batch_provenance/<batch>/run_*.ps1`; pass `-RepoRoot`/`-ActrHome` or
rely on their `$PSScriptRoot`-relative defaults.

## 3. Analysis only (no model runs)

To look up published table values, open the archived CSV or JSON files in
[batch provenance](analysis/batch_provenance/). Each factorial cell has a row
in [the archived cell summary](analysis/batch_provenance/draft36_check090_factorial/cell_summary.csv).

To recompute the factorial outputs with `analyze_ablation_2x2x2.py`, use an
assembled batch from section 2 or an existing copy. It must contain
`source_hashes.json`, `seed_list.txt`, and the per-run `task_times.csv`,
`condition_manifest.json`, `attention_shifts.csv`, `keypresses.csv`, and
`run_postcheck.json` for all eight cells. The script also reads these two
IRB-restricted files from your authorized human-data directory.

- `HumanCompletionTime.csv`
- `Human Data/eye_tracking_analysis/task_time_windows_from_breakdown.csv`

From the repository root, point these settings at your own directories. The
analysis writes its results into the batch root unless you set
`ABLATION_OUT_DIR` to a separate existing directory. Leave the optional
`ABLATION_TASK1_OVERRIDE_DIR` unset for the reported factorial.

```powershell
$env:ABLATION_BATCH_ROOT = Join-Path $PWD 'reproduce_output/factorial_142'
$env:ABLATION_N_RUNS = '142'
$env:ABLATION_MODEL_SOURCE = 'New_Error (3-5-2-TCP-7-21-2026).lisp'
$env:ABLATION_CHECK_PROB = '0.90'
$env:EVISITOR_HUMAN_DATA_ROOT = 'C:\path\to\authorized-human-data'
python analysis/analyze_ablation_2x2x2.py
```

## 4. LLM parsing eval

The complete raw model outputs are shipped under `llm_parsing_eval/` (one JSON
per model × instruction variant × grounding condition) plus the gold workbook,
so you can **re-score** without any API access using the scripts in
`knowledge_acquisition/EnvironmentParsers/`. To **re-run** the parsers you need
your own API keys (billed) and results will differ run-to-run.

---

## The reproduction "trap"

The reusable wrappers default to `New_Error (3-5-2-TCP).lisp` and a
formula-check probability of `0.40` in checking cells. The smoke script selects
the July 21 build and takes `FORMULA_CHECK_PROB` from your shell. For the
reported factorial, use the model and probability together in sections 1–2.
Use the matching Python settings in section 3 so the analysis validates the
source hashes and run manifests against that configuration.

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
