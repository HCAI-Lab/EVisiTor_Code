# Instruction -> ACT-R chunk pipeline: model comparison

- Gold subtasks: **93**
- Variants per model: **3** (original, paraphrase_1, paraphrase_2)
- Verbs: `Goto, Move, Select, Type, Press`
- Targets compared lower-cased + stripped; `Goto` ≡ `Move`.

## Summary (mean across variants)

| Model | Provider | Variants OK | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % |
|---|---|---:|---:|---:|---:|---:|---:|
| `gpt-5.5` | openai | 3/3 | 100.00 | 99.46 | 91.75 | 91.75 | 90.68 |
| `gpt-5.4-mini` | openai | 3/3 | 100.00 | 99.46 | 90.86 | 90.86 | 89.97 |
| `gpt-5.4-nano` | openai | 3/3 | 83.51 | 77.12 | 64.66 | 64.66 | 60.57 |
| `gemini-3.5-flash` | gemini | 3/3 | 100.00 | 99.46 | 93.01 | 93.01 | 92.47 |
| `gemini-3.1-flash-lite` | gemini | 3/3 | 99.28 | 99.28 | 93.01 | 93.01 | 92.47 |
| `openai/gpt-oss-120b` | openrouter | 3/3 | 86.74 | 80.57 | 68.23 | 68.23 | 63.80 |
| `deepseek/deepseek-v4-flash` | openrouter | 3/3 | 100.00 | 99.28 | 95.88 | 95.88 | 94.62 |
| `nvidia/nemotron-3-super-120b-a12b` | openrouter | 2/3 | 99.46 | 97.86 | 90.34 | 90.34 | 89.78 |

## Per-variant detail

### `gpt-5.5` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 92.47 | 92.47 | 91.40 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 90.32 | 90.32 | 89.25 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_3, subtask11_6, subtask11_8, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 100.00 | 99.46 | 92.47 | 92.47 | 91.40 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 99.46 | 99.46 | 99.46 | 0.00 |
| target_accuracy_pct | 90.32 | 92.47 | 91.75 | 2.15 |
| exact_match_pct | 90.32 | 92.47 | 91.75 | 2.15 |
| full_subtask_sequence_pct | 89.25 | 91.40 | 90.68 | 2.15 |

### `gpt-5.4-mini` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 92.47 | 92.47 | 91.40 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 100.00 | 99.46 | 89.78 | 89.78 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 99.46 | 99.46 | 99.46 | 0.00 |
| target_accuracy_pct | 89.78 | 92.47 | 90.86 | 2.69 |
| exact_match_pct | 89.78 | 92.47 | 90.86 | 2.69 |
| full_subtask_sequence_pct | 89.25 | 91.40 | 89.97 | 2.15 |

### `gpt-5.4-nano` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 100.00 | 93.01 | 93.01 | 92.47 | subtask1_3, subtask2_2, subtask2_3, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 50.54 | 31.91 | 10.64 | 10.64 | 0.00 | subtask1_1, subtask1_2, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_2, subtask12_1, subtask13_1, subtask14_1, subtask14_2, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 50.54 | 100.00 | 83.51 | 49.46 |
| action_accuracy_pct | 31.91 | 100.00 | 77.12 | 68.09 |
| target_accuracy_pct | 10.64 | 93.01 | 64.66 | 82.37 |
| exact_match_pct | 10.64 | 93.01 | 64.66 | 82.37 |
| full_subtask_sequence_pct | 0.00 | 92.47 | 60.57 | 92.47 |

### `gemini-3.5-flash` (gemini)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 90.86 | 90.86 | 90.32 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 93.01 | 93.01 | 92.47 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_3 |
| paraphrase_2 | OK | 100.00 | 99.46 | 95.16 | 95.16 | 94.62 | subtask1_3, subtask2_2, subtask2_4, subtask11_1, subtask11_6 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 99.46 | 99.46 | 99.46 | 0.00 |
| target_accuracy_pct | 90.86 | 95.16 | 93.01 | 4.30 |
| exact_match_pct | 90.86 | 95.16 | 93.01 | 4.30 |
| full_subtask_sequence_pct | 90.32 | 94.62 | 92.47 | 4.30 |

### `gemini-3.1-flash-lite` (gemini)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 100.00 | 95.16 | 95.16 | 94.62 | subtask1_3, subtask2_2, subtask11_1, subtask11_6, subtask14_1 |
| paraphrase_1 | OK | 100.00 | 100.00 | 93.01 | 93.01 | 92.47 | subtask1_3, subtask2_2, subtask2_3, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 97.85 | 97.85 | 90.86 | 90.86 | 90.32 | subtask1_3, subtask2_2, subtask2_3, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 97.85 | 100.00 | 99.28 | 2.15 |
| action_accuracy_pct | 97.85 | 100.00 | 99.28 | 2.15 |
| target_accuracy_pct | 90.86 | 95.16 | 93.01 | 4.30 |
| exact_match_pct | 90.86 | 95.16 | 93.01 | 4.30 |
| full_subtask_sequence_pct | 90.32 | 94.62 | 92.47 | 4.30 |

