#|
Full-realistic wrapper for independent word/formula error-rate sweeps.
FORMULA_TYPO_RATE and WORD_TYPO_RATE are decimal probabilities supplied by
the batch harness.  All other full-realistic mechanisms remain enabled.
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
 :visual-search t
 :formula-lookback t
 :error-correction t
 :variant :full-realistic-rate-sweep
 :typing-error-rate
 (spreadsheet-rate-from-env "FORMULA_TYPO_RATE" 0.034)
 :word-typing-error-rate
 (spreadsheet-rate-from-env "WORD_TYPO_RATE" 0.063))
