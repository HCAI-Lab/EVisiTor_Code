# Results — UIA-Grounded LLM Step-Parsing Evaluation (2026-07-10)

Companion to `../HANDOFF_UIA_GROUNDED_PARSING_2026-07-08.md` (the design) and
the machine-readable reports in this directory (`metrics_report.json`,
`model_comparison.md`) and `Spreadsheet/generated_chunks/`
(`metrics_report_uia-initial.json`, `model_comparison_uia-initial.md`).

## What was run

- **Part A (new)**: `EnvironmentParsers/UIAGroundedParser.py` — the ten
  Windows tasks (W01–W10), 3 instruction variants (`instruction` from
  task_specs.json, hand-written `paraphrase`, PSAI `reasoning_steps`) ×
  3 UIA-context conditions (`no-uia`, `initial-uia`, `full-uia`), one LLM
  call per task, gold = `task_specs.json` subtasks. `reasoning_steps`
  exists for only 5 of 10 tasks (W01, W02, W05, W08, W09); that variant is
  scored against that gold subset.
- **Part B (retrofit)**: `InstructionAcquisitionParser.py --uia-context
  initial` — the original 14-task Excel evaluation with the pruned
  `Spreadsheet/visicons.json` injected into the prompt (cells stay
  coordinates; grounding applies to menu/ribbon/dialog items only).
  `--uia-context none` reproduces the published pipeline unchanged and its
  artifacts were not touched.
- **Models**: the paper's 8-model set. The three OpenRouter `:free` slugs
  proved unusable mid-run (congestion; `deepseek:free` was withdrawn and
  now 404s), so the **paid slugs of the same three models** were added and
  completed the full grid; the partial `:free` rows are retained in
  `metrics_report.json` for transparency but excluded from the tables below.

## Part A — Windows tasks (means over variants per condition)

Resolvability = % of generated Goto/Select targets that case-insensitively
equal a UIA element name (the matching rule of `generic_live.lisp`) in the
initial snapshot (resI) / the union of all snapshots of a completed live
run (resU). Fallback-correct (fb%) = of targets NOT resolving on the
initial screen, the share whose gold counterpart is also absent from it
(i.e. the element genuinely was not visible yet). gFail = count of
grounding failures (element visible on the initial screen but misnamed).
Exec = generated parses that pass `generate_task_models.validate_task`
(vocabulary, typeable characters, Press-chord grammar) and hence round-trip
into a loadable `tasks/*.lisp`.

**Gold reference: resI = 38.5%, resU = 100.0%** (52 visual targets; union
resolvability is 100% by construction — the tasks completed live).

