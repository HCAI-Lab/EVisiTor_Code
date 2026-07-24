#|
Ablation_Typing_Errors_Only.lisp

Deprecated exploratory variant.  This is no longer part of the canonical
paper ablation set because errors without checking are difficult to interpret
cognitively.  Use Ablation_Correction_Checking.lisp for the current
"error making + error checking, no visual search" condition.
|#

(defparameter *spreadsheet-ablation-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-ablation-file (name)
  (namestring (merge-pathnames name *spreadsheet-ablation-root*)))

(load (spreadsheet-ablation-file "Perfect_model.lisp"))
(load (spreadsheet-ablation-file "Ablation_support.lisp"))

(apply-spreadsheet-ablation :typing-errors-only)
