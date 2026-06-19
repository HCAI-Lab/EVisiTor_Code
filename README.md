# Draft20 modeling and analysis code package

This package accompanies `Draft20_Frontiers_Template_Final.docx`.

## Included

- `Modeling/`: ACT-R spreadsheet models, model support functions, notes, and saved visicon artifacts.
- `VisiTor/`: Python/Lisp bridge code for visual perception, external keyboard/mouse action, and instruction-to-knowledge conversion.
- `Analysis/code/`: analysis scripts used for completion-time, keypress, fixation, perfect-vs-realistic, and ablation comparisons.
- `Analysis/model_outputs/`: compact model-generated summaries and analysis tables retained as reproducibility evidence.
- `actr7.x/`: the ACT-R runtime snapshot used by the project.
- `manuscript/`: the paper associated with this code package.

## Excluded

No participant-level or aggregate human-data files are included. In particular, the package excludes the repository's `Analysis/Human Data/`, `Analysis/HumanData_Video/`, `Analysis/HumanCompletionTime.csv`, and other participant-derived spreadsheets/CSVs.

The large per-run model log directories under the 150-run and 25-run ablation folders are also omitted; their compact `batch_summary.csv`, overall ablation summary, and generated analysis-output tables are included.

## Environment

- ACT-R 7 (runtime snapshot included)
- Python dependencies for VisiTor are listed in `VisiTor/requirements.txt`.
- Some VisiTor functions interact with Microsoft Excel and Windows UI Automation, so reproducing live interface runs requires Windows, Excel, and the interface state expected by the model.

## Notes

Analysis scripts that compare models with humans still reference human-data inputs. Those private inputs are intentionally absent from this archive. The scripts, model outputs, and model-only summaries are included so the computational workflow can be inspected and rerun when authorized human data are supplied separately.