### `openai/gpt-oss-120b` (openrouter)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 98.39 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 90.32 | 90.32 | 89.25 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_3, subtask11_6, subtask11_8, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 60.22 | 43.85 | 24.06 | 24.06 | 12.90 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_6, subtask12_1, subtask13_1, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 60.22 | 100.00 | 86.74 | 39.78 |
| action_accuracy_pct | 43.85 | 99.46 | 80.57 | 55.61 |
| target_accuracy_pct | 24.06 | 90.32 | 68.23 | 66.26 |
| exact_match_pct | 24.06 | 90.32 | 68.23 | 66.26 |
| full_subtask_sequence_pct | 12.90 | 89.25 | 63.80 | 76.35 |

### `deepseek/deepseek-v4-flash` (openrouter)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 96.77 | 96.77 | 95.70 | subtask1_3, subtask2_2, subtask2_4, subtask14_1 |
| paraphrase_1 | OK | 100.00 | 99.46 | 96.77 | 96.77 | 95.70 | subtask1_3, subtask2_2, subtask2_4, subtask14_1 |
| paraphrase_2 | OK | 100.00 | 98.92 | 94.09 | 94.09 | 92.47 | subtask1_3, subtask2_2, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_4 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 98.92 | 99.46 | 99.28 | 0.54 |
| target_accuracy_pct | 94.09 | 96.77 | 95.88 | 2.68 |
| exact_match_pct | 94.09 | 96.77 | 95.88 | 2.68 |
| full_subtask_sequence_pct | 92.47 | 95.70 | 94.62 | 3.23 |

### `nvidia/nemotron-3-super-120b-a12b` (openrouter)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 98.39 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | NO | - | - | - | - | - | _error: task 7: duplicate subtask_id 20, task 9: duplicate subtask_id 20_ |
| paraphrase_2 | OK | 98.92 | 97.33 | 90.37 | 90.37 | 90.32 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 98.92 | 100.00 | 99.46 | 1.08 |
| action_accuracy_pct | 97.33 | 98.39 | 97.86 | 1.06 |
| target_accuracy_pct | 90.32 | 90.37 | 90.34 | 0.05 |
| exact_match_pct | 90.32 | 90.37 | 90.34 | 0.05 |
| full_subtask_sequence_pct | 89.25 | 90.32 | 89.78 | 1.07 |

## Authoring reduction (variant = original)

_From `gpt-5.5`:_
- NL lines authored: **42**
- Generated subtask chunks: **94**
- Generated action items: **187**
- Chunks/items avoided vs manual authoring: **281**


## UIA grounding (context = initial Excel scan)

Resolvability: % of generated Goto/Select targets that case-insensitively equal a UIA element name in `Spreadsheet/visicons.json`. Cell references (letter+digit) are exempt — they resolve through the grid, not the scan. The no-context column re-scores the published baseline artifacts of the same model/variant.

| Model | Variant | Resolvability (UIA ctx) % | Resolvability (no ctx) % | Fallback correct | Grounding failures | Unresolved |
|---|---|---:|---:|---:|---:|---:|
| _gold reference_ | - | 52.63 | 52.63 | 18 | 0 | 18 |
| `gpt-5.5` | original | 50.00 | 50.00 | 18 | 2 | 20 |
| `gpt-5.5` | paraphrase_1 | 50.00 | 50.00 | 18 | 2 | 20 |
| `gpt-5.5` | paraphrase_2 | 50.00 | 50.00 | 18 | 2 | 20 |
| `gpt-5.4-mini` | original | 50.00 | 52.63 | 18 | 2 | 20 |
| `gpt-5.4-mini` | paraphrase_1 | 50.00 | 40.00 | 18 | 2 | 20 |
| `gpt-5.4-mini` | paraphrase_2 | 50.00 | 50.00 | 18 | 2 | 20 |
| `gpt-5.4-nano` | original | 55.00 | 47.62 | 18 | 0 | 18 |
| `gpt-5.4-nano` | paraphrase_1 | 50.00 | 0.00 | 18 | 2 | 20 |
| `gpt-5.4-nano` | paraphrase_2 | 70.00 | 50.00 | 6 | 6 | 12 |
| `gemini-3.5-flash` | original | 50.00 | 50.00 | 18 | 2 | 20 |
| `gemini-3.5-flash` | paraphrase_1 | 65.00 | 50.00 | 14 | 0 | 14 |
| `gemini-3.5-flash` | paraphrase_2 | 65.00 | 50.00 | 14 | 0 | 14 |
| `gemini-3.1-flash-lite` | original | 65.00 | 52.63 | 14 | 0 | 14 |
| `gemini-3.1-flash-lite` | paraphrase_1 | 75.00 | 50.00 | 10 | 0 | 10 |
| `gemini-3.1-flash-lite` | paraphrase_2 | 73.68 | 50.00 | 10 | 0 | 10 |
| `openai/gpt-oss-120b` | original | 52.63 | - | 16 | 2 | 18 |
| `openai/gpt-oss-120b` | paraphrase_1 | 50.00 | - | 18 | 2 | 20 |
| `openai/gpt-oss-120b` | paraphrase_2 | 50.00 | - | 18 | 2 | 20 |
| `deepseek/deepseek-v4-flash` | original | 50.00 | - | 18 | 2 | 20 |
| `deepseek/deepseek-v4-flash` | paraphrase_1 | 55.00 | - | 18 | 0 | 18 |
| `deepseek/deepseek-v4-flash` | paraphrase_2 | 60.00 | - | 14 | 2 | 16 |
| `nvidia/nemotron-3-super-120b-a12b` | original | 63.16 | - | 12 | 2 | 14 |
| `nvidia/nemotron-3-super-120b-a12b` | paraphrase_2 | 65.00 | - | 14 | 0 | 14 |