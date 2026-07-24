#|
Run_CheckProb_Shard.lisp

Same contract as Run_Ablation_2x2x2_Shard.lisp, with one addition: the run
stops once the goal has moved past STOP_AFTER_TASK (default 10), so each run
executes tasks 1..10 instead of the full 14.

Why not tasks 3..10 only?  The model drives a live spreadsheet: task 3 edits
cells that tasks 1 and 2 create, and there is no start-at-task entry point
(only *stop-after-task*).  Beginning at task 3 would require a pre-built
workbook state and would break seed comparability, because run N's random
draws depend on everything consumed before it.  Tasks 1-2 are therefore
executed to establish state but are NOT scored; the analyzer scores tasks
3-10 only.

Env vars:
  CELL_SOURCE, CELL_CODE, SEED_FILE, SEED_START, SEED_COUNT, BATCH_ROOT
  SPREADSHEET_ABLATION_BASE_MODEL, FORMULA_CHECK_PROB
  STOP_AFTER_TASK   (default 10)
|#

(defvar *shard-cell-source* (sb-ext:posix-getenv "CELL_SOURCE"))
(defvar *shard-cell-code* (sb-ext:posix-getenv "CELL_CODE"))
(defvar *shard-seed-file* (sb-ext:posix-getenv "SEED_FILE"))
(defvar *shard-seed-start* (parse-integer (or (sb-ext:posix-getenv "SEED_START") "1")))
(defvar *shard-seed-count* (parse-integer (or (sb-ext:posix-getenv "SEED_COUNT") "142")))
(defvar *shard-batch-root* (sb-ext:posix-getenv "BATCH_ROOT"))
(defvar *shard-stop-after-task*
  (parse-integer (or (sb-ext:posix-getenv "STOP_AFTER_TASK") "10")))

(unless (and *shard-cell-source* *shard-cell-code* *shard-seed-file* *shard-batch-root*)
  (format *error-output*
          "~&Missing required env vars (CELL_SOURCE, CELL_CODE, SEED_FILE, BATCH_ROOT).~%")
  (sb-ext:exit :code 2))

(unless (equal (sb-ext:posix-getenv "ACTR_RECOMPILE") "1")
  (pushnew :dont-compile-actr *features*))

(load "actr7.x/load-act-r.lisp")
(load "Spreadsheet/Complete_error_model_tcp.lisp")

(use-saved-visicon-toggle)

(setf *stop-after-task* *shard-stop-after-task*)

(defvar *shard-seeds*
  (with-open-file (in *shard-seed-file*)
    (loop for line = (read-line in nil nil)
          while line
          for trimmed = (string-trim '(#\Space #\Tab #\Return) line)
          unless (zerop (length trimmed))
          collect (parse-integer trimmed))))

(let ((needed (+ *shard-seed-start* *shard-seed-count* -1)))
  (unless (<= needed (length *shard-seeds*))
    (format *error-output* "~&Seed file ~a has ~a seeds; shard needs index ~a.~%"
            *shard-seed-file* (length *shard-seeds*) needed)
    (sb-ext:exit :code 2)))

(setf *batch-run-seed-list* *shard-seeds*
      *batch-run-index-offset* (1- *shard-seed-start*)
      *batch-run-label-prefix* (format nil "cell~acheck" *shard-cell-code*)
      *batch-post-rebuild-hook* 'spreadsheet-factorial-write-run-manifest
      *batch-post-run-hook* 'spreadsheet-factorial-write-run-postcheck)

(format t "~&==== check-prob shard: cell ~a (~a), stop after task ~a, runs ~a..~a -> ~a ====~%"
        *shard-cell-code* *shard-cell-source* *shard-stop-after-task*
        *shard-seed-start* (+ *shard-seed-start* *shard-seed-count* -1)
        *shard-batch-root*)
(finish-output)

(run-model-sources-one-by-one
 :model-sources (list *shard-cell-source*)
 :runs *shard-seed-count*
 :batch-root *shard-batch-root*
 :retain-run-results t)

(format t "~&Shard complete: cell ~a runs ~a..~a.~%"
        *shard-cell-code* *shard-seed-start*
        (+ *shard-seed-start* *shard-seed-count* -1))
(finish-output)
(sb-ext:exit :code 0)
