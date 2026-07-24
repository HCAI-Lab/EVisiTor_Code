# UIA-grounded step parsing: Windows tasks W01-W10

- Gold: `task_specs.json` subtasks (21 subtask lists over 10 tasks).
- Variants: instruction, paraphrase, reasoning_steps, guide (reasoning_steps exists for only 5 of 10 tasks; its metrics are computed against that subset of the gold).
- Conditions: no-uia (baseline), initial-uia (visicons_001.json of the newest completed live run), full-uia (deduped union of all snapshots of that run).
- Resolvability: % of generated Goto/Select targets that case-insensitively equal a UIA element name (matching semantics of generic_live.lisp) in the initial snapshot / in the union of all snapshots.
- Fallback-correct: among targets NOT resolving in the initial snapshot, those whose gold counterpart is also absent from it (the element genuinely was not visible yet); the complement, grounding failures, were visible but misnamed.

Gold reference: resolvability initial = 36.00%, union = 100.00% (25 visual targets). Gold targets absent from the union are cases where the live scan never captured the element under that exact name.

## Summary (mean over variants, per condition)

| Model | Condition | Cells OK | Coverage % | Action acc % | Target acc % | Exact % | Resolv (initial) % | Resolv (union) % | Fallback correct % of unresolved | Exec-valid tasks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gpt-5.5` | no-uia | 4/4 | 88.89 | 73.41 | 52.83 | 52.83 | 18.30 | 64.22 | 57.64 | 20/21 |
| `gpt-5.5` | initial-uia | 4/4 | 88.89 | 73.26 | 48.84 | 47.33 | 25.30 | 67.53 | 48.81 | 21/21 |
| `gpt-5.5` | full-uia | 2/2 | 97.62 | 80.00 | 76.25 | 75.00 | 36.75 | 100.00 | 80.41 | 12/12 |
| `gpt-5.4-mini` | no-uia | 4/4 | 81.75 | 65.73 | 42.91 | 42.11 | 21.59 | 60.84 | 49.08 | 20/21 |
| `gpt-5.4-mini` | initial-uia | 4/4 | 84.13 | 71.68 | 46.04 | 44.52 | 33.53 | 75.69 | 60.22 | 19/21 |
| `gpt-5.4-mini` | full-uia | 2/2 | 90.47 | 86.17 | 81.77 | 80.30 | 41.91 | 100.00 | 85.41 | 12/12 |
| `gpt-5.4-nano` | no-uia | 4/4 | 90.08 | 57.39 | 44.67 | 44.05 | 22.25 | 75.17 | 52.69 | 21/21 |
| `gpt-5.4-nano` | initial-uia | 4/4 | 92.46 | 58.14 | 35.93 | 34.61 | 38.43 | 80.68 | 51.56 | 20/21 |
| `gpt-5.4-nano` | full-uia | 2/2 | 95.24 | 64.34 | 59.69 | 58.55 | 29.10 | 100.00 | 61.84 | 12/12 |
| `gemini-3.5-flash` | no-uia | 2/3 | 84.92 | 59.89 | 27.19 | 27.19 | 12.50 | 46.43 | 30.95 | 8/9 |
| `gemini-3.5-flash` | initial-uia | 2/3 | 84.92 | 65.76 | 26.06 | 24.55 | 25.00 | 62.50 | 32.50 | 8/9 |
| `gemini-3.5-flash` | full-uia | 0/0 | - | - | - | - | - | - | - | - |
| `gemini-3.1-flash-lite` | no-uia | 4/4 | 87.70 | 65.55 | 45.11 | 44.38 | 14.12 | 57.15 | 52.22 | 21/21 |
| `gemini-3.1-flash-lite` | initial-uia | 4/4 | 84.13 | 76.62 | 46.03 | 45.26 | 41.96 | 78.12 | 60.89 | 20/21 |
| `gemini-3.1-flash-lite` | full-uia | 2/2 | 90.47 | 83.23 | 78.83 | 77.35 | 40.91 | 100.00 | 82.21 | 12/12 |
| `openai/gpt-oss-120b:free` | no-uia | 0/0 | - | - | - | - | - | - | - | - |
| `openai/gpt-oss-120b:free` | initial-uia | 0/0 | - | - | - | - | - | - | - | - |
| `openai/gpt-oss-120b:free` | full-uia | 0/0 | - | - | - | - | - | - | - | - |
| `deepseek/deepseek-v4-flash:free` | no-uia | 0/0 | - | - | - | - | - | - | - | - |
| `deepseek/deepseek-v4-flash:free` | initial-uia | 0/0 | - | - | - | - | - | - | - | - |
| `deepseek/deepseek-v4-flash:free` | full-uia | 0/0 | - | - | - | - | - | - | - | - |
| `nvidia/nemotron-3-super-120b-a12b:free` | no-uia | 0/0 | - | - | - | - | - | - | - | - |
| `nvidia/nemotron-3-super-120b-a12b:free` | initial-uia | 0/0 | - | - | - | - | - | - | - | - |
| `nvidia/nemotron-3-super-120b-a12b:free` | full-uia | 0/0 | - | - | - | - | - | - | - | - |
| `openai/gpt-oss-120b` | no-uia | 4/4 | 87.70 | 68.91 | 46.19 | 46.19 | 18.54 | 63.70 | 56.21 | 20/21 |
| `openai/gpt-oss-120b` | initial-uia | 4/4 | 88.49 | 73.06 | 50.00 | 49.26 | 35.44 | 81.58 | 61.95 | 20/21 |
| `openai/gpt-oss-120b` | full-uia | 2/2 | 90.47 | 79.72 | 75.56 | 74.16 | 40.00 | 100.00 | 79.47 | 12/12 |
| `deepseek/deepseek-v4-flash` | no-uia | 4/4 | 92.46 | 65.44 | 44.71 | 44.71 | 22.35 | 70.44 | 57.98 | 21/21 |
| `deepseek/deepseek-v4-flash` | initial-uia | 4/4 | 84.13 | 67.59 | 41.24 | 41.24 | 28.23 | 79.17 | 60.00 | 20/21 |
| `deepseek/deepseek-v4-flash` | full-uia | 2/2 | 90.47 | 68.60 | 49.85 | 49.85 | 28.57 | 100.00 | 57.64 | 12/12 |
| `nvidia/nemotron-3-super-120b-a12b` | no-uia | 4/4 | 91.27 | 61.19 | 39.51 | 38.88 | 21.72 | 69.47 | 48.27 | 20/21 |
| `nvidia/nemotron-3-super-120b-a12b` | initial-uia | 4/4 | 92.46 | 68.86 | 42.87 | 41.59 | 29.61 | 74.41 | 53.37 | 20/21 |
| `nvidia/nemotron-3-super-120b-a12b` | full-uia | 2/2 | 92.85 | 75.88 | 71.47 | 70.00 | 39.43 | 100.00 | 81.25 | 12/12 |

## Per-cell detail

### `gpt-5.5` (openai)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 85.71 | 69.70 | 63.64 | 63.64 | 27.27 | 81.82 | 8 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 85.71 | 84.85 | 75.76 | 72.73 | 42.86 | 80.95 | 8 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 95.24 | 70.00 | 62.50 | 60.00 | 37.50 | 100.00 | 11 | 2 | 6/6 |
| paraphrase | no-uia | 6/6 | 80.95 | 62.50 | 43.75 | 43.75 | 20.00 | 40.00 | 6 | 4 | 5/6 |
| paraphrase | initial-uia | 6/6 | 80.95 | 51.52 | 12.12 | 9.09 | 25.00 | 50.00 | 4 | 6 | 6/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 71.43 | 21.43 | 21.43 | 0.00 | 46.15 | 3 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 66.67 | 20.00 | 20.00 | 0.00 | 42.86 | 4 | 4 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 82.50 | 82.50 | 25.93 | 88.89 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 87.50 | 87.50 | 33.33 | 96.30 | 14 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 36.00 | 100.00 | 14 | 0 | 6/6 |

### `gpt-5.4-mini` (openai)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 71.43 | 77.42 | 54.84 | 51.61 | 43.75 | 75.00 | 5 | 4 | 6/6 |
| instruction | initial-uia | 6/6 | 76.19 | 66.67 | 54.55 | 48.48 | 72.22 | 88.89 | 5 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 80.95 | 82.35 | 73.53 | 70.59 | 47.83 | 100.00 | 10 | 0 | 6/6 |
| paraphrase | no-uia | 6/6 | 66.67 | 36.67 | 16.67 | 16.67 | 16.67 | 33.33 | 4 | 4 | 5/6 |
| paraphrase | initial-uia | 6/6 | 71.43 | 58.62 | 20.69 | 20.69 | 28.57 | 71.43 | 4 | 6 | 4/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 58.82 | 17.65 | 17.65 | 0.00 | 46.15 | 4 | 6 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 71.43 | 21.43 | 21.43 | 0.00 | 46.15 | 3 | 4 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 82.50 | 82.50 | 25.93 | 88.89 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 87.50 | 87.50 | 33.33 | 96.30 | 14 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 36.00 | 100.00 | 14 | 0 | 6/6 |

### `gpt-5.4-nano` (openai)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 90.48 | 50.00 | 47.50 | 45.00 | 37.50 | 100.00 | 8 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 90.48 | 52.63 | 28.95 | 23.68 | 85.71 | 100.00 | 2 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 90.48 | 47.73 | 43.18 | 40.91 | 28.57 | 100.00 | 10 | 2 | 6/6 |
| paraphrase | no-uia | 6/6 | 80.95 | 47.06 | 41.18 | 41.18 | 18.18 | 54.55 | 7 | 2 | 6/6 |
| paraphrase | initial-uia | 6/6 | 90.48 | 36.59 | 9.76 | 9.76 | 27.27 | 72.73 | 5 | 5 | 5/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 60.00 | 20.00 | 20.00 | 0.00 | 46.15 | 4 | 2 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 53.33 | 20.00 | 20.00 | 0.00 | 50.00 | 4 | 2 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 72.50 | 70.00 | 70.00 | 33.33 | 100.00 | 11 | 0 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 85.00 | 85.00 | 40.74 | 100.00 | 12 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 80.95 | 76.19 | 76.19 | 29.63 | 100.00 | 14 | 1 | 6/6 |

### `gemini-3.5-flash` (gemini)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 0/6 | - | - | - | - | - | - | - | - | - |
| instruction | initial-uia | 0/6 | - | - | - | - | - | - | - | - | - |
| paraphrase | no-uia | 6/6 | 80.95 | 53.12 | 34.38 | 34.38 | 25.00 | 50.00 | 4 | 4 | 5/6 |
| paraphrase | initial-uia | 6/6 | 80.95 | 51.52 | 12.12 | 9.09 | 33.33 | 58.33 | 4 | 6 | 6/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 66.67 | 20.00 | 20.00 | 0.00 | 42.86 | 4 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 80.00 | 40.00 | 40.00 | 16.67 | 66.67 | 4 | 2 | 2/3 |

### `gemini-3.1-flash-lite` (gemini)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 85.71 | 61.76 | 52.94 | 50.00 | 20.00 | 60.00 | 9 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 76.19 | 68.75 | 53.12 | 50.00 | 68.75 | 87.50 | 5 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 80.95 | 76.47 | 67.65 | 64.71 | 45.83 | 100.00 | 10 | 0 | 6/6 |
| paraphrase | no-uia | 6/6 | 76.19 | 43.75 | 25.00 | 25.00 | 10.53 | 36.84 | 6 | 4 | 6/6 |
| paraphrase | initial-uia | 6/6 | 71.43 | 67.74 | 19.35 | 19.35 | 41.67 | 58.33 | 4 | 4 | 6/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 66.67 | 20.00 | 20.00 | 0.00 | 42.86 | 4 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 80.00 | 26.67 | 26.67 | 16.67 | 66.67 | 4 | 2 | 2/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 82.50 | 82.50 | 25.93 | 88.89 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 85.00 | 85.00 | 40.74 | 100.00 | 12 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 36.00 | 100.00 | 14 | 0 | 6/6 |

### `openai/gpt-oss-120b:free` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

### `deepseek/deepseek-v4-flash:free` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

### `nvidia/nemotron-3-super-120b-a12b:free` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

### `openai/gpt-oss-120b` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 71.43 | 65.62 | 46.88 | 46.88 | 35.71 | 78.57 | 8 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 90.48 | 77.14 | 60.00 | 60.00 | 68.42 | 100.00 | 6 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 80.95 | 69.44 | 61.11 | 58.33 | 44.00 | 100.00 | 10 | 0 | 6/6 |
| paraphrase | no-uia | 6/6 | 90.48 | 48.57 | 31.43 | 31.43 | 12.50 | 37.50 | 6 | 4 | 5/6 |
| paraphrase | initial-uia | 6/6 | 85.71 | 55.88 | 29.41 | 26.47 | 40.00 | 70.00 | 6 | 4 | 5/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 71.43 | 21.43 | 21.43 | 0.00 | 46.15 | 3 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 77.78 | 69.23 | 23.08 | 23.08 | 0.00 | 60.00 | 2 | 4 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 85.00 | 85.00 | 25.93 | 92.59 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 87.50 | 87.50 | 33.33 | 96.30 | 14 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 36.00 | 100.00 | 14 | 0 | 6/6 |

### `deepseek/deepseek-v4-flash` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 90.48 | 67.57 | 51.35 | 51.35 | 38.46 | 100.00 | 8 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 76.19 | 75.76 | 51.52 | 51.52 | 52.94 | 100.00 | 8 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 80.95 | 56.25 | 18.75 | 18.75 | 23.81 | 100.00 | 6 | 4 | 6/6 |
| paraphrase | no-uia | 6/6 | 90.48 | 37.50 | 25.00 | 25.00 | 25.00 | 50.00 | 4 | 2 | 6/6 |
| paraphrase | initial-uia | 6/6 | 71.43 | 37.93 | 3.45 | 3.45 | 10.00 | 50.00 | 4 | 6 | 5/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 66.67 | 20.00 | 20.00 | 0.00 | 42.86 | 4 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 66.67 | 20.00 | 20.00 | 16.67 | 66.67 | 4 | 2 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 82.50 | 82.50 | 25.93 | 88.89 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 33.33 | 100.00 | 14 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 80.95 | 80.95 | 80.95 | 33.33 | 100.00 | 14 | 0 | 6/6 |

### `nvidia/nemotron-3-super-120b-a12b` (openrouter)

| Variant | Condition | Tasks parsed | Coverage % | Action % | Target % | Exact % | Resolv init % | Resolv union % | Fallback ok | Grounding fail | Exec valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction | no-uia | 6/6 | 100.00 | 50.00 | 45.00 | 42.50 | 46.67 | 100.00 | 6 | 0 | 6/6 |
| instruction | initial-uia | 6/6 | 95.24 | 66.67 | 58.97 | 53.85 | 56.52 | 91.30 | 8 | 0 | 6/6 |
| instruction | full-uia | 6/6 | 85.71 | 61.76 | 52.94 | 50.00 | 42.86 | 100.00 | 6 | 2 | 6/6 |
| paraphrase | no-uia | 6/6 | 76.19 | 33.33 | 9.09 | 9.09 | 14.29 | 42.86 | 3 | 5 | 5/6 |
| paraphrase | initial-uia | 6/6 | 85.71 | 50.00 | 18.75 | 18.75 | 28.57 | 71.43 | 2 | 6 | 5/6 |
| reasoning_steps | no-uia | 3/3 | 88.89 | 71.43 | 21.43 | 21.43 | 0.00 | 46.15 | 3 | 4 | 3/3 |
| reasoning_steps | initial-uia | 3/3 | 88.89 | 68.75 | 18.75 | 18.75 | 0.00 | 57.14 | 5 | 3 | 3/3 |
| guide | no-uia | 6/6 | 100.00 | 90.00 | 82.50 | 82.50 | 25.93 | 88.89 | 14 | 2 | 6/6 |
| guide | initial-uia | 6/6 | 100.00 | 90.00 | 75.00 | 75.00 | 33.33 | 77.78 | 14 | 0 | 6/6 |
| guide | full-uia | 6/6 | 100.00 | 90.00 | 90.00 | 90.00 | 36.00 | 100.00 | 14 | 0 | 6/6 |
