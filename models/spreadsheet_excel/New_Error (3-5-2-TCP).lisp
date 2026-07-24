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

;; QWERTY-adjacent substitutions for the word-typing path.  Includes digits
;; and symbols so characters like the "-" in "normalization-subject" or the
;; "()" in "=today()" can be mistyped, mirroring *fallback-typo-map* on the
;; formula path.
(defparameter *model-typo-fallback-map*
    '(("a" . "s") ("b" . "n") ("c" . "v") ("d" . "f") ("e" . "r")
        ("f" . "g") ("g" . "h") ("h" . "j") ("i" . "o") ("j" . "k")
        ("k" . "l") ("l" . ";") ("m" . ",") ("n" . "m") ("o" . "p")
        ("p" . "[") ("q" . "w") ("r" . "t") ("s" . "d") ("t" . "y")
        ("u" . "i") ("v" . "b") ("w" . "e") ("x" . "c") ("y" . "u")
        ("z" . "x")
        ("0" . "9") ("1" . "2") ("2" . "3") ("3" . "4") ("4" . "5")
        ("5" . "6") ("6" . "7") ("7" . "8") ("8" . "9") ("9" . "0")
        ("=" . "-") ("-" . "=") ("/" . ".") ("*" . "/")
        ("(" . ")") (")" . "(") (":" . ";") (";" . ":")
        ("." . "/") ("," . ".")))

