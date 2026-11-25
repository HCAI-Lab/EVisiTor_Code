;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; A cognitive Excel model that makes sense!
; Author: Amir Bagherzadeh
;(clear-all)
#|
HFES Paper:
- Author: ambkh
- Date: 2024-07-24
|#
;;;Task descriptions:
;;; This one includes both typing and visual search at the same time.
;;; This one includes VLM features
;;; Final Model
;;; 2026-07-21 perceptual correction variant (file: 3-5-2-TCP-7-21-2026):
;;;   * attend the editable area ONCE, before the first keypress of an entry;
;;;   * every delivered keystroke changes that same attended display feature,
;;;     so the vision module re-encodes it automatically (case [3] of
;;;     UPDATE-ATTENDED-LOC in actr7.x/core-modules/vision.lisp) and the
;;;     fresh percept arrives in the =visual buffer with the normal
;;;     :visual-attention-latency (85 ms), in parallel with the ongoing
;;;     motor activity; and
;;;   * the production that decides the check harvests =visual> TEXT-VALUE
;;;     and compares the accumulated entry against the intended prefix on its
;;;     own LHS --
;;;     one production per check, no find-location/move-attention chain.
;;; Checking productions therefore never issue a +visual> request of their
;;; own: a request cannot be issued and harvested inside one production
;;; (requests are asynchronous), but none is needed because the re-encoded
;;; percept is already in the buffer when the check fires.  The vision
;;; module is busy from the instant of the display change until
;;; ENCODING-COMPLETE, so a check that waits for ?visual free can never
;;; read the pre-keystroke text.
;;; Typos are injected by the keyboard interface at key delivery
;;; (INJECT-TYPO-IF-NEEDED in fucntion_new_tcp.lisp): the model always
;;; issues the INTENDED key and can only find out what really happened by
;;; looking, like a person.  No production ever inspects the sampled key.
;;;
(reset)
(delete-model)
(require-extra "emma")
(defvar *clicking-occurred* nil)

