#|
Ablation_support.lisp

Small runtime switches for the spreadsheet ablation models.

The large spreadsheet models define the productions.  The ablation source
files load one of those base models and then call APPLY-SPREADSHEET-ABLATION
to pin the perceptual/motor/checking mechanisms for a specific paper variant.
|#

(defparameter *spreadsheet-ablation-variant* nil)

;; Human-calibrated per-keystroke error rates for the Excel normalization
;; task, estimated from correction episodes per content keystroke in the
;; participant keystroke logs (19 subjects; see
;; Spreadsheet/analyze_human_error_rates.py and
;; logs/human_error_analysis/human_error_rates_summary.csv):
;;   formula typing: 0.034 (pooled; mean 0.034, SD 0.017)
;;   word typing:    0.063 (pooled; mean 0.067, SD 0.072)
(defparameter *spreadsheet-ablation-default-typing-error-rate* 0.034)
(defparameter *spreadsheet-ablation-default-word-typing-error-rate* 0.063)
(defparameter *spreadsheet-ablation-visual-search-enabled* t)
(defparameter *spreadsheet-ablation-formula-lookback-enabled* t)

(defparameter *spreadsheet-ablation-known-object-targets*
  '("File Tab" "Open" "normalization.xlsx" "Save a Copy" "file_name"
    "Home" "Insert Cells"))

;; Idealized no-search coordinates for controls which are not present in the
;; first saved snapshot (notably FILE_NAME).  These are task-environment
;; locations used only by V=0 cells; V=1 continues to find live features.
(defparameter *spreadsheet-ablation-known-object-fallback-locations*
  '(("File Tab" 32 64)
    ("Open" 81 194)
    ("normalization.xlsx" 200 340)
    ("Save a Copy" 81 330)
    ("file_name" 664 153)
    ("Home" 86 64)
    ("Insert Cells" 768 95)))

(defvar *motor-error-rate*)
(defvar *target-keypress-typo-rate*)
(defvar *actual-word-immediate-check-probability*)

;; Sweep override: when a number, it wins over every other source of the
;; typing error rate.  A DEFVAR so per-run reloads of this file cannot clobber
;; a rate set by an external sweep harness.
(defvar *spreadsheet-ablation-forced-typing-error-rate* nil)

(defun spreadsheet-ablation-effective-typing-error-rate (&optional rate)
  ;; NOTE: *motor-error-rate* from motor_model.json is deliberately NOT used
  ;; here: that value (0.467) is P(adjacent-key | substitution error), a
  ;; conditional probability, not a per-keystroke rate.
  (cond
    ((numberp *spreadsheet-ablation-forced-typing-error-rate*)
     *spreadsheet-ablation-forced-typing-error-rate*)
    ((numberp rate) rate)
    (t *spreadsheet-ablation-default-typing-error-rate*)))

(defun spreadsheet-ablation-effective-word-typing-error-rate (&optional rate)
  (cond
    ((numberp *spreadsheet-ablation-forced-typing-error-rate*)
     *spreadsheet-ablation-forced-typing-error-rate*)
    ((numberp rate) rate)
    (t *spreadsheet-ablation-default-word-typing-error-rate*)))