(defun adjacent-key-fallback (key)
    (let* ((k (string-downcase (string key)))
                 (pair (assoc k *model-typo-fallback-map* :test #'string-equal)))
        (if pair (cdr pair) k)))

(defun typo-key-from-motor-model (key)
    (let ((k (string-downcase (string key))))
        (if (fboundp 'sample-motor-typo-key)
                (let ((picked (sample-motor-typo-key k)))
                    (if (string-equal picked k)
                            (adjacent-key-fallback k)
                        picked))
            (adjacent-key-fallback k))))

(defun mark-keypress-for-check (expected typed)
    (cond
      ((fboundp 'set-keypress-override)
            (set-keypress-override expected typed))
      ((fboundp 'set-last-typed-keys)
            (set-last-typed-keys expected typed))
      (t t)))

;; Actual-word typing usually checks immediately, but sometimes defers and
;; only notices the mistake after continuing to type.
(defparameter *actual-word-immediate-check-probability* 0.85)

(defun choose-actual-word-check-mode ()
    (if (< (random 1.0) *actual-word-immediate-check-probability*)
            "check-now"
        "check-later"))

(defun maybe-store-delayed-error-position (current-error check-mode expected typed position)
    (declare (ignore check-mode))
    (if (and (eq current-error 'none)
             (not (string-equal (string expected) (string typed))))
            position
        current-error))

(defun maybe-store-delayed-error-next-position (current-error-next check-mode expected typed next-position)
    (declare (ignore check-mode))
    (if (and (eq current-error-next 'none)
             (not (string-equal (string expected) (string typed))))
            next-position
        current-error-next))

;; Probability of selecting a nearby visual target during non-cell search.
(defparameter *local-neighbor-search-probability* 0.9)


(defun choose-visual-search-mode ()
    (if (< (random 1.0) *local-neighbor-search-probability*)
            "local"
        "global"))

(defun choose-key-with-typo-rate (expected)
    ;; Typo injection for the actual-word typing path.  Uses the word-specific
    ;; rate when set (calibrated separately from formulas against the human
    ;; keystroke data), falling back to the shared formula/target rate.
    (let* ((k (string-downcase (string expected)))
           (rate (cond ((and (boundp '*word-keypress-typo-rate*)
                             (numberp *word-keypress-typo-rate*))
                        *word-keypress-typo-rate*)
                       ((and (boundp '*target-keypress-typo-rate*)
                             (numberp *target-keypress-typo-rate*))
                        *target-keypress-typo-rate*)
                       (t 0.0))))
        (if (< (random 1.0) rate)
                (let ((picked (if (fboundp 'sample-motor-typo-key)
                                  (sample-motor-typo-key k)
                                  k)))
                    (if (string-equal picked k)
                            (adjacent-key-fallback k)
                        picked))
            k)))

(defun keypress-correct-state (expected typed)
    (if (string-equal (string expected) (string typed))
            t
        "pending"))

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

(defun learned-formula-char-at (formula index)
    (let* ((s (string formula))
           (n (length s)))
        (if (and (>= index 0) (< index n))
            (string (char s index))
            "__end_of_formula__")))

(defparameter *learned-formula-practice-threshold* 2)
(defparameter *formula-pattern-practice-counts* (make-hash-table :test 'equal))

(defun formula-cell-token-p (token)
    (let ((s (string token))
          (saw-letter nil)
          (saw-digit nil))
        (and (> (length s) 1)
             (loop for ch across s always
                   (cond
                     ((alpha-char-p ch) (setf saw-letter t) t)
                     ((digit-char-p ch) (setf saw-digit t) t)
                     (t nil)))
             saw-letter
             saw-digit)))

(defun formula-learning-pattern (formula)
    (let ((tokens (cached-formula-tokens formula)))
        (cond
          ((and (= (length tokens) 5)
                (string-equal (first tokens) "=")
                (string-equal (second tokens) "len")
                (string-equal (third tokens) "(")
                (formula-cell-token-p (fourth tokens))
                (string-equal (fifth tokens) ")"))
           "len-cell")
          ((and (= (length tokens) 4)
                (string-equal (first tokens) "=")
                (formula-cell-token-p (second tokens))
                (string-equal (third tokens) "*")
                (formula-cell-token-p (fourth tokens)))
           "cell-times-cell")
          (t nil))))

(defun learned-formula-pattern-ready-p (formula)
    (let ((pattern (formula-learning-pattern formula)))
        (and pattern
             (>= (gethash pattern *formula-pattern-practice-counts* 0)
                 *learned-formula-practice-threshold*))))

(defun formula-typing-strategy (retrieved-type formula)
    (declare (ignore formula))
    retrieved-type)

(defun record-formula-practice (formula)
    (let ((pattern (formula-learning-pattern formula)))
        (when pattern
            (incf (gethash pattern *formula-pattern-practice-counts* 0)))))

(defun reset-formula-practice ()
    (clrhash *formula-pattern-practice-counts*))

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

(defun right-hand-on-mouse-p ()
    ;; True when the right hand is (or will be) on the mouse device.  Used to
    ;; decide whether a real hand-to-mouse movement is needed before a cursor
    ;; action, so hand homing costs real motor time instead of teleporting.
    (equalp (notify-interface "motor" (list 'get-hand-device 'right))
            (list "motor" "cursor" "mouse")))


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

(start-hand-at-mouse)
;;;;Define the chunk-types
    (chunk-type Task Number)
    (chunk-type  Subtask actions items)
    (chunk-type action  action item)
    (chunk-type actionencode action meaning)
    (chunk-type WORD TYPE (SPELLING SYMBOL))
    (chunk-type intention   job task subtask subsubtask sx sy item meaning type column row word check correct)
    (chunk-type remembered-location item sx sy)
    (chunk-type typing  word type correct check phase token-index char-index current-token target-cell formula-source source-marker next-char token-done error-position error-next-position last-position task subtask subsubtask job item meaning)
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
;; Aliases: LLM-generated chunks name this target by the UIA element name "1"
;; or the instruction wording "Row 1"; all three labels resolve to the same
;; perceptual lookup (numeral "1" in the row-header strip).
(row-1-target-uia ISA target-spec label "1" lookup-text "1" lookup-cell-type "row" target-type T)
(row-1-target-nl ISA target-spec label "Row 1" lookup-text "1" lookup-cell-type "row" target-type T)

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
(first-goal ISA intention job "retrieve-task" task 1 )
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
    !eval! (when (= =x 1) (reset-formula-practice))
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
(P  7-2-pressing-enter
    =goal>
        isa     intention
        job     "do-action"
        meaning "enter"
        subsubtask =z
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
    =visual>  ; Test visual buffer and bind to =visual
    ?imaginal>
        state free
    ?manual>
        state free
    !eval! (right-hand-on-mouse-p)
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
)
; The right hand is still on the keyboard: bring it to the mouse first as a
; real motor movement (KLM H), then move the cursor once the hand arrives.
(P move-attention-N-cursor-cell-hand-to-mouse
        =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
        subsubtask =x
        type T
    =visual>
    ?imaginal>
        state free
    ?manual>
        state free
    !eval! (not (right-hand-on-mouse-p))
    ==>
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
        isa     hand-to-mouse
    =visual>
    =goal>
        isa     intention
        job     "hand-to-mouse-then-move"
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
    =visual>
        text-value  =j
    ?visual>
        state   free
    ?manual>
        state   free
    ?imaginal>
        state   free
    !eval! (right-hand-on-mouse-p)
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
)
; Same as above, but the right hand is still on the keyboard: make the real
; hand-to-mouse movement first, then move the cursor once the hand arrives.
(P move-attention-N-cursor-hand-to-mouse
    =goal>
        isa     intention
        job     "moving-attention-N-cursor"
        item =j
        subsubtask =x
        type "nil"
    =visual>
        text-value  =j
    ?visual>
        state   free
    ?manual>
        state   free
    ?imaginal>
        state   free
    !eval! (not (right-hand-on-mouse-p))
    ==>
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
        isa     hand-to-mouse
    =visual>
    =goal>
        isa     intention
        job     "hand-to-mouse-then-move"
)
; Shared continuation for both hand-to-mouse variants: the hand is on the
; mouse now, so issue the cursor move and advance to the next action.
(P move-cursor-after-hand-to-mouse
    =goal>
        isa     intention
        job     "hand-to-mouse-then-move"
        subsubtask =x
    =visual>
    ?manual>
        state   free
    ==>
    !bind!  =y (+ 1 =x)
    +manual>
        isa     move-cursor
        loc     =visual
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask =y
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
    !eval! (or (not (boundp '*spreadsheet-ablation-visual-search-enabled*))
               *spreadsheet-ablation-visual-search-enabled*)
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
(P  ready-to-type
    =goal>
        isa     intention
        job     "do-action"
        meaning  "type"
        type   "pending"
        item        =y
    ?manual>
        state   free
==>
    ; Homing is a real motor movement (KLM H): the hand travels from the mouse
    ; back to the home row, and the press-key productions wait on ?manual>
    ; state free, so typing cannot begin until the hand has arrived.
    +manual>
        isa     hand-to-home
    =goal>
        isa     intention
        job     "typing"
        word    =y
    +retrieval>
        isa     word
        SPELLING    =y
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
    =retrieval>
        type    =r
   ?visual-location>
        state    free
    ==>
    !bind!  =j  (cadr (nth (1- =z) (symbol-value (read-from-string (concatenate-strings-subtask =x (- =y 1))))))
    !bind!  =typing-type (formula-typing-strategy =r =w)

    =goal>
        isa     typing
        word    =w
        type    =typing-type
        CORRECT t
        check   "done"
        phase   nil           ; We will use the phase slot to keep track of the different stages within the typing process (e.g., typing actual char, checking actual char, etc.)
        token-index nil     ; We will use this slot to keep track of which character in the word we are currently typing
        char-index nil          ; We will use this slot to keep track of which character in the word we are currently checking (it can be the same as token-index or one ahead depending on the check mode)
        current-token nil       ; Formula only: We will use this slot to keep the current token we are trying to type (it can be a character or a group of characters depending on the type of the formula)
        target-cell nil         ; We will use this slot to keep track of the target cell we are trying to type into (it can be nil if we are not sure yet or if the target is not a cell)
        source-marker nil     ; We will use this slot to keep track of the source of the word we are typing. (e.g., is it from the memory, is it from the screen, etc.) Used for formula only.
        next-char nil       ; We will use this slot to keep track of the next character we are expecting to see on the screen after typing the current character. 
        token-done nil       ; We will use this slot to keep track of whether we have finished typing the current token or not (used for formulas, for text it will always be nil)
        error-position none      ; We will use this slot to keep track of the position of the first error we made while typing the word (it can be nil if we have not made any error or if we have not checked for errors yet)
        error-next-position none    ; We will use this slot to keep track of the position of the next error (the error after the first one) we made while typing the word (it can be nil if we have not made any error or if we have not checked for errors yet)
        last-position nil       ; We will use this slot to keep track of the last position we checked for correctness (used for optimization, to avoid checking the same position multiple times)
    +retrieval>
        isa     item
        word    =w
        position    first
    ;shift the attention to the instruction
   +visual-location>
        isa     visual-location
        Text    T
        text-value   =j
)
; We start typing. We get the current letter that we want to press from the retrieval and then retrieve the next letter. We then decide if we want to check for the error through the check-mode, if we need to make error through choose-key-with-typo-rate 
(p start-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      CORRECT   t
      phase     nil
      error-position =errpos
      error-next-position =errnext

   =retrieval>
      position  =pos
      current   =l
    - next      nil
      next      =x
   ?manual>
        state   free
   ?visual>
        state    free
   =visual-location>
        text-value =j
   ==>
    !bind! =typed-key (choose-key-with-typo-rate =l) ; Decide whether to make typo or not when pressing the key
    !eval! (mark-keypress-for-check =l =typed-key)   ; check the keypress for error after we press it
    !bind! =check-mode (choose-actual-word-check-mode)    ; Decide when to check for the error (immediately after pressing the key or after typing the whole word)
    !bind! =base (shifted-formula-base-key =typed-key)    ; If the key we need to press is a shifted key (e.g., uppercase letter, or symbol that requires shift), we will need to press shift + the base key (the key without shift). This function gives us the base key that we need to press along with shift if we need to press shift.
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes") ; Check if we need to press shift or not
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =typed-key)  ; If we need to press shift, the key we will press will be "shift" + the base key, if we don't need to press shift, the key we will press is just the typed key
    !bind! =next-phase (if (string-equal =needs-shift "yes")   ; If we need to press shift, the next phase will be typing-actual-char-shift-base or typing-actual-char-shift-base-skip depending on the check mode, if we don't need to press shift, the next phase will be verify-actual-char or skip-actual-char-check depending on the check mode
                           (if (string-equal =check-mode "check-now")
                               "typing-actual-char-shift-base"
                               "typing-actual-char-shift-base-skip")
                           (if (string-equal =check-mode "check-now")
                               "verify-actual-char"
                               "skip-actual-char-check"))
    !bind! =new-error-pos (maybe-store-delayed-error-position =errpos =check-mode =l =typed-key =pos)
    !bind! =new-error-next (maybe-store-delayed-error-next-position =errnext =check-mode =l =typed-key =x)
   !eval! (what-is-on-screen '(=j))
    !eval! (log-attention-shift-explicit =visual-location "start-typing")
   =goal>
      ISA       typing
      word      =w
      correct   "pending"
      check     "not done"
      phase     =next-phase
      source-marker =base
      next-char =l
      error-position =new-error-pos
      error-next-position =new-error-next
      last-position =pos
   +manual>
      ISA       press-key
        key       =press-key
   +retrieval>
        isa         item
        word        =w
        position    =x
   +visual>
        isa     move-attention
        screen-pos  =visual-location

)

(p type-actual-word-shift-base
    =goal>
        ISA           typing
        type          "actual-word"
        phase         "typing-actual-char-shift-base"
        source-marker =base
    ?manual>
        state         free
    ==>
    +manual>
        ISA           press-key
        key           =base
    =goal>
        phase         "verify-actual-char"
)

(p type-actual-word-shift-base-skip
    =goal>
        ISA           typing
        type          "actual-word"
        phase         "typing-actual-char-shift-base-skip"
        source-marker =base
    ?manual>
        state         free
    ==>
    +manual>
        ISA           press-key
        key           =base
    =goal>
        phase         "skip-actual-char-check"
)
; After starting to type we keep recalling this. Very very similar to start typing but different in the sense that we are now in the middle of typing the word, so we need to keep track of the position of the next character to type and we also need to update the error position if we made an error in the previous character and we didn't check for it yet.
(p continue-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      CORRECT   t
      phase     nil
      error-position =errpos
      error-next-position =errnext

   =retrieval>
      position  =pos
      current   =l
    -  position   first
    - next      nil
      next      =x
   ?manual>
        state   free

   ==>
    !bind! =typed-key (choose-key-with-typo-rate =l)
    !eval! (mark-keypress-for-check =l =typed-key)
    !bind! =check-mode (choose-actual-word-check-mode) ; Decides whether the character will be checked immediately or skipped for now. It returns "check-now" if we want to check immediately and "check-later" if we want to skip the check for now and check it later (after typing more characters or after finishing typing the whole word)
    !bind! =base (shifted-formula-base-key =typed-key)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =typed-key)
    !bind! =next-phase (if (string-equal =needs-shift "yes")
                           (if (string-equal =check-mode "check-now")
                               "typing-actual-char-shift-base"
                               "typing-actual-char-shift-base-skip")
                           (if (string-equal =check-mode "check-now")
                               "verify-actual-char"
                               "skip-actual-char-check"))
    !bind! =new-error-pos (maybe-store-delayed-error-position =errpos =check-mode =l =typed-key =pos)
    !bind! =new-error-next (maybe-store-delayed-error-next-position =errnext =check-mode =l =typed-key =x)
   =goal>
      ISA       typing
      word      =w
      correct   "pending"
      check     "not done"
      phase     =next-phase
      source-marker =base
      next-char =l
      error-position =new-error-pos
      error-next-position =new-error-next
      last-position =pos
   +manual>
      ISA       press-key
        key       =press-key
   +retrieval>
        isa         item
        word        =w
        position    =x
)

(p continue-typing-with-visual-check
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     nil
   -   check     "done"
   =retrieval>
    -  position  first
   ?manual>
      state     free
   ==>
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   "pending"
   =retrieval>
;TODO fix the visual location

)

(p skip-actual-word-check
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "skip-actual-char-check"
      correct   "pending"
   ?manual>
      state     free
   ==>
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "done"
      phase     nil
)

(p realize-delayed-error-start
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-actual-char"
      correct   "pending"
    - error-position none
      error-position =ep
      error-next-position =en
      last-position =lp
   ?manual>
      state     free
   ==>
   !eval! (clear-pending-shift-keypress)
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     "delete-back-to-error"
      error-position =ep
      error-next-position =en
      last-position =lp
   +retrieval>
      isa       item
      word      =w
      position  =lp
)

(p delete-back-or-retype-delayed-error
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     "delete-back-to-error"
      error-position =ep
   =retrieval>
      position  =pos
      previous  =prev
   ?manual>
      state     free
   ==>
   !bind! =at-error (if (equal =pos =ep) "yes" "no")
   !bind! =next-phase (if (string-equal =at-error "yes")
                          "retype-actual-char"
                          "delete-back-to-error")
   !bind! =resume-pos (if (string-equal =at-error "yes") =ep =prev)
   !bind! =next-error-pos (if (string-equal =at-error "yes") 'none =ep)
   !bind! =next-error-next (if (string-equal =at-error "yes") 'none =resume-pos)
   +manual>
      ISA       press-key
      key       "delete"
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     =next-phase
      error-position =next-error-pos
      error-next-position =next-error-next
      last-position =resume-pos
   +retrieval>
      isa       item
      word      =w
      position  =resume-pos
)

(p delete-first-delayed-error-and-retype
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     "delete-back-to-error"
      error-position first
   =retrieval>
      position  first
   ?manual>
      state     free
   ==>
   +manual>
      ISA       press-key
      key       "delete"
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     "retype-actual-char"
      error-position none
      error-next-position none
      last-position first
   +retrieval>
      isa       item
      word      =w
      position  first
)
; We check if we can find any typos until this point.
(p check-letter
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-actual-char"
      correct   "pending"
      error-position none
   =retrieval>
   ?manual>
      state     free
   ==>

   !bind!       =res (if (equal (type-check) "false") "false"    t)
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   =res
      check     "done"
      phase     nil
    =retrieval>
)

(p correct-letter
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     nil
      correct   "false"
   ?manual>
      state     free
   =retrieval>
      previous      =x
   ==>
   !eval! (clear-pending-shift-keypress)
   +manual>
      ISA       press-key
      key       "delete"
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     "retype-actual-char"
   +retrieval>
      isa     item
      word    =w
      position    =x
)

(p retype-corrected-letter
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "retype-actual-char"
      correct   t
   =retrieval>
      position  =pos
      current   =l
    - next      nil
      next      =x
   ?manual>
      state     free
   ==>
    !bind! =base (shifted-formula-base-key =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =l)
    !bind! =next-phase (if (string-equal =needs-shift "yes")
                           "retype-actual-char-shift-base"
                           "verify-actual-char")
   =goal>
      ISA       typing
      word      =w
      correct   "pending"
      check     "not done"
      phase     =next-phase
      source-marker =base
      next-char =l
      last-position =pos
   +manual>
      ISA       press-key
      key       =press-key
   +retrieval>
      isa       item
      word      =w
      position  =x
)

(p retype-final-corrected-letter
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "retype-actual-char"
      correct   t
   =retrieval>
      position  =pos
      current   =l
      next      nil
   ?manual>
      state     free
   ==>
    !bind! =base (shifted-formula-base-key =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =l)
    !bind! =next-phase (if (string-equal =needs-shift "yes")
                           "retype-final-char-shift-base"
                           "verify-final-char")
   =goal>
      ISA       typing
      word      =w
      correct   "pending"
      check     "not done"
      phase     =next-phase
      source-marker =base
      next-char =l
      last-position =pos
   +manual>
      ISA       press-key
      key       =press-key
)

(p retype-corrected-letter-shift-base
   =goal>
      ISA           typing
      type          "actual-word"
      phase         "retype-actual-char-shift-base"
      source-marker =base
      correct       "pending"
   ?manual>
      state         free
   ==>
   +manual>
      ISA           press-key
      key           =base
   =goal>
      phase         "verify-actual-char"
)

(p retype-final-corrected-letter-shift-base
   =goal>
      ISA           typing
      type          "actual-word"
      phase         "retype-final-char-shift-base"
      source-marker =base
      correct       "pending"
   ?manual>
      state         free
   ==>
   +manual>
      ISA           press-key
      key           =base
   =goal>
      phase         "verify-final-char"
)
(p finish-typing
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      phase     nil
   ?manual>
      state     free
   =retrieval>
      position  =pos
      current   =l
      next      nil
   ==>
    !bind! =typed-key (choose-key-with-typo-rate =l)
    !eval! (mark-keypress-for-check =l =typed-key)
    !bind! =base (shifted-formula-base-key =typed-key)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =typed-key)
    !bind! =next-phase (if (string-equal =needs-shift "yes") "final-char-shift-base" "verify-final-char")
   =goal>
      ISA       typing
      word      =w
      correct   "pending"
      check     "not done"
        phase     =next-phase
        source-marker =base
      next-char =l
      last-position =pos
   +manual>
      ISA       press-key
        key       =press-key
)

(p type-final-char-shift-base
    =goal>
        ISA           typing
        type          "actual-word"
        phase         "final-char-shift-base"
        source-marker =base
        correct       "pending"
    ?manual>
        state         free
    ==>
    +manual>
        ISA           press-key
        key           =base
    =goal>
        phase         "verify-final-char"
)
; Now we are finishing the word. We check fi the final character is correct. If it is correct, we are done. If it is not correct, we will need to repair it. 
(p verify-final-typed-char
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-final-char"
      correct   "pending"
      error-position none
   ?manual>
      state     free
   ==>
   !bind!  =res (if (equal (type-check) "false") "false" "done")
   =goal>
      ISA       typing
      word      =w
      correct   =res
      check     "done"
)
; A deferred (check-later) error can still be pending when the word's final
; character is verified.  Realize it here and run the same delete-back-to-error
; repair, so a word never finishes with a known-but-unfixed typo.
(p realize-delayed-error-at-final-char
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-final-char"
      correct   "pending"
    - error-position none
      error-position =ep
      error-next-position =en
      last-position =lp
   ?manual>
      state     free
   ==>
   !eval! (clear-pending-shift-keypress)
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      correct   t
      check     "not done"
      phase     "delete-back-to-error"
      error-position =ep
      error-next-position =en
      last-position =lp
   +retrieval>
      isa       item
      word      =w
      position  =lp
)
(p repair-final-typed-char-delete
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-final-char"
      correct   "false"
      next-char =l
   ?manual>
      state     free
   ==>
   !eval! (clear-pending-shift-keypress)
   +manual>
      ISA       press-key
      key       "delete"
   =goal>
      ISA       typing
      word      =w
      phase     "retype-final-char"
      correct   t
      check     "not done"
)
(p repair-final-typed-char-retype
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "retype-final-char"
      next-char =l
   ?manual>
      state     free
   ==>
    !bind! =base (shifted-formula-base-key =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" =l)
    !bind! =next-phase (if (string-equal =needs-shift "yes") "retype-final-char-shift-base" "verify-final-char")
   +manual>
      ISA       press-key
        key       =press-key
   =goal>
      ISA       typing
      word      =w
        phase     =next-phase
        source-marker =base
      correct   "pending"
      check     "not done"
)

(p repair-final-typed-char-retype-shift-base
    =goal>
        ISA           typing
        type          "actual-word"
        phase         "retype-final-char-shift-base"
        source-marker =base
        correct       "pending"
    ?manual>
        state         free
    ==>
    +manual>
        ISA           press-key
        key           =base
    =goal>
        phase         "verify-final-char"
)

; Learned formulas are simple repeated formula schemas. The model types them
; from memory without shifting attention back to the formula instruction
; between tokens.
(p start-typing-learned-formula
        =goal>
            ISA       typing
            word      =w
            type      "learned-formula"
            phase     nil
        =visual-location>
            text-value =target
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ?manual>
            state free
        ==>
        !bind!  =ch (learned-formula-char-at =w 0)
        !bind!  =base (shifted-formula-base-key =ch)
        !bind!  =next-phase (if (string-equal =base *no-shift-base-key*)
                                "learned-have-char"
                                "learned-have-shifted-char")
        !eval! (what-is-on-screen '(=target))
        !eval! (respond-to-eye-move-xy =sx =sy)
        !eval! (log-attention-shift-explicit =visual-location "start-typing-learned-formula")
        =goal>
            phase =next-phase
            char-index 1
            next-char =ch
            source-marker =base
            correct t
        +visual>
            isa       move-attention
            screen-pos =visual-location
)

(p compute-next-learned-formula-char
        =goal>
            ISA       typing
            word      =w
            type      "learned-formula"
            phase     "learned-typing-formula"
            correct   t
            char-index =i
        ==>
        !bind!  =ch (learned-formula-char-at =w =i)
        !bind!  =base (shifted-formula-base-key =ch)
        !bind!  =next-phase (cond ((string-equal =ch "__end_of_formula__")
                                    "learned-formula-done")
                                   ((string-equal =base *no-shift-base-key*)
                                    "learned-have-char")
                                   (t
                                    "learned-have-shifted-char"))
        !bind!  =next-i (if (string-equal =ch "__end_of_formula__") =i (+ =i 1))
        =goal>
            phase =next-phase
            char-index =next-i
            next-char =ch
            source-marker =base
)

(p type-learned-formula-char
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-have-char"
            next-char =ch
        ?manual>
            state free
        ==>
        +manual>
            cmd      press-key
            key      =ch
        =goal>
            phase "verify-learned-formula-char"
            correct "pending"
)

(p type-learned-formula-shift-prefix
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-have-shifted-char"
          - source-marker "__no_shift__"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            cmd      press-key
            key      "shift"
        =goal>
            phase "learned-have-shifted-char-base"
)

(p type-learned-formula-shift-base
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-have-shifted-char-base"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            cmd      press-key
            key      =base
        =goal>
            phase "verify-learned-formula-char"
            correct "pending"
)

(p verify-learned-formula-char
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "verify-learned-formula-char"
        ?manual>
            state free
        ==>
        !bind! =res (if (equal (type-check) "false") "false" t)
        !bind! =next-phase (if (equal =res "false")
                               "learned-repair-delete"
                               "learned-typing-formula")
        =goal>
            phase =next-phase
            correct =res
)

(p repair-learned-formula-char-delete
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-repair-delete"
            correct   "false"
        ?manual>
            state free
        ==>
        !eval! (clear-pending-shift-keypress)
        +manual>
            ISA       press-key
            key       "delete"
        =goal>
            phase "learned-retype-char"
            correct t
)

(p retype-learned-formula-char
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-retype-char"
            next-char =ch
            source-marker "__no_shift__"
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       =ch
        =goal>
            phase "verify-learned-formula-char"
            correct "pending"
)

(p retype-learned-formula-shift-prefix
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-retype-char"
          - source-marker "__no_shift__"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       "shift"
        =goal>
            phase "learned-retype-shifted-char-base"
)

(p retype-learned-formula-shift-base
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-retype-shifted-char-base"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       =base
        =goal>
            phase "verify-learned-formula-char"
            correct "pending"
)

(p finish-learned-formula
        =goal>
            ISA       typing
            type      "learned-formula"
            phase     "learned-formula-done"
        ==>
        =goal>
            correct "done"
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
            phase     nil
        ?visual>
            state free
        ?visual-location>
            state free
        ==>
        !bind!  =target  (cadr (nth (1- =z) (symbol-value (read-from-string (concatenate-strings-subtask =x (- =y 1))))))
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
        +visual-location>
            isa       visual-location
            Text      T
            text-value =target
)
; We shift the attention and memorize the first token of the formula. shift the attention to the formula. The current format may need a little attention and the current-token needs to be defined here not in the start-typing-formula.
; It also needs to come from visual buffer.
(p memorize-token-and-shift-to-target
        =goal>
            ISA       typing
            type      formula
            phase     "memorize-token"
          - current-token nil
                    - current-token "__end_of_formula__"
            current-token =tok
            target-cell =target
        =visual-location>
            text-value =target
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ==>
        !output! ("memorized formula token")
        !output! ("formula target")
        !output! =target
        !output! ("formula token")
        !output! =tok
        !eval! (what-is-on-screen '(=target))
        !eval! (respond-to-eye-move-xy =sx =sy)
        !eval! (log-attention-shift-explicit =visual-location "memorize-token-and-shift-to-target")
        =goal>
            phase     "typing-token"
            char-index 0
        +visual>
            isa       move-attention
            screen-pos =visual-location
)
; As long as we have not checked or the typed characters are correct, keep finding the next char to type. 
(p compute-next-char-of-current-token
        =goal>
            ISA       typing
            type      formula
            phase     "typing-token"
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
        ?manual>
            state free
        ==>
        !bind!  =next (+ =i 1)
        !output! ("type char")
        !output! =ch
        +manual>
            cmd      press-key
            key      =ch
        =goal>
            phase "verify-formula-char"
            correct "pending"
            char-index =next
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
            state free
        ==>
        +manual>
            cmd      press-key
            key      "shift"
        =goal>
            phase "have-shifted-char-base"
)
; We then press the base key while holding shift to type the shifted char (technically we are not holding the shift key but this is the best emulation of that).
(p type-shifted-char-base
        =goal>
            ISA       typing
            type      formula
            phase     "have-shifted-char-base"
            token-done "no"
            source-marker =base
            char-index =i
        ?manual>
            state free
        ==>
        !bind!  =next (+ =i 1)
        !output! ("type shifted char")
        !output! =base
        +manual>
            cmd      press-key
            key      =base
        =goal>
            phase "verify-formula-char"
            correct "pending"
            char-index =next
)
; If the phase is verify-formula-char, it means  we need to check if the typed characters are correct or not. If they are correct, we keep going with the next char. If it is not correct, we will need to repair it.
(p verify-formula-char
        =goal>
            ISA       typing
            type      formula
            phase     "verify-formula-char"
        ?manual>
            state free
        ==>
        !bind! =res (if (equal (type-check) "false") "false" t)
        =goal>
            phase "typing-token"
            correct =res
)

(p correct-formula-char-delete
        =goal>
            ISA       typing
            type      formula
            phase     "typing-token"
            correct   "false"
        ?manual>
            state free
        ==>
        !eval! (clear-pending-shift-keypress)
        +manual>
            ISA       press-key
            key       "delete"
        =goal>
            phase "retype-formula-char"
)

(p correct-formula-char-retype
        =goal>
            ISA       typing
            type      formula
            phase     "retype-formula-char"
            next-char =ch
            source-marker "__no_shift__"
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       =ch
        =goal>
            phase "verify-formula-char"
)

(p correct-shifted-formula-char-retype-prefix
        =goal>
            ISA       typing
            type      formula
            phase     "retype-formula-char"
          - source-marker "__no_shift__"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       "shift"
        =goal>
            phase "retype-shifted-formula-char-base"
)

(p correct-shifted-formula-char-retype-base
        =goal>
            ISA       typing
            type      formula
            phase     "retype-shifted-formula-char-base"
            source-marker =base
        ?manual>
            state free
        ==>
        +manual>
            ISA       press-key
            key       =base
        =goal>
            phase "verify-formula-char"
)
; When we are done with a token, move to the next one.
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
        ?visual>
            state free
        ?visual-location>
            state free
        !eval! (or (not (boundp '*spreadsheet-ablation-formula-lookback-enabled*))
                   *spreadsheet-ablation-formula-lookback-enabled*)
        ==>
        !bind!  =nti (next-formula-token-index =ti)
        !bind!  =next-token (formula-token-at-safe =w =nti)
        !output! ("next formula token")
        !output! =next-token
        =goal>
            phase "look-back-to-formula"
            token-index =nti
            char-index 0
            current-token =next-token
            next-char nil
            token-done nil
        +visual-location>
            isa visual-location
            Text T
            text-value =source
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
; Now we request for the cell we want to type stuff in.
(p return-attention-to-formula-target
        =goal>
            ISA       typing
            type      formula
            phase     "return-to-formula-target"
            target-cell =target
        ?visual>
            state free
        ?visual-location>
            state free
            buffer empty
        ==>
        +visual-location>
            isa visual-location
            Text T
            text-value =target
)
; We shift the attention to the target cell.
(p resume-formula-typing-after-lookback
        =goal>
            ISA       typing
            type      formula
            phase     "return-to-formula-target"
            current-token =tok
            target-cell =target
        =visual-location>
            text-value =target
            screen-x =sx
            screen-y =sy
        ?visual>
            state free
        ==>
        !bind! =next-phase (if (string-equal =tok "__end_of_formula__")
                               "memorize-token"
                               "typing-token")
        !eval! (what-is-on-screen '(=target))
        !eval! (respond-to-eye-move-xy =sx =sy)
        !eval! (log-attention-shift-explicit =visual-location "resume-formula-typing-after-lookback")
        =goal>
            phase =next-phase
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
        ==>
        !bind! =w (+ 1 =z)
        !eval! (record-formula-practice =formula)
        =goal>
            isa     intention
            job     "retrieve-actions-of-subtask"
            subsubtask  =w
            type    nil
            word    nil
            meaning nil
)

;When typing is over, we move on to the next action!
(P on-to-the-next-typing
    =goal>
        isa         typing
        correct     "done"
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