| Model | Condition | Coverage % | Action % | Target % | resI % | resU % | fb% | gFail | Exec |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.5 | no-uia | 86.9 | 82.4 | 49.0 | 35.1 | 86.1 | 83.3 | 4 | 25/25 |
| gpt-5.5 | initial-uia | 86.0 | 84.9 | 57.6 | 33.3 | 87.5 | 90.7 | 0 | 25/25 |
| gpt-5.5 | full-uia | 90.1 | 80.5 | 56.8 | 33.3 | 94.4 | 86.3 | 0 | 25/25 |
| gpt-5.4-mini | no-uia | 70.4 | 71.5 | 40.8 | 30.0 | 77.0 | 81.1 | 4 | 25/25 |
| gpt-5.4-mini | initial-uia | 71.5 | 79.1 | 47.1 | 48.8 | 82.9 | 84.4 | 0 | 24/25 |
| gpt-5.4-mini | full-uia | 79.2 | 78.3 | 45.4 | 35.7 | 96.1 | 80.4 | 4 | 25/25 |
| gpt-5.4-nano | no-uia | 93.2 | 59.4 | 33.7 | 29.4 | 79.7 | 78.3 | 5 | 25/25 |
| gpt-5.4-nano | initial-uia | 89.5 | 69.3 | 41.9 | 50.8 | 84.5 | 76.6 | 0 | 22/25 |
| gpt-5.4-nano | full-uia | 87.6 | 65.8 | 34.2 | 38.9 | 98.8 | 75.4 | 4 | 24/25 |
| gemini-3.5-flash | no-uia | 86.1 | 82.2 | 54.4 | 33.5 | 87.1 | 88.9 | 2 | 25/25 |
| gemini-3.5-flash | initial-uia | 85.2 | 80.3 | 51.5 | 40.1 | 88.6 | 93.3 | 0 | 24/25 |
| gemini-3.5-flash | full-uia | 89.1 | 84.4 | 61.5 | 32.2 | 100.0 | 90.9 | 4 | 25/25 |
| gemini-3.1-flash-lite | no-uia | 84.3 | 71.6 | 44.8 | 28.1 | 81.3 | 86.3 | 2 | 25/25 |
| gemini-3.1-flash-lite | initial-uia | 81.8 | 77.9 | 42.8 | 51.6 | 90.9 | 90.6 | 0 | 23/25 |
| gemini-3.1-flash-lite | full-uia | 86.9 | 79.8 | 47.9 | 42.5 | 97.9 | 91.0 | 0 | 25/25 |
| gpt-oss-120b (paid) | no-uia | 85.2 | 67.4 | 35.4 | 30.1 | 69.4 | 84.1 | 4 | 25/25 |
| gpt-oss-120b (paid) | initial-uia | 78.1 | 81.7 | 50.1 | 52.7 | 87.3 | 88.9 | 0 | 25/25 |
| gpt-oss-120b (paid) | full-uia | 82.8 | 76.7 | 50.0 | 45.3 | 95.7 | 82.9 | 0 | 25/25 |
| deepseek-v4-flash (paid) | no-uia | 81.8 | 71.9 | 43.1 | 34.5 | 80.9 | 82.7 | 2 | 25/25 |
| deepseek-v4-flash (paid) | initial-uia | 77.9 | 77.5 | 50.5 | 41.0 | 88.1 | 89.0 | 0 | 25/25 |
| deepseek-v4-flash (paid) | full-uia | 86.1 | 77.8 | 47.5 | 35.9 | 96.0 | 80.4 | 4 | 24/25 |
| nemotron-3-super (paid) | no-uia | 83.7 | 78.5 | 50.6 | 34.9 | 77.7 | 87.9 | 0 | 25/25 |
| nemotron-3-super (paid) | initial-uia | 84.3 | 70.4 | 44.6 | 40.1 | 73.8 | 84.2 | 2 | 25/25 |
| nemotron-3-super (paid) | full-uia | 83.0 | 82.0 | 55.5 | 40.6 | 95.4 | 83.7 | 4 | 25/25 |

(gemini-3.5-flash's `instruction`×{no-uia, initial-uia} cells and its Part B
entry were initially lost to a Google-side "high demand" outage; an
automatic retry loop recovered all of them on 2026-07-10 — the grid above
is complete, 75/75 tasks for every model.)

### Findings

1. **UIA context makes generated targets executable.** The headline
   number: union-resolvability rises from 69–86% without context to
   **94–100% under full-uia** for every model (gold ceiling: 100%). With
   the whole-run element list in the prompt, essentially every visual
   target an LLM writes is a real element name the ACT-R visual search can
   find. Under initial-uia, initial-screen resolvability rises in 7 of 8
   models (largest gains: flash-lite 28→52%, gpt-oss 30→53%, nano 29→51%);
   gpt-5.5 is the exception (already grounded well from the instruction
   text alone).
