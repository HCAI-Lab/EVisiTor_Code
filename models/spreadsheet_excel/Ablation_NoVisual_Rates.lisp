#|
Error-rate sweep wrapper with visual search DISABLED (cell 011: V=0, B=1, C=1).

Identical to Ablation_Full_Realistic_Rates.lisp except that visual search is
off, so the sweep isolates the effect of the typing-error rates without
visual-search variance on top.  FORMULA_TYPO_RATE and WORD_TYPO_RATE are
decimal probabilities supplied by the batch harness.
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
 :variant :no-visual-rate-sweep
 :typing-error-rate
 (spreadsheet-rate-from-env "FORMULA_TYPO_RATE" 0.034)
 :word-typing-error-rate
 (spreadsheet-rate-from-env "WORD_TYPO_RATE" 0.063))
