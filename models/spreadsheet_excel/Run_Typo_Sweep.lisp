#|
Run_Typo_Sweep.lisp

Sweeps the per-keystroke typing error rate of the Full-Realistic spreadsheet
model and writes one batch-log directory per rate, so model completion time
and keystroke error rate can be compared against human data at each rate.

Usage (from the repository root, e.g. G:\ACT-RModels):
  sbcl --noinform --non-interactive --load "Spreadsheet/Run_Typo_Sweep.lisp"

Output:
  Spreadsheet/logs/typo_sweep/rate_XXX/Ablation_Full_Realistic/run_NNN/*.csv
  where XXX is the rate in tenths of a percent (rate_060 = 6%).
|#

(load "actr7.x/load-act-r.lisp")
(load "Spreadsheet/Complete_error_model_tcp.lisp")

(use-saved-visicon-toggle)

;; Defined ahead of Ablation_support.lisp (a DEFVAR there too, so per-run
;; reloads never clobber the swept value).
(defvar *spreadsheet-ablation-forced-typing-error-rate* nil)

(defparameter *typo-sweep-rates*
  '(0.00 0.01 0.02 0.03 0.04 0.06 0.08 0.10 0.12))
(defparameter *typo-sweep-runs* 25)

(dolist (rate *typo-sweep-rates*)
  (setf *spreadsheet-ablation-forced-typing-error-rate* rate)
  (format t "~&==== Typo sweep: rate ~,3f (~a runs) ====~%" rate *typo-sweep-runs*)
  (finish-output)
  (run-model-sources-one-by-one
   :model-sources (list "Ablation_Full_Realistic.lisp")
   :runs *typo-sweep-runs*
   :batch-root (format nil "Spreadsheet/logs/typo_sweep/rate_~3,'0d/"
                       (round (* 1000 rate)))))

(setf *spreadsheet-ablation-forced-typing-error-rate* nil)
(format t "~&Typo sweep complete.~%")