(defun set-spreadsheet-typing-error-rate (rate &optional word-rate)
  ;; Sets the formula-path rate (*target-keypress-typo-rate*) and the
  ;; word-path rate (*word-keypress-typo-rate*) together.  With no arguments
  ;; both take their human-calibrated defaults; a forced sweep rate overrides
  ;; both uniformly.
  (let ((effective-rate (spreadsheet-ablation-effective-typing-error-rate rate))
        (effective-word-rate
         (spreadsheet-ablation-effective-word-typing-error-rate word-rate)))
    (when (boundp '*target-keypress-typo-rate*)
      (setf *target-keypress-typo-rate* effective-rate))
    (when (boundp '*word-keypress-typo-rate*)
      (setf *word-keypress-typo-rate* effective-word-rate))
    (list effective-rate effective-word-rate)))

(defun disable-spreadsheet-typing-errors ()
  (when (boundp '*target-keypress-typo-rate*)
    (setf *target-keypress-typo-rate* 0.0))
  (when (boundp '*word-keypress-typo-rate*)
    (setf *word-keypress-typo-rate* 0.0))
  0.0)

(defun spreadsheet-ablation-type-check-default ()
  (if (or (not (boundp '*last-expected-key*))
          (not (boundp '*last-typed-key*))
          (null *last-expected-key*)
          (null *last-typed-key*)
          (string-equal *last-expected-key* *last-typed-key*))
      "true"
    "false"))

(defun enable-spreadsheet-correction-checking ()
  ;; Restore the keyboard monitor's check function.  TYPE-CHECK is defined in
  ;; fucntion_new_tcp.lisp, not in each model source, so a previous ablation can
  ;; otherwise leave it disabled across subsequent model reloads.
  (when (boundp '*actual-word-immediate-check-probability*)
    (setf *actual-word-immediate-check-probability* 0.85))
  ;; Restore the session default for perceptual checking (NIL since
  ;; 2026-07-18: the paper model uses the instant check; see
  ;; Perceptual_Checking_Report_2026-07-18.md) rather than forcing it on.
  (when (boundp '*visual-error-checking-enabled*)
    (setf *visual-error-checking-enabled*
          (and (boundp '*visual-error-checking-default*)
               *visual-error-checking-default*)))
  (when (boundp '*typed-echo-failures*)
    (setf *typed-echo-failures* 0))
  (when (fboundp 'reset-formula-entry-tracking)
    (reset-formula-entry-tracking))
  (setf (symbol-function 'type-check)
        (symbol-function 'spreadsheet-ablation-type-check-default))
  t)

(defun disable-spreadsheet-correction-checking ()
  ;; Preserve delivered motor errors, but make the cognitive checking path
  ;; believe the typed character is acceptable.  Delayed error discovery is
  ;; also disabled so the repair productions do not become eligible later.
  (when (boundp '*actual-word-immediate-check-probability*)
    (setf *actual-word-immediate-check-probability* 0.0))
  ;; No checking also means no looking: skip the attend/encode chain entirely.
  (when (boundp '*visual-error-checking-enabled*)
    (setf *visual-error-checking-enabled* nil))
  (when (fboundp 'reset-formula-entry-tracking)
    (reset-formula-entry-tracking))

  (defun type-check ()
    "true")

  (defun maybe-store-delayed-error-position
      (current-error check-mode expected typed position)
    (declare (ignore check-mode expected typed position))
    current-error)

  (defun maybe-store-delayed-error-next-position
      (current-error-next check-mode expected typed next-position)
    (declare (ignore check-mode expected typed next-position))
    current-error-next)

  t)

(defun enable-spreadsheet-visual-search ()
  (setf *spreadsheet-ablation-visual-search-enabled* t))

(defun disable-spreadsheet-visual-search ()
  (setf *spreadsheet-ablation-visual-search-enabled* nil))

(defun disable-spreadsheet-learned-formulas ()
  ;; With *formula-practice-learning-enabled* NIL (the default, and every
  ;; published configuration) this reproduces the study's inert strategy: the
  ;; retrieved type passes straight through and the learned-formula path is
  ;; never selected.  When the practice-learning switch is on (see
  ;; fucntion_new_tcp.lisp), formulas whose pattern has been practiced
  ;; *learned-formula-practice-threshold* times switch to the from-memory
  ;; learned-formula productions.  This redefinition must stay in sync with
  ;; FORMULA-TYPING-STRATEGY in the model file — it overwrites it on every
  ;; per-run reload.
  (defun formula-typing-strategy (retrieved-type formula)
    (when (fboundp 'formula-practice-note-current-word)
      (formula-practice-note-current-word formula))
    (if (and (boundp '*formula-practice-learning-enabled*)
             (symbol-value '*formula-practice-learning-enabled*)
             retrieved-type
             (string-equal (princ-to-string retrieved-type) "formula")
             (fboundp 'learned-formula-pattern-ready-p)
             (learned-formula-pattern-ready-p formula))
        "learned-formula"
        retrieved-type)))

(defun enable-spreadsheet-formula-lookback ()
  (setf *spreadsheet-ablation-formula-lookback-enabled* t)
  (disable-spreadsheet-learned-formulas))

(defun disable-spreadsheet-formula-lookback ()
  (setf *spreadsheet-ablation-formula-lookback-enabled* nil)
  (disable-spreadsheet-learned-formulas))

(defun spreadsheet-ablation-clean-label (label)
  (when label
    (let ((s (string label)))
      (remove-if (lambda (ch)
                   (member (char-code ch) '(8234 8235 8236 8237 8238 8206 8207)))
                 s))))

(defun spreadsheet-ablation-string-contains-p (haystack needle)
  (and haystack needle
       (search (string-downcase needle)
               (string-downcase haystack)
               :test #'char=)))

(defun spreadsheet-ablation-visicon-labels (visicon)
  (remove-duplicates
   (remove-if (lambda (s) (or (null s) (zerop (length s))))
              (mapcar #'spreadsheet-ablation-clean-label
                      (list (getf visicon :name)
                            (getf visicon :text)
                            (getf visicon :text-vlm))))
   :test #'string-equal))

(defun spreadsheet-ablation-add-remembered-location (label x y)
  (when (and label x y)
    (ignore-errors
      (add-dm-fct
       (list (list 'isa 'remembered-location
                   'item label
                   'sx x
                   'sy y))))))

(defun spreadsheet-ablation-known-object-location (label)
  (find label *spreadsheet-ablation-known-object-fallback-locations*
        :key #'first :test #'string-equal))

(defun spreadsheet-ablation-ensure-known-object-feature (label)
  (let ((entry (spreadsheet-ablation-known-object-location label)))
    (when entry
      (ignore-errors
        (add-visicon-features
         `(screen-x ,(second entry) screen-y ,(third entry)
           height 24 width 80 type "text" text T
           value ,label text-value ,label)))
      t)))

(defun spreadsheet-ablation-seed-known-locations ()
  ;; The no-search conditions represent idealized knowledge of where objects
  ;; are.  Seed remembered-location chunks from the current visicon snapshot so
  ;; the model uses the recalled-location path rather than random visual search.
  (when (not *spreadsheet-ablation-visual-search-enabled*)
    (dolist (entry *spreadsheet-ablation-known-object-fallback-locations*)
      (spreadsheet-ablation-add-remembered-location
       (first entry) (second entry) (third entry))))
  (when (and (not *spreadsheet-ablation-visual-search-enabled*)
             (fboundp 'read-json-visicons)
             (fboundp 'active-visicon-json-path))
    (dolist (visicon (ignore-errors (read-json-visicons (active-visicon-json-path))))
      (let* ((position (getf visicon :position))
             (x (first position))
             (y (second position)))
        (when (and x y (< x 960))
          (dolist (label (spreadsheet-ablation-visicon-labels visicon))
            (spreadsheet-ablation-add-remembered-location label x y))
          (dolist (target *spreadsheet-ablation-known-object-targets*)
            (when (some (lambda (label)
                          (spreadsheet-ablation-string-contains-p label target))
                        (spreadsheet-ablation-visicon-labels visicon))
              (spreadsheet-ablation-add-remembered-location target x y))))))))

(unless (fboundp 'spreadsheet-ablation-base-main)
  (when (fboundp 'main)
    (setf (symbol-function 'spreadsheet-ablation-base-main)
          (symbol-function 'main))))

(when (fboundp 'spreadsheet-ablation-base-main)
  (defun main ()
    (funcall (symbol-function 'spreadsheet-ablation-base-main))
    (spreadsheet-ablation-seed-known-locations)))

(P ablation-direct-known-object-location
    =goal>
        isa     intention
        job     "do-action"
        meaning "attention-N-movecursor"
        item    =x
        type    "nil"
    ?visual-location>
        state   free
    ?visual>
        state   free
    !eval! (not *spreadsheet-ablation-visual-search-enabled*)
==>
    =goal>
        isa     intention
        job     "ablation-direct-object-attention"
        item    =x
        type    "nil"
    +visual-location>
        isa     visual-location
        text-value =x
        type    "text"
        <       screen-x 960)

(P ablation-use-recalled-object-location
    =goal>
        isa     intention
        job     "checking-object-location-memory"
        item    =x
    =retrieval>
        isa     remembered-location
        sx      =sx
        sy      =sy
    ?visual-location>
        state   free
    !eval! (not *spreadsheet-ablation-visual-search-enabled*)
==>
    =goal>
        isa     intention
        job     "ablation-direct-object-attention"
        item    =x
        type    "nil"
    +visual-location>
        isa     visual-location
        screen-x =sx
        screen-y =sy
        type    "text"
    -   text-value nil
    -   cell t
    -   cell-type "column"
    -   cell-type "row"
        <       screen-x 960)

(P ablation-direct-known-object-location-failed
    =goal>
        isa     intention
        job     "ablation-direct-object-attention"
        item    =x
    ?visual-location>
        state   error
    !eval! (not *spreadsheet-ablation-visual-search-enabled*)
    !eval! (null (spreadsheet-ablation-known-object-location =x))
==>
    =goal>
        isa     intention
        job     "checking-object-location-memory"
        item    =x
        type    "nil"
    +retrieval>
        isa     remembered-location
        item    =x
    -   sx      nil
    -   sy      nil)

(P ablation-materialize-known-object-location
    =goal>
        isa     intention
        job     "ablation-direct-object-attention"
        item    =x
    ?visual-location>
        state   error
    !eval! (not *spreadsheet-ablation-visual-search-enabled*)
    !eval! (spreadsheet-ablation-known-object-location =x)
==>
    !eval! (spreadsheet-ablation-ensure-known-object-feature =x)
    =goal>
        job     "ablation-direct-object-attention"
        item    =x
        type    "nil"
    +visual-location>
        isa     visual-location
        text-value =x
        type    "text"
        <       screen-x 960)

(P ablation-direct-known-object-location-succeeded
    =goal>
        isa     intention
        job     "ablation-direct-object-attention"
        item    =item
        subsubtask =x
        type    "nil"
    =visual-location>
        screen-x =sx
        screen-y =sy
    ?visual>
        state   free
==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "direct-known-object-location")
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item    =item
        subsubtask =x
        type    "nil"
        sx      =sx
        sy      =sy
        right-hand-location "mouse"
    +visual>
        isa     move-attention
        screen-pos =visual-location)

; In V=0 the direct-location path can finish all visual work before ACT-R's
; HAND-TO-HOME command completes.  That motor command clears the manual buffer
; without scheduling a fresh conflict-resolution event, so the dated model's
; two-stage hand-homing continuation can otherwise idle forever.  Start the
; word retrieval together with the homing movement; later typing productions
; still require the motor processor to be free before issuing a key.
(P ablation-home-hand-and-retrieve-word
    =goal>
        isa     intention
        job     "do-action"
        meaning "type"
        type    "pending"
        item    =y
        right-hand-location "mouse"
    ?manual>
        state   free
    !eval! (not *spreadsheet-ablation-visual-search-enabled*)
==>
    +manual>
        isa     hand-to-home
        hand    right
    =goal>
        job     "typing"
        word    =y
        right-hand-location "keyboard"
    +retrieval>
        isa     word
        spelling =y)

(P ablation-finished-current-token-without-lookback
    =goal>
        ISA       typing
        word      =w
        type      formula
        phase     "have-char"
        token-done "yes"
        token-index =ti
        target-cell =target
        formula-source =source
    ?visual>
        state free
    ?visual-location>
        state free
    !eval! (not *spreadsheet-ablation-formula-lookback-enabled*)
==>
    !bind!  =nti (next-formula-token-index =ti)
    !bind!  =next-token (formula-token-at-safe =w =nti)
    !bind!  =next-phase (if (string-equal =next-token "__end_of_formula__")
                            "memorize-token"
                            "typing-token")
    =goal>
        phase =next-phase
        token-index =nti
        char-index 0
        current-token =next-token
        next-char nil
        token-done nil)

(ignore-errors
  (spp ablation-direct-known-object-location :u 100)
  (spp ablation-use-recalled-object-location :u 100)
  (spp ablation-direct-known-object-location-failed :u 100)
  (spp ablation-materialize-known-object-location :u 100)
  (spp ablation-direct-known-object-location-succeeded :u 100)
  (spp ablation-home-hand-and-retrieve-word :u 100)
  (spp ablation-finished-current-token-without-lookback :u 100))

;; --- 2x2x2 factorial configuration -------------------------------------------
;; The July 20 perceptual/final-check model is the factorial baseline.  Three
;; independent factors:
;;   V  visual-search      live local/global search vs. idealized direct
;;                         (remembered) target locations
;;   B  formula-lookback   token-batched typing with instruction look-backs
;;                         vs. typing from memory after initial encoding
;;   C  error-correction   the PACKAGE of human-calibrated typo injection plus
;;                         the overt perceptual checking/repair chain (word
;;                         immediate/final checks, probabilistic per-keystroke
;;                         formula checks, guaranteed pre-Enter read-back)
;; C=1 must PIN the checking switches AFTER enable-spreadsheet-correction-
;; checking, because that helper restores *visual-error-checking-enabled*
;; from the mutable *visual-error-checking-default* (deliberately NIL in the
;; source so older instant-check runs stay reproducible).

(defparameter *spreadsheet-factorial-levels* nil)
(defparameter *spreadsheet-factorial-config* nil)

;; July 20 human-calibrated configuration
;; (Check_Rate_Sweep_Report_2026-07-20.md, paper-rate condition): formula
;; typo rate 0.034, word typo rate 0.063, formula visual-check probability
;; 0.40, word immediate-check probability 0.85, and the guaranteed final
;; formula check enabled.  The two typo rates must remain independent.
(defparameter *spreadsheet-factorial-c1-formula-typing-error-rate* 0.034)
(defparameter *spreadsheet-factorial-c1-word-typing-error-rate* 0.063)
(defparameter *spreadsheet-factorial-c1-check-probability* 0.40)
(defparameter *spreadsheet-factorial-c1-word-immediate-check-probability* 0.85)

(defun spreadsheet-factorial-assert (name ok)
  (unless ok
    (error "Factorial configuration assertion failed: ~a" name)))

(defun spreadsheet-factorial-assert-consistency ()
  (let ((levels *spreadsheet-factorial-levels*))
    (destructuring-bind (&key visual-search formula-lookback error-correction)
        levels
      (spreadsheet-factorial-assert
       "visual-search switch"
       (eq (and *spreadsheet-ablation-visual-search-enabled* t)
           (and visual-search t)))
      (spreadsheet-factorial-assert
       "formula-lookback switch"
       (eq (and *spreadsheet-ablation-formula-lookback-enabled* t)
           (and formula-lookback t)))
      (if error-correction
          (let ((rate (getf *spreadsheet-factorial-config* :typing-error-rate))
                (word-rate
                 (getf *spreadsheet-factorial-config* :word-typing-error-rate))
                (checkp (getf *spreadsheet-factorial-config* :check-probability))
                (wordp (getf *spreadsheet-factorial-config*
                             :word-immediate-check-probability)))
            (spreadsheet-factorial-assert
             "C=1 uniform forced typo rate cleared"
             (null *spreadsheet-ablation-forced-typing-error-rate*))
            (spreadsheet-factorial-assert
             "C=1 formula typo rate"
             (and (boundp '*target-keypress-typo-rate*)
                  (= *target-keypress-typo-rate* rate)))
            (spreadsheet-factorial-assert
             "C=1 word typo rate"
             (and (boundp '*word-keypress-typo-rate*)
                  (numberp *word-keypress-typo-rate*)
                  (= *word-keypress-typo-rate* word-rate)))
            (spreadsheet-factorial-assert
             "C=1 visual checking enabled"
             (and (boundp '*visual-error-checking-enabled*)
                  *visual-error-checking-enabled*))
            (spreadsheet-factorial-assert
             "C=1 visual checking default"
             (and (boundp '*visual-error-checking-default*)
                  *visual-error-checking-default*))
            (spreadsheet-factorial-assert
             "C=1 formula visual check probability"
             (and (boundp '*formula-visual-check-probability*)
                  (= *formula-visual-check-probability* checkp)))
            (spreadsheet-factorial-assert
             "C=1 word immediate check probability"
             (and (boundp '*actual-word-immediate-check-probability*)
                  (= *actual-word-immediate-check-probability* wordp))))
        (progn
          (spreadsheet-factorial-assert
           "C=0 forced typo rate cleared"
           (null *spreadsheet-ablation-forced-typing-error-rate*))
          (spreadsheet-factorial-assert
           "C=0 formula typo rate 0"
           (and (boundp '*target-keypress-typo-rate*)
                (zerop *target-keypress-typo-rate*)))
          (spreadsheet-factorial-assert
           "C=0 word typo rate 0"
           (or (not (boundp '*word-keypress-typo-rate*))
               (null *word-keypress-typo-rate*)
               (zerop *word-keypress-typo-rate*)))
          (spreadsheet-factorial-assert
           "C=0 visual checking disabled"
           (or (not (boundp '*visual-error-checking-enabled*))
               (null *visual-error-checking-enabled*)))
          (spreadsheet-factorial-assert
           "C=0 visual checking default nil"
           (or (not (boundp '*visual-error-checking-default*))
               (null *visual-error-checking-default*)))
          (spreadsheet-factorial-assert
           "C=0 word immediate check probability 0"
           (and (boundp '*actual-word-immediate-check-probability*)
                (zerop *actual-word-immediate-check-probability*)))))))
  t)

(defun apply-spreadsheet-factorial
    (&key visual-search formula-lookback error-correction
          (variant nil)
          (typing-error-rate
           *spreadsheet-factorial-c1-formula-typing-error-rate*)
          (word-typing-error-rate
           *spreadsheet-factorial-c1-word-typing-error-rate*)
          (check-probability *spreadsheet-factorial-c1-check-probability*)
          (word-immediate-check-probability
           *spreadsheet-factorial-c1-word-immediate-check-probability*))
  ;; Configure the three factors independently.  No factor may silently
  ;; change another: V and B only touch their own switches; C owns the whole
  ;; error-generation + perceptual-checking/repair package.
  (setf *spreadsheet-ablation-variant*
        (or variant
            (intern (format nil "FACTORIAL-V~dB~dC~d"
                            (if visual-search 1 0)
                            (if formula-lookback 1 0)
                            (if error-correction 1 0))
                    :keyword)))
  (if visual-search
      (enable-spreadsheet-visual-search)
    (disable-spreadsheet-visual-search))
  (if formula-lookback
      (enable-spreadsheet-formula-lookback)
    (disable-spreadsheet-formula-lookback))
  (cond
    (error-correction
     ;; Calibrated typo injection uses independent human-measured formula and
     ;; word rates.  A uniform forced rate would silently collapse these two
     ;; parameters, so it must be cleared for the factorial experiment.
     (setf *spreadsheet-ablation-forced-typing-error-rate* nil)
     (set-spreadsheet-typing-error-rate
      typing-error-rate word-typing-error-rate)
     (enable-spreadsheet-correction-checking)
     ;; Pin the perceptual chain AFTER the enable helper: it restores
     ;; *visual-error-checking-enabled* from the mutable session default.
     (when (boundp '*visual-error-checking-default*)
       (setf *visual-error-checking-default* t))
     (when (boundp '*visual-error-checking-enabled*)
       (setf *visual-error-checking-enabled* t))
     (when (boundp '*formula-visual-check-probability*)
       (setf *formula-visual-check-probability* check-probability))
     (when (boundp '*actual-word-immediate-check-probability*)
       (setf *actual-word-immediate-check-probability*
             word-immediate-check-probability)))
    (t
     ;; Error-free typing with the whole checking chain off: no typed-text
     ;; checks, no formula-final read-back/repair loop (the instant escape
     ;; hatch produces the verdict on a provably clean entry).
     (setf *spreadsheet-ablation-forced-typing-error-rate* nil)
     (disable-spreadsheet-typing-errors)
     (disable-spreadsheet-correction-checking)
     (when (boundp '*visual-error-checking-default*)
       (setf *visual-error-checking-default* nil))
     (when (boundp '*formula-visual-check-probability*)
       (setf *formula-visual-check-probability* 0.0))))
  (when (boundp '*formula-final-direct-count*)
    (setf *formula-final-direct-count* 0))
  (when (boundp '*typed-echo-failures*)
    (setf *typed-echo-failures* 0))
  (setf *spreadsheet-factorial-levels*
        (list :visual-search (and visual-search t)
              :formula-lookback (and formula-lookback t)
              :error-correction (and error-correction t))
        *spreadsheet-factorial-config*
        (list :typing-error-rate (if error-correction typing-error-rate 0.0)
              :word-typing-error-rate
              (if error-correction word-typing-error-rate 0.0)
              :check-probability (if error-correction check-probability 0.0)
              :word-immediate-check-probability
              (if error-correction word-immediate-check-probability 0.0)
              :guaranteed-final-check (and error-correction t)))
  (spreadsheet-factorial-assert-consistency)
  *spreadsheet-factorial-levels*)

;; --- Per-run condition manifests ---------------------------------------------
;; Written into the current run's log directory by the batch harness hooks
;; (*batch-post-rebuild-hook* / *batch-post-run-hook* in running_model_v4).

(defun spreadsheet-factorial-json-escape (s)
  (with-output-to-string (out)
    (loop for ch across (princ-to-string s) do
          (case ch
            (#\" (write-string "\\\"" out))
            (#\\ (write-string "\\\\" out))
            (#\Newline (write-string "\\n" out))
            (t (write-char ch out))))))

(defun spreadsheet-factorial-json-value (v)
  (cond ((eq v t) "true")
        ((null v) "false")
        ((eq v :null) "null")
        ((floatp v) (format nil "~f" v))
        ((numberp v) (format nil "~a" v))
        (t (format nil "\"~a\"" (spreadsheet-factorial-json-escape v)))))

(defun spreadsheet-factorial-write-json (path alist)
  (ensure-directories-exist path)
  (with-open-file (out path :direction :output
                       :if-exists :supersede :if-does-not-exist :create)
    (format out "{~%")
    (loop for (key . value) on alist by #'cddr
          for v = (first value)
          for rest = (rest value)
          do (format out "  \"~a\": ~a~:[~;,~]~%"
                     key (spreadsheet-factorial-json-value v)
                     rest))
    (format out "}~%")))

(defun spreadsheet-factorial-current-seed ()
  (if (and (boundp '*batch-current-run-seed*)
           (symbol-value '*batch-current-run-seed*))
      (symbol-value '*batch-current-run-seed*)
    :null))

(defun spreadsheet-factorial-write-run-manifest (&optional run-index)
  ;; Pre-run manifest: requested factor levels plus the ACTUAL values of every
  ;; switch after configuration, and both random seeds.
  (when (and (boundp '*model-log-dir*) *spreadsheet-factorial-levels*)
    (let ((levels *spreadsheet-factorial-levels*)
          (config *spreadsheet-factorial-config*))
      (spreadsheet-factorial-write-json
       (merge-pathnames #P"condition_manifest.json"
                        (symbol-value '*model-log-dir*))
       (list "run_index" (or run-index :null)
             "variant" (princ-to-string *spreadsheet-ablation-variant*)
             "model_source" (if (boundp '*spreadsheet-model-source-file*)
                                (namestring
                                 (symbol-value '*spreadsheet-model-source-file*))
                              :null)
             "seed" (spreadsheet-factorial-current-seed)
             "actr_seed" (spreadsheet-factorial-current-seed)
             "visual_search" (getf levels :visual-search)
             "formula_lookback" (getf levels :formula-lookback)
             "error_correction" (getf levels :error-correction)
             "visual_error_checking_enabled"
             (and (boundp '*visual-error-checking-enabled*)
                  *visual-error-checking-enabled* t)
             "visual_error_checking_default"
             (and (boundp '*visual-error-checking-default*)
                  *visual-error-checking-default* t)
             "formula_visual_check_probability"
             (if (boundp '*formula-visual-check-probability*)
                 *formula-visual-check-probability* :null)
             "formula_typo_rate"
             (if (boundp '*target-keypress-typo-rate*)
                 *target-keypress-typo-rate* :null)
             "word_typo_rate"
             (if (and (boundp '*word-keypress-typo-rate*)
                      (numberp *word-keypress-typo-rate*))
                 *word-keypress-typo-rate* 0.0)
             "forced_typing_error_rate"
             (if (numberp *spreadsheet-ablation-forced-typing-error-rate*)
                 *spreadsheet-ablation-forced-typing-error-rate* :null)
             "word_immediate_check_probability"
             (if (boundp '*actual-word-immediate-check-probability*)
                 *actual-word-immediate-check-probability* :null)
             "guaranteed_final_check_enabled"
             (getf config :guaranteed-final-check))))))

(defun spreadsheet-factorial-write-run-postcheck (&optional run-index)
  ;; Post-run diagnostics: whether the perceptual chain survived the whole run
  ;; and how often the direct escape hatch fired.
  (when (boundp '*model-log-dir*)
    (spreadsheet-factorial-write-json
     (merge-pathnames #P"run_postcheck.json"
                      (symbol-value '*model-log-dir*))
     (list "run_index" (or run-index :null)
           "seed" (spreadsheet-factorial-current-seed)
           "visual_error_checking_enabled_at_end"
           (and (boundp '*visual-error-checking-enabled*)
                *visual-error-checking-enabled* t)
           "typed_echo_failures_at_end"
           (if (boundp '*typed-echo-failures*) *typed-echo-failures* :null)
           "formula_final_direct_count"
           (if (boundp '*formula-final-direct-count*)
               *formula-final-direct-count* :null)))))

(defun apply-spreadsheet-ablation
    (variant &key typing-error-rate word-typing-error-rate)
  ;; Legacy entry point: the paper's named variants, now routed through the
  ;; factorial configuration so every cell uses identical switch logic.
  (ecase variant
    (:perfect
     (apply-spreadsheet-factorial
      :visual-search nil :formula-lookback nil :error-correction nil
      :variant variant))

    (:visual-search-only
     (apply-spreadsheet-factorial
      :visual-search t :formula-lookback nil :error-correction nil
      :variant variant))

    (:formula-lookback-only
     (apply-spreadsheet-factorial
      :visual-search nil :formula-lookback t :error-correction nil
      :variant variant))

    (:typing-errors-only
     ;; Not a factorial cell: motor misexecution without noticing/repair.
     ;; Kept for backward compatibility with the older five-condition study.
     (setf *spreadsheet-ablation-variant* variant)
     (set-spreadsheet-typing-error-rate typing-error-rate)
     (disable-spreadsheet-correction-checking)
     (setf *spreadsheet-factorial-levels* nil
           *spreadsheet-factorial-config* nil))

    (:correction-checking
     (apply-spreadsheet-factorial
      :visual-search nil :formula-lookback nil :error-correction t
      :variant variant
      :typing-error-rate (or typing-error-rate
                             *spreadsheet-factorial-c1-formula-typing-error-rate*)
      :word-typing-error-rate
      (or word-typing-error-rate
          *spreadsheet-factorial-c1-word-typing-error-rate*)))

    (:full-realistic
     (apply-spreadsheet-factorial
      :visual-search t :formula-lookback t :error-correction t
      :variant variant
      :typing-error-rate (or typing-error-rate
                             *spreadsheet-factorial-c1-formula-typing-error-rate*)
      :word-typing-error-rate
      (or word-typing-error-rate
          *spreadsheet-factorial-c1-word-typing-error-rate*))))
  *spreadsheet-ablation-variant*)
