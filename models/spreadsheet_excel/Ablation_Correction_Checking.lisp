#|
Ablation_Correction_Checking.lisp

Paper variant: error making + error checking, no visual search
Purpose: isolate the model's error-recovery mechanism by enabling both motor
misexecution and the existing checking/repair productions while disabling
visual search.
|#

(defparameter *spreadsheet-ablation-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-ablation-file (name)
  (namestring (merge-pathnames name *spreadsheet-ablation-root*)))

(load (spreadsheet-ablation-file
       (or #+sbcl (sb-ext:posix-getenv "SPREADSHEET_ABLATION_BASE_MODEL")
           "New_Error (3-5-2-TCP).lisp")))
(load (spreadsheet-ablation-file "Ablation_support.lisp"))

(apply-spreadsheet-ablation :correction-checking)
