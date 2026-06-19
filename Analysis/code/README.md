# ExcelDataAnalysis Workspace Guide

This README documents:
- what each Python script does,
- what data and outputs are stored in each folder,
- and what generated files currently exist in this workspace.

## 1) Workspace Overview

Top-level items:
- `.vscode/`
- `analyze_keypress_patterns.py`
- `breakdown_fixations_by_task.py`
- `compare_human_vs_model_fixations_by_step.py`
- `compute_run_stats.py`
- `count_fixations_by_side.py`
- `eyetracking_analysis.py`
- `plot_subtask_comparison.py`
- `Human Data/`
- `HumanCompletionTime.csv`
- `HumanData_Video/`
- `New_Error (3-5-2-TCP)/`
- `OGModelCompletionTime.xlsx`
- `Perfect_model/`
- `ritter_simulation_runs.md`
- `__pycache__/`


## 2) Python Scripts (What Each One Does)

### `eyetracking_analysis.py`
Purpose:
- Detects fixations from raw eye-tracking samples using an I-DT (dispersion-threshold) approach.

Inputs:
- `Human Data/Eye tracking data/*.csv`

Main processing:
- Valid sample filtering using `found` and `score`.
- Optional interpolation and smoothing.
- Fixation detection with thresholds:
  - minimum fixation duration,
  - dispersion threshold.
- Optional merge of close fixations.
- Labels each sample with `fixation_id`.

Outputs (per subject file):
- `Human Data/eye_tracking_analysis/*_fixations.csv`
- `Human Data/eye_tracking_analysis/*_samples_labeled.csv`

---

### `count_fixations_by_side.py`
Purpose:
- Counts fixations on the left vs right side of screen per subject.

Inputs:
- `Human Data/eye_tracking_analysis/*_fixations.csv`

Logic:
- Uses `x_px < 960` as left and `x_px > 960` as right.

Output:
- `Human Data/eye_tracking_analysis/fixation_side_counts_by_subject.csv`

---

### `breakdown_fixations_by_task.py`
Purpose:
- Assigns fixations to task steps based on predefined time windows and summarizes left/right counts by subject and step.

Inputs:
- `Human Data/eye_tracking_analysis/*_fixations.csv`
- Embedded `RAW_STEP_ROWS` timing breakdown inside script.

Outputs:
- `Human Data/eye_tracking_analysis/task_time_windows_from_breakdown.csv`
- `Human Data/eye_tracking_analysis/fixation_side_counts_by_subject_by_step.csv`

---

### `compare_human_vs_model_fixations_by_step.py`
Purpose:
- Compares human fixation-side counts by step against model attention shifts by step.

Inputs:
- `Human Data/eye_tracking_analysis/fixation_side_counts_by_subject_by_step.csv`
- `New_Error (3-5-2-TCP)/run_*/attention_shifts.csv`

Notable behavior:
- Excludes `Subject1` from human aggregation.
- Deduplicates repeated model attention shift rows.

Outputs:
- `Human Data/eye_tracking_analysis/human_fixation_counts_by_step_excl_subject1.csv`
- `Human Data/eye_tracking_analysis/model_attention_shift_counts_by_step_by_run.csv`
- `Human Data/eye_tracking_analysis/model_attention_shift_counts_by_step.csv`
- `Human Data/eye_tracking_analysis/comparison_human_vs_model_by_step.csv`

---

### `analyze_keypress_patterns.py`
Purpose:
- Parses keyboard event logs in `Human Data` CSV files and extracts key-down events.

Inputs:
- `Human Data/**/*.csv` (excluding files under `Human Data/key_analysis/`)

Main processing:
- Detects keyboard events (`K ... D` and `K ... U`).
- Produces:
  - raw key-down events,
  - deduplicated key presses while key is held,
  - per-file keypress summaries,
  - per-subject keypress totals,
  - per-subject dedup keypress files.

Outputs:
- `Human Data/key_analysis/key_down_events_raw.csv`
- `Human Data/key_analysis/key_down_events_dedup.csv`
- `Human Data/key_analysis/keypress_summary_by_file.csv`
- `Human Data/key_analysis/key_presses_total_by_user.csv`
- `Human Data/key_analysis/subjects_dedup/subject*_key_presses.csv`

