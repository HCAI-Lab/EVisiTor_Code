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
                                               (enforce-150-for-medium-large nil))
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
                                                  (enforce-150-for-medium-large nil))
  ;; completion-time-effect-size is Cohen's d for task completion time differences
  ;; between the two model conditions being compared.
  (recommended-runs-from-effect-size
   :effect-size completion-time-effect-size
   :run-cost run-cost
   :enforce-150-for-medium-large enforce-150-for-medium-large))

(defun run-model-paper-guided (&key (effect-size 0.5)
                                    (run-cost :inexpensive)
                                    (batch-root nil)
                                    (enforce-150-for-medium-large nil)
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
                                                    (enforce-150-for-medium-large nil)
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
                                                             (enforce-150-for-medium-large nil)
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

(defun spreadsheet-ablation-model-sources ()
  ;; Complete 2x2x2 factorial (V visual search, B batched formula typing,
  ;; C error+correction package), in canonical cell order
  ;; 000, 100, 010, 001, 110, 101, 011, 111.
  (list "Ablation_Perfect.lisp"
        "Ablation_Visual_Search_Only.lisp"
        "Ablation_Batched_Formula_Typing.lisp"
        "Ablation_Correction_Checking.lisp"
        "Ablation_Visual_Plus_Batched.lisp"
        "Ablation_Visual_Plus_Checking.lisp"
        "Ablation_Batched_Plus_Checking.lisp"
        "Ablation_Full_Realistic.lisp"))

(defun run-spreadsheet-ablation-models (&key (runs 25)
                                             (batch-root nil)
                                             (retain-run-results nil)
                                             (verbose t))
  (run-model-sources-one-by-one
   :model-sources (spreadsheet-ablation-model-sources)
   :runs runs
   :batch-root batch-root
   :retain-run-results retain-run-results
   :verbose verbose))

(defun run-spreadsheet-ablation-paper-guided-completion-time
    (&key (completion-time-effect-size 0.5)
          (run-cost :inexpensive)
          (batch-root nil)
          (enforce-150-for-medium-large nil)
          (retain-run-results nil)
          (verbose t))
  (run-model-sources-paper-guided-completion-time
   :model-sources (spreadsheet-ablation-model-sources)
   :completion-time-effect-size completion-time-effect-size
   :run-cost run-cost
   :batch-root batch-root
   :enforce-150-for-medium-large enforce-150-for-medium-large
   :retain-run-results retain-run-results
   :verbose verbose))

;; ---- Adaptive run counts (2026-07-21) ---------------------------------------
;; Run only as many times as the power analysis actually needs, instead of a
;; fixed 150 per condition.  The run count comes from the same formula the
;; paper-guided helpers above already use (delta = d * sqrt(N/2), so
;; N = 2 * (delta / d)^2 per condition; delta 3.30 for power .90 and 4.20
;; for power .99 at alpha = .05, from Ritter et al.'s run-count guidance).
;; The difference: instead of assuming a Cohen's d up front, the adaptive
;; runner measures the completion-time SD from a pilot batch of this very
;; model, converts the smallest effect the study cares about (in seconds)
;; into d = effect / SD, and keeps running only until the resulting N.
;; The estimate is refreshed after every run, so a noisier-than-expected
;; model raises the target and a quieter one lowers it.

(defun sample-mean (xs)
  (/ (reduce #'+ xs) (length xs)))

(defun sample-sd (xs)
  (if (< (length xs) 2)
      0.0
    (let ((m (sample-mean xs)))
      (sqrt (/ (reduce #'+ (mapcar (lambda (x) (expt (- x m) 2)) xs))
               (1- (length xs)))))))

(defun runs-needed-for-effect-seconds (sd effect-seconds &optional (run-cost :expensive))
  ;; Runs per condition needed to detect a completion-time difference of
  ;; EFFECT-SECONDS given the observed between-run SD.
  (let ((delta (paper-delta-for-run-cost run-cost)))
    (if (or (null sd) (<= sd 0) (<= effect-seconds 0))
        2
      (max 2 (ceiling (* 2 (expt (/ (* delta sd) effect-seconds) 2)))))))

(defun run-model-adaptive (&key (model-source nil)
                                (effect-seconds 15.0)
                                (run-cost :expensive)
                                (pilot-runs 8)
                                (max-runs 150)
                                (batch-root nil)
                                (verbose t))
  "Run MODEL-SOURCE repeatedly, stopping as soon as the run count satisfies
   the power analysis for detecting EFFECT-SECONDS.  PILOT-RUNS runs are
   always performed to get a first SD estimate; MAX-RUNS caps the total.
   Returns a plist with :runs :needed :mean :sd :times :batch-root."
  (let* ((root (ensure-directory-pathname (or batch-root (default-batch-log-root))))
         (source (and model-source (ensure-model-source-path model-source)))
         (original-source (and (boundp '*spreadsheet-model-source-file*)
                               *spreadsheet-model-source-file*))
         (had-tcp-debug (boundp '*tcp-debug*))
         (original-tcp-debug (and had-tcp-debug *tcp-debug*))
         (had-quiet-output (boundp '*batch-quiet-output*))
         (original-quiet-output (and had-quiet-output *batch-quiet-output*))
         (times nil)
         (needed pilot-runs)
         (run-index 0))
    (unwind-protect
        (progn
          (when had-tcp-debug
            (setf *tcp-debug* nil))
          (when had-quiet-output
            (setf *batch-quiet-output* t))
          (when source
            (setf *spreadsheet-model-source-file* source))
          (loop while (< run-index (min (max needed pilot-runs) max-runs))
                do (incf run-index)
                   (let ((run-dir (merge-pathnames (run-subdirectory-name run-index) root))
                         (status "finished"))
                     (handler-case
                         (progn
                           (set-model-log-directory run-dir)
                           (rebuild-model-for-run)
                           (apply-batch-run-seed run-index)
                           (run-model-loop)
                           (push (mp-time) times))
                       (error (e)
                         (setf status (format nil "error: ~a" e))
                         (when verbose
                           (format t "~&[adaptive] run ~d failed: ~a~%" run-index status))))
                     (cleanup-run-state))
                   (when (and times (>= (length times) (min pilot-runs 2)))
                     (let ((sd (sample-sd times)))
                       (setf needed (runs-needed-for-effect-seconds sd effect-seconds run-cost))
                       (when verbose
                         (format t "~&[adaptive] run ~d: mean=~,1fs sd=~,1fs -> need ~d run~:p for a ~,1fs effect (cap ~d)~%"
                                 run-index (sample-mean times) sd needed effect-seconds max-runs)
                         (finish-output))))))
      (when original-source
        (setf *spreadsheet-model-source-file* original-source))
      (when had-tcp-debug
        (setf *tcp-debug* original-tcp-debug))
      (when had-quiet-output
        (setf *batch-quiet-output* original-quiet-output)))
    (list :model-source (or source *spreadsheet-model-source-file*)
          :runs run-index
          :needed needed
          :completed (length times)
          :mean (and times (sample-mean times))
          :sd (and times (sample-sd times))
          :times (reverse times)
          :batch-root (namestring root))))

(defun run-spreadsheet-ablation-adaptive (&key (effect-seconds 15.0)
                                               (run-cost :expensive)
                                               (pilot-runs 8)
                                               (max-runs 150)
                                               (batch-root nil)
                                               (verbose t))
  "Adaptive-run-count version of RUN-SPREADSHEET-ABLATION-MODELS: each
   factorial cell runs only until its own completion-time noise says the
   target effect is resolvable."
  (let ((root (if batch-root
                  (ensure-directory-pathname batch-root)
                (default-batch-log-root))))
    (loop for source in (spreadsheet-ablation-model-sources)
          collect (let ((label (default-model-label source)))
                    (when verbose
                      (format t "~&==== Adaptive ablation cell: ~a ====~%" label)
                      (finish-output))
                    (run-model-adaptive
                     :model-source source
                     :effect-seconds effect-seconds
                     :run-cost run-cost
                     :pilot-runs pilot-runs
                     :max-runs max-runs
                     :batch-root (merge-pathnames (format nil "~a/" label) root)
                     :verbose verbose)))))

;; Default behavior: keep using live UIA output unless the user switches modes.
; (use-saved-visicon-toggle)
; (use-uia-direct-toggle)
;(load "/home/amir/ACT-R Models/Spreadsheet/Visicon_generator.lisp")
; (run-model-sources-paper-guided-completion-time
;  :model-sources (list "New_Error (3-5-2-TCP).lisp")
;  :completion-time-effect-size 0.5
;  :run-cost :inexpensive)
; (run-spreadsheet-ablation-paper-guided-completion-time
;  :completion-time-effect-size 0.5
;  :run-cost :inexpensive)
