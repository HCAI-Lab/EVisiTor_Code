# Instruction -> ACT-R chunk pipeline: model comparison

- Gold subtasks: **93**
- Variants per model: **3** (original, paraphrase_1, paraphrase_2)
- Verbs: `Goto, Move, Select, Type, Press`
- Targets compared lower-cased + stripped; `Goto` ≡ `Move`.

## Summary (mean across variants)

| Model | Provider | Variants OK | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % |
|---|---|---:|---:|---:|---:|---:|---:|
| `gpt-5.5` | openai | 3/3 | 100.00 | 99.46 | 92.29 | 92.29 | 91.40 |
| `gpt-5.4-mini` | openai | 3/3 | 82.44 | 76.65 | 63.06 | 63.06 | 58.78 |
| `gpt-5.4-nano` | openai | 3/3 | 81.36 | 68.90 | 62.18 | 59.85 | 56.27 |
| `gemini-3.5-flash` | gemini | 3/3 | 100.00 | 99.46 | 94.62 | 94.62 | 93.55 |
| `gemini-3.1-flash-lite` | gemini | 3/3 | 83.51 | 77.36 | 65.57 | 65.57 | 60.58 |
| `openai/gpt-oss-120b:free` | openrouter | 3/3 | 83.87 | 78.25 | 65.38 | 65.38 | 60.22 |

## Per-variant detail

### `gpt-5.5` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 96.77 | 96.77 | 95.70 | subtask1_3, subtask2_2, subtask2_4, subtask14_1 |
| paraphrase_2 | OK | 100.00 | 99.46 | 89.78 | 89.78 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 99.46 | 99.46 | 99.46 | 0.00 |
| target_accuracy_pct | 89.78 | 96.77 | 92.29 | 6.99 |
| exact_match_pct | 89.78 | 96.77 | 92.29 | 6.99 |
| full_subtask_sequence_pct | 89.25 | 95.70 | 91.40 | 6.45 |

### `gpt-5.4-mini` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 98.39 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 88.17 | 88.17 | 87.10 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_2, subtask11_3, subtask11_6, subtask11_7, subtask11_8, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 47.31 | 32.09 | 10.70 | 10.70 | 0.00 | subtask1_1, subtask2_1, subtask2_2, subtask2_3, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_2, subtask12_1, subtask13_1, subtask14_1, subtask14_2 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 47.31 | 100.00 | 82.44 | 52.69 |
| action_accuracy_pct | 32.09 | 99.46 | 76.65 | 67.37 |
| target_accuracy_pct | 10.70 | 90.32 | 63.06 | 79.62 |
| exact_match_pct | 10.70 | 90.32 | 63.06 | 79.62 |
| full_subtask_sequence_pct | 0.00 | 89.25 | 58.78 | 89.25 |

### `gpt-5.4-nano` (openai)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 98.94 | 89.89 | 89.89 | 90.32 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 79.03 | 86.02 | 79.03 | 78.49 | subtask1_1, subtask1_2, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_2, subtask11_3, subtask11_4, subtask11_5, subtask11_6, subtask11_7, subtask11_8, subtask11_9, subtask11_10, subtask14_1, subtask14_2, subtask14_3 |
| paraphrase_2 | OK | 44.09 | 28.72 | 10.64 | 10.64 | 0.00 | subtask1_1, subtask2_1, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_2, subtask12_1, subtask13_1, subtask14_1 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 44.09 | 100.00 | 81.36 | 55.91 |
| action_accuracy_pct | 28.72 | 98.94 | 68.90 | 70.22 |
| target_accuracy_pct | 10.64 | 89.89 | 62.18 | 79.25 |
| exact_match_pct | 10.64 | 89.89 | 59.85 | 79.25 |
| full_subtask_sequence_pct | 0.00 | 90.32 | 56.27 | 90.32 |

