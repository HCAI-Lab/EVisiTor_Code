#|
Run_Ablation_2x2x2_Shard.lisp

Runs ONE contiguous seed-slice of ONE cell of the 2x2x2 spreadsheet ablation
factorial, parameterized by environment variables so many shards can run in
parallel (one sbcl process per shard):

  CELL_SOURCE  wrapper file, e.g. "Ablation_Visual_Plus_Batched.lisp"  (required)
  CELL_CODE    three-digit V/B/C code, e.g. "110"                      (required)
  SEED_FILE    text file with one integer seed per line; line N is the
               seed for global run_N (shared by ALL cells)             (required)
  SEED_START   1-based global index of the first run in this shard     (default 1)
  SEED_COUNT   number of runs in this shard                            (default 150)
  BATCH_ROOT   shard output root (required; each shard MUST have its
               own root so batch_summary.csv has a single writer)
  ACTR_RECOMPILE  set to "1" to allow FASL compilation (default: off —
               shards assume a warm FASL cache; see run_2x2x2_full.ps1)

Run directories are numbered by the GLOBAL seed index (run_007 <-> seed line 7)
so the seed <-> run pairing is identical across cells and shards.  Every run
gets a condition_manifest.json (factor levels + actual switch values + seed)
and a run_postcheck.json (perceptual-chain survival diagnostics).

Usage (from G:\ACT-RModels):
  $env:CELL_SOURCE="Ablation_Perfect.lisp"; $env:CELL_CODE="000"; ...
  sbcl --noinform --non-interactive --load "Spreadsheet/Run_Ablation_2x2x2_Shard.lisp"
|#

(defvar *shard-cell-source* (sb-ext:posix-getenv "CELL_SOURCE"))
(defvar *shard-cell-code* (sb-ext:posix-getenv "CELL_CODE"))
(defvar *shard-seed-file* (sb-ext:posix-getenv "SEED_FILE"))
(defvar *shard-seed-start* (parse-integer (or (sb-ext:posix-getenv "SEED_START") "1")))
(defvar *shard-seed-count* (parse-integer (or (sb-ext:posix-getenv "SEED_COUNT") "150")))
(defvar *shard-batch-root* (sb-ext:posix-getenv "BATCH_ROOT"))

(unless (and *shard-cell-source* *shard-cell-code* *shard-seed-file* *shard-batch-root*)
  (format *error-output*
          "~&Missing required env vars (CELL_SOURCE, CELL_CODE, SEED_FILE, BATCH_ROOT).~%")
  (sb-ext:exit :code 2))

;; Shards assume the ACT-R FASLs were warmed by a single prior load; skipping
;; compilation makes parallel cold starts safe (no recompilation race).
(unless (equal (sb-ext:posix-getenv "ACTR_RECOMPILE") "1")
  (pushnew :dont-compile-actr *features*))

(load "actr7.x/load-act-r.lisp")
(load "Spreadsheet/Complete_error_model_tcp.lisp")

(use-saved-visicon-toggle)

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
      *batch-run-label-prefix* (format nil "cell~a" *shard-cell-code*)
      *batch-post-rebuild-hook* 'spreadsheet-factorial-write-run-manifest
      *batch-post-run-hook* 'spreadsheet-factorial-write-run-postcheck)

(format t "~&==== 2x2x2 shard: cell ~a (~a), runs ~a..~a -> ~a ====~%"
        *shard-cell-code* *shard-cell-source*
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
