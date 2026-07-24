;;; ============================================================================
;;; generic_helpers.lisp — support layer for the generic-interface ACT-R model
;;;
;;; Load order:  fucntion_new_tcp.lisp  ->  THIS FILE  ->  tasks/Wxx_*.lisp
;;;              ->  generic_interface_model.lisp
;;;
;;; This file adds the minimum that Windows-native tasks need on top of the
;;; Excel study's TCP/logging layer:
;;;   1. key COMMANDS beyond "enter" (single named keys and modifier chords
;;;      such as "win+r", "ctrl+shift+esc") delivered through the same
;;;      output-key monitor pathway;
;;;   2. shift handling for UPPERCASE letters (the Excel model only shifted
;;;      symbol keys), so words like "Projects" type with case;
;;;   2b. extended mouse actions built on the ACT-R "extended-motor-actions"
;;;      extra: RIGHT-CLICK (punch of the right middle finger — the virtual
;;;      mouse's right button), mouse-button HOLD/RELEASE for drag
;;;      (ClickDown -> Move -> ClickUp), and a SCROLL-WHEEL motor style
;;;      with per-notch execution events;
;;;   3. a typing visual anchor that generalizes the Excel model's
;;;      look-at-the-target-cell-while-typing behavior to arbitrary
;;;      interfaces, with a guaranteed fallback to the instruction panel;
;;;   4. task-file plumbing: globals a task chunk file sets, and the
;;;      instruction-panel installer the model file calls.
;;;
;;; Everything else (typo injection, immediate-vs-delayed checking, local vs
;;; global visual search, CSV logging, TCP bridge) is reused unchanged from
;;; fucntion_new_tcp.lisp.
;;; ============================================================================

;;; ----------------------------------------------------------------------
;;; Fix for fucntion_new_tcp.lisp: maybe-act-r-output there does
;;; (apply #'act-r-output ...), but act-r-output is a MACRO in ACT-R 7.x,
;;; so any non-quiet call errors. (The paper's batch runs set
;;; *batch-quiet-output* and never hit it.) Redefine with plain format.
;;; ----------------------------------------------------------------------

(defun maybe-act-r-output (format-string &rest args)
  (unless *batch-quiet-output*
    (fresh-line)
    (apply #'format t format-string args)
    (terpri)))

;;; ----------------------------------------------------------------------
;;; Globals a task chunk file overrides (tasks/Wxx_*.lisp)
;;; ----------------------------------------------------------------------

(defvar *generic-total-tasks* 1
  "Number of tasks defined by the loaded task file. The controller stops
after completing task number *generic-total-tasks*.")

(defvar *generic-offline-visicon* t
  "When T, install-task-visicon adds placeholder UI features so the model
can run without a live UIA bridge. Set NIL for live VisiTor runs.")

;;; Instruction-panel geometry.
;;; The x<960 split is an Excel-study convention (its UI occupies the left
;;; half, the virtual instruction panel the right).  The generic Windows tasks
;;; drive the WHOLE screen -- real UI targets (taskbar icons, cascading context
;;; menus, right-half controls) can sit anywhere in 0..1920 -- so the boundary
;;; is pushed past the physical screen and the instruction-panel markers are
;;; parked off-screen beyond it.  The panel markers are located by their VALUE
;;; (productions 1/3 search `value =...` with no screen-x constraint), so their
;;; coordinates are irrelevant to reading them; the boundary's only job is to
;;; keep the general UI-target search (`< screen-x =limit`) from attending them.
(defparameter *instruction-panel-x-boundary* 2560)
(defparameter *instruction-panel-task-x* 3000)
(defparameter *instruction-panel-subtask-x* 3200)

(defun instruction-panel-boundary () *instruction-panel-x-boundary*)

;;; ----------------------------------------------------------------------
;;; Behavior parameters (same names/semantics as the Excel study where they
;;; overlap; redefined here so the generic model does not need to load the
;;; Excel model source)
;;; ----------------------------------------------------------------------

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

;; Probability of selecting a nearby visual target during object search.
(defparameter *local-neighbor-search-probability* 0.9)

(defun choose-visual-search-mode ()
  (if (< (random 1.0) *local-neighbor-search-probability*)
      "local"
      "global"))

(defparameter *model-typo-fallback-map*
  '(("a" . "s") ("b" . "n") ("c" . "v") ("d" . "f") ("e" . "r")
    ("f" . "g") ("g" . "h") ("h" . "j") ("i" . "o") ("j" . "k")
    ("k" . "l") ("l" . ";") ("m" . ",") ("n" . "m") ("o" . "p")
    ("p" . "[") ("q" . "w") ("r" . "t") ("s" . "d") ("t" . "y")
    ("u" . "i") ("v" . "b") ("w" . "e") ("x" . "c") ("y" . "u")
    ("z" . "x")))

(defun adjacent-key-fallback (key)
  (let* ((k (string-downcase (string key)))
         (pair (assoc k *model-typo-fallback-map* :test #'string-equal)))
    (if pair (cdr pair) k)))

(defun choose-key-with-typo-rate (expected)
  "Return the key the model intends to hit for EXPECTED: usually EXPECTED
itself (downcased), with probability *target-keypress-typo-rate* a
neighboring key from the MSR motor model."
  (let* ((k (string-downcase (string expected)))
         (rate (if (and (boundp '*target-keypress-typo-rate*)
                        (numberp *target-keypress-typo-rate*))
                   *target-keypress-typo-rate*
                   0.06)))
    (if (< (random 1.0) rate)
        (let ((picked (if (fboundp 'sample-motor-typo-key)
                          (sample-motor-typo-key k)
                          k)))
          (if (string-equal picked k)
              (adjacent-key-fallback k)
              picked))
        k)))

(defun mark-keypress-for-check (expected typed)
  (cond
    ((fboundp 'set-keypress-override) (set-keypress-override expected typed))
    ((fboundp 'set-last-typed-keys) (set-last-typed-keys expected typed))
    (t t)))

;;; ----------------------------------------------------------------------
;;; 1. Key commands: named keys and modifier chords
;;; ----------------------------------------------------------------------

(defparameter *key-command-chord-separator* #\+)

(defun key-chord-string-p (key)
  (and (stringp (string key))
       (find *key-command-chord-separator* (string key))
       t))

(defun key-chord-components (key)
  (let ((s (string-downcase (string key)))
        (out nil)
        (start 0))
    (loop for pos = (position *key-command-chord-separator* s :start start)
          do (if pos
                 (progn (push (subseq s start pos) out)
                        (setf start (1+ pos)))
                 (progn (push (subseq s start) out)
                        (return))))
    (nreverse out)))

(defparameter *plain-enter-names* '("enter" "return" "newline"))

(defun plain-enter-key-p (key)
  (member (string-downcase (string key)) *plain-enter-names*
          :test #'string-equal))

(defun single-typeable-key-p (s)
  (let ((str (string s)))
    (and (= (length str) 1)
         (or (alphanumericp (char str 0))
             (find (char str 0) "-=[]\\;',./`")))))

(defun key-command-surrogate (key)
  "Physical key the manual module presses for a key command. It only
determines motor timing; the DELIVERED key is forced by the override
below. Chords use their final component when it is a plain typeable key."
  (let* ((k (string-downcase (string key)))
         (last-part (car (last (key-chord-components k)))))
    (cond
      ((plain-enter-key-p k) "return")
      ((single-typeable-key-p last-part) last-part)
      (t "return"))))

(defun prepare-key-command (key)
  "Arrange for KEY to be delivered verbatim to VisiTor. Plain enter keeps
the Excel model's original path (typo-exempt, screen refresh); every other
named key or chord is pinned via the keypress override so no typo is
injected and the chord string reaches the bridge as one payload."
  (unless (plain-enter-key-p key)
    (mark-keypress-for-check key key))
  t)

;;; ----------------------------------------------------------------------
;;; 2. Shift handling that also covers uppercase letters
;;; ----------------------------------------------------------------------

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

(defun upper-alpha-string-p (s)
  (let ((str (string s)))
    (and (= (length str) 1)
         (alpha-char-p (char str 0))
         (upper-case-p (char str 0)))))

(defun generic-shift-base-key (intended typed)
  "Return the base key to press while shift is held, or *no-shift-base-key*.
INTENDED is the character from the letter chunk (case preserved); TYPED is
the possibly-typo key chosen for it (already downcased)."
  (cond
    ((upper-alpha-string-p intended) (string-downcase (string typed)))
    (t (shifted-formula-base-key typed))))

(defun actr-key-for-char (ch)
  "Map a character string to the ACT-R keyboard key name."
  (let ((s (string ch)))
    (if (string= s " ") "space" s)))

;;; ----------------------------------------------------------------------
;;; 2b. Extended mouse actions: right-click, button hold/release (drag),
;;;     and a scroll wheel.
;;;
;;; Built on the ACT-R extra "extended-motor-actions" (replaces the motor
;;; module with the officially distributed extended version; existing
;;; punch/peck/press-key behavior is unchanged, but every button action
;;; now also generates a release signal, and cursor moves made while a
;;; finger is held down are slowed per :cursor-drag-delay — MacKenzie,
;;; Sellen & Buxton, 1991).
;;;
;;; ACT-R models mouse buttons as fingers of the right hand on the mouse:
;;; the built-in CLICK-MOUSE is "punch right index" (other-files/
;;; mouse.lisp), and the virtual mouse device decodes the punched finger
;;; from its position offset. RIGHT-CLICK-MOUSE below is therefore
;;; "punch right middle" — the right button — mirroring the built-in
;;; definition exactly. The click-mouse/release-mouse monitors receive
;;; the finger name and dispatch left vs right button delivery to VisiTor.
;;;
;;; Drag is decomposed exactly as the physical action decomposes:
;;;   HOLD-MOUSE (button down) -> MOVE-CURSOR (drag) -> RELEASE-MOUSE (up)
;;; issued by the ClickDown / Move / ClickUp productions in the model.
;;;
;;; The scroll wheel has no counterpart in the distributed motor devices,
;;; so it is added the documented way (examples/extend-manual-requests/
;;; using-a-style/): a new SCROLL-WHEEL movement style with the standard
;;; preparation/initiation/execution stages; each wheel notch is a
;;; burst-time-spaced execution event that delivers one scroll step.
;;; ----------------------------------------------------------------------

(require-extra "extended-motor-actions")

(defvar *clicking-occurred* nil)        ; shared with the model file
(defvar *mouse-hold-pending* nil
  "Set by the mouse-button-down production immediately before its
HOLD-MOUSE request so the click-mouse monitor can tell the button-down
of a drag from an ordinary click.")
(defvar *mouse-dragging* nil
  "T between a delivered button-down and the matching button-up.")

;;; The Excel-heritage productions "teleport" the hand back onto the mouse
;;; with start-hand-at-mouse before every mouse action. That sets only the
;;; hand's CURRENT position; the extended motor module prepares punches
;;; from the PLANNED position (next-loc), which typing/press-key actions
;;; leave parked at the keyboard — the punch then notifies the mouse
;;; device with keyboard coordinates and the click is dropped ("Invalid
;;; MOUSE cursor click finger position"). Clearing the planned position
;;; makes every :current nil query fall back to the just-teleported
;;; current position. Only called from productions that already require
;;; ?manual state free, so no prepared movement is in flight.
(defun snap-hand-to-mouse ()
  (start-hand-at-mouse)
  (let ((mtr (get-module :motor)))
    (when mtr
      (setf (next-loc (right-hand mtr)) nil)))
  t)

;; Symmetric fix for the keyboard direction: after mouse punches the
;; planned position is in screen-pixel coordinates, and key presses
;; prepared from it index outside the 23x7 virtual keyboard array
;; ("keyboard-interface-fn" INVALID-ARRAY-INDEX warnings, dropped keys).
(defun snap-hands-to-home ()
  (start-hands-at-home)
  (let ((mtr (get-module :motor)))
    (when mtr
      (setf (next-loc (right-hand mtr)) nil
            (next-loc (left-hand mtr)) nil)))
  t)

;;; --- right-click-mouse manual request --------------------------------

(defmethod right-click-mouse ((mtr-mod motor-module) request)
  "Punch the right MIDDLE finger (the virtual mouse's right button).
Exactly parallel to the built-in CLICK-MOUSE (punch right index)."
  (let* ((model (current-model))
         (mouse (find-model-cursor (list model 'mouse))))
    (if mouse
        (if (equalp (device-for-hand 'right :current nil)
                    (list "motor" "cursor" "mouse"))
            (punch mtr-mod :hand 'right :finger 'middle :request-spec request)
          (model-warning "RIGHT-CLICK-MOUSE requested when hand not at mouse!"))
      (model-warning "RIGHT-CLICK-MOUSE requested but no mouse device available."))))

(extend-manual-requests (right-click-mouse) handle-simple-command-request)

;;; --- mouse event logging + monitors ----------------------------------

(defun mouse-log-file ()
  (merge-pathnames "mouse_events.csv" *model-log-dir*))

(defun log-mouse-event (event)
  (let ((path (mouse-log-file)))
    (ensure-csv-header path '("run_id" "model_time" "event"))
    (append-csv-row path (list (ensure-log-run-id) (safe-model-time) event))))

;; Redefines the fucntion_new_tcp.lisp version (same pattern as
;; respond-to-key-press below). The click-mouse signal carries
;; (model position finger); the finger IS the button.
(defun respond-to-click-mouse (model position finger)
  (declare (ignore model position))
  (let ((f (normalize-key-string finger)))
    (cond
      ;; right button = middle finger
      ((string-equal f "middle")
       (log-mouse-event "rightclick")
       (when *tcp-interactions-enabled*
         (run-shell-command "rightclick" '("temp"))
         ;; Live: a context menu just appeared — refresh the visicon so the
         ;; model can find its transient entries. Win11 menus are rebuilt
         ;; again after "Show more options" and each submenu hover; those
         ;; later levels are captured by the matching refresh now added to
         ;; the plain-click branch below.
         (when (fboundp 'update-model-click)
           (update-model-click)))
       (setf *clicking-occurred* T))
      ;; left-button press that starts a drag (HOLD-MOUSE request)
      (*mouse-hold-pending*
       (setf *mouse-hold-pending* nil
             *mouse-dragging* t)
       (log-mouse-event "mousedown")
       (when *tcp-interactions-enabled*
         (run-shell-command "mousedown" '("temp"))))
      ;; ordinary left click
      (t
       (log-mouse-event "click")
       (when *tcp-interactions-enabled*
         (run-shell-command "click" '("temp"))
         ;; Live: a left-click can reveal the NEXT level of a cascading
         ;; context menu (W04: "Show more options" -> classic menu ->
         ;; "Send to" -> "Compressed (zipped) folder" submenu). Refresh the
         ;; visicon so the model can find the newly revealed transient
         ;; entries, exactly as the right-click branch above does. This is
         ;; the plain-click refresh the rightclick-branch comment predicted
         ;; W04 would need. Generic-only (Excel path never loads this file).
         (when (fboundp 'update-model-click)
           (update-model-click)))
       (setf *clicking-occurred* T)))))

;; The extended motor module emits release-mouse after every button
;; action; only the release that ends a drag is delivered (the full
;; click/rightclick was already delivered as one event on the press).
(defun respond-to-release-mouse (model position finger)
  (declare (ignore model position))
  (when (and *mouse-dragging*
             (string-equal (normalize-key-string finger) "index"))
    (setf *mouse-dragging* nil)
    (log-mouse-event "mouseup")
    (when *tcp-interactions-enabled*
      (run-shell-command "mouseup" '("temp")))
    (setf *clicking-occurred* T)))

;;; --- scroll wheel motor style -----------------------------------------

(defparameter *scroll-notches-per-action* 3
  "Wheel notches produced by one Scroll action.")

(defvar *generic-scroll-reveal-features* nil
  "Offline stand-in for content that scrolling brings into view: visicon
features a task file defers until the first scroll executes. A live run
leaves this NIL and relies on the real UIA refresh.")

(defun normalize-scroll-direction (dir)
  (let ((d (string-downcase (string dir))))
    (if (member d '("up" "down") :test #'string-equal)
        d
      (progn
        (model-warning "Unknown scroll direction ~s; defaulting to \"down\"." dir)
        "down"))))

(defun reveal-scroll-visicon-features ()
  (dolist (f *generic-scroll-reveal-features*)
    (add-visicon-features f))
  (setf *generic-scroll-reveal-features* nil)
  t)

(defun scroll-wheel-action (direction &optional last-notch-p)
  "One wheel notch: log it, deliver it to VisiTor, and (offline) reveal
any deferred below-the-fold visicon features. After the LAST notch of a
live scroll, refresh the visicon — scrolling changes what's on screen."
  (let ((dir (normalize-scroll-direction direction)))
    (log-mouse-event (format nil "scroll-~a" dir))
    (when *tcp-interactions-enabled*
      (run-shell-command "scroll" (list dir)))
    (when (and *generic-offline-visicon* *generic-scroll-reveal-features*)
      (reveal-scroll-visicon-features))
    (when (and last-notch-p
               (not *generic-offline-visicon*)
               (fboundp 'update-model-click))
      (update-model-click))
    t))

(defstyle scroll-wheel () hand direction notches)

(defun scroll-notch-count (n)
  (if (and (numberp n) (>= n 1))
      (round n)
    *scroll-notches-per-action*))

(defmethod feat-differences ((s1 scroll-wheel) (s2 scroll-wheel))
  (let ((count 0))
    (unless (eql (hand s1) (hand s2)) (incf count))
    (unless (equalp (direction s1) (direction s2)) (incf count))
    (unless (equalp (notches s1) (notches s2)) (incf count))
    count))

;; First notch registers one burst after initiation; the wheel is flicked
;; once per notch at burst-time intervals thereafter.
;; (Plain slot reads, no bt: lock forms — the single-threaded ACT-R build
;; used for offline validation has no bordeaux-threads package.)
(defmethod compute-exec-time ((mtr-mod motor-module) (self scroll-wheel))
  (+ (init-time mtr-mod) (burst-time mtr-mod)))

(defmethod compute-finish-time ((mtr-mod motor-module) (self scroll-wheel))
  (+ (init-time mtr-mod)
     (* (1+ (scroll-notch-count (notches self))) (burst-time mtr-mod))))

(defmethod queue-output-events ((mtr-mod motor-module) (self scroll-wheel))
  (let ((burst (burst-time mtr-mod))
        (n (scroll-notch-count (notches self))))
    (dotimes (i n)
      (schedule-event-relative (+ (exec-time self) (* i burst))
                               'scroll-wheel-action
                               :params (list (direction self) (= i (1- n)))
                               :module :motor
                               :output 'medium
                               :details (format nil "SCROLL-WHEEL ~a notch ~d of ~d"
                                                (direction self) (1+ i) n)))))

(extend-manual-requests (scroll-wheel hand direction notches) handle-style-request)

;;; ----------------------------------------------------------------------
;;; 3. Typing visual anchor
;;; ----------------------------------------------------------------------

(defparameter *visual-action-verbs* '(goto move select))

(defun subtask-list-symbol (task subtask)
  (read-from-string (concatenate-strings-subtask task subtask)))

(defun subtask-list-if-bound (task subtask)
  (let ((sym (subtask-list-symbol task subtask)))
    (and (boundp sym) (symbol-value sym))))

(defun typing-anchor-label (task subtask subsubtask)
  "Label the model looks at while typing: the target of the most recent
Goto/Move/Select before the current action (same subtask first, then
earlier subtasks), else the current subtask's instruction-panel label,
which is always in the visicon."
  (labels ((scan (steps upto)
             (loop for idx from (min upto (1- (length steps))) downto 0
                   for step = (nth idx steps)
                   when (and (listp step)
                             (member (car step) *visual-action-verbs*
                                     :test #'string-equal)
                             (stringp (cadr step)))
                     do (return (cadr step)))))
    (or (let ((steps (subtask-list-if-bound task subtask)))
          (and steps (scan steps (- subsubtask 2))))
        (loop for sub from (1- subtask) downto 1
              for steps = (subtask-list-if-bound task sub)
              for hit = (and steps (scan steps (1- (length steps))))
              when hit do (return hit))
        (concatenate-strings-subtask task subtask))))

;;; ----------------------------------------------------------------------
;;; Keyboard output monitor — generic-interface version.
;;;
;;; Same contract as respond-to-key-press in fucntion_new_tcp.lisp (which
;;; this REDEFINES), with three changes:
;;;   a. shift + single letter delivers the UPPERCASE letter;
;;;   b. a delivered chord (contains '+') also triggers the screen refresh
;;;      hook, since command chords change the UI state like Enter does;
;;;   c. update-model-click is guarded so offline validation runs do not
;;;      require running_model_v4.lisp.
;;; ----------------------------------------------------------------------

(defun generic-shift-delivered-key (typed shift-pending)
  (let* ((s (string typed))
         (single-alpha (and (= (length s) 1) (alpha-char-p (char s 0)))))
    (cond
      ((and shift-pending single-alpha) (string-upcase s))
      ((listp shift-pending) typed)      ; NIL falls through here unchanged
      (shift-pending (shifted-output-for-key typed))
      (t typed))))

(defun respond-to-key-press (k)
  (let* ((raw-key (extract-keypress-token k))
         (expected (or *keypress-override-expected* raw-key))
         (override-typed *keypress-override-typed*))
    (let* ((now (safe-model-time))
           (sig (normalize-key-string raw-key))
           (duplicate-p (and *last-keypress-signature*
                             *last-keypress-time*
                             (string-equal sig *last-keypress-signature*)
                             (< (abs (- now *last-keypress-time*)) 0.001))))
      (when duplicate-p
        (return-from respond-to-key-press nil))
      (setf *last-keypress-signature* sig
            *last-keypress-time* now))
    (cond
      ((shift-key-name-p raw-key)
       (if override-typed
           (setf *pending-shift-keypress*
                 (list :expected (normalize-key-string expected)
                       :typed (normalize-key-string override-typed)))
           (progn
             (setf *pending-shift-keypress* t)
             (log-keypress-event expected expected expected)))
       nil)
      (t
       (let* ((shift-pending *pending-shift-keypress*)
              (pending-expected (and (listp shift-pending)
                                     (getf shift-pending :expected)))
              (pending-typed (and (listp shift-pending)
                                  (getf shift-pending :typed)))
              (effective-expected (or pending-expected expected))
              (typed (or pending-typed
                         override-typed
                         (inject-typo-if-needed effective-expected)))
              (delivered (cond
                           ((string-equal typed "return") "enter")
                           ((string-equal typed "newline") "enter")
                           ((string-equal typed "delete") "backspace")
                           ((string-equal typed "forward-delete") "delete")
                           (t (generic-shift-delivered-key typed shift-pending))))
              (payload (list delivered)))
         (setf *pending-shift-keypress* nil)
         (clear-keypress-override)
         ;; The keyboard output monitor is the single source of truth for
         ;; intended and delivered keys, which keeps typo generation and
         ;; checking aligned.
         (set-last-typed-keys effective-expected typed)
         (log-keypress-event effective-expected typed delivered)
         (when *tcp-interactions-enabled*
           (run-shell-command "Keypress" payload))
         (when (and (or (string-equal delivered "enter")
                        (key-chord-string-p delivered))
                    (fboundp 'update-model-click))
           (update-model-click)))))))

;; ACT-R output-key monitor entry point: output-key is called with
;; (model key) after a valid keyboard mapping actually produces a key.
(defun respond-to-key-press-monitor (&rest args)
  (let ((key (car (last args))))
    (respond-to-key-press (if (listp key) key (list key)))))

;;; ----------------------------------------------------------------------
;;; 4. Task-file plumbing
;;; ----------------------------------------------------------------------

(defun proclaim-subtask-specials (&optional (max-tasks 30) (max-subtasks 60))
  (loop for task from 1 to max-tasks do
        (loop for sub from 1 to max-subtasks do
              (let ((sym (read-from-string
                          (format nil "SUBTASK~D_~D_LIST" task sub))))
                (proclaim `(special ,sym)))))
  t)

(defun clear-subtask-lists (&optional (max-tasks 30) (max-subtasks 60))
  "Unbind every subtaskN_M_list so a freshly loaded task file never sees
stale lists from a previously loaded task."
  (loop for task from 1 to max-tasks do
        (loop for sub from 1 to max-subtasks do
              (let ((sym (read-from-string
                          (format nil "SUBTASK~D_~D_LIST" task sub))))
                (when (boundp sym) (makunbound sym)))))
  t)

(defun install-instruction-panel ()
  "Add the task/subtask instruction-panel markers for every bound
subtaskN_M_list, using the Excel model's panel layout."
  (dotimes (i *generic-total-tasks*)
    (let ((name (format nil "task~d" (1+ i))))
      (add-visicon-features
       `(screen-x ,*instruction-panel-task-x*
         screen-y ,(+ 290 (* 100 i))
         value ,name text-value ,name type "text" text T))))
  (loop for task from 1 to *generic-total-tasks* do
        (loop for sub from 1 to 60
              for label = (format nil "subtask~d_~d_list" task sub)
              for sym = (read-from-string label)
              while (boundp sym)
              do (add-visicon-features
                  `(screen-x ,*instruction-panel-subtask-x*
                    screen-y ,(+ 290 (* 100 (1- task)) (* 20 (1- sub)))
                    value ,label text-value ,label type "text" text T))))
  t)

(defun install-generic-task-knowledge ()
  "Called by generic_interface_model.lisp after define-model: installs the
task file's declarative chunks, visicon, and goal focus."
  (unless (fboundp 'install-task-chunks)
    (error "No task file loaded: install-task-chunks is undefined. Load a tasks/Wxx_*.lisp file before the model."))
  (funcall 'install-task-chunks)
  (install-instruction-panel)
  (when (and *generic-offline-visicon* (fboundp 'install-task-visicon))
    (funcall 'install-task-visicon))
  (goal-focus-fct 'first-goal)
  t)