### `gemini-3.5-flash` (gemini)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 99.46 | 94.62 | 94.62 | 93.55 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_4, subtask14_1 |
| paraphrase_1 | OK | 100.00 | 99.46 | 92.47 | 92.47 | 91.40 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 100.00 | 99.46 | 96.77 | 96.77 | 95.70 | subtask1_3, subtask2_2, subtask2_4, subtask14_1 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 100.00 | 100.00 | 100.00 | 0.00 |
| action_accuracy_pct | 99.46 | 99.46 | 99.46 | 0.00 |
| target_accuracy_pct | 92.47 | 96.77 | 94.62 | 4.30 |
| exact_match_pct | 92.47 | 96.77 | 94.62 | 4.30 |
| full_subtask_sequence_pct | 91.40 | 95.70 | 93.55 | 4.30 |

### `gemini-3.1-flash-lite` (gemini)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 98.39 | 91.40 | 91.40 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 92.47 | 92.47 | 91.40 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 50.54 | 34.22 | 12.83 | 12.83 | 1.08 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask2_4, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_2, subtask12_1, subtask13_1, subtask14_1, subtask14_2 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 50.54 | 100.00 | 83.51 | 49.46 |
| action_accuracy_pct | 34.22 | 99.46 | 77.36 | 65.24 |
| target_accuracy_pct | 12.83 | 92.47 | 65.57 | 79.64 |
| exact_match_pct | 12.83 | 92.47 | 65.57 | 79.64 |
| full_subtask_sequence_pct | 1.08 | 91.40 | 60.58 | 90.32 |

### `openai/gpt-oss-120b:free` (openrouter)

| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |
|---|:---:|---:|---:|---:|---:|---:|---|
| original | OK | 100.00 | 100.00 | 90.32 | 90.32 | 89.25 | subtask1_1, subtask1_3, subtask2_1, subtask2_2, subtask2_3, subtask3_8, subtask11_1, subtask11_6, subtask14_1, subtask14_3 |
| paraphrase_1 | OK | 100.00 | 99.46 | 88.17 | 88.17 | 87.10 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask11_1, subtask11_2, subtask11_3, subtask11_6, subtask11_7, subtask11_8, subtask14_1, subtask14_3 |
| paraphrase_2 | OK | 51.61 | 35.29 | 17.65 | 17.65 | 4.30 | subtask1_3, subtask2_2, subtask2_3, subtask2_4, subtask3_1, subtask3_2, subtask3_3, subtask3_4, subtask3_5, subtask4_1, subtask5_1, subtask5_2, subtask5_3, subtask5_4, subtask5_5, subtask6_1, subtask7_1, subtask7_2, subtask7_3, subtask7_4, subtask7_5, subtask7_6, subtask7_7, subtask7_8, subtask7_9, subtask7_10, subtask8_1, subtask9_1, subtask9_2, subtask9_3, subtask9_4, subtask9_5, subtask9_6, subtask9_7, subtask9_8, subtask9_9, subtask9_10, subtask10_1, subtask11_1, subtask11_2, subtask12_1, subtask13_1, subtask14_1, subtask14_3 |

_Robustness across paraphrases (min / max / mean / spread):_

| Metric | min | max | mean | spread |
|---|---:|---:|---:|---:|
| subtask_coverage_pct | 51.61 | 100.00 | 83.87 | 48.39 |
| action_accuracy_pct | 35.29 | 100.00 | 78.25 | 64.71 |
| target_accuracy_pct | 17.65 | 90.32 | 65.38 | 72.67 |
| exact_match_pct | 17.65 | 90.32 | 65.38 | 72.67 |
| full_subtask_sequence_pct | 4.30 | 89.25 | 60.22 | 84.95 |

## Authoring reduction (variant = original)

_From `gpt-5.5`:_
- NL lines authored: **42**
- Generated subtask chunks: **94**
- Generated action items: **187**
- Chunks/items avoided vs manual authoring: **281**
