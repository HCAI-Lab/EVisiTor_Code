# EVisiTor — code and materials

Code and materials for *AI-augmented ACT-R modeling in real interfaces:
Automating visual perception, knowledge acquisition, and motor misexecution*
(Bagherzadeh & Tehranchi, 2026).

All model sources in `models/spreadsheet_excel/` are the exact builds that
produced the reported results: their SHA-256 hashes match
`analysis/batch_provenance/draft36_check090_factorial/source_hashes.json`
(the freeze recorded when the reported batch was launched).

## Reproducing

See **[`REPRODUCE.md`](REPRODUCE.md)** for step-by-step instructions, the full
environment-variable list, and a matrix of what reproduces from a clone alone
versus what additionally needs the ACT-R runtime, IRB-restricted human data, or
the licensed dataset. Two requirements are easy to miss:

- **ACT-R 7.x is not bundled** (it is distributed separately). Download it from
  <https://github.com/asmaloney/ACT-R> and unpack it to `actr7.x/`, or set
  `EVISITOR_ACTR_HOME`. `reproduce/Setup-Layout.ps1` wires it into the layout the
  frozen Lisp drivers expect; `reproduce/Run-Smoke-Test.ps1` then runs a short
  end-to-end check.
- **Select the reported build.** Set
  `SPREADSHEET_ABLATION_BASE_MODEL="New_Error (3-5-2-TCP-7-21-2026).lisp"` — the
  default fallback is the *earlier* build without the per-token formula check.
  See REPRODUCE.md → "The reproduction trap".

## Layout

- `models/spreadsheet_excel/` — ACT-R spreadsheet models. The reported
  factorial batch loads `Complete_error_model_tcp.lisp`, which pulls in
  `fucntion_new_tcp.lisp` (sic; literal filename), `Visicon_generator_V3.lisp`,
  `running_model_v4.lisp`, and `Ablation_support.lisp`; each ablation cell
  loads the base model named by the `SPREADSHEET_ABLATION_BASE_MODEL`
  environment variable, which the reported batch set to
  `New_Error (3-5-2-TCP-7-21-2026).lisp` (its default fallback,
  `New_Error (3-5-2-TCP).lisp`, is the earlier build and is kept here only for
  reference — it does **not** implement the per-token formula check reported in
  the paper). Also included: all eight 2x2x2 factorial cells, the shard driver
  `Run_Ablation_2x2x2_Shard.lisp`, the Appendix L sweep drivers
  (`Ablation_NoVisual_Rates.lisp`, `Ablation_NoVisual_CheckProb.lisp`,
  `Run_CheckProb_Shard.lisp`, `Ablation_Full_Realistic_Rates.lisp`), saved
  visicon snapshots used for batch replay (`visicons_saved*/`), the generated
  declarative chunks (`generated_chunks/`), and the KST starting workbook
  (`task_environment/normalization.xlsx`).

  The eight factorial cells (VBC coding, Supplementary Appendix K):

  | cell | file | cell | file |
  |------|------|------|------|
  | 000 | `Ablation_Perfect.lisp` | 110 | `Ablation_Visual_Plus_Batched.lisp` |
  | 100 | `Ablation_Visual_Search_Only.lisp` | 101 | `Ablation_Visual_Plus_Checking.lisp` |
  | 010 | `Ablation_Batched_Formula_Typing.lisp` | 011 | `Ablation_Batched_Plus_Checking.lisp` |
  | 001 | `Ablation_Correction_Checking.lisp` | 111 | `Ablation_Full_Realistic.lisp` |

  Legacy drivers from the earlier 150-run design (`Run_Ablation_150.lisp`,
  `Run_Ablation_25.lisp`, `Run_Typo_Sweep.lisp`, `Perfect_model.lisp`,
  `Realistic_user.lisp`, `Ablation_Typing_Errors_Only.lisp`) are retained for
  history; they are not the pipeline behind the reported numbers.
- `models/windows_tasks/` — the six-task Windows generalization probe:
  task-independent model (`generic_interface_model.lisp`,
  `generic_helpers.lisp`), task specs and gold/generated chunks, live-run
  driver files, resolver name maps and transcript (`agent_resolution/`),
  per-task completion logs (`logs/<task>/task_times.csv`), and screen
  recordings of the six live model runs (`model_run_recordings/`).
