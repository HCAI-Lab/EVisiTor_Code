#|
Ablation_Visual_Plus_Batched.lisp

2x2x2 factorial cell 110: V=1 (visual search), B=1 (batched formula typing
with look-backs), C=0 (error-free typing, checking off).
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
 :formula-lookback t
 :error-correction nil)
