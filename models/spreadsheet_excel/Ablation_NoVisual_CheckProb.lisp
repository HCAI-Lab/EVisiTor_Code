#|
Formula-check-probability sweep wrapper, visual search DISABLED
(cell 011: V=0, B=1, C=1).

FORMULA_CHECK_PROB is the probability that the model visually checks a formula
keystroke; it is supplied by the batch harness as a decimal.  Typing-error
rates stay at the calibrated human values (formula 3.4%, word 6.3%) so the
only thing varying across conditions is the checking probability.
|#

(defparameter *spreadsheet-ablation-root*
  (make-pathname :name nil :type nil
                 :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-ablation-file (name)
  (namestring (merge-pathnames name *spreadsheet-ablation-root*)))

(load (spreadsheet-ablation-file
       (or #+sbcl (sb-ext:posix-getenv "SPREADSHEET_ABLATION_BASE_MODEL")
           "New_Error (3-5-2-TCP-7-21-2026).lisp")))
(load (spreadsheet-ablation-file "Ablation_support.lisp"))

(defun spreadsheet-rate-from-env (name default)
  (let ((raw #+sbcl (sb-ext:posix-getenv name) #-sbcl nil))
    (if raw
        (let ((*read-eval* nil))
          (coerce (read-from-string raw) 'single-float))
      default)))

(apply-spreadsheet-factorial
 :visual-search nil
 :formula-lookback t
 :error-correction t
 :variant :no-visual-check-probability-sweep
 :check-probability
 (spreadsheet-rate-from-env "FORMULA_CHECK_PROB" 0.40)
 :typing-error-rate 0.034
 :word-typing-error-rate 0.063)
