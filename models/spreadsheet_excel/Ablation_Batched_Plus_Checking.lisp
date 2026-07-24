#|
Ablation_Batched_Plus_Checking.lisp

2x2x2 factorial cell 011: V=0 (idealized direct target locations), B=1
(batched formula typing with look-backs), C=1 (calibrated typo injection
plus the overt perceptual checking/repair package).
|#

(defparameter *spreadsheet-ablation-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-ablation-file (name)
  (namestring (merge-pathnames name *spreadsheet-ablation-root*)))

(load (spreadsheet-ablation-file
       (or #+sbcl (sb-ext:posix-getenv "SPREADSHEET_ABLATION_BASE_MODEL")
           "New_Error (3-5-2-TCP).lisp")))
(load (spreadsheet-ablation-file "Ablation_support.lisp"))

(apply-spreadsheet-factorial
 :visual-search nil
 :formula-lookback t
 :error-correction t)
