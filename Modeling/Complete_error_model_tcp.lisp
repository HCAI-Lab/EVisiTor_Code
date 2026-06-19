#|
Complete_error_model.lisp:
- Author: ambkh
- Date: 2024-07-22
|#
;; TCP variant: make sure TCP_VisiTor.py is running before loading this file.
(defparameter *spreadsheet-root*
	(make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun spreadsheet-file (name)
	(namestring (merge-pathnames name *spreadsheet-root*)))

(load (spreadsheet-file "fucntion_new_tcp.lisp"))
(load (spreadsheet-file "Visicon_generator_V3.lisp"))

;(load "c:/Users/ambkh/OneDrive - The Pennsylvania State University/Amir_abb6024/Spreadsheet/New_error (3-3).lisp")
(load (spreadsheet-file "New_Error (3-5-2-TCP).lisp"))
;(load "c:/Users/ambkh/OneDrive - The Pennsylvania State University/Amir_abb6024/Spreadsheet/New_error (3-5).lisp")
;(load "c:/Users/ambkh/OneDrive - The Pennsylvania State University/Amir_abb6024/Spreadsheet/New_error (3-6).lisp")
(load (spreadsheet-file "running_model_v4.lisp"))

(defun use-saved-visicon-toggle (&optional (directory (merge-pathnames #P"visicons_saved/" *spreadsheet-root*)))
  (use-saved-visicons-iteratively directory))

(defun use-uia-direct-toggle (&optional (json-path (spreadsheet-file "visicons.json")))
  (use-uia-direct-visicons json-path))

(defun run-model-n-times (&optional (runs 25) (batch-root nil))
  (if batch-root
      (run-model-multiple-times runs batch-root)
    (run-model-multiple-times runs)))

(defparameter *paper-delta-power-0-90* 3.30)
(defparameter *paper-delta-power-0-99* 4.20)
(defparameter *paper-recommended-stable-runs* 150)

(defun paper-delta-for-run-cost (&optional (run-cost :inexpensive))
  (ecase run-cost
    (:expensive *paper-delta-power-0-90*)
    (:inexpensive *paper-delta-power-0-99*)))

(defun recommended-runs-from-effect-size (&key (effect-size 0.5) (run-cost :inexpensive)
                                               (enforce-150-for-medium-large t))
  ;; Based on Ritter et al.: delta = effect-size * sqrt(N/2), so N = 2*(delta/effect-size)^2.
  (when (<= effect-size 0)
    (error "EFFECT-SIZE must be > 0. Got: ~a" effect-size))
  (let* ((delta (paper-delta-for-run-cost run-cost))
         (n (ceiling (* 2 (expt (/ delta effect-size) 2)))))
    (if (and enforce-150-for-medium-large
             (>= effect-size 0.5)
             (< n *paper-recommended-stable-runs*))
        *paper-recommended-stable-runs*
      n)))

(defun recommended-runs-for-completion-time (&key (completion-time-effect-size 0.5)
                                                  (run-cost :inexpensive)
                                                  (enforce-150-for-medium-large t))
  ;; completion-time-effect-size is Cohen's d for task completion time differences
  ;; between the two model conditions being compared.
  (recommended-runs-from-effect-size
   :effect-size completion-time-effect-size
   :run-cost run-cost
   :enforce-150-for-medium-large enforce-150-for-medium-large))

(defun run-model-paper-guided (&key (effect-size 0.5)
                                    (run-cost :inexpensive)
                                    (batch-root nil)
                                    (enforce-150-for-medium-large t)
                                    (verbose t))
  (let ((runs (recommended-runs-from-effect-size
               :effect-size effect-size
               :run-cost run-cost
               :enforce-150-for-medium-large enforce-150-for-medium-large)))
    (when verbose
      (format t "~&Paper-guided run count: ~a (effect-size=~a, run-cost=~a)~%"
              runs effect-size run-cost))
    (if batch-root
        (run-model-multiple-times runs batch-root)
      (run-model-multiple-times runs))))

(defun run-model-paper-guided-completion-time (&key (completion-time-effect-size 0.5)
                                                    (run-cost :inexpensive)
                                                    (batch-root nil)
                                                    (enforce-150-for-medium-large t)
                                                    (verbose t))
  (let ((runs (recommended-runs-for-completion-time
               :completion-time-effect-size completion-time-effect-size
               :run-cost run-cost
               :enforce-150-for-medium-large enforce-150-for-medium-large)))
    (when verbose
      (format t "~&Paper-guided run count for completion time: ~a (d=~a, run-cost=~a)~%"
              runs completion-time-effect-size run-cost))
    (if batch-root
        (run-model-multiple-times runs batch-root)
      (run-model-multiple-times runs))))

(defun ensure-model-source-path (model-source)
  (namestring
   (if (pathname-name (pathname model-source))
       (merge-pathnames model-source *spreadsheet-root*)
     (error "MODEL-SOURCE must include a file name. Got: ~a" model-source))))

(defun default-model-label (model-source)
  (or (pathname-name (pathname model-source))
      "model"))

(defun run-model-sources-one-by-one (&key model-sources
                                          (runs 25)
                                          (batch-root nil)
                                          (retain-run-results nil)
                                          (verbose t))
  ;; Run each model source sequentially (never in parallel): load source A, run A,
  ;; then load source B, run B, etc.
  (let* ((sources (or model-sources
                      (list "New_Error (3-5-2-TCP).lisp")))
         (root (if batch-root
                   (ensure-directory-pathname batch-root)
                 (default-batch-log-root)))
         (original-source (and (boundp '*spreadsheet-model-source-file*)
                               *spreadsheet-model-source-file*))
         (results nil))
    (unwind-protect
         (dolist (source sources)
           (let* ((resolved-source (ensure-model-source-path source))
                  (label (default-model-label source))
                  (model-root (merge-pathnames
                               (format nil "~a/" label)
                               root))
                  (run-summary nil))
             (setf *spreadsheet-model-source-file* resolved-source)
             (when verbose
               (format t "~&Running model source one-by-one: ~a (runs=~a)~%"
                       resolved-source runs))
             (setf run-summary
                   (run-model-multiple-times runs model-root retain-run-results))
             (push (list :model-source resolved-source
                         :runs runs
                         :batch-root (namestring model-root)
                         :results run-summary)
                   results)
             (maybe-run-full-gc)))
      (when original-source
        (setf *spreadsheet-model-source-file* original-source)))
    (nreverse results)))

(defun run-model-sources-paper-guided-completion-time (&key model-sources
                                                             (completion-time-effect-size 0.5)
                                                             (run-cost :inexpensive)
                                                             (batch-root nil)
                                                             (enforce-150-for-medium-large t)
                                                             (retain-run-results nil)
                                                             (verbose t))
  (let ((runs (recommended-runs-for-completion-time
               :completion-time-effect-size completion-time-effect-size
               :run-cost run-cost
               :enforce-150-for-medium-large enforce-150-for-medium-large)))
    (when verbose
      (format t "~&Paper-guided per-model runs for completion time: ~a (d=~a, run-cost=~a)~%"
              runs completion-time-effect-size run-cost))
    (run-model-sources-one-by-one
     :model-sources model-sources
     :runs runs
     :batch-root batch-root
     :retain-run-results retain-run-results
     :verbose verbose)))

;; Default behavior: keep using live UIA output unless the user switches modes.
; (use-saved-visicon-toggle)
; (use-uia-direct-toggle)
;(load "/home/amir/ACT-R Models/Spreadsheet/Visicon_generator.lisp")
; (run-model-sources-paper-guided-completion-time
;  :model-sources (list "New_Error (3-5-2-TCP).lisp")
;  :completion-time-effect-size 0.5
;  :run-cost :inexpensive)