Note:
- `key_down_events_dedup_updated.csv` appears as an alternate output when the main dedup file is locked.

---

### `compute_run_stats.py`
Purpose:
- Main run-level statistics script for model output directories.

Inputs:
- Required base run folder (default is `New_Error (3-5-2-TCP)`), with per-run:
  - `task_times.csv`
  - `keypresses.csv`
- Optional human reference:
  - `HumanCompletionTime.csv`
- Optional third comparison source:
  - `--perfect-model-dir` (run folders), or
  - `--og-model-xlsx` (summary file).

Computes:
- Task duration mean/std across runs.
- Keypress count mean/std:
  - overall per run,
  - per task (using task time windows).
- Human vs model comparison.
- Three-way completion-time comparison:
  - New Error vs Human vs Perfect Model (or OG model reference).
- Optional CSV exports and PNG bar plots/statistical summary image.

Typical outputs in `New_Error (3-5-2-TCP)/`:
- `task_duration_stats.csv`
- `overall_keypress_stats.csv`
- `task_keypress_stats.csv`
- `human_vs_model_task_time_comparison.csv`
- `completion_time_three_way_stats_perfect_model.csv`
- `completion_time_overall_stats_perfect_model.csv`
- `completion_time_barplot_by_task_perfect_model.png`
- `completion_time_barplot_overall_perfect_model.png`
- `completion_time_statistical_summary_perfect_model.png`

Legacy OG reference outputs (also present):
- `completion_time_three_way_stats.csv`
- `completion_time_overall_stats.csv`
- `completion_time_barplot_by_task.png`
- `completion_time_barplot_overall.png`
- `completion_time_statistical_summary.png`

---

### `plot_subtask_comparison.py`
Purpose:
- Compares subtask durations between New Error model and Perfect model and generates CSV + PNG outputs.

Inputs:
- `--new-dir` (e.g., `New_Error (3-5-2-TCP)`)
- `--perfect-dir` (e.g., `Perfect_model`)
- per-run `subtask_times.csv`

Computes:
- Per-task/subtask mean/std/count comparison.
- Task-level durations derived by summing subtasks per run.
- Overall completion time from summed subtasks per run.

Outputs (saved to chosen `--output-dir`):
- `subtask_time_comparison_new_vs_perfect.csv`
- `subtask_derived_task_time_comparison_new_vs_perfect.csv`
- `subtask_overall_time_comparison_new_vs_perfect.csv`
- `subtask_time_barplot_new_vs_perfect.png`
- `task_time_barplot_from_subtasks_new_vs_perfect.png`
- `overall_time_barplot_from_subtasks_new_vs_perfect.png`


## 3) Data and Output Files by Folder

### `Human Data/`
Subfolders:
- `Eye tracking data/`
  - Raw eye-tracking input CSV files (e.g., `Subject1_red_cross.csv`, etc.).
- `eye_tracking_analysis/`
  - Derived fixation and comparison outputs, including:
    - `Subject*_red_cross_fixations.csv`
    - `Subject*_red_cross_samples_labeled.csv`
    - `fixation_side_counts_by_subject.csv`
    - `fixation_side_counts_by_subject_by_step.csv`
    - `task_time_windows_from_breakdown.csv`
    - `human_fixation_counts_by_step_excl_subject1.csv`
    - `model_attention_shift_counts_by_step_by_run.csv`
    - `model_attention_shift_counts_by_step.csv`
    - `comparison_human_vs_model_by_step.csv`
- `key_analysis/`
  - Keyboard event analysis outputs:
    - `key_down_events_raw.csv`
    - `key_down_events_dedup.csv`
    - `key_down_events_dedup_updated.csv`
    - `keypress_summary_by_file.csv`
    - `key_presses_total_by_user.csv`
    - `subjects_dedup/subject1_key_presses.csv` ... `subject23_key_presses.csv`
- `Typing Data/`
  - Per-subject typing log files (`subject1.csv` ... `subject23.csv`).