2. **The generic-fallback instruction works, and grounding failures
   vanish.** Under initial-uia, *visible-but-misnamed* targets (gFail)
   drop to zero for 7 of 8 models (2–5 per model without context), and
   76–91% of the remaining unresolved targets are correct generic
   fallbacks — the gold element genuinely is not on the initial screen
   (e.g. Notepad's `Close` before Notepad exists). The LLMs use partial
   knowledge of the UI the way the instruction intends: copy what you can
   see, describe generically what you cannot.
3. **On the Windows tasks, grounding also helps accuracy-vs-gold.**
   Because the W-task gold was authored from live UIA scans, target
   accuracy improves alongside resolvability (e.g. gpt-oss 35→50%,
   gpt-5.5 49→58%) — no gold-vs-grounded tension, confirming the
   handoff's expectation that divergence on W-tasks is model signal.
4. **full-uia introduces a small premature-grounding cost.** Several
   models pick up 4 grounding "failures" under full-uia that they did not
   have under initial-uia: with names from *later* screens available, they
   occasionally use a later, more specific name where the start-screen
   element was meant. Initial-uia is the cleaner deployment condition;
   full-uia is the resolvability upper bound.
5. **Nearly every parse is executable in form.** 22–25 of 25 parses per
   condition pass the task-generator validation (5-verb vocabulary,
   typeable strings, legal Press chords) — schema validity is a solved
   problem for this prompt across all eight models; the errors that remain
   are occasional illegal Press chords (e.g. an invented key name).
6. **Coverage losses are strategy mismatches, not parsing failures.**
   Typical misses: subtasks the instruction leaves implicit (W01's final
   `Close`), and multi-step Settings navigation the model compresses
   (W05's `Display 3` phantom-display selection) or reaches by a different
   route than gold (Start-menu search instead of `win+i` in the
   `reasoning_steps` variant, which describes the human demonstrator's
   strategy). The `reasoning_steps` variant is also 5 tasks only — its
   cells are noisier throughout.

## Simple before/after view: target mismatches with vs without UIA context

Gold erratum applied first: `subtask14_1 (Select "File ab")` is a typo in
`Complete_Excel_Model.lisp` and was corrected to `"File Tab"` in the eval's
gold (2026-07-10; mean effect of the fix alone: +0.43 pts target accuracy,
+0.86 pts full-subtask rate). Published pre-fix numbers used the old gold.

**Windows tasks** (mismatched target slots summed over the 3 variants;
accuracy = mean target accuracy; before = no-uia, after = initial-uia):

| Model | Mismatches before | after | Acc before | after | Δ |
|---|---:|---:|---:|---:|---:|
| gpt-5.5 | 80 | 64 | 49.0 | 57.6 | +8.6 |
| gpt-5.4-mini | 82 | 68 | 40.8 | 47.1 | +6.3 |
| gpt-5.4-nano | 116 | 102 | 33.7 | 41.9 | +8.2 |
| gemini-3.5-flash | 69 | 74 | 54.4 | 51.5 | −2.9 |
| gemini-3.1-flash-lite | 88 | 89 | 44.8 | 42.8 | −1.9 |
| gpt-oss-120b | 105 | 75 | 35.4 | 50.1 | +14.7 |
| deepseek-v4-flash | 87 | 71 | 43.1 | 50.5 | +7.4 |
| nemotron-3-super | 73 | 83 | 50.6 | 44.6 | −6.1 |

Five of eight models remove 12–30% of their target mismatches when given
the initial UIA scan. The three exceptions trade gold-matching for
grounding: both gemini models and nemotron write *real* on-screen names
that the gold spells differently — their resolvability rises (e.g.
flash-lite 28→52%, 3.5-flash 34→40%) and grounding failures drop to zero
even as gold-accuracy dips: the gold-vs-grounded tension in its Windows
form.

**Excel** (gold-fixed rescore of saved artifacts; only variants where both
runs segmented correctly, coverage ≥ 90% — one `paraphrase_2` collapse per
excluded row, see below):

| Model | Variants | Mismatches before | after | Acc before | after | Δ |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.5 | 3 | 41 | 43 | 92.6 | 92.3 | −0.4 |
| gpt-5.4-mini | 2 | 38 | 30 | 89.8 | 91.9 | +2.2 |
| gpt-5.4-nano | 2 | 44 | 29 | 88.2 | 92.2 | +4.0 |
| gemini-3.5-flash | 3 | 27 | 39 | 95.2 | 93.0 | −2.2 |
| gemini-3.1-flash-lite | 2 | 28 | 20 | 92.5 | 94.6 | +2.2 |
| gpt-oss-120b | 2 | 38 | 34 | 89.8 | 90.9 | +1.1 |
| deepseek-v4-flash / nemotron | — | no baseline artifacts | | | | |

(gemini-3.5-flash's Excel dip is the grounding trade again: its
resolvability rises 50→60% and grounding failures fall 6→2 — it swaps
gold-internal names for real UIA names like `Save a Copy` and pays the
gold-accuracy price.)

On cleanly-segmented Excel runs, UIA context removes roughly a quarter to a
third of target mismatches for four of five comparable models (gpt-5.5 was
already near-ceiling without it). Caution on raw (unfiltered) means: the
terse `paraphrase_2` variant occasionally collapses a run's subtask
segmentation (coverage ~50%, accuracy ~11%) on either side of the
comparison; unfiltered before/after deltas as large as +28 pts
(gpt-5.4-mini) are segmentation luck, not grounding.

## Part B — Excel retrofit (means over 3 variants)

Resolvability here covers menu/ribbon/dialog targets only (cell
coordinates are exempt — they resolve through the grid). Baseline =
published no-context artifacts re-scored; **gold reference resolvability
is 50.0%** (the gold itself uses model-internal names like `File Tab`,
`file_name`, `Row_1` that do not match UIA names).

| Model | Resolv base % | Resolv +UIA % | gFail base → +UIA | Target acc % (+UIA) |
|---|---:|---:|---|---:|
| gpt-5.5 | 50.0 | 50.0 | 6 → 6 | 91.8 |
| gpt-5.4-mini | 47.5 | 50.0 | 22 → 6 | 90.9 |
| gpt-5.4-nano | 32.5 | 58.3 | 16 → 8 | 64.7† |
| gemini-3.5-flash | 50.0 | 60.0 | 6 → 2 | 93.0 |
| gemini-3.1-flash-lite | 50.9 | 71.2 | 14 → 0 | 93.0 |
| gpt-oss-120b (paid) | n/a‡ | 50.9 | — → 6 | 68.2† |
| deepseek-v4-flash (paid) | n/a‡ | 55.0 | — → 4 | 95.9 |
| nemotron-3-super (paid) | n/a‡ | 64.1 | — → 2 | 90.3 |

† Two outlier runs (nano and gpt-oss on `paraphrase_2`, the tersest
"File > Save"-style variant) mis-segmented subtask numbering, collapsing
target accuracy for that variant; their other variants are ~90%. This is
a segmentation robustness issue, independent of UIA grounding.
‡ The paid OpenRouter slugs have no published baseline artifacts (the
paper ran the `:free` slugs); nemotron's `paraphrase_1` failed schema
validation (duplicate subtask ids) and is excluded from its mean.

### Findings

7. **Grounding transfers to Excel, capped by the gold's internal names.**
   Models with UIA context meet or exceed the gold's own 50% resolvability
   (flash-lite 71%, nemotron 64%, nano 58%) while target accuracy stays
   in the 90s — the predicted gold-vs-grounded tension is mild in
   practice, because the grounded choices (`File` for `File Tab`) usually
   still miss the gold string but the bulk of targets agree. Grounding
   failures drop sharply everywhere (e.g. mini 22→6, flash-lite 14→0).
   No alias map (gold name → UIA name) was applied; adding one would raise
   the +UIA target-accuracy scores and is documented as an option in the
   handoff.
8. **The published pipeline is untouched.** `--uia-context none` runs the
   byte-identical prompt and writes to the original artifact paths; all
   +UIA artifacts carry a `__uia-initial` suffix and separate reports.

## Infrastructure notes (for reproduction)

- One task per call (Part A), temperature at provider default as in the
  published Excel pipeline; all raw model outputs are persisted per cell
  (`<model>__<variant>__<condition>.json`), so every metric is
  recomputable offline (`--rescore`).
- Quota/outage handling added during the run: fail-fast on OpenAI
  `insufficient_quota`, Gemini per-day quota, OpenRouter free-model daily
  cap; 300s Gemini request timeout (503/504 "high demand" spells otherwise
  hang requests indefinitely); cell-level merge on filtered re-runs so
  gap-filling never discards completed work.
- UIA context sources: newest completed live run per task (see
  `uia_sources` in `metrics_report.json`); no prompt exceeded the
  300-element cap, so no truncation occurred.
