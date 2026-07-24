#|
Ablation_Visual_Plus_Checking.lisp

2x2x2 factorial cell 101: V=1 (visual search), B=0 (formulas typed from
memory after initial encoding), C=1 (calibrated typo injection plus the
overt perceptual checking/repair package).
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
 :visual-search t
 :formula-lookback nil
 :error-correction t)