---

### `HumanData_Video/`
Contains video/normalization/participant summary resources, including:
- `normalization-excel-tasks-v2.xlsx`
- `normalization.xlsx`
- `Participants-errors.xlsx`
- `Participants-errors_cogsci.xlsx`
- `sample.xlsx`
- Subject folders:
  - `Subject1/`, `Subject2/`, `Subject7/`, `Subject11/`, `Subject12/`, `Subject13/`, `Subject14/`, `Subject17/`, `Subject18/`, `Subject19/`
  - `Subjects-withoutVideo/`

---

### `New_Error (3-5-2-TCP)/`
Contains model run data and generated summaries/figures.

Run data:
- `run_001/` ... `run_150/`
- Each run folder contains:
  - `attention_shifts.csv`
  - `keypresses.csv`
  - `subtask_times.csv`
  - `task_times.csv`
- `batch_summary.csv`

Generated analysis CSV files currently present:
- `task_duration_stats.csv`
- `overall_keypress_stats.csv`
- `task_keypress_stats.csv`
- `human_vs_model_task_time_comparison.csv`
- `completion_time_three_way_stats.csv`
- `completion_time_overall_stats.csv`
- `completion_time_three_way_stats_perfect_model.csv`
- `completion_time_overall_stats_perfect_model.csv`
- `subtask_time_comparison_new_vs_perfect.csv`
- `subtask_derived_task_time_comparison_new_vs_perfect.csv`
- `subtask_overall_time_comparison_new_vs_perfect.csv`

Generated PNG files currently present:
- `human_vs_model_task_time_plot.png`
- `completion_time_barplot_by_task.png`
- `completion_time_barplot_overall.png`
- `completion_time_statistical_summary.png`
- `completion_time_barplot_by_task_perfect_model.png`
- `completion_time_barplot_overall_perfect_model.png`
- `completion_time_statistical_summary_perfect_model.png`
- `subtask_time_barplot_new_vs_perfect.png`
- `task_time_barplot_from_subtasks_new_vs_perfect.png`
- `overall_time_barplot_from_subtasks_new_vs_perfect.png`

---

### `Perfect_model/`
Contains baseline/perfect model runs:
- `run_001/` ... `run_027/`
- Each run folder contains:
  - `attention_shifts.csv`
  - `keypresses.csv`
  - `subtask_times.csv`
  - `task_times.csv`
- `batch_summary.csv`

---

### Top-level reference files
- `HumanCompletionTime.csv`
  - Human task completion summary (Step, average time, standard deviation).
- `OGModelCompletionTime.xlsx`
  - Original model summary completion-time reference.
- `ritter_simulation_runs.md`
  - Methodology notes on simulation run counts/stability/power.


## 4) Typical Commands

Run task/keypress stats and three-way completion comparison:
- `python compute_run_stats.py --base-dir "F:/ExcelDataAnalysis/New_Error (3-5-2-TCP)" --save-csv --output-dir "F:/ExcelDataAnalysis/New_Error (3-5-2-TCP)" --human-csv "F:/ExcelDataAnalysis/HumanCompletionTime.csv" --perfect-model-dir "F:/ExcelDataAnalysis/Perfect_model" --save-plot`

Run subtask comparison and plots:
- `python plot_subtask_comparison.py --new-dir "F:/ExcelDataAnalysis/New_Error (3-5-2-TCP)" --perfect-dir "F:/ExcelDataAnalysis/Perfect_model" --output-dir "F:/ExcelDataAnalysis/New_Error (3-5-2-TCP)"`

Run fixation preprocessing:
- `python eyetracking_analysis.py`
- `python count_fixations_by_side.py`
- `python breakdown_fixations_by_task.py`
- `python compare_human_vs_model_fixations_by_step.py`

Run keypress event analysis:
- `python analyze_keypress_patterns.py`


## 5) Notes

- Some outputs are cumulative and may reflect multiple analysis runs.
- Files with `_updated` suffix were created as fallback when a target file was locked.
- This workspace contains both raw data and derived analysis artifacts; avoid overwriting raw sources unless intended.
