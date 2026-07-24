# Superseded analysis (7-14 July 2026)

These scripts and outputs belong to the earlier 150-run batch
(`Spreadsheet/logs/ablation_150_formula_latest`, `.../typo_sweep`) analysed
before the revision. **None of the values here appear in the submitted
manuscript.** For example `revision_stats.json` reports r = 0.943 and
RMSE = 16.16 s for the realistic model, whereas the submitted Table 4 reports
r = 0.950 and RMSE = 17.37 s from the 2026-07-22 factorial batch.

The current pipeline is in the parent directory; its inputs and aggregate
outputs are in `../batch_provenance/`.

| file | superseded by |
|------|---------------|
| `compute_revision_stats.py`, `revision_stats.json` | `../analyze_ablation_2x2x2.py`, `../batch_provenance/draft36_check090_factorial/` |
| `ablation_results_2026-07-07.csv`, `statistics_summary.txt`, `regenerated_tables.txt` | `../batch_provenance/draft36_check090_factorial/cell_summary.csv`, `factorial_effects.json`, `w1_results.json` |
| `analyze_typo_sweep.py`, `typo_sweep_summary.md` | `../analyze_draft34_error_rate_sweeps.py`, `../batch_provenance/draft36_novisual_rate_sweeps_check090/` |