- `bridge/VisiTor/` — the VisiTor/EVisiTor eyes-and-hands bridge (UIA
  perception -> visicon, motor execution, `knowledge_descipherer.py` (sic)).
- `knowledge_acquisition/EnvironmentParsers/` — instruction-to-chunk and
  UIA-grounded parsers (prompt templates are embedded in the parser
  sources), scoring (`functional_check.py`, `analyze_w6_uia.py`,
  `build_w6_excel.py`, `run_perstep.py`), and vision-parser evaluations.
  `Dismal_annotated/` and `Dismal_json/` hold the annotated Dismal interface
  states behind Supplementary Figures S5-S7.
- `llm_parsing_eval/` — complete raw LLM outputs (one JSON per model x
  instruction variant x grounding condition), run logs, scoring workbook
  (`W6_model_IO_and_gold_2026-07-16.xlsx`), and results report for the
  generalization probe.
- `analysis/` — the scripts behind the reported results:
  `setup_2x2x2_batch.py` (seed list + source freeze), `assemble_2x2x2_shards.py`,
  `analyze_ablation_2x2x2.py` + `ablation_2x2x2_common.py` (cell summaries,
  saturated factorial fit, Wasserstein-1), `w1_per_task_check_rate.py`,
  `analyze_draft34_error_rate_sweeps.py` and `analyze_checkprob_sweep.py`
  (Supplementary Appendix L), `analyze_human_error_rates.py` (calibrated
  0.034 / 0.063 typo rates), and `compare_model_human_times.py`.
  - `analysis/batch_provenance/` — per-batch reproducibility configuration and
    aggregate outputs: the 142-element seed list, the SHA-256 source freeze
    (`source_hashes.json`), the `design_manifest.json` of each Appendix L sweep,
    and the aggregates behind Tables 4 and 7-9 and S11-S16
    (`cell_summary.csv`, `factorial_effects.{csv,json}`, `w1_results.json`,
    `task_interactions.csv`, `mechanism_diagnostics.csv`,
    `error_rate_fit_summary.*`, `checkprob_fit_summary.*`). The check-probability
    sweep ran against a slightly earlier `Ablation_support.lisp` than the
    factorial freeze, so that sweep's own `frozen_sources/` set is kept intact
    alongside its manifest.
  - `analysis/human_data_scripts/` and `analysis/regen_scripts/` — the scripts
    that produced the human-side statistics (keystroke, transition, IKI, and
    gaze analyses); scripts only, see below.
  - `analysis/legacy_pre-revision_2026-07/` — superseded outputs and scripts
    from the 7-14 July 2026 analysis of the earlier 150-run batch. **These do
    not correspond to any number in the submitted manuscript** and are kept only
    for revision history.
- `tools/` — auxiliary utilities (UIA latency measurement, standalone
  parsers).

## What is deliberately NOT here

- **Human participant data** (keystroke logs, completion times, gaze
  videos). The data are IRB-restricted (protocol STUDY00012835) and are
  available upon request, per the paper's Data Availability statement.
  `analysis/human_data_scripts/` documents exactly how the published
  human-side statistics were computed, but ships no data. The analysis
  scripts read the human CSVs from a local `G:\ExcelDataAnalysis` path by
  default; set `EVISITOR_HUMAN_DATA_ROOT` to point at your own copy (no script
  edits needed — see REPRODUCE.md).
- **Raw per-run model batches** (the 1,136-run factorial plus the Appendix L
  sweeps, several hundred MB of per-run CSVs). They are regenerable with the
  run scripts and archived seed list above; the aggregate outputs are in
  `analysis/batch_provenance/`.
- **Paradigm Shift AI dataset content** (demonstration recordings and event
  streams). Obtain the dataset from its publishers; tasks used here are
  identified by their `unique_data_id` in `models/windows_tasks/` and
  Supplementary Appendix M.

API keys are read from environment variables (`OPENAI_API_KEY`,
`GEMINI_API_KEY`, `OPENROUTER_API_KEY`); no credentials are stored in this
repository.
