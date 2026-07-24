#|
Ablation_Batched_Formula_Typing.lisp

Paper variant: batched formula typing
Purpose: isolate the base formula-typing behavior in which the model checks
the formula instruction between typed token batches. Visual search, typing
errors, and correction checking are disabled.
|#

(defparameter *spreadsheet-ablation-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-ablation-file (name)
  (namestring (merge-pathnames name *spreadsheet-ablation-root*)))

(load (spreadsheet-ablation-file
       (or #+sbcl (sb-ext:posix-getenv "SPREADSHEET_ABLATION_BASE_MODEL")
           "New_Error (3-5-2-TCP).lisp")))
(load (spreadsheet-ablation-file "Ablation_support.lisp"))

(apply-spreadsheet-ablation :formula-lookback-only)
