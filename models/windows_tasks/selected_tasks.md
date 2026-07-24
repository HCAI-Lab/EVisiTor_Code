# Selected Windows Tasks from the PSAI Computer-Use Dataset

**Dataset:** [anaisleila/computer-use-data-psai](https://huggingface.co/datasets/anaisleila/computer-use-data-psai) (MIT license, Paradigm Shift AI, 2025)
**Local clone:** set `EVISITOR_PSAI_ROOT` to your copy (the authors used `G:\computer-use-data-psai`; 49.2 GB total: 16 parquet shards in `data/`, MP4 screen recordings in `videos/`, DOM snapshots in `dom_snaps/`)
**Filter applied:** `os == 'WINDOWS'` → 142 unique recordings, 105 unique task templates (many templates performed by two vendors)
**Full filtered metadata:** `windows_tasks_all.json` (this folder; `windows_tasks_partial.json` is an earlier partial scan kept for provenance)
**Full rows for the 9 candidate recordings (incl. `reasoning_steps` and `events` JSON):** `candidate_tasks_full.json` (this folder)

## Why these tasks

Selection criteria, in order of priority:

1. **UIA-friendly applications** — File Explorer, Windows Settings, Task Manager, the Run dialog, Command Prompt, and Excel all expose full accessibility trees, so the existing VisiTor UIA→visicon converter should work without a new perception backend.
2. **Coverage of all three EVisiTor pathways** — each task exercises visual search (Goto/Select of labeled objects), knowledge acquisition (natural-language instruction → Subtask chunks), and motor execution (typing with possible misexecution + Press commands).
3. **Difficulty spread** — EASY through HARD, so the generalization claim is not limited to trivial tasks.
4. **Ground truth available** — every recording has a screen video plus a timestamped event stream (`move`, `click` with x/y/button, `press`/`release`) that plays the same role the GazeTracker keypress logs played in the Excel study: it is the human trace the model output can be compared against.

## The selected tasks (W1–W8 selected 2026-07-06; W9–W10 added 2026-07-07 to reach ten)

| # | unique_data_id | App | Difficulty | Task |
|---|----------------|-----|------------|------|
| W1 | `cmaela4ed001gzr0xhfhqg921` | Run dialog | EASY | Use the Run dialog (Win+R) to open Notepad on Windows. |
| W2 | `cmaela4el00dezr0xar3kk07l` | File Explorer | EASY | Rename the file 'budget.xlsx' to 'budget_2025.xlsx' using File Explorer. |
| W3 | `cm9egbfne005d0e0v3a0rw2pb` | File Explorer | EASY | Create a new folder named 'Projects' on the Desktop using File Explorer. |
| W4 | `cmaela4el00dgzr0xvj1od7q9` | File Explorer | MEDIUM | Compress the folder 'Logs' into a ZIP archive. |
| W5 | `cma092ib300e6wu0v1mk0doaw` | Windows Settings | EASY | Adjust the screen resolution in Windows to 1920x1080 via Settings. |
| W6 | `cmaela4ef004uzr0xjcxi49z5` | Task Manager | MEDIUM | Open Task Manager on Windows and end a running process. |
| W7 | `cmaela4em00ggzr0xbdq9jgok` | Command Prompt | MEDIUM | Use Command Prompt to find your IP address (using ipconfig). |
| W8 | `cm9qi2tb9004zx60wq4sez68x` | Microsoft Excel | HARD | Create a macro to sort multiple columns simultaneously. |
| W9 | `cma092ib400ghwu0v52t3qxia` | Start menu | EASY | Open the Calculator via the Windows Start menu search bar. |
| W10 | `cm9egbkl7005j0e0v774e8iqr` | File Explorer (Windows search) | EASY | Search for a file named 'report.docx' in the Documents folder using Windows search. |

Videos are at `G:\computer-use-data-psai\videos\{unique_data_id}.mp4`. Full rows
(reasoning_steps + events) for W9/W10 are in `new_candidate_tasks_full.json`.

## Human demonstration summaries (from `reasoning_steps` + event streams)

- **W1 (Run → Notepad):** Win+R → type `notepad` → Enter → close window. Event stream: 10 keypresses, 2 trailing clicks (close). Pure keyboard-command task; exercises the Press pathway with a modifier combo.
- **W2 (Rename):** Click `budget.xlsx` → click Rename icon in the command bar → edit name to `budget_2025.xlsx` → Enter. Event stream: 4 clicks then 8 keypresses (vendor appended `_2025` rather than retyping the whole name — a strategy difference worth noting when comparing against the model, which will retype or edit differently). Direct analogue of the paper's "file name → type subject → enter" subtask.
- **W3 (New folder):** Open File Explorer → Desktop → right-click empty area → New → Folder → type `Projects` → Enter. Event stream: 5 clicks, 11 keypresses ("Projects" + Enter + extras).
- **W4 (Zip Logs):** Select `Logs` folder → right-click → Show more options → Send to → Compressed (zipped) folder → accept/confirm name with Enter. Event stream: 6 distinct click targets + 1 keypress. Deep context-menu navigation = heavy visual search.
- **W5 (Resolution):** Win+I → System → Display → Display resolution dropdown → 1920×1080 → Keep changes → close. Event stream: 2 keypresses + 6 click targets. Settings app menu navigation.
- **W6 (End process):** Ctrl+Shift+Esc → right-click a running app in the process list → End task. Event stream: 3 keypresses + 3 click targets. Dynamic-content visual search (process list changes between machines/runs).
- **W7 (ipconfig):** Start/search → type `cmd` → Enter → type `ipconfig` → Enter → visually scan output for "IPv4 Address". Terminal typing; output reading is a pure visual-search step with no action.
- **W8 (Excel macro):** View → Macros → Record Macro → name it (`MultiColumnSort`) → OK → select data range → Data → Sort → set two sort levels (Sort by / Add Level / Then by) → OK → View → Macros → Stop Recording. 25+ ordered actions, dialog interaction, in the same application as the paper. NOTE: the vendor's reasoning steps 9–10 (stopping the screen recorder and uploading to the PSAI portal) are data-collection overhead, NOT part of the task, and are excluded from the chunk decomposition.
- **W9 (Calculator via Start search):** click the taskbar search box → type `calculator` → open the top result. Vendor reasoning: "Go to the start menu and navigate to the search bar. Type 'calculator' and press Enter." Event stream: 4 keypresses (vendor typed a shortened query) + result click. Final chunk subtask is attention-only verification (Goto "Calculator" with no Select).
- **W10 (search report.docx):** open File Explorer from the taskbar → Documents → click the search box (`Search Documents`) → type `report.docx` → Enter → locate the result. Event stream: 13+4 keypresses across 6 click targets. Heavy typing task (11-char string with a dot), good exerciser for the typing-check pathway; final subtask attention-only.

## Known schema pressure points discovered during chunking

These are findings, not blockers — they should be reported in the revision as what generalization actually requires:

1. **Key combinations.** The gold vocabulary's `Press` was only ever used with `"enter"`. Windows-native tasks require modifier combos (`win+r`, `ctrl+shift+esc`, `win+i`, `ctrl+shift+n`, `shift+f10`). The chunks below write these as single quoted `Press` targets; the VisiTor motor bridge must map them to chorded keypresses (protected-command handling already exists for single command keys).
2. **Right-click.** The 5-verb vocabulary has no context-click. Two options: (a) stay within vocabulary by using the keyboard context-menu key (`Press "shift+f10"` after selecting the object) — used below; (b) extend the vocabulary with a 6th verb (`Context` or `RightClick`). Option (b) is more faithful to what the vendors actually did.
3. **Drag / range selection.** Excel range highlighting (W8) is done here with `Press "ctrl+shift+end"` instead of mouse drag, which VisiTor cannot yet produce.
4. **Protected names on new interfaces.** Windows 11 UIA labels need the same protected-name treatment as `File Tab`/`Row 1`: e.g., the resolution dropdown item literal is `1920 × 1080` (with the multiplication sign ×, not the letter x), the zip menu item is `Compressed (zipped) folder`, the Task Manager button is `End task` (lowercase t). Each label below marked `#VERIFY-UIA` must be checked against the live UIA tree before execution.
5. **Non-action attention step.** W7's final step ("look for IPv4 Address") is a Goto with no Select — visual search as the goal itself. The gold schema allows it structurally (every action has one object) but no gold subtask ever ended without an action; the scorer should accept it.