;; Predeclare generated subtask globals so top-level SETQ forms compile cleanly.
(eval-when (:compile-toplevel :load-toplevel :execute)
    (loop for task from 1 to 14 do
                (loop for sub from 1 to 30 do
                            (let ((sym (read-from-string (format nil "SUBTASK~D_~D_LIST" task sub))))
                                (proclaim `(special ,sym))))))

(setq subtask1_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask1_2_list '((Goto "Open") (Select "Open") (end)))
(setq subtask1_3_list '((Goto "normalization.xlsx") (Select "normalization.xlsx") (endsub)))
;;; Task 2: Save As
(setq subtask2_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask2_2_list '((Goto "Save a Copy") (Select "Save a Copy") (end)))
(setq subtask2_3_list '((Goto "file_name") (Select "file_name") (end)));type: edit, value = normalization
(setq subtask2_4_list '((Type "subject") (Press "enter") (endsub)))


; (setq subtask2_1_list '((Type "subject") (Press "enter") (endsub)))


;;; Task 3: Calculate Frequency (B7 to B11)
(setq subtask3_1_list '((Goto "B7") (Select "B7") (end)))
(setq subtask3_2_list '((Type "=(C7*B13)/100") (Press "enter") (end)))
(setq subtask3_3_list '((Goto "B8") (Select "B8") (end)))
(setq subtask3_4_list '((Type "=(C8*B13)/100") (Press "enter") (end)))
(setq subtask3_5_list '((Goto "B9") (Select "B9") (end)))
(setq subtask3_6_list '((Type "=(C9*B13)/100") (Press "enter") (end)))
(setq subtask3_7_list '((Goto "B10") (Select "B10") (end)))
(setq subtask3_8_list '((Type "=(C10*B13)/100") (Press "enter") (end)))
(setq subtask3_9_list '((Goto "B11") (Select "B11") (end)))
(setq subtask3_10_list '((Type "=(C11*B13)/100") (Press "enter") (endsub)))

;;; Task 4: Calculate Total Frequency (B14)
(setq subtask4_1_list '((Goto "B14") (Select "B14") (end)))
(setq subtask4_2_list '((Type "=sum(B2:B11)") (Press "enter") (endsub)))

;;; Task 5: Calculate Normalization (C2 to C6)
(setq subtask5_1_list '((Goto "C2") (Select "C2") (end)))
(setq subtask5_2_list '((Type "=(B2*100)/B13") (Press "enter") (end)))
(setq subtask5_3_list '((Goto "C3") (Select "C3") (end)))
(setq subtask5_4_list '((Type "=(B3*100)/B13") (Press "enter") (end)))
(setq subtask5_5_list '((Goto "C4") (Select "C4") (end)))
(setq subtask5_6_list '((Type "=(B4*100)/B13") (Press "enter") (end)))
(setq subtask5_7_list '((Goto "C5") (Select "C5") (end)))
(setq subtask5_8_list '((Type "=(B5*100)/B13") (Press "enter") (end)))
(setq subtask5_9_list '((Goto "C6") (Select "C6") (end)))
(setq subtask5_10_list '((Type "=(B6*100)/B13") (Press "enter") (endsub)))

;;; Task 6: Calculate Total Normalization (C14)
(setq subtask6_1_list '((Goto "C14") (Select "C14") (end)))
(setq subtask6_2_list '((Type "=sum(C2:C11)") (Press enter) (endsub)))

;;; Task 7: Calculate Length (D2 to D11)
(setq subtask7_1_list '((Goto "D2") (Select "D2") (end)))
(setq subtask7_2_list '((Type "=len(A2)") (Press enter) (end)))
(setq subtask7_3_list '((Goto "D3") (Select "D3") (end)))
(setq subtask7_4_list '((Type "=len(A3)") (Press enter) (end)))
(setq subtask7_5_list '((Goto "D4") (Select "D4") (end)))
(setq subtask7_6_list '((Type "=len(A4)") (Press enter) (end)))
(setq subtask7_7_list '((Goto "D5") (Select "D5") (end)))
(setq subtask7_8_list '((Type "=len(A5)") (Press enter) (end)))
(setq subtask7_9_list '((Goto "D6") (Select "D6") (end)))
(setq subtask7_10_list '((Type "=len(A6)") (Press enter) (end)))
(setq subtask7_11_list '((Goto "D7") (Select "D7") (end)))
(setq subtask7_12_list '((Type "=len(A7)") (Press enter) (end)))
(setq subtask7_13_list '((Goto "D8") (Select "D8") (end)))
(setq subtask7_14_list '((Type "=len(A8)") (Press enter) (end)))
(setq subtask7_15_list '((Goto "D9") (Select "D9") (end)))
(setq subtask7_16_list '((Type "=len(A9)") (Press enter) (end)))
(setq subtask7_17_list '((Goto "D10") (Select "D10") (end)))
(setq subtask7_18_list '((Type "=len(A10)") (Press enter) (end)))
(setq subtask7_19_list '((Goto "D11") (Select "D11") (end)))
(setq subtask7_20_list '((Type "=len(A11)") (Press enter) (endsub)))

;;; Task 8: Calculate Total Length (D14)
(setq subtask8_1_list '((Goto "D14") (Select "D14") (end)))
(setq subtask8_2_list '((Type "=sum(D2:D11)") (Press enter) (endsub)))

;;; Task 9: Calculate Typed Characters (E2 to E11)
(setq subtask9_1_list '((Goto "E2") (Select "E2") (end)))
(setq subtask9_2_list '((Type "=D2*B2") (Press enter) (end)))
(setq subtask9_3_list '((Goto "E3") (Select "E3") (end)))
(setq subtask9_4_list '((Type "=D3*B3") (Press enter) (end)))
(setq subtask9_5_list '((Goto "E4") (Select "E4") (end)))
(setq subtask9_6_list '((Type "=D4*B4") (Press enter) (end)))
(setq subtask9_7_list '((Goto "E5") (Select "E5") (end)))
(setq subtask9_8_list '((Type "=D5*B5") (Press enter) (end)))
(setq subtask9_9_list '((Goto "E6") (Select "E6") (end)))
(setq subtask9_10_list '((Type "=D6*B6") (Press enter) (end)))
(setq subtask9_11_list '((Goto "E7") (Select "E7") (end)))
(setq subtask9_12_list '((Type "=D7*B7") (Press enter) (end)))
(setq subtask9_13_list '((Goto "E8") (Select "E8") (end)))
(setq subtask9_14_list '((Type "=D8*B8") (Press enter) (end)))
(setq subtask9_15_list '((Goto "E9") (Select "E9") (end)))
(setq subtask9_16_list '((Type "=D9*B9") (Press enter) (end)))
(setq subtask9_17_list '((Goto "E10") (Select "E10") (end)))
(setq subtask9_18_list '((Type "=D10*B10") (Press enter) (end)))
(setq subtask9_19_list '((Goto "E11") (Select "E11") (end)))
(setq subtask9_20_list '((Type "=D11*B11") (Press enter) (endsub)))

;;; Task 10: Calculate Total Typed Characters (E14)
(setq subtask10_1_list '((Move "E14") (Select "E14")(end)))
(setq subtask10_2_list '((Type "=sum(E2:E11)") (Press enter)(endsub)))

;;; Task 11: Insert two rows (B15)
(setq subtask11_1_list '((Goto "Row_1") (Select "Row_1")(end))) ;has to change to 1
(setq subtask11_2_list '((Goto "Home") (Select "Home")(end)))
(setq subtask11_3_list '((Goto "Insert Cells") (Select "Insert Cells")(end)))
(setq subtask11_4_list '((Goto "Row_1") (Select "Row_1")(end))) ;has to change to 1
(setq subtask11_5_list '((Goto "Home") (Select "Home")(end)))
(setq subtask11_6_list '((Goto "Insert Cells") (Select "Insert Cells")(endsub)))

;;; Task 12: Type in name (A1)
(setq subtask12_1_list '((Goto "A1") (Select "A1")(end)))
(setq subtask12_2_list '((Type "subject") (Press enter)(endsub)))
;;; Task 13: Calculate Average Length (D15)
(setq subtask13_1_list '((Goto "A2") (Select "A2")(end)))
(setq subtask13_2_list '((Type "=today()") (Press enter)(endsub)))
;;; Task 14: Calculate Average Typed Characters (E15)
(setq subtask14_1_list '((Goto "File Tab") (Select "File Tab")(end)))
(setq subtask14_2_list '((Goto "Save a Copy") (Select "Save a Copy")(end)))
(setq subtask14_3_list '((Goto "file_name") (Select "file_name") (end)))
(setq subtask14_4_list '((Type "normalization-subject") (Press enter) (endsub)))


; Map ACT-R keyboard output notifications to the existing keypress handler.
; output-key is called with (model key) after a valid keyboard mapping
; actually produces a key, which is the right point to forward the key
; to the external task environment.
(defun respond-to-key-press-monitor (&rest args)
    (let ((key (car (last args))))
        (respond-to-key-press (if (listp key) key (list key)))))

;; Actual-word typing usually checks immediately, but sometimes defers and
;; only notices the mistake after continuing to type.
(defparameter *actual-word-immediate-check-probability* 0.85)

(defun choose-actual-word-check-mode ()
    (if (< (random 1.0) *actual-word-immediate-check-probability*)
            "check-now"
        "check-later"))

;; Probability of selecting a nearby visual target during non-cell search.
(defparameter *local-neighbor-search-probability* 0.9)


(defun choose-visual-search-mode ()
    (if (< (random 1.0) *local-neighbor-search-probability*)
            "local"
        "global"))

(defun right-hand-on-mouse-p ()
    (equalp (notify-interface "motor" (list 'get-hand-device 'right))
            (list "motor" "cursor" "mouse")))

(defparameter *formula-token-cache* (make-hash-table :test 'equal))

(defun formula-char-class (ch)
    (cond
      ((alpha-char-p ch) :alpha)
      ((digit-char-p ch) :digit)
      (t :other)))

(defun formula-tokenize (formula)
    (let ((s (string-downcase (string formula)))
          (i 0)
          (n (length (string formula)))
          (tokens nil))
      (labels ((emit-range (start end)
                 (when (< start end)
                   (push (subseq s start end) tokens))))
        (loop while (< i n) do
              (let* ((ch (char s i))
                     (class (formula-char-class ch)))
                (cond
                  ((or (char= ch #\Space) (char= ch #\Tab) (char= ch #\Newline) (char= ch #\Return))
                   (incf i))
                  ((eq class :alpha)
                   (let ((start i))
                     (loop while (and (< i n)
                                      (or (alpha-char-p (char s i))
                                          (digit-char-p (char s i))))
                           do (incf i))
                     (emit-range start i)))
                  ((eq class :digit)
                   (let ((start i))
                     (loop while (and (< i n) (digit-char-p (char s i))) do (incf i))
                     (emit-range start i)))
                  (t
                   (push (string ch) tokens)
                   (incf i))))))
      (nreverse tokens)))

(defun cached-formula-tokens (formula)
    (let* ((key (string-downcase (string formula)))
           (cached (gethash key *formula-token-cache*)))
      (if cached
          cached
          (setf (gethash key *formula-token-cache*) (formula-tokenize key)))))

(defun formula-token-at (formula index)
    (let ((tokens (cached-formula-tokens formula)))
      (if (and (>= index 0) (< index (length tokens)))
          (nth index tokens)
          nil)))

(defun formula-token-at-safe (formula index)
    (or (formula-token-at formula index) "__end_of_formula__"))

(defun token-char-at (token index)
    (let* ((s (string token))
           (n (length s)))
      (if (and (>= index 0) (< index n))
          (string (char s index))
          nil)))

(defparameter *shifted-formula-base-key-map*
    '(("!" . "1") ("@" . "2") ("#" . "3") ("$" . "4") ("%" . "5")
      ("^" . "6") ("&" . "7") ("*" . "8") ("(" . "9") (")" . "0")
      ("_" . "-") ("+" . "=") ("{" . "[") ("}" . "]") ("|" . "\\")
      (":" . ";") ("\"" . "'") ("<" . ",") (">" . ".") ("?" . "/")
      ("~" . "`")))

(defparameter *no-shift-base-key* "__no_shift__")

(defun shifted-formula-base-key (ch)
    (let* ((k (string ch))
           (pair (assoc k *shifted-formula-base-key-map* :test #'string-equal)))
        (if pair (cdr pair) *no-shift-base-key*)))

(defun next-formula-token-index (index)
    (+ index 1))

;; Pure representation helpers used on production RHSs.  They update or
;; inspect values already present in ACT-R buffers; none consults the keyboard
;; monitor's correctness bookkeeping.
(defun entry-string (value)
    (if value (normalize-key-string value) ""))

(defun extend-intended-entry (prefix character)
    (concatenate 'string (entry-string prefix) (entry-string character)))

(defun entry-mismatch-index (seen intended)
    (let* ((screen (entry-string seen))
           (target (entry-string intended))
           (position (mismatch screen target :test #'char-equal)))
        (or position (min (length screen) (length target)))))

(defun entry-repair-delete-count (seen mismatch-index)
    (max 0 (- (length (entry-string seen)) mismatch-index)))

(defun entry-string-length (entry)
    (length (entry-string entry)))

(defun entry-character-at (entry index)
    (let ((text (entry-string entry)))
        (and (integerp index)
             (<= 0 index)
             (< index (length text))
             (string (char text index)))))

(defun entry-character-shifted-p (entry index)
    (let ((character (entry-character-at entry index)))
        (and character
             (not (string-equal (shifted-formula-base-key character)
                                *no-shift-base-key*)))))

(defun entry-character-base-key (entry index)
    (shifted-formula-base-key (entry-character-at entry index)))

(defun repair-state-for-plan (delete-count index limit)
    (cond ((> delete-count 0) "delete")
          ((< index limit) "type")
          (t "drain")))

(defun repair-state-after-delete (remaining index limit)
    (if (> remaining 0)
        "delete"
      (if (< index limit) "type" "drain")))

(defun repair-state-after-type (next-index limit)
    (if (< next-index limit) "type" "drain"))

(defun formula-more-tokens-p (formula token-index)
    (not (null (formula-token-at formula (next-formula-token-index token-index)))))

(defun choose-formula-token-check-mode ()
    (if (and (visual-error-checking-p)
             (< (random 1.0) (formula-current-check-probability)))
        "check-now"
      "check-later"))

;; Saved UIA snapshots sometimes omit the selected cell immediately after a
;; click even though a real spreadsheet still exposes an editable field there.
;; This is task-environment rendering, not a model verdict: if no visicon
;; feature exists near the remembered selection, render a minimal editable
;; feature so ACT-R can overtly attend and subsequently perceive its changes.
(defun typing-area-feature-near-p (x y &optional (radius 8))
    (let ((vision (ignore-errors (get-module :vision))))
        (and vision
             (some (lambda (feature)
                       (let* ((location (ignore-errors (chunk-visual-loc feature)))
                              (fx (and location
                                       (ignore-errors
                                         (chunk-slot-value-fct location 'screen-x))))
                              (fy (and location
                                       (ignore-errors
                                         (chunk-slot-value-fct location 'screen-y)))))
                            (and (numberp fx) (numberp fy)
                                 (< fx 960)
                                 (< (abs (- fx x)) radius)
                                 (< (abs (- fy y)) radius))))
                   (ignore-errors (visicon vision))))))

(defun ensure-editable-typing-feature (x y label)
    (when (and (numberp x) (numberp y)
               (not (typing-area-feature-near-p x y)))
        (add-visicon-features
          `(screen-x ,x screen-y ,y height 18 width 70
            type "text" text T cell T value ,label text-value ,label)))
    t)

;; This focused variant keeps the source model's formula strategy.  The live
;; July model can replace this with a learned-formula strategy, but that
;; learning state is intentionally not kept outside ACT-R here.
(defun formula-typing-strategy (retrieved-type formula)
    (declare (ignore formula))
    retrieved-type)



(defun neighbor-item-label (item)
    ;; Return a likely neighboring label for memory-anchored search.
    ;; For column labels this returns the previous Excel-style label.
    ;; For numeric row labels this returns the previous number as a string.
    (let ((raw (string item)))
        (labels ((letters-only-p (s)
                     (and (> (length s) 0)
                          (every (lambda (ch) (and (alpha-char-p ch) (char<= #\A (char-upcase ch) #\Z))) s)))
                 (digits-only-p (s)
                     (and (> (length s) 0)
                          (every #'digit-char-p s)))
                 (excel-col->number (s)
                     (loop with n = 0
                           for ch across (string-upcase s)
                           do (setf n (+ (* n 26) (- (char-code ch) (char-code #\A) -1)))
                           finally (return n)))
                 (number->excel-col (n)
                     (let ((value n)
                           (out nil))
                         (loop while (> value 0) do
                               (decf value)
                               (push (code-char (+ (char-code #\A) (mod value 26))) out)
                               (setf value (floor value 26)))
                         (coerce out 'string))))
            (cond
              ((letters-only-p raw)
               (let* ((n (excel-col->number raw))
                      (neighbor (if (> n 1) (1- n) 2)))
                   (number->excel-col neighbor)))
              ((digits-only-p raw)
               (let* ((n (parse-integer raw))
                      (neighbor (if (> n 1) (1- n) 2)))
                   (write-to-string neighbor)))
               (t nil)))))

;; Keypresses change the display feature which was attended before typing.
;; That is sensory/task-environment state, not a hidden correctness flag.
;; Configure every switch explicitly so variants can be loaded safely in any
;; order within one Lisp session.
(configure-perceptual-typing-environment
 :reuse-attended-feature t
 :accumulated-entry-percept t
 :typed-echo-offset 0
 :visual-checking-default t
 :visual-checking-enabled t)


;Define the model...

(define-model GoodExcel3-TCP


  (buffer-chunk)
;(define-chunks
;
;;; Converted versions of the lists
;
;)
;;;;Monitoring commands
(defvar *my-agi-window* (open-exp-window "My AGI Window" :visible t))
(add-act-r-command "my-move-cursor" 'respond-to-move-cursor-monitor "sth")
(monitor-act-r-command "move-cursor" "my-move-cursor")
(add-act-r-command "my-click-mouse" 'respond-to-click-mouse "temp" "temp" "sth")
(monitor-act-r-command "click-mouse" "my-click-mouse")
(add-act-r-command "my-press-key" 'respond-to-key-press-monitor "sth")
(add-act-r-command "my-move-attention" 'respond-to-move-attention-monitor "sth")
(monitor-act-r-command "output-key" "my-press-key")
(monitor-act-r-command "move-attention" "my-move-attention")
(install-device '("motor" "cursor" "mouse" ))
(install-device '("motor" "keyboard"))

; Initial motor state: both hands begin at keyboard home, then the right hand
; is placed on the mouse.  These are pre-run initial conditions; every later
; mouse/keyboard transition is requested through the manual buffer.
(start-hands-at-home)
(start-hand-at-mouse)
;;;;Define the chunk-types
    (chunk-type Task Number)
    (chunk-type  Subtask actions items)
    (chunk-type action  action item)
    (chunk-type actionencode action meaning)
    (chunk-type WORD TYPE (SPELLING SYMBOL))
    (chunk-type intention   job task subtask subsubtask sx sy item meaning type column row word check correct phase typed-so-far pending-check seen-entry repair-target repair-index repair-limit repair-remaining repair-state repair-context resume-phase source-marker right-hand-location left-hand-location)
    (chunk-type remembered-location item sx sy)
    (chunk-type typing  word type correct check phase token-index char-index current-token target-cell formula-source source-marker next-char token-done task subtask subsubtask job item meaning sx sy typed-so-far pending-check seen-entry repair-target repair-index repair-limit repair-remaining repair-state repair-context resume-phase right-hand-location left-hand-location)
    (chunk-type item    word    current after   position next previous)
    (chunk-type memory  task subtask subsubtask action item meaning)
    (chunk-type target-spec label lookup-text lookup-cell-type target-type)

;Define the chunks



(add-visicon-features '(screen-x 1159 screen-y 290 value "task1" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 390 height 30 width 70 color blue value "task2" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 490 height 30 width 70 color blue value "task3" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 610 height 30 width 70 color blue value "task4" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 710 height 30 width 70 color blue value "task5" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 830 height 30 width 70 color blue value "task6" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 930 height 30 width 70 color blue value "task7" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1050 height 30 width 70 color blue value "task8" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1150 height 30 width 70 color blue value "task9" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1270 height 30 width 70 color blue value "task10" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1370 height 30 width 70 color blue value "task11" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1470 height 30 width 70 color blue value "task12" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1570 height 30 width 70 color blue value "task13" type "text" text T))
(add-visicon-features '(screen-x 1159 screen-y 1670 height 30 width 70 color blue value "task14" type "text" text T))
(add-visicon-features '(screen-x 100 screen-y 245 height 30 width 70 color red value "WORKBOOKS" text-value "WORKBOOKS" type "text" text T))
(add-visicon-features '(screen-x 200 screen-y 340 height 30 width 70 color red value "NORMALIZATION_FILE" text-value "NORMALIZATION_FILE" type "text" text T))
(add-visicon-features '(screen-x 350 screen-y 245 height 30 width 70 color red value "file_name" text-value "file_name" type "text" text T))
(add-visicon-features '(screen-x 86 screen-y 64 height 30 width 70 color red value "Home" text-value "Home" type "text" text T))
(add-visicon-features '(screen-x 100 screen-y 520 height 30 width 70 color red value "FileName" text-value "normalization" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 290 value "subtask1_1_list" text-value "subtask1_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 310 value "subtask1_2_list" text-value "subtask1_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 330 value "subtask1_3_list" text-value "subtask1_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 390 value "subtask2_1_list" text-value "subtask2_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 410 value "subtask2_2_list" text-value "subtask2_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 430 value "subtask2_3_list" text-value "subtask2_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 450 value "subtask2_4_list" text-value "subtask2_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 490 value "subtask3_1_list" text-value "subtask3_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 510 value "subtask3_2_list" text-value "subtask3_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 530 value "subtask3_3_list" text-value "subtask3_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_4_list" text-value "subtask3_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_5_list" text-value "subtask3_5_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_6_list" text-value "subtask3_6_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_7_list" text-value "subtask3_7_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_8_list" text-value "subtask3_8_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_9_list" text-value "subtask3_9_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 550 value "subtask3_10_list" text-value "subtask3_10_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 610 value "subtask4_1_list" text-value "subtask4_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 630 value "subtask4_2_list" text-value "subtask4_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 710 value "subtask5_1_list" text-value "subtask5_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 730 value "subtask5_2_list" text-value "subtask5_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 750 value "subtask5_3_list" text-value "subtask5_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_4_list" text-value "subtask5_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_5_list" text-value "subtask5_5_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_6_list" text-value "subtask5_6_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_7_list" text-value "subtask5_7_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_8_list" text-value "subtask5_8_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_9_list" text-value "subtask5_9_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 770 value "subtask5_10_list" text-value "subtask5_10_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 830 value "subtask6_1_list" text-value "subtask6_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 850 value "subtask6_2_list" text-value "subtask6_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 930 value "subtask7_1_list" text-value "subtask7_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 950 value "subtask7_2_list" text-value "subtask7_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 970 value "subtask7_3_list" text-value "subtask7_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_4_list" text-value "subtask7_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_5_list" text-value "subtask7_5_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_6_list" text-value "subtask7_6_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_7_list" text-value "subtask7_7_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_8_list" text-value "subtask7_8_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_9_list" text-value "subtask7_9_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_10_list" text-value "subtask7_10_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_11_list" text-value "subtask7_11_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_12_list" text-value "subtask7_12_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_13_list" text-value "subtask7_13_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_14_list" text-value "subtask7_14_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_15_list" text-value "subtask7_15_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_16_list" text-value "subtask7_16_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_17_list" text-value "subtask7_17_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_18_list" text-value "subtask7_18_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_19_list" text-value "subtask7_19_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 990 value "subtask7_20_list" text-value "subtask7_20_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1050 value "subtask8_1_list" text-value "subtask8_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1070 value "subtask8_2_list" text-value "subtask8_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1150 value "subtask9_1_list" text-value "subtask9_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1170 value "subtask9_2_list" text-value "subtask9_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1190 value "subtask9_3_list" text-value "subtask9_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_4_list" text-value "subtask9_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_5_list" text-value "subtask9_5_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_6_list" text-value "subtask9_6_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_7_list" text-value "subtask9_7_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_8_list" text-value "subtask9_8_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_9_list" text-value "subtask9_9_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_10_list" text-value "subtask9_10_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_11_list" text-value "subtask9_11_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_12_list" text-value "subtask9_12_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_13_list" text-value "subtask9_13_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_14_list" text-value "subtask9_14_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_15_list" text-value "subtask9_15_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_16_list" text-value "subtask9_16_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_17_list" text-value "subtask9_17_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_18_list" text-value "subtask9_18_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_19_list" text-value "subtask9_19_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1210 value "subtask9_20_list" text-value "subtask9_20_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1270 value "subtask10_1_list" text-value "subtask10_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1290 value "subtask10_2_list" text-value "subtask10_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1370 value "subtask11_1_list" text-value "subtask11_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1390 value "subtask11_2_list" text-value "subtask11_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1410 value "subtask11_3_list" text-value "subtask11_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_4_list" text-value "subtask11_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_5_list" text-value "subtask11_5_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_6_list" text-value "subtask11_6_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_7_list" text-value "subtask11_7_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_8_list" text-value "subtask11_8_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_9_list" text-value "subtask11_9_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1430 value "subtask11_10_list" text-value "subtask11_10_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1470 value "subtask12_1_list" text-value "subtask12_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1490 value "subtask12_2_list" text-value "subtask12_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1510 value "subtask12_3_list" text-value "subtask12_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1530 value "subtask12_4_list" text-value "subtask12_4_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1570 value "subtask13_1_list" text-value "subtask13_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1590 value "subtask13_2_list" text-value "subtask13_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1670 value "subtask14_1_list" text-value "subtask14_1_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1690 value "subtask14_2_list" text-value "subtask14_2_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1710 value "subtask14_3_list" text-value "subtask14_3_list" type "text" text T))
(add-visicon-features '(screen-x 1683 screen-y 1730 value "subtask14_4_list" text-value "subtask14_4_list" type "text" text T))
(sgp :v t :needs-mouse t :show-focus t :trace-detail high :emma t)
 (sgp
    		:TT                          3                ;default: 2.0        : Threshold time
		:PCT                         NIL                ;default: NIL        : Production Compilation Trace
              ;default: NIL        : Enable Production Learning
		;--------------------------------
		;DECLARATIVE module
		;--------------------------------
		:SPREADING-HOOK              NIL              ;default: NIL        : Spreading component hook
		:MAS                         1.6              ;default: NIL        : Maximum Associative Strength
		:ACTIVATION-OFFSETS          NIL              ;default: NIL        : Add additional activation equation components

            ;--------------------------------
            ;Parameters related to memory retrieval
            ;--------------------------------

		:BLL                         0.1              ;default: NIL        : Base Level Learning
		:RT                          0                ;default: 0.0        : Retrieval Threshold
        :LF                          0.05             ;default: 1.0        : Latency Factor
		:LE                          1.0              ;default: 1.0        : Latency Exponent
		:BLC                         5.0              ;default: 0.0        : Base Level Constant
		:ANS                         0.005            ;default: NIL        : Activation Noise S



		:CHUNK-MERGE-HOOK            NIL              ;default: NIL        : Hook called when a chunk is merged into dm
		:MD                          -1.0             ;default: -1.0       : Maximum Difference
		:PAS                         NIL              ;default: NIL        : Permanent Activation noise S
		:RETRIEVAL-REQUEST-HOOK      NIL              ;default: NIL        : Retrieval notification hook
		:BL-HOOK                     NIL              ;default: NIL        : Baselevel component hook
		:MS                          0.0              ;default: 0.0        : Maximum Similarity
		:PARTIAL-MATCHING-HOOK       NIL              ;default: NIL        : Partial matching component hook
		:SIM-HOOK                    NIL              ;default: NIL        : Similarity hook
		:RETRIEVAL-SET-HOOK          NIL              ;default: NIL        : Prospective retrievals hook
		:MP                          NIL              ;default: NIL        : Mismatch Penalty
		:RETRIEVED-CHUNK-HOOK        NIL              ;default: NIL        : Retrieval completion hook
		:DECLARATIVE-NUM-FINSTS      4                ;default: 4          : Number of declarative finst markers
		:DECLARATIVE-FINST-SPAN      3.0              ;default: 3.0        : Duration of declarative finst markers in seconds
		:ACT                         NIL              ;default: NIL        : Activation Trace
		:CHUNK-ADD-HOOK              NIL              ;default: NIL        : Hook called when a chunk is added to dm
		:SJI-HOOK                    NIL              ;default: NIL        : Sji hook
		:NOISE-HOOK                  NIL              ;default: NIL        : Noise component hook
		:W-HOOK                      NIL              ;default: NIL        : Wkj hook
		:OL                          T                ;default: T          : Optimized Learning
		:ESC                         T                ;default: NIL        : Enable Subsymbolic Computations
		:ER                          NIL              ;default: NIL        : Enable Randomness
		:EGS                         0.1              ;default: 0.0        : Expected Gain S
		:UT                          NIL              ;default: NIL        : Utility Threshold
		:UTILITY-OFFSETS             NIL              ;default: NIL        : Add additional utility equation components
		:NU                          20               ;default: 0          : default U(0) value for a newly learned production
		:UL                          T                ;default: NIL        : Utility learning switch
		:ALPHA                       0.2              ;default: 0.2        : Production learning rate
		:IU                          10               ;default: 0          : default U(0) value for an initial (user defined) production
		:UTILITY-HOOK                NIL              ;default: NIL        : Utility computation hook
        :VISUAL-NUM-FINSTS           1000
        :VISUAL-FINST-SPAN           1000

    )

(add-dm
;First word and then spelling:
(word1 ISA WORD TYPE "actual-word" SPELLING "subject")
(letter1-1 ISA item word "subject" current "s" after t position first next second previous nil)

(letter1-2 ISA item word "subject" current "u" after t position second next third previous first)

(letter1-3 ISA item word "subject" current "b" after t position third next fourth previous second)

(letter1-4 ISA item word "subject" current "j" after t position fourth next fifth previous third)

(letter1-5 ISA item word "subject" current "e" after t position fifth next sixth previous fourth)

(letter1-6 ISA item word "subject" current "c" after t position sixth next seventh previous fifth)

(letter1-7 ISA item word "subject" current "t" after nil position seventh next nil previous sixth)

(word2 ISA WORD TYPE "actual-word" SPELLING "normalization-subject")
;;;;TODO: Add after==> Done!
(letter2-1 ISA item word "normalization-subject" current "n" after t position first next second previous nil)

(letter2-2 ISA item word "normalization-subject" current "o" after t position second next third previous first)

(letter2-3 ISA item word "normalization-subject" current "r" after t position third next fourth previous second)

(letter2-4 ISA item word "normalization-subject" current "m" after t position fourth next fifth previous third)

(letter2-5 ISA item word "normalization-subject" current "a" after t position fifth next sixth previous fourth)

(letter2-6 ISA item word "normalization-subject" current "l" after t position sixth next seventh previous fifth)

(letter2-7 ISA item word "normalization-subject" current "i" after t position seventh next eighth previous sixth)

(letter2-8 ISA item word "normalization-subject" current "z" after t position eighth next ninth previous seventh)

(letter2-9 ISA item word "normalization-subject" current "a" after t position ninth next tenth previous eighth)

(letter2-10 ISA item word "normalization-subject" current "t" after t position tenth next eleventh previous ninth)

(letter2-11 ISA item word "normalization-subject" current "i" after t position eleventh next twelfth previous tenth)

(letter2-12 ISA item word "normalization-subject" current "o" after t position twelfth next thirteenth previous eleventh)

(letter2-13 ISA item word "normalization-subject" current "n" after t position thirteenth next fourteenth previous twelfth)

(letter2-14 ISA item word "normalization-subject" current "-" after t position fourteenth next fifteenth previous thirteenth)

(letter2-15 ISA item word "normalization-subject" current "s" after t position fifteenth next sixteenth previous fourteenth)

(letter2-16 ISA item word "normalization-subject" current "u" after t position sixteenth next seventeenth previous fifteenth)

(letter2-17 ISA item word "normalization-subject" current "b" after t position seventeenth next eighteenth previous sixteenth)

(letter2-18 ISA item word "normalization-subject" current "j" after t position eighteenth next nineteenth previous seventeenth)

(letter2-19 ISA item word "normalization-subject" current "e" after t position nineteenth next twentieth previous eighteenth)

(letter2-20 ISA item word "normalization-subject" current "c" after t position twentieth next twenty-first previous nineteenth)

(letter2-21 ISA item word "normalization-subject" current "t" after nil position twenty-first next nil previous twentieth)


(word3 ISA WORD TYPE "actual-word" SPELLING "=today()")

(letter3-1 ISA item word "=today()" current "=" after t position first next second previous nil)

(letter3-2 ISA item word "=today()" current "t" after t position second next third previous first)

(letter3-3 ISA item word "=today()" current "o" after t position third next fourth previous second)

(letter3-4 ISA item word "=today()" current "d" after t position fourth next fifth previous third)

(letter3-5 ISA item word "=today()" current "a" after t position fifth next sixth previous fourth)

(letter3-6 ISA item word "=today()" current "y" after t position sixth next seventh previous fifth)

(letter3-7 ISA item word "=today()" current "(" after t position seventh next eighth previous sixth)

(letter3-8 ISA item word "=today()" current ")" after nil position eighth next nil previous seventh)

;Now interpetations

(Goto ISA actionencode action Goto meaning "attention-N-movecursor")
(moveto ISA actionencode action move meaning "attention-N-movecursor")
(type ISA actionencode action type meaning "type")
(select ISA actionencode action select meaning  "click")
(press ISA actionencode action press meaning  "enter")

; Declarative target classification for all visual movement targets.
; target-type preserves the existing downstream convention:
; T for spreadsheet cells/headers, "nil" for ordinary visual objects.
(file-tab-target ISA target-spec label "File Tab" lookup-text "File Tab" lookup-cell-type "object" target-type "nil")
(open-target ISA target-spec label "Open" lookup-text "Open" lookup-cell-type "object" target-type "nil")
(normalization-file-target ISA target-spec label "normalization.xlsx" lookup-text "normalization.xlsx" lookup-cell-type "object" target-type "nil")
(save-copy-target ISA target-spec label "Save a Copy" lookup-text "Save a Copy" lookup-cell-type "object" target-type "nil")
(file-name-target ISA target-spec label "file_name" lookup-text "file_name" lookup-cell-type "object" target-type "nil")
(home-target ISA target-spec label "Home" lookup-text "Home" lookup-cell-type "object" target-type "nil")
(insert-cells-target ISA target-spec label "Insert Cells" lookup-text "Insert Cells" lookup-cell-type "object" target-type "nil")

(row-1-target ISA target-spec label "Row_1" lookup-text "1" lookup-cell-type "row" target-type T)

(a1-target ISA target-spec label "A1" lookup-text "A1" lookup-cell-type "cell" target-type T)
(a2-target ISA target-spec label "A2" lookup-text "A2" lookup-cell-type "cell" target-type T)
(b7-target ISA target-spec label "B7" lookup-text "B7" lookup-cell-type "cell" target-type T)
(b8-target ISA target-spec label "B8" lookup-text "B8" lookup-cell-type "cell" target-type T)
(b9-target ISA target-spec label "B9" lookup-text "B9" lookup-cell-type "cell" target-type T)
(b10-target ISA target-spec label "B10" lookup-text "B10" lookup-cell-type "cell" target-type T)
(b11-target ISA target-spec label "B11" lookup-text "B11" lookup-cell-type "cell" target-type T)
(b14-target ISA target-spec label "B14" lookup-text "B14" lookup-cell-type "cell" target-type T)
(c2-target ISA target-spec label "C2" lookup-text "C2" lookup-cell-type "cell" target-type T)
(c3-target ISA target-spec label "C3" lookup-text "C3" lookup-cell-type "cell" target-type T)
(c4-target ISA target-spec label "C4" lookup-text "C4" lookup-cell-type "cell" target-type T)
(c5-target ISA target-spec label "C5" lookup-text "C5" lookup-cell-type "cell" target-type T)
(c6-target ISA target-spec label "C6" lookup-text "C6" lookup-cell-type "cell" target-type T)
(c14-target ISA target-spec label "C14" lookup-text "C14" lookup-cell-type "cell" target-type T)
(d2-target ISA target-spec label "D2" lookup-text "D2" lookup-cell-type "cell" target-type T)
(d3-target ISA target-spec label "D3" lookup-text "D3" lookup-cell-type "cell" target-type T)
(d4-target ISA target-spec label "D4" lookup-text "D4" lookup-cell-type "cell" target-type T)
(d5-target ISA target-spec label "D5" lookup-text "D5" lookup-cell-type "cell" target-type T)
(d6-target ISA target-spec label "D6" lookup-text "D6" lookup-cell-type "cell" target-type T)
(d7-target ISA target-spec label "D7" lookup-text "D7" lookup-cell-type "cell" target-type T)
(d8-target ISA target-spec label "D8" lookup-text "D8" lookup-cell-type "cell" target-type T)
(d9-target ISA target-spec label "D9" lookup-text "D9" lookup-cell-type "cell" target-type T)
(d10-target ISA target-spec label "D10" lookup-text "D10" lookup-cell-type "cell" target-type T)
(d11-target ISA target-spec label "D11" lookup-text "D11" lookup-cell-type "cell" target-type T)
(d14-target ISA target-spec label "D14" lookup-text "D14" lookup-cell-type "cell" target-type T)
(e2-target ISA target-spec label "E2" lookup-text "E2" lookup-cell-type "cell" target-type T)
(e3-target ISA target-spec label "E3" lookup-text "E3" lookup-cell-type "cell" target-type T)
(e4-target ISA target-spec label "E4" lookup-text "E4" lookup-cell-type "cell" target-type T)
(e5-target ISA target-spec label "E5" lookup-text "E5" lookup-cell-type "cell" target-type T)
(e6-target ISA target-spec label "E6" lookup-text "E6" lookup-cell-type "cell" target-type T)
(e7-target ISA target-spec label "E7" lookup-text "E7" lookup-cell-type "cell" target-type T)
(e8-target ISA target-spec label "E8" lookup-text "E8" lookup-cell-type "cell" target-type T)
(e9-target ISA target-spec label "E9" lookup-text "E9" lookup-cell-type "cell" target-type T)
(e10-target ISA target-spec label "E10" lookup-text "E10" lookup-cell-type "cell" target-type T)
(e11-target ISA target-spec label "E11" lookup-text "E11" lookup-cell-type "cell" target-type T)
(e14-target ISA target-spec label "E14" lookup-text "E14" lookup-cell-type "cell" target-type T)
;Formulas

(formula1 ISA WORD TYPE formula SPELLING "=(C7*B13)/100")
(formula2 ISA WORD TYPE formula SPELLING "=(C8*B13)/100")
(formula3 ISA WORD TYPE formula SPELLING "=(C9*B13)/100")
(formula4 ISA WORD TYPE formula SPELLING "=(C10*B13)/100")
(formula5 ISA WORD TYPE formula SPELLING "=(C11*B13)/100")
(formula6 ISA WORD TYPE formula SPELLING "=sum(B2:B11)")
(formula7 ISA WORD TYPE formula SPELLING "=(B2*100)/B13")
(formula8 ISA WORD TYPE formula SPELLING "=(B3*100)/B13")
(formula9 ISA WORD TYPE formula SPELLING "=(B4*100)/B13")
(formula10 ISA WORD TYPE formula SPELLING "=(B5*100)/B13")
(formula11 ISA WORD TYPE formula SPELLING "=(B6*100)/B13")
(formula12 ISA WORD TYPE formula SPELLING "=(B7*100)/B13")
(formula13 ISA WORD TYPE formula SPELLING "=(B8*100)/B13")
(formula14 ISA WORD TYPE formula SPELLING "=(B9*100)/B13")
(formula15 ISA WORD TYPE formula SPELLING "=(B10*100)/B13")
(formula16 ISA WORD TYPE formula SPELLING "=(B11*100)/B13")
(formula17 ISA WORD TYPE formula SPELLING "=sum(C2:C11)")
(formula18 ISA WORD TYPE formula SPELLING "=len(A2)")
(formula19 ISA WORD TYPE formula SPELLING "=len(A3)")
(formula20 ISA WORD TYPE formula SPELLING "=len(A4)")
(formula21 ISA WORD TYPE formula SPELLING "=len(A5)")
(formula22 ISA WORD TYPE formula SPELLING "=len(A6)")
(formula23 ISA WORD TYPE formula SPELLING "=len(A7)")
(formula24 ISA WORD TYPE formula SPELLING "=len(A8)")
(formula25 ISA WORD TYPE formula SPELLING "=len(A9)")
(formula26 ISA WORD TYPE formula SPELLING "=len(A10)")
(formula27 ISA WORD TYPE formula SPELLING "=len(A11)")
(formula28 ISA WORD TYPE formula SPELLING "=sum(D2:D11)")
(formula29 ISA WORD TYPE formula SPELLING "=D2*B2")
(formula30 ISA WORD TYPE formula SPELLING "=D3*B3")
(formula31 ISA WORD TYPE formula SPELLING "=D4*B4")
(formula32 ISA WORD TYPE formula SPELLING "=D5*B5")
(formula33 ISA WORD TYPE formula SPELLING "=D6*B6")
(formula34 ISA WORD TYPE formula SPELLING "=D7*B7")
(formula35 ISA WORD TYPE formula SPELLING "=D8*B8")
(formula36 ISA WORD TYPE formula SPELLING "=D9*B9")
(formula37 ISA WORD TYPE formula SPELLING "=D10*B10")
(formula38 ISA WORD TYPE formula SPELLING "=D11*B11")
(formula39 ISA WORD TYPE formula SPELLING "=sum(E2:E11)")
(formula40 ISA WORD TYPE formula SPELLING "=average(B2:B11)")
(formula41 ISA WORD TYPE formula SPELLING "=average(C2:C11)")
(formula42 ISA WORD TYPE formula SPELLING "=average(D2:D11)")
(formula43 ISA WORD TYPE formula SPELLING "=average(E2:E11)")

;Task chunks

;;; Task 1: Open File
(Task1 ISA Task Number 1)

;;; Task 2: Save As
(Task2 ISA Task Number 2)

;;; Task 3: Calculate Frequency (B7 to B11)
(Task3 ISA Task Number 3)

;;; Task 4: Calculate Total Frequency (B14)
(Task4 ISA Task Number 4)

;;; Task 5: Calculate Normalization (C2 to C6)
(Task5 ISA Task Number 5)

;;; Task 6: Calculate Total Normalization (C14)
(Task6 ISA Task Number 6)

;;; Task 7: Calculate Length (D2 to D11)
(Task7 ISA Task Number 7)

;;; Task 8: Calculate Total Length (D14)
(Task8 ISA Task Number 8)

;;; Task 9: Calculate Typed Characters (E2 to E11)
(Task9 ISA Task Number 9)

;;; Task 10: Calculate Total Typed Characters (E14)
(Task10 ISA Task Number 10)

;;; Task 11: Insert Two Rows
(Task11 ISA Task Number 11)

;;; Task 12: Type in Name (A1)
(Task12 ISA Task Number 12)

;;; Task 13: Insert Current Date (A2)
(Task13 ISA Task Number 13)

;;; Task 14: Save As
(Task14 ISA Task Number 14)
(first-goal ISA intention job "retrieve-task" task 1
            right-hand-location "mouse"
            left-hand-location "keyboard")
    )
(goal-focus first-goal)
(sgp-fct (list :cmdt (no-output (car (sgp :v)))))
;We first start by checking the goal and if it is to retrieving a task, we will put the the main task to visual-location
; and we put the task number in the imaginal and as we are just starting to
;do a new task, the subtask and subsubtask should be 1
(P 1-start-task
    =goal>
        isa     intention
        job     "retrieve-task"
        task    =x

    ?visual-location>
        state   free
    ==>
    !bind! =y (concatenate-strings =x)
    !eval! (prepare-task-and-subtask-logging =x)
    !output!    ("start task")
    =goal>
        isa     intention
        job     "move-vision-task"
        subtask 1
        subsubtask  1
    +visual-location>
        isa visual-location
        Text    T
        value   =y
    !output! (=y)

)
(P 2-move-vision-to-task
    =goal>
        isa     intention
        job     "move-vision-task"
    =visual-location>
        value   =y
        screen-x =sx
        screen-y =sy
    ?visual>
        state   free
    ==>
    !output! ("[DBG] move-vision-to-task fired")
    !output! (=y)
    !eval!  (what-is-on-screen '(=y))
    !output! ("[DBG] move-vision-to-task returned from what-is-on-screen")
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "move-vision-to-task")
    =goal>
        isa     intention
        job     "retrieve-subtask"
    +visual>
          isa         move-attention
          screen-pos  =visual-location
)
;Now that we know what task we are looking for, we move attention to the task location. It is now time to start retrieving subtasks
(P 3-move-attention-to-task
    =goal>
        isa     intention
        job     "retrieve-subtask"
        task    =x
        subtask =y
    ?visual-location>
        state   free
;    ?visual>
;        state   free
    ==>
    !bind! =z (concatenate-strings-subtask =x =y)
    !output! =z
    =goal>
        isa     intention
        job   "move-attention-subtask"
    +visual-location>
        isa     visual-location
        Text    T
        value   =z
)

;Again same for subtasks and now we are ready to retrieve actions (subsubtask)
(P 4-move-attention-to-subtask
    =goal>
        isa     intention
        job     "move-attention-subtask"
    =visual-location>
        text-value   =j
        screen-x =sx
        screen-y =sy
    ?visual>
        state   free
    ==>
    !eval! (what-is-on-screen '(=j))
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "move-attention-to-subtask")
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
    +visual>
        isa     move-attention
        screen-pos  =visual-location
)
;Now we put actions and item in the imaginal buffer. Action function will take three argument: Task, subtask and the action (subsubtask). It will output the action and also the item
(P 5-retrieve-meaning-subtask
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        task    =x
        subtask =y
        subsubtask  =z
    ?retrieval>
        state free
    ==>
    !bind!  =step (nth (1- =z) (symbol-value (read-from-string (concatenate-strings-subtask =x =y))))
    !bind!  =k  (car =step)
    !bind!  =j  (or (cadr =step) "none")
    !output! =k
    =goal>
        isa     intention
        job     "comprehend-action"
    -imaginal>
    +imaginal>
        isa memory
        action      =k
        item        =j
    +retrieval>
        isa         actionencode
        action      =k
    -   meaning     nil
    )
;Now the model should understand what we mean by the action. Meaning the agent is comprehending what is the meaning of what he just read
(P 6-comprehend-action
    =goal>
        isa     intention
        job     "comprehend-action"
    =imaginal>
        action      =k
      - action      end
      - action      endsub
        item        =j
        meaning nil
    =retrieval>
        isa         actionencode
        action      =k
        meaning     =w
==>
    !output!    ("comprehend action")
    -imaginal>
    =goal>
        isa     intention
        job     "do-action"
        item        =j
        meaning     =w
        type    "pending"
)
;Now we will do the task.
;We start by the action of moving attention and cursor
(P  7-1-item-categorization
    =goal>
        isa     intention
        job     "do-action"
        meaning  "attention-N-movecursor"
        item    =x
        type    "pending"
    ?visual-location>
        state   free

==>
    !output! =x
    =goal>
        job     "resolve-item-category"
        column  nil
        row     nil
    +retrieval>
        isa     target-spec
        label   =x

)
; Enter is only pressed after the pre-Enter read found the entry clean.
(P  7-2-pressing-enter
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
        check   "clean"
        subsubtask =z
        right-hand-location "keyboard"
    ?manual>
        state   free
    ==>
    !eval! (clear-pending-shift-keypress)
    +manual>
        cmd     press-key
        key     "return"
    !bind! =w (+ 1 =z)
        =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =w
        item        nil
        check       nil
        phase       nil
        typed-so-far nil
        pending-check nil
        seen-entry  nil
        repair-target nil
        repair-index nil
        repair-limit nil
        repair-remaining nil
        repair-state nil
        repair-context nil
        resume-phase nil
    )

; ---- Guaranteed pre-Enter check (2026-07-21) --------------------------------
; Attention is still parked at the editable field, so the accumulated entry
; is already encoded.  These mutually-exclusive productions compare the
; percept against the intention carried in the goal by normal ACT-R slot
; matching.  The keyboard monitor's tracking lists are not consulted.
(p pre-enter-read-entry-clean
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
      - check   "clean"
      - check   "dirty"
        repair-state nil
        typed-so-far =expected
    =visual>
        text-value =expected
    ?visual>
        state   free
    ?manual>
        state   free
    !eval! (visual-error-checking-p)
    ==>
    =goal>
        check   "clean"
    =visual>
)

(p pre-enter-read-entry-dirty
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
      - check   "clean"
      - check   "dirty"
        repair-state nil
        typed-so-far =expected
    =visual>
        text-value =seen
      - text-value =expected
    ?visual>
        state   free
    ?manual>
        state   free
    !eval! (visual-error-checking-p)
    ==>
    !bind! =mismatch (entry-mismatch-index =seen =expected)
    !bind! =deletes (entry-repair-delete-count =seen =mismatch)
    !bind! =limit (entry-string-length =expected)
    !bind! =repair-state (repair-state-for-plan =deletes =mismatch =limit)
    !eval! (clear-pending-shift-keypress)
    =goal>
        check   "dirty"
        seen-entry =seen
        repair-target =expected
        repair-index =mismatch
        repair-limit =limit
        repair-remaining =deletes
        repair-state =repair-state
        repair-context "pre-enter"
        resume-phase nil
    =visual>
)

; Fallback pair: the entry percept is not in the buffer (e.g. it was
; harvested and no keystroke followed).  Attention has not moved, so glance
; at the stored typing location to refresh the percept, then the read above
; fires on the fresh encoding.
(p pre-enter-refresh-entry
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
      - check   "clean"
      - check   "dirty"
      - check   "refreshing"
        repair-state nil
        sx      =sx
        sy      =sy
    ?visual>
        state   free
        buffer  empty
    ?visual-location>
        state   free
    !eval! (visual-error-checking-p)
    ==>
    =goal>
        check   "refreshing"
    +visual-location>
        isa     visual-location
        screen-x =sx
        screen-y =sy
)

; Factorial C=0 turns off both error generation and perceptual checking.  The
; dated 7-21 model normally requires a final visual read before Enter, but the
; no-check bridge deliberately stops updating the editable-field percept.  An
; explicit bypass is therefore required for a genuine no-check ablation.  It
; is unreachable in the full realistic model because that model keeps visual
; checking enabled.
(p pre-enter-bypass-when-checking-disabled
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
      - check   "clean"
      - check   "dirty"
        repair-state nil
    ?manual>
        state   free
    !eval! (not (visual-error-checking-p))
    ==>
    =goal>
        check   "clean"
)

(p pre-enter-attend-entry
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
        check   "refreshing"
    =visual-location>
        screen-x =sx
        screen-y =sy
    ?visual>
        state   free
    ==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "pre-enter-read-entry")
    +visual>
        isa     move-attention
        screen-pos =visual-location
)

(P 7-3-resolve-direct-cell-target
    =goal>
        isa     intention
        job     "resolve-item-category"
        item    =item
    =retrieval>
        isa              target-spec
        label            =item
        lookup-text      =lookup
        lookup-cell-type "cell"
        target-type      T
    ==>
    =goal>
        job     "do-action"
        item    =lookup
        type    T
)
; Resolve direct row/column/header aliases through declarative target knowledge.
(P 7-4-resolve-aliased-visual-target
    =goal>
        isa     intention
        job     "resolve-item-category"
        item    =item
    =retrieval>
        isa              target-spec
        label            =item
        lookup-text      =row-text
        lookup-cell-type "row"
        target-type      T
    ==>
    =goal>
        job     "do-action"
        type    T
        row     =row-text
        column  nil
        sx      nil
        sy      nil
)

(P 7-6-find-row-header-location-direct
    =goal>
        isa intention
        job "do-action"
        meaning "attention-N-movecursor"
        type T
        item =item
        row =row
        column nil
        sx nil
        sy nil
    ?visual-location>
        state free
    ?visual>
        state free
    ==>
    =goal>
        isa intention
        job "attending-row-header"
    +visual-location>
        isa visual-location
        text-value =row
        cell-type "row"
        < screen-x 960
        :nearest current
)

(P attend-row-header-location-direct
    =goal>
        isa intention
        job "attending-row-header"
        meaning "attention-N-movecursor"
        type T
        item =item
        row =row
        column nil
        subsubtask =x
    =visual-location>
        text-value =row
    ?visual>
        state free
    ==>
    =goal>
        isa intention
        job "moving-attention-N-cursor"
        item =item
        row =row
        column nil
        subsubtask =x
        type T
    !eval! (log-attention-shift-explicit =visual-location "attend-row-header-location-direct")
    +visual>
        isa move-attention
        screen-pos =visual-location
)

(P use-column-target-spec
    =goal>
        isa     intention
        job     "resolve-item-category"
        item    =item
    =retrieval>
        isa              target-spec
        label            =item
        lookup-text      =column-text
        lookup-cell-type "column"
        target-type      T
    ==>
    =goal>
        job     "do-action"
        type    T
        column  =column-text
        row     nil
        sx      nil
        sy      nil
)

(P use-object-target-spec
    =goal>
        isa     intention
        job     "resolve-item-category"
        item    =item
    =retrieval>
        isa              target-spec
        label            =item
        lookup-text      =lookup
        lookup-cell-type "object"
        target-type      "nil"
    ==>
    =goal>
        job     "do-action"
        item    =lookup
        type    "nil"
)
; If target knowledge is genuinely missing, fall back to non-cell visual search.
(P no-target-spec-found
    =goal>
        isa     intention
        job     "resolve-item-category"
    ?retrieval>
        buffer  failure
    ==>
    =goal>
        job     "do-action"
        type    "nil"
)
; Now that we know the item is not a direct row or column header, we need to visually search for it. We first check if we have the location of the item in the memory, if not we will do a top-down visual search, if we have the location in the memory, we will move attention there and if the visual search failed, we will do a bottom-up visual search.
(P  ready-to-attention-to-do-task-not-cell
    =goal>
        isa     intention
        job     "do-action"
        meaning  "attention-N-movecursor"
        item    =x
        type    "nil"
    ?visual-location>
        state   free
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)

==>
    !output! =x
    =goal>
        isa     intention
        job     "checking-object-location-memory"
        type    "nil"
    +retrieval>
        isa     remembered-location
        item    =x
            - sx      nil
            - sy      nil
)

(P use-recalled-object-location
    =goal>
        isa     intention
        job     "checking-object-location-memory"
    =retrieval>
        isa     remembered-location
        sx      =sx
        sy      =sy
    ?visual-location>
        state   free
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
==>
    =goal>
        isa     intention
        job     "waiting-visual-search"
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
    <   screen-x 960
)
;Now we know that the item is not in a memry (we don't know its location), we need to do a visual search for it. We will randomly choose between a local and global visual search. Local visual search means that we will first check the area around the current attended location, if we could not find it there, we will do a global visual search which means that we will check the entire screen.
(P no-recalled-object-location
    =goal>
        isa     intention
        job     "checking-object-location-memory"
    ?retrieval>
        buffer  failure
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
==>
    !bind! =search-mode (choose-visual-search-mode)
    =goal>
        isa     intention
        job     "request-visual-search"
        type    =search-mode
)
; We have decided to do a local visual search, we will find the nearest unattended location around the current attended location. This location cannot be a cell (row or column header) as we already know that the item is not a direct row or column header. If we find the item there, it means that we are lucky and we found it without doing a global visual search, if we could not find it there, we will do a global visual search.
(P request-local-neighbor-visual-search
    =goal>
        isa     intention
        job     "request-visual-search"
        type    "local"
    ?visual-location>
        state   free
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
==>
    =goal>
        isa     intention
        job     "waiting-visual-search"
        type    "nil"
    +visual-location>
        isa     visual-location
        type    "text"
    -   text-value nil
    -   cell t
    -   cell-type "column"
    -   cell-type "row"
    <   screen-x 960
        :attended nil
        :nearest current
)
; We have decided to do a global visual search, this time, we will remove the condition of :nearest current and as a result, it will randomly select an item on the screen that is not a cell and that is not attended. 
(P request-global-away-visual-search
    =goal>
        isa     intention
        job     "request-visual-search"
        type    "global"
    ?visual-location>
        state   free
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
==>
    =goal>
        isa     intention
        job     "waiting-visual-search"
        type    "nil"
    +visual-location>
        isa     visual-location
        type    "text"
    -   text-value nil
    -   cell t
    -   cell-type "column"
    -   cell-type "row"
    <   screen-x 960
        :attended nil
)
; We have done the visual search and have found an item. Next, we need to check if this item is the one we are looking for, by moving the attention there, if it is not, we will do another visual search until we find the item or we exhaust all possible locations on the screen.
(P visual-search-request-succeeded
    =goal>
        isa     intention
        job     "waiting-visual-search"
        item    =item
    =visual-location>
        screen-x =sx
        screen-y =sy
    ?visual-location>
        buffer  requested
==>

    
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "visual-search-request-succeeded")
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        type    "nil"
    +visual>
        isa     move-attention
        screen-pos  =visual-location
)

(P visual-search-request-fallback-local
    =goal>
        isa     intention
        job     "waiting-visual-search"
    ?visual-location>
        state   error
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
==>
    +visual-location>
        isa     visual-location
        :attended nil
    -   text-value nil
    -   cell t
    -   cell-type "column"
    -   cell-type "row"
    <   screen-x 960
)
(P  ready-to-attention-to-do-task-cell
    =goal>
        isa     intention
        job     "do-action"
        meaning  "attention-N-movecursor"
        item    =x
        type    T
        column nil
        row   nil
    ?visual-location>
        state   free
==>
    =goal>
        isa     intention
        job     "checking-highlighted-cell"
    +visual-location>
        isa     visual-location
        highlighted T
        cell    T
        <       screen-x 960
)

(P attend-highlighted-cell
    =goal>
        isa     intention
        job     "checking-highlighted-cell"
        meaning "attention-N-movecursor"
        type    T
    =visual-location>
        highlighted T
    ?visual>
        state   free
==>
    !eval! (log-attention-shift-explicit =visual-location "attend-highlighted-cell")
    +visual>
        isa     move-attention
        screen-pos =visual-location
    =goal>
        isa     intention
        job     "verify-highlighted-cell"
)

(P highlighted-cell-is-target
    =goal>
        isa     intention
        job     "verify-highlighted-cell"
        item    =j
        subsubtask =x
        type    T
    =visual>
        text-value =j
    ?imaginal>
        state free
==>
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item    =j
        subsubtask =x
        type    T
)

(P highlighted-cell-is-not-target
    =goal>
        isa     intention
        job     "verify-highlighted-cell"
        item    =x
        type    T
    =visual>
      - text-value =x
==>
    !bind! =col (first (breakdown-cell =x))
    !bind! =r (second (breakdown-cell =x))
    -visual>
    -visual-location>
    =goal>
        isa     intention
        job     "do-action"
        column =col
        row    =r
    sx     nil
    sy     nil
)

(P no-highlighted-cell-found
    =goal>
        isa     intention
        job     "checking-highlighted-cell"
        item    =x
        type    T
    ?visual-location>
        state   error
==>
    !bind! =col (first (breakdown-cell =x))
    !bind! =r (second (breakdown-cell =x))
    -visual-location>
    =goal>
        isa     intention
        job     "do-action"
        column =col
        row    =r
        sx     nil
        sy     nil
)
(P find-column-location
      =goal>
          isa intention
          job "do-action"
          meaning "attention-N-movecursor"
          type T
          column =col
     ?visual-location>
        buffer      empty
     ?imaginal>
          state free
          buffer empty
    ?visual>
        state free
      ==>
       =goal>
        job "checking-column-location-memory"
       +retrieval>
        isa remembered-location
        item =col
    - sx   nil
    - sy   nil
)

(P use-recalled-column-location
    =goal>
        isa intention
        job "checking-column-location-memory"
        column =col
    =retrieval>
        isa remembered-location
        item =col
        sx =sx
        sy =sy
    ?visual-location>
        state free
    ==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =col
        cell-type   "column"
        < screen-x 960
   ;     :attended nil
        :nearest current
)

(P no-recalled-column-location-try-neighbor
    =goal>
        isa intention
        job "checking-column-location-memory"
        column =col
    ?retrieval>
        buffer failure
    ==>
    !bind! =near (neighbor-item-label =col)
    =goal>
        isa intention
        job "checking-column-neighbor-memory"
    +retrieval>
        isa remembered-location
        item =near
            - sx   nil
            - sy   nil
)

(P use-neighbor-column-location
    =goal>
        isa intention
        job "checking-column-neighbor-memory"
        column =col
    =retrieval>
        isa remembered-location
        sx =sx
        sy =sy
    ?visual-location>
        state free
    ==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =col
        cell-type   "column"
        < screen-x 960
        :attended nil
        :nearest current
)

(P no-neighbor-column-location-fallback
    =goal>
        isa intention
        job "checking-column-neighbor-memory"
        column =col
    ?retrieval>
        buffer failure
    ==>
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =col
        cell-type   "column"
        < screen-x 960
)

(P attending-column-location
    =goal>
        isa intention
        job "do-action"
        meaning "attention-N-movecursor"
        type T
        column =col
    =visual-location>
        text-value =col
        SCREEN-X   =x
        SCREEN-Y   =y
    ?visual>
        state       free
    ==>
    =goal>
        job "waiting-column-encoding"
        sx =x
        sy nil
    !eval! (log-attention-shift-explicit =visual-location "attending-column-location")
    +visual>
        isa move-attention
        screen-pos =visual-location
    -visual-location>
    )

(P encode-attended-column-location
    =goal>
        isa intention
        job "waiting-column-encoding"
        meaning "attention-N-movecursor"
        type T
        column =col
    =visual>
        text-value =col
        screen-pos =loc
    ?imaginal>
        state free
    ==>
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    -imaginal>
    =goal>
        job "do-action"
    +imaginal>
        isa remembered-location
        item =col
        sx =sx
        sy =sy
    -visual>
)

    (P find-row-location
        =goal>
            isa intention
            job "do-action"
            meaning "attention-N-movecursor"
            type T
            row =row
            sx =x
            sy nil
        ?visual-location>
            buffer      empty
            state   free
        ?visual>
            state free
            buffer empty
        ==>
        =goal>
            isa intention
            job "checking-row-location-memory"
        +retrieval>
            isa remembered-location
            item =row
                    - sx   nil
                    - sy   nil
)

(P use-recalled-row-location
    =goal>
        isa intention
        job "checking-row-location-memory"
        row =row
    =retrieval>
        isa remembered-location
        item =row
        sx =sx
        sy =sy
    ?visual-location>
        state free
    ==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =row
        cell-type   "row"
        < screen-x 960
 ;       :attended nil
        :nearest current
)

(P no-recalled-row-location-try-neighbor
    =goal>
        isa intention
        job "checking-row-location-memory"
        row =row
    ?retrieval>
        buffer failure
    ==>
    !bind! =near (neighbor-item-label =row)
    =goal>
        isa intention
        job "checking-row-neighbor-memory"
    +retrieval>
        isa remembered-location
        item =near
            - sx   nil
            - sy   nil
)

(P use-neighbor-row-location
    =goal>
        isa intention
        job "checking-row-neighbor-memory"
        row =row
    =retrieval>
        isa remembered-location
        sx =sx
        sy =sy
    ?visual-location>
        state free
    ==>
    !eval! (respond-to-eye-move-xy =sx =sy)
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =row
        cell-type   "row"
        < screen-x 960
        :attended nil
        :nearest current
)

(P no-neighbor-row-location-fallback
    =goal>
        isa intention
        job "checking-row-neighbor-memory"
        row =row
    ?retrieval>
        buffer failure
    ==>
    =goal>
        isa intention
        job "do-action"
    +visual-location>
        isa visual-location
        text-value =row
        cell-type   "row"
        < screen-x 960
    )
    (P attending-row-location
        =goal>
            isa intention
            job "do-action"
            meaning "attention-N-movecursor"
            type T
            row =row
            sx =x
        =visual-location>
            text-value =row
            SCREEN-X   =rx
            SCREEN-Y   =y
        ?visual>
            state       free
        ==>
        =goal>
            sx =x
            sy =y
        !eval! (log-attention-shift-explicit =visual-location "attending-row-location")
        +visual>
            isa move-attention
            screen-pos =visual-location
    )

(P encode-attended-row-location
    =goal>
        isa intention
        job "do-action"
        meaning "attention-N-movecursor"
        type T
        row =row
    =visual>
        text-value =row
        screen-pos =loc
    ?imaginal>
        state free
    ==>
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    -imaginal>
    +imaginal>
        isa remembered-location
        item =row
        sx =sx
        sy =sy
    -visual>
)

(P find-intersection
            =goal>
                isa intention
                job "do-action"
                meaning "attention-N-movecursor"
                type T
                sx =x
                sy =y
            ?visual>
                state free
                buffer empty
      ?visual-location>
        state   free
      ==>
    +visual-location>
        isa visual-location
        SCREEN-X =x
        SCREEN-Y =y
    =goal>
    JOB "shift-attention-to-cell"
  )

(P shift-to-intersection
    =goal>
        JOB "shift-attention-to-cell"
        ITEM =J
       SUBSUBTASK =X
       TYPE T
    ?visual>
        state   free
    =visual-location>


      ==>
        !eval! (log-attention-shift-explicit =visual-location "shift-to-intersection")
    +visual>
        isa move-attention
        screen-pos =visual-location
   =GOAL>
       JOB "moving-attention-N-cursor"
       ITEM =J
       SUBSUBTASK =X
       TYPE T
  )

(P move-attention-N-cursor-cell
        =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
        subsubtask =x
        type T
        right-hand-location "mouse"
    =visual>  ; Test visual buffer and bind to =visual
    ?manual>
        state free
    ?imaginal>
        state free

    ==>
    !bind!  =y (+ 1 =x)
    !bind! =loc (chunk-slot-value-fct =visual 'screen-pos)
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    -imaginal>
    +imaginal>
        isa remembered-location
        item =j
        sx =sx
        sy =sy
    +manual>
        isa     move-cursor
        loc     =visual
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask =y
        sx      =sx
        sy      =sy
)

; If typing left the right hand on the keyboard, moving it to the mouse is a
; genuine motor action.  Keep the attended target in the visual buffer and
; issue MOVE-CURSOR only after HAND-TO-MOUSE has completed.
(P move-hand-to-mouse-before-cursor-cell
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item    =j
        type    T
        right-hand-location "keyboard"
    =visual>
    ?manual>
        state   free
    ==>
    +manual>
        isa     hand-to-mouse
    =goal>
        job     "move-cursor-after-hand-to-mouse"
    =visual>
)
(P move-attention-to-assure
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
    =visual-location>
        text-value  =e
    ?visual>
        state   free
        buffer  empty

    ==>
    !bind! =xx (move-attention-output-creator =e)
    !output! =xx
    !eval! (log-attention-shift-explicit =visual-location "move-attention-to-assure")
    +visual>
        isa     move-attention
        screen-pos  =visual-location
)
; If we have found the item (item in the goal matches the =visaul> text-value), we will clear the imagainal buffer, we create a memory chunk that stores the loction of the item. At the same time, we move the cursor to that location.
(P move-attention-N-cursor
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
        subsubtask =x
        type "nil"
        right-hand-location "mouse"
    =visual>
        text-value  =j
    ?visual>
        state   free
    ?manual>
        state   free
    ?imaginal>
        state   free
    ==>
    !bind!  =y (+ 1 =x)
    !bind! =loc (chunk-slot-value-fct =visual 'screen-pos)
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    !eval! (remove-visual-finsts)
    -imaginal>
    +imaginal>
        isa remembered-location
        item =j
        sx =sx
        sy =sy
    +manual>
        isa     move-cursor
        loc     =visual
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask =y
        sx      =sx
        sy      =sy
)

(P move-hand-to-mouse-before-cursor
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item    =j
        type    "nil"
        right-hand-location "keyboard"
    =visual>
        text-value =j
    ?visual>
        state   free
    ?manual>
        state   free
    ==>
    !eval! (remove-visual-finsts)
    +manual>
        isa     hand-to-mouse
    =goal>
        job     "move-cursor-after-hand-to-mouse"
    =visual>
)

(P move-cursor-after-hand-to-mouse
    =goal>
        isa     intention
        job     "move-cursor-after-hand-to-mouse"
        item    =j
        subsubtask =x
    =visual>
    ?manual>
        state   free
    ?imaginal>
        state   free
    ==>
    !bind! =y (+ 1 =x)
    !bind! =loc (chunk-slot-value-fct =visual 'screen-pos)
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    -imaginal>
    +imaginal>
        isa remembered-location
        item =j
        sx =sx
        sy =sy
    +manual>
        isa move-cursor
        loc =visual
    =goal>
        job "retrieve-actions-of-subtask"
        subsubtask =y
        sx =sx
        sy =sy
        right-hand-location "mouse"
)
; We have checked the location of the item and our target is not there. We will need to perform another visual search. We again randomly choose between local and global visual search. 
(P move-attention-fail
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
        subsubtask =x
        type "nil"
    ?visual>
        buffer full
    =visual>
        screen-pos =loc
      -  text-value  =j

    ?manual>
        state   free
    ==>
    !bind! =search-mode (choose-visual-search-mode)
    !bind! =sx (chunk-slot-value-fct =loc 'screen-x)
    !bind! =sy (chunk-slot-value-fct =loc 'screen-y)
    !eval! (respond-to-eye-move-xy =sx =sy)
    -visual>
    =goal>
        job     "request-visual-search"
        type    =search-mode
)
;Now if the action is click, we click. We then move to the next subsubtask.
(P  clicking
    =goal>
        isa     intention
        job     "do-action"
        meaning  "click"
        subsubtask  =x
        right-hand-location "mouse"
    ?manual>
        state       free
==>
    !bind! =y (+ 1 =x)

    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =y
   +manual>
      isa        click-mouse
)
;The hardest action is typing. We will start by setting the goal and trying to retrieve the type of the word we need to type. 
(P  move-right-hand-to-keyboard-before-typing
    =goal>
        isa     intention
        job     "do-action"
        meaning  "type"
        type   "pending"
        item        =y
        right-hand-location "mouse"
    ?manual>
        state   free
    !eval! (right-hand-on-mouse-p)
==>
    +manual>
        isa     hand-to-home
        hand    right
    =goal>
        isa     intention
        job     "finish-moving-right-hand-to-keyboard"
        word    =y
)

; The symbolic hand marker can lag the motor module in idealized V=0 paths.
; If the motor query says the hand is already at home, do not issue a
; redundant HAND-TO-HOME request (ACT-R clears that request without scheduling
; another conflict-resolution event, which otherwise leaves the model idle).
(P ready-to-type-when-motor-hand-already-home
    =goal>
        isa     intention
        job     "do-action"
        meaning "type"
        type    "pending"
        item    =y
        right-hand-location "mouse"
    ?manual>
        state   free
    !eval! (not (right-hand-on-mouse-p))
    ==>
    =goal>
        job     "typing"
        word    =y
        right-hand-location "keyboard"
    +retrieval>
        isa     word
        SPELLING =y
)

(P finish-moving-right-hand-to-keyboard
    =goal>
        isa     intention
        job     "finish-moving-right-hand-to-keyboard"
        word    =y
    ?manual>
        state   free
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
    ==>
    =goal>
        job     "typing"
        right-hand-location "keyboard"
    +retrieval>
        isa     word
        SPELLING    =y
)

; A no-search ablation can leave the symbolic hand marker at "mouse" after
; the motor module has already returned the hand to home.  ACT-R reports a
; repeated HAND-TO-HOME request as a manual-buffer error.  Treat that error as
; confirmation that the hand is already at the keyboard and continue through
; the same word-retrieval path; the full realistic path normally uses the
; successful production above.
(P finish-moving-right-hand-to-keyboard-already-home
    =goal>
        isa     intention
        job     "finish-moving-right-hand-to-keyboard"
        word    =y
    ?manual>
        state   error
    ==>
    -manual>
    =goal>
        job     "typing"
        right-hand-location "keyboard"
    +retrieval>
        isa     word
        SPELLING =y
)

; This path makes the hand-state representation robust if a task introduces
; consecutive typing actions without an intervening mouse action.
(P ready-to-type-with-hand-on-keyboard
    =goal>
        isa     intention
        job     "do-action"
        meaning "type"
        type    "pending"
        item    =y
        right-hand-location "keyboard"
    ?manual>
        state   free
    ==>
    =goal>
        job     "typing"
        word    =y
    +retrieval>
        isa     word
        SPELLING =y
)
; Now we have retrieved the word and we need the type of the word (is it a formula, or a text). 
(P retrieving-word
    =goal>
        isa     intention
        job     "typing"
        word    =w
        ; type    "nil"
        type   "pending"
      task      =x
      subtask   =y
      subsubtask =z
      sx        =target-sx
      sy        =target-sy
    < sx        960
    =retrieval>
        type    =r
   ?visual-location>
        state    free
    ==>
    !bind!  =j  (cadr (nth (1- =z) (symbol-value (read-from-string (concatenate-strings-subtask =x (- =y 1))))))
    !bind!  =typing-type (formula-typing-strategy =r =w)
    !eval!  (ensure-editable-typing-feature =target-sx =target-sy =j)
    !bind!  =min-x (- =target-sx 8)
    !bind!  =max-x (+ =target-sx 8)
    !bind!  =min-y (- =target-sy 8)
    !bind!  =max-y (+ =target-sy 8)

    =goal>
        isa     typing
        word    =w
        type    =typing-type
        CORRECT t
        check   "done"
        phase   "find-typing-area" ; Attend the editable area before the first keypress.
        token-index nil     ; We will use this slot to keep track of which character in the word we are currently typing
        char-index nil          ; We will use this slot to keep track of which character in the word we are currently checking (it can be the same as token-index or one ahead depending on the check mode)
        current-token nil       ; Formula only: We will use this slot to keep the current token we are trying to type (it can be a character or a group of characters depending on the type of the formula)
        target-cell =j          ; Label of the field/cell where typing will occur.
        sx      =target-sx
        sy      =target-sy
        source-marker nil     ; We will use this slot to keep track of the source of the word we are typing. (e.g., is it from the memory, is it from the screen, etc.) Used for formula only.
        next-char nil       ; We will use this slot to keep track of the next character we are expecting to see on the screen after typing the current character. 
        token-done nil       ; We will use this slot to keep track of whether we have finished typing the current token or not (used for formulas, for text it will always be nil)
        typed-so-far ""
        pending-check nil
        seen-entry nil
        repair-target nil
        repair-index nil
        repair-limit nil
        repair-remaining nil
        repair-state nil
        repair-context nil
        resume-phase nil
    +retrieval>
        isa     item
        word    =w
        position    first
    ; Find the field/cell at the coordinates encoded by the immediately
    ; preceding Goto/Select action.  Matching coordinates is robust when a
    ; nonempty cell displays its contents instead of its address.  Keep the
    ; sheet-area bound so an instruction-panel feature can never be selected.
   +visual-location>
        isa     visual-location
      > screen-x =min-x
      < screen-x =max-x
      > screen-y =min-y
      < screen-y =max-y
      < screen-x 960
)

; Shift attention once, before typing.  Subsequent changes to this same visual
; feature are automatically re-encoded by ACT-R; checking does not shift again.
(p attend-typing-area-before-entry
   =goal>
      ISA       typing
      phase     "find-typing-area"
   =visual-location>
      screen-x  =actual-sx
      screen-y  =actual-sy
   ?visual>
      state     free
   ==>
   !eval! (respond-to-eye-move-xy =actual-sx =actual-sy)
   !eval! (log-attention-shift-explicit =visual-location "attend-typing-area-before-entry")
   +visual>
      isa       move-attention
      screen-pos =visual-location
   =goal>
      phase     "typing-area-attended"
      sx        =actual-sx
      sy        =actual-sy
)

; Recovery: the editable-area feature was not found (e.g. the visicon was
; refreshed between the click and the find).  Re-issue the same request; the
; feature for the just-clicked field is regenerated with the display.
(p typing-area-find-failed
   =goal>
      ISA       typing
      phase     "find-typing-area"
      target-cell =target-cell
      sx        =target-sx
      sy        =target-sy
    < sx        960
   ?visual-location>
      state     error
   ==>
   !eval!  (ensure-editable-typing-feature =target-sx =target-sy =target-cell)
   !bind!  =min-x (- =target-sx 8)
   !bind!  =max-x (+ =target-sx 8)
   !bind!  =min-y (- =target-sy 8)
   !bind!  =max-y (+ =target-sy 8)
   +visual-location>
      isa       visual-location
    > screen-x  =min-x
    < screen-x  =max-x
    > screen-y  =min-y
    < screen-y  =max-y
    < screen-x  960
)

; Word typing keeps its original 0.85 stochastic decision.  A selected check
; compares the complete intended prefix with the accumulated screen entry;
; a skipped check proceeds directly and costs no extra production.
(p start-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     "typing-area-attended"
      typed-so-far =typed
   =retrieval>
      current   =letter
    - next      nil
      next      =next-position
   ?manual>
      processor free
   ?visual>
      state     free
   =visual>
   ==>
   !bind! =check-mode (choose-actual-word-check-mode)
   !bind! =base (shifted-formula-base-key =letter)
   !bind! =shifted (if (string-equal =base *no-shift-base-key*) "no" "yes")
   !bind! =press-key (if (string-equal =shifted "yes") "shift" =letter)
   !bind! =next-phase (if (string-equal =shifted "yes")
                          (if (string-equal =check-mode "check-now")
                              "typing-actual-char-shift-base"
                            "typing-actual-char-shift-base-skip")
                        (if (string-equal =check-mode "check-now")
                            "verify-entry"
                          "word-continue"))
   !bind! =correct (if (string-equal =check-mode "check-now") "pending" t)
   !bind! =new-typed (extend-intended-entry =typed =letter)
   =goal>
      phase     =next-phase
      correct   =correct
      check     =check-mode
      typed-so-far =new-typed
      pending-check =check-mode
      resume-phase "word-continue"
      repair-context "word-continue"
      source-marker =base
      next-char =letter
   +manual>
      ISA       press-key
      key       =press-key
   +retrieval>
      isa       item
      word      =w
      position  =next-position
   -visual>
)

(p type-actual-word-shift-base
   =goal>
      ISA       typing
      type      "actual-word"
      phase     "typing-actual-char-shift-base"
      source-marker =base
   ?manual>
      processor free
   ==>
   +manual>
      ISA       press-key
      key       =base
   =goal>
      phase     "verify-entry"
      pending-check "check-now"
      correct   "pending"
   -visual>
)

(p type-actual-word-shift-base-skip
   =goal>
      ISA       typing
      type      "actual-word"
      phase     "typing-actual-char-shift-base-skip"
      source-marker =base
   ?manual>
      processor free
   ==>
   +manual>
      ISA       press-key
      key       =base
   =goal>
      phase     "word-continue"
      pending-check "check-later"
      correct   t
   -visual>
)

(p continue-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     "word-continue"
    - pending-check "check-now"
      typed-so-far =typed
   =retrieval>
      current   =letter
    - position  first
    - next      nil
      next      =next-position
   ?manual>
      processor free
   ==>
   !bind! =check-mode (choose-actual-word-check-mode)
   !bind! =base (shifted-formula-base-key =letter)
   !bind! =shifted (if (string-equal =base *no-shift-base-key*) "no" "yes")
   !bind! =press-key (if (string-equal =shifted "yes") "shift" =letter)
   !bind! =next-phase (if (string-equal =shifted "yes")
                          (if (string-equal =check-mode "check-now")
                              "typing-actual-char-shift-base"
                            "typing-actual-char-shift-base-skip")
                        (if (string-equal =check-mode "check-now")
                            "verify-entry"
                          "word-continue"))
   !bind! =correct (if (string-equal =check-mode "check-now") "pending" t)
   !bind! =new-typed (extend-intended-entry =typed =letter)
   =goal>
      phase     =next-phase
      correct   =correct
      check     =check-mode
      typed-so-far =new-typed
      pending-check =check-mode
      resume-phase "word-continue"
      repair-context "word-continue"
      source-marker =base
      next-char =letter
   +manual>
      ISA       press-key
      key       =press-key
   +retrieval>
      isa       item
      word      =w
      position  =next-position
   -visual>
)

; The last word character is always checked before the typing goal exits.
(p finish-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     "word-continue"
    - pending-check "check-now"
      typed-so-far =typed
   =retrieval>
      current   =letter
      next      nil
   ?manual>
      processor free
   !eval! (visual-error-checking-p)
   ==>
   !bind! =base (shifted-formula-base-key =letter)
   !bind! =shifted (if (string-equal =base *no-shift-base-key*) "no" "yes")
   !bind! =press-key (if (string-equal =shifted "yes") "shift" =letter)
   !bind! =next-phase (if (string-equal =shifted "yes") "final-char-shift-base" "verify-entry")
   !bind! =new-typed (extend-intended-entry =typed =letter)
   =goal>
      phase     =next-phase
      correct   "pending"
      check     "check-now"
      typed-so-far =new-typed
      pending-check "check-now"
      resume-phase "entry-finished"
      repair-context "word-final"
      source-marker =base
      next-char =letter
   +manual>
      ISA       press-key
      key       =press-key
   -visual>
)

; C=0 counterpart of FINISH-TYPING.  With perceptual checking disabled the
; final character is issued normally, but the model does not wait for a
; display update or compare the entry.  Enter still waits for the motor module
; to settle, so advancing the goal here cannot overtake the delivered key.
(p finish-typing-without-checking
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     "word-continue"
    - pending-check "check-now"
      typed-so-far =typed
   =retrieval>
      current   =letter
      next      nil
   ?manual>
      processor free
   !eval! (not (visual-error-checking-p))
   ==>
   !bind! =base (shifted-formula-base-key =letter)
   !bind! =shifted (if (string-equal =base *no-shift-base-key*) "no" "yes")
   !bind! =press-key (if (string-equal =shifted "yes") "shift" =letter)
   !bind! =next-phase (if (string-equal =shifted "yes")
                         "final-char-shift-base-without-checking"
                       "entry-finished")
   !bind! =new-typed (extend-intended-entry =typed =letter)
   =goal>
      phase     =next-phase
      correct   t
      check     "done"
      typed-so-far =new-typed
      pending-check nil
      resume-phase nil
      repair-context nil
      source-marker =base
      next-char =letter
   +manual>
      ISA       press-key
      key       =press-key
   -visual>
)

(p type-final-char-shift-base-without-checking
   =goal>
      ISA       typing
      type      "actual-word"
      phase     "final-char-shift-base-without-checking"
      source-marker =base
   ?manual>
      processor free
   !eval! (not (visual-error-checking-p))
   ==>
   +manual>
      ISA       press-key
      key       =base
   =goal>
      phase     "entry-finished"
      pending-check nil
      correct   t
)

(p type-final-char-shift-base
   =goal>
      ISA       typing
      type      "actual-word"
      phase     "final-char-shift-base"
      source-marker =base
   ?manual>
      processor free
   ==>
   +manual>
      ISA       press-key
      key       =base
   =goal>
      phase     "verify-entry"
      pending-check "check-now"
      correct   "pending"
   -visual>
)

; Shared whole-entry check.  ACT-R's native chunk-slot equality compares the
; two strings (case-insensitively); no external correctness verdict is used.
(p verify-entry-ok
   =goal>
      ISA       typing
      phase     "verify-entry"
      pending-check "check-now"
      typed-so-far =expected
      resume-phase =resume
   =visual>
      text-value =expected
   ?visual>
      state      free
   ?manual>
      state      free
   ==>
   =goal>
      phase      =resume
      pending-check nil
      correct    t
      seen-entry nil
      repair-target nil
      repair-index nil
      repair-limit nil
      repair-remaining nil
      repair-state nil
   =visual>
)

(p verify-entry-error
   =goal>
      ISA       typing
      phase     "verify-entry"
      pending-check "check-now"
      typed-so-far =expected
   =visual>
      text-value =seen
    - text-value =expected
   ?visual>
      state      free
   ?manual>
      state      free
   ==>
   !bind! =mismatch (entry-mismatch-index =seen =expected)
   !bind! =deletes (entry-repair-delete-count =seen =mismatch)
   !bind! =limit (entry-string-length =expected)
   !bind! =repair-state (repair-state-for-plan =deletes =mismatch =limit)
   !eval! (clear-pending-shift-keypress)
   =goal>
      phase      "inline-repair"
      pending-check nil
      correct    "false"
      seen-entry =seen
      repair-target =expected
      repair-index =mismatch
      repair-limit =limit
      repair-remaining =deletes
      repair-state =repair-state
   =visual>
)

; A repair is planned once while the motor module is fully settled, then its
; known suffix-delete/retype commands are issued whenever the motor processor
; is free.  Execution remains ACT-R's serial FIFO; only preparation overlaps.
(p repair-burst-delete
   =goal>
      repair-state "delete"
      repair-remaining =remaining
      repair-index =index
      repair-limit =limit
    > repair-remaining 0
   ?manual>
      processor free
   ==>
   !bind! =next-remaining (- =remaining 1)
   !bind! =next-state (repair-state-after-delete =next-remaining =index =limit)
   +manual>
      ISA       press-key
      key       "delete"
   =goal>
      repair-remaining =next-remaining
      repair-state =next-state
)

(p repair-burst-type-unshifted
   =goal>
      repair-state "type"
      repair-target =target
      repair-index =index
      repair-limit =limit
    < repair-index =limit
   !eval! (not (entry-character-shifted-p =target =index))
   ?manual>
      processor free
   ==>
   !bind! =character (entry-character-at =target =index)
   !bind! =next-index (+ =index 1)
   !bind! =next-state (repair-state-after-type =next-index =limit)
   +manual>
      ISA       press-key
      key       =character
   =goal>
      repair-index =next-index
      repair-state =next-state
)

(p repair-burst-type-shift-prefix
   =goal>
      repair-state "type"
      repair-target =target
      repair-index =index
      repair-limit =limit
    < repair-index =limit
   !eval! (entry-character-shifted-p =target =index)
   ?manual>
      processor free
   ==>
   !bind! =base (entry-character-base-key =target =index)
   +manual>
      ISA       press-key
      key       "shift"
   =goal>
      repair-state "type-shift-base"
      source-marker =base
)

(p repair-burst-type-shift-base
   =goal>
      repair-state "type-shift-base"
      repair-index =index
      repair-limit =limit
      source-marker =base
   ?manual>
      processor free
   ==>
   !bind! =next-index (+ =index 1)
   !bind! =next-state (repair-state-after-type =next-index =limit)
   +manual>
      ISA       press-key
      key       =base
   =goal>
      repair-index =next-index
      repair-state =next-state
)

; Do not declare a burst complete until every queued key has executed and the
; last display change has finished encoding.  Then verify the repaired entry
; again, so motor noise during repair cannot escape.
(p repair-burst-drain-typing
   =goal>
      ISA       typing
      phase     "inline-repair"
    - repair-context "pre-enter"
      repair-state "drain"
   ?manual>
      state     free
   ?visual>
      state     free
   ==>
   =goal>
      phase     "verify-entry"
      pending-check "check-now"
      correct   "pending"
      repair-state nil
)

(p repair-burst-drain-pre-enter
   =goal>
      ISA       intention
      job       "do-action"
      meaning   "enter"
      repair-context "pre-enter"
      repair-state "drain"
   ?manual>
      state     free
   ?visual>
      state     free
   ==>
   =goal>
      check     nil
      seen-entry nil
      repair-target nil
      repair-index nil
      repair-limit nil
      repair-remaining nil
      repair-state nil
      repair-context nil
)

; Rare recovery if strict harvesting left the visual buffer empty when an
; inline repair settled.  Attention has not moved, so refresh the stored cell.
(p inline-check-refresh-entry
   =goal>
      ISA       typing
      phase     "verify-entry"
      pending-check "check-now"
      sx        =sx
      sy        =sy
   ?visual>
      state     free
      buffer    empty
   ?visual-location>
      state     free
   ==>
   =goal>
      phase     "refresh-entry"
   +visual-location>
      ISA       visual-location
      screen-x  =sx
      screen-y  =sy
)

(p inline-check-attend-refreshed-entry
   =goal>
      ISA       typing
      phase     "refresh-entry"
   =visual-location>
      screen-x  =sx
      screen-y  =sy
   ?visual>
      state     free
   ==>
   +visual>
      ISA       move-attention
      screen-pos =visual-location
   =goal>
      phase     "verify-entry"
)

; After identifying the word type as formula, we start typing it. The first step is to identify read the formula from the subtask location 
(p start-typing-formula
        =goal>
            ISA       typing
            word      =w
            type      formula
            task      =x
            subtask   =y
            subsubtask =z
            phase     "typing-area-attended"
            target-cell =target
        =visual>
        ?visual>
            state free
        ==>
        !bind!  =formula-source (concatenate-strings-subtask =x =y)
        !bind!  =tok (formula-token-at =w 0)    ; We start with the first token of the formula. We will keep track of which token we are currently typing with the token-index slot in the goal and we will update it as we finish typing each token.
        =goal>
            ISA       typing
            word      =w
            type      formula
            task      =x
            subtask   =y
            subsubtask =z
            phase     "memorize-token"
            token-index 0
            char-index 0
            current-token =tok
            target-cell =target
            formula-source =formula-source
            source-marker nil
        =visual>
)
; The editable area was already attended before START-TYPING-FORMULA.  Keep
; that percept available while the model prepares the first formula token.
(p memorize-token-and-shift-to-target
        =goal>
            ISA       typing
            type      formula
            phase     "memorize-token"
          - current-token nil
                    - current-token "__end_of_formula__"
            current-token =tok
            target-cell =target
        =visual>
        ?visual>
            state free
        ==>
        !output! ("memorized formula token")
        !output! ("formula target")
        !output! =target
        !output! ("formula token")
        !output! =tok
        =goal>
            phase     "typing-token"
            char-index 0
        =visual>
)
; As long as we have not checked or the typed characters are correct, keep finding the next char to type. 
(p compute-next-char-of-current-token
        =goal>
            ISA       typing
            type      formula
            phase     "typing-token"
            pending-check nil
          - correct   "false"
            current-token =tok
            char-index =i
        ==>
        !bind!  =ch (or (token-char-at =tok =i) "__end_of_token__")
        !bind!  =done (if (string-equal =ch "__end_of_token__") "yes" "no")
        !bind!  =base (shifted-formula-base-key =ch)
        !bind!  =next-phase (if (string-equal =base *no-shift-base-key*)
                                "have-char"
                                "have-shifted-char")
        !output! ("compute char")
        !output! =tok
        !output! =i
        !output! =ch
        =goal>
            phase =next-phase
            next-char =ch
            token-done =done
            source-marker =base
)
; Type the char from the production rule above.
(p type-next-char-of-current-token
        =goal>
            ISA       typing
            type      formula
            phase     "have-char"
            token-done "no"
            next-char =ch
            char-index =i
            typed-so-far =typed
        ?manual>
            processor free
        =visual>
        ?visual>
            state     free
        ==>
        !bind!  =next (+ =i 1)
        !bind!  =new-typed (extend-intended-entry =typed =ch)
        !output! ("type char")
        !output! =ch
        +manual>
            cmd      press-key
            key      =ch
        =goal>
            phase "typing-token"
            correct t
            char-index =next
            typed-so-far =new-typed
            pending-check nil
        -visual>
)
; if the char requires us to hold shift, we fire this production rule and press shift
(p type-shifted-char-prefix
        =goal>
            ISA       typing
            type      formula
            phase     "have-shifted-char"
            token-done "no"
          - source-marker "__no_shift__"
            source-marker =base
        ?manual>
            processor free
        =visual>
        ?visual>
            state     free
        ==>
        +manual>
            cmd      press-key
            key      "shift"
        =goal>
            phase "have-shifted-char-base"
        =visual>
)
; We then press the base key while holding shift to type the shifted char (technically we are not holding the shift key but this is the best emulation of that).
(p type-shifted-char-base
        =goal>
            ISA       typing
            type      formula
            phase     "have-shifted-char-base"
            token-done "no"
            source-marker =base
            next-char =ch
            char-index =i
            typed-so-far =typed
        ?manual>
            processor free
        ==>
        !bind!  =next (+ =i 1)
        !bind!  =new-typed (extend-intended-entry =typed =ch)
        !output! ("type shifted char")
        !output! =base
        +manual>
            cmd      press-key
            key      =base
        =goal>
            phase "typing-token"
            correct t
            char-index =next
            typed-so-far =new-typed
            pending-check nil
        -visual>
)
; Formula checks occur once per completed nonfinal token, after the normal
; source lookback and return to the target.  The final token is covered by the
; guaranteed pre-Enter check.
(p finished-current-token-go-back-to-formula
        =goal>
            ISA       typing
            word      =w
            type      formula
            phase     "have-char"
            token-done "yes"
            token-index =ti
            target-cell =target
            formula-source =source
        !eval! (formula-more-tokens-p =w =ti)
        ?manual>
            state free
        ?visual>
            state free
        ?visual-location>
            state free
        ==>
        !bind!  =nti (next-formula-token-index =ti)
        !bind!  =next-token (formula-token-at-safe =w =nti)
        !bind!  =check-mode (choose-formula-token-check-mode)
        !output! ("next formula token")
        !output! =next-token
        =goal>
            phase "look-back-to-formula"
            token-index =nti
            char-index 0
            current-token =next-token
            next-char nil
            token-done nil
            pending-check =check-mode
            resume-phase "typing-token"
            repair-context "formula-token"
        +visual-location>
            isa visual-location
            Text T
            text-value =source
)

(p finished-final-formula-token
        =goal>
            ISA       typing
            word      =w
            type      formula
            phase     "have-char"
            token-done "yes"
            token-index =ti
        !eval! (not (formula-more-tokens-p =w =ti))
        ?manual>
            state free
        ?visual>
            state free
        ==>
        !bind!  =nti (next-formula-token-index =ti)
        !bind!  =next-token (formula-token-at-safe =w =nti)
        =goal>
            phase "memorize-token"
            token-index =nti
            char-index 0
            current-token =next-token
            next-char nil
            token-done nil
            pending-check nil
)

(p look-back-to-formula-before-next-token
        =goal>
            ISA       typing
            type      formula
            phase     "look-back-to-formula"
            formula-source =source
            target-cell =target
        =visual-location>
            text-value =source
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ==>
        !eval! (what-is-on-screen '(=source))
        !eval! (respond-to-eye-move-xy =sx =sy)
        !eval! (log-attention-shift-explicit =visual-location "look-back-to-formula-before-next-token")
        =goal>
            phase "return-to-formula-target"
        +visual>
            isa       move-attention
            screen-pos =visual-location
)
; Return to the editable-area percept.  Its TEXT-VALUE contains the complete
; delivered entry prefix.
(p return-attention-to-formula-target
        =goal>
            ISA       typing
            type      formula
            phase     "return-to-formula-target"
            target-cell =target
            sx        =sx
            sy        =sy
        ?visual>
            state free
        ?visual-location>
            state free
            buffer empty
        ==>
        +visual-location>
            isa visual-location
            screen-x =sx
            screen-y =sy
)
; Re-attend the target, then either let the shared check compare the fresh
; accumulated percept or resume immediately when this token's draw skipped.
(p resume-formula-typing-after-lookback-check
        =goal>
            ISA       typing
            type      formula
            phase     "return-to-formula-target"
            current-token =tok
            pending-check "check-now"
            target-cell =target
            sx        =sx
            sy        =sy
        =visual-location>
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ==>
        =goal>
            phase "verify-entry"
            pending-check "check-now"
            resume-phase "typing-token"
            repair-context "formula-token"
            correct "pending"
        +visual>
            isa       move-attention
            screen-pos =visual-location
)

(p resume-formula-typing-after-lookback-skip
        =goal>
            ISA       typing
            type      formula
            phase     "return-to-formula-target"
            pending-check "check-later"
            target-cell =target
            sx        =sx
            sy        =sy
        =visual-location>
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ==>
        =goal>
            phase "typing-token"
            pending-check nil
            correct t
        +visual>
            isa       move-attention
            screen-pos =visual-location
)

(p end-of-formula
        =goal>
            ISA       typing
            word      =formula
            type      formula
            phase     "memorize-token"
            current-token "__end_of_formula__"
            subsubtask =z
            typed-so-far =typed
        ==>
        !bind! =w (+ 1 =z)
        =goal>
            isa     intention
            job     "retrieve-actions-of-subtask"
            subsubtask  =w
            type    nil
            word    nil
            meaning nil
            typed-so-far =typed
            pending-check nil
            repair-state nil
            repair-context nil
            ; Clear the typing-path check state so the pre-Enter read (which
            ; keys off the CHECK slot) always starts fresh.
            check   nil
)

;When typing is over, we move on to the next action!
(P on-to-the-next-typing
    =goal>
        isa         typing
        type        "actual-word"
        phase       "entry-finished"
        correct     t
        typed-so-far =typed
        task =x
        subtask =y
        subsubtask  =z
    ==>
    !bind!     =nxt (+ 1 =z)
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =nxt
        type    nil
        word    nil
        check   nil
        correct nil
        phase   nil
        typed-so-far =typed
        pending-check nil
        repair-state nil
        repair-context nil

)

;Now if there is no more action, we go to the next subtask
(P on-to-the-next-subtask
    =goal>
        isa     intention
        job     "comprehend-action"
        task    =t
        subtask =y
    =imaginal>
        action end
    ==>
    !eval! (mark-subtask-complete =t =y)
    !bind! =x (+ 1 =y)
    !eval! (mark-subtask-start =t =x)
    =goal>
        isa     intention
        job     "retrieve-subtask"
        subtask =x
        subsubtask 1
)
(P on-to-the-next-task
    =goal>
        isa     intention
        job     "comprehend-action"
        task =x
        subtask =s
    =imaginal>
        action endsub
    ==>
    !eval! (mark-subtask-complete =x =s)
    !eval! (mark-task-complete =x)
    !bind! =y (+ 1 =x)
    !eval! (when (< =y 15) (mark-task-start =y))
    !eval! (when (< =y 15) (mark-subtask-start =y 1))
    !bind! =next-job (if (< =y 15) "retrieve-task" "done")
    !bind! =next-task (if (< =y 15) =y 15)
    !bind! =next-subtask (if (< =y 15) 1 =s)
    !bind! =next-subsubtask 1
    =goal>
        isa     intention
        job     =next-job
        task        =next-task
        subtask     =next-subtask
        subsubtask  =next-subsubtask
)

(P stop-at-task-15
    =goal>
        isa     intention
        job     "done"
        task    15
    ==>
    !output! ("model complete at task 15")
    !stop!)

(set-similarities
 (first second -0.5)
 (second third -0.5)
 (third fourth -0.5)
 (fourth fifth -0.5)
 (fifth sixth -0.5)
 (sixth seventh -0.5)
 (seventh eighth -0.5)
 (eighth ninth -0.5)
 (ninth tenth -0.5)
 (tenth eleventh -0.5)
 (eleventh twelfth -0.5)
 (twelfth thirteenth -0.5)
 (thirteenth fourteenth -0.5)
 (fourteenth fifteenth -0.5)
 (fifteenth sixteenth -0.5)
 (sixteenth seventeenth -0.5)
 (seventeenth eighteenth -0.5)
 (eighteenth nineteenth -0.5)
 (nineteenth twentieth -0.5)
 (twentieth twenty-first -0.5))


   )
(main)
