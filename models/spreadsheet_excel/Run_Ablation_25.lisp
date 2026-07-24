(load "actr7.x/load-act-r.lisp")
(load "Spreadsheet/Complete_error_model_tcp.lisp")

(use-saved-visicon-toggle)
(run-spreadsheet-ablation-models
 :runs 25
 :batch-root "Spreadsheet/logs/ablation_25_formula_latest/"
 :retain-run-results t)
