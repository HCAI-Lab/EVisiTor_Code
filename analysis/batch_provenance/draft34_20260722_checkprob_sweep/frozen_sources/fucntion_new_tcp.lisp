(ql:quickload :inferior-shell)

;; Resolve AmirPatterns relative to this file so the tree can live on any drive.
(defvar *directory*
  (namestring (merge-pathnames "AmirPatterns"
                               (make-pathname :name nil :type nil
                                              :defaults (or *load-truename* *load-pathname*)))))
(defparameter *tcp-visitor-host* "127.0.0.1")
(defparameter *tcp-visitor-port* 65432)
(defparameter *tcp-use-uia-output* t)
(defparameter *tcp-uia-json-path* nil)
(defparameter *tcp-debug* t)
(defparameter *tcp-interactions-enabled* t)
(defparameter *batch-quiet-output* nil)
(ql:quickload '(:usocket :cl-json))
(defvar *clicking-occurred* nil)
(defvar *pattern-global* nil)
;; Opt-in task-environment mode used by the 7-21 model: typed text replaces
;; the content of the visual feature that the model attended before typing.
(defvar *reuse-attended-typing-feature* nil)
;; A second opt-in used by the chunk-level checking variant.  In this mode the
;; attended feature's TEXT-VALUE is the complete delivered entry, as it would
;; be in an editable spreadsheet cell, rather than only the latest character.
;; Keeping this separate preserves the older single-character model variants.
(defvar *accumulated-entry-percept* nil)
(defvar *typed-echo-x* 500)
(defvar *typed-echo-y* 500)
(defvar *typed-echo-feature* nil)
(defvar *last-delivered-key* nil)
(defvar *last-expected-delivered-key* nil)

;; Forward declarations keep compile-time style warnings down when these
;; functions are referenced before their definitions later in the file.
(declaim (ftype (function (t) string) normalize-key-string))
(declaim (ftype (function (t) t) sample-motor-typo-key))
(declaim (ftype (function (t t) t) set-last-typed-keys))
(declaim (ftype (function () t) update-model-click))

(defun char-alpha-p (ch)
  (alpha-char-p ch))

(defun tcp-debug-log (format-string &rest args)
  (when *tcp-debug*
    (apply #'format t (concatenate 'string "~&[TCP-DEBUG] " format-string "~%") args)
    (finish-output)))

(defun enable-tcp-debug ()
  (setf *tcp-debug* t)
  *tcp-debug*)

(defun disable-tcp-debug ()
  (setf *tcp-debug* nil)
  *tcp-debug*)

(defun maybe-act-r-output (format-string &rest args)
  (unless *batch-quiet-output*
    (apply #'format t (concatenate 'string "~&" format-string "~%") args)))

(defparameter *model-log-dir*
  (merge-pathnames #P"logs/"
                   (make-pathname :name nil :type nil
                                  :defaults (or *load-truename* *load-pathname*))))

(defparameter *attention-log-file* (merge-pathnames #P"attention_shifts.csv" *model-log-dir*))
(defparameter *keypress-log-file* (merge-pathnames #P"keypresses.csv" *model-log-dir*))
(defparameter *subtask-time-log-file* (merge-pathnames #P"subtask_times.csv" *model-log-dir*))
(defparameter *task-time-log-file* (merge-pathnames #P"task_times.csv" *model-log-dir*))

(defvar *model-log-run-id* nil)
(defvar *subtask-start-times* (make-hash-table :test 'equal))
(defvar *task-start-times* (make-hash-table :test 'equal))

#+sb-thread
(defvar *csv-log-mutex* (sb-thread:make-mutex :name "csv-log-mutex"))

;; Optional label appended to every run id (set by batch harnesses so a run id
;; also carries the condition and seed, e.g. "2026-07-20_14-01-33_cell110_r042_s123456").
;; DEFVAR so per-run model reloads never clobber a harness-assigned label.
(defvar *batch-run-id-label* nil)

(defun make-log-run-id ()
  (multiple-value-bind (sec min hour day month year)
      (decode-universal-time (get-universal-time))
    (let ((stamp (format nil "~4,'0d-~2,'0d-~2,'0d_~2,'0d-~2,'0d-~2,'0d"
                         year month day hour min sec)))
      (if *batch-run-id-label*
          (format nil "~a_~a" stamp *batch-run-id-label*)
        stamp))))

(defun ensure-directory-pathname (pathish)
  (let* ((base (pathname pathish))
         (name (pathname-name base))
         (type (pathname-type base)))
    (if (or name type)
        (make-pathname :name nil :type nil :defaults base)
      base)))

(defun refresh-log-file-paths ()
  (setf *attention-log-file* (merge-pathnames #P"attention_shifts.csv" *model-log-dir*)
        *keypress-log-file* (merge-pathnames #P"keypresses.csv" *model-log-dir*)
        *subtask-time-log-file* (merge-pathnames #P"subtask_times.csv" *model-log-dir*)
        *task-time-log-file* (merge-pathnames #P"task_times.csv" *model-log-dir*))
  *model-log-dir*)

(defun reset-model-log-state ()
  (setf *model-log-run-id* nil)
  (clrhash *subtask-start-times*)
  (clrhash *task-start-times*)
  t)

(defun set-model-log-directory (pathish)
  (setf *model-log-dir* (ensure-directory-pathname pathish))
  (refresh-log-file-paths)
  (reset-model-log-state)
  (ensure-log-files-exist)
  *model-log-dir*)

(defun csv-field (value)
  (let ((s (princ-to-string (or value ""))))
    (if (or (find #\, s)
            (find #\" s)
            (find #\Newline s)
            (find #\Return s))
        (format nil "\"~a\"" (with-output-to-string (out)
                                 (loop for ch across s do
                                       (if (char= ch #\")
                                           (write-string "\"\"" out)
                                         (write-char ch out)))))
      s)))

(defun ensure-csv-header (path header-fields)
  (ensure-directories-exist path)
  (unless (probe-file path)
    (with-open-file (stream path
                            :direction :output
                            :if-exists :supersede
                            :if-does-not-exist :create)
      (format stream "~{~a~^,~}~%" header-fields))))

(defun fallback-log-path (path)
  (make-pathname :name (concatenate 'string (or (pathname-name path) "log") "_fallback")
                 :type (or (pathname-type path) "csv")
                 :defaults path))

(defun %append-csv-row-once (path fields)
  (ensure-directories-exist path)
  (with-open-file (stream path
                          :direction :output
                          :if-exists :append
                          :if-does-not-exist :create)
    (format stream "~{~a~^,~}~%" (mapcar #'csv-field fields))))

(defun append-csv-row (path fields &key (retries 8) (retry-delay 0.02))
  (labels ((attempt (n)
             (handler-case
                 (progn
                   #+sb-thread
                   (sb-thread:with-mutex (*csv-log-mutex*)
                     (%append-csv-row-once path fields))
                   #-sb-thread
                   (%append-csv-row-once path fields)
                   t)
               (file-error (e)
                 (if (< n retries)
                     (progn
                       (sleep (* retry-delay (1+ n)))
                       (attempt (1+ n)))
                   (progn
                     (tcp-debug-log "CSV write failed for ~a after ~a retries: ~a" path retries e)
                     (let ((fallback (fallback-log-path path)))
                       (handler-case
                           (progn
                             #+sb-thread
                             (sb-thread:with-mutex (*csv-log-mutex*)
                               (%append-csv-row-once fallback fields))
                             #-sb-thread
                             (%append-csv-row-once fallback fields)
                             (tcp-debug-log "Wrote log row to fallback file ~a" fallback)
                             t)
                         (error (e2)
                           (tcp-debug-log "Fallback CSV write also failed: ~a" e2)
                           nil)))))))))
    (attempt 0)))

(defun safe-model-time ()
  (or (ignore-errors (mp-time))
      0.0))

(defun ensure-log-files-exist ()
  (ensure-csv-header *attention-log-file*
                     '("run_id" "model_time" "task" "subtask" "location_name" "screen_x" "screen_y" "source"))
  (ensure-csv-header *keypress-log-file*
                     '("run_id" "model_time" "expected_key" "typed_key" "delivered_key"))
  (ensure-csv-header *subtask-time-log-file*
                     '("run_id" "task" "subtask" "start_time" "end_time" "duration"))
  (ensure-csv-header *task-time-log-file*
                     '("run_id" "task" "start_time" "end_time" "duration")))

(defun start-new-model-log-run ()
  (ensure-log-files-exist)
  (setf *model-log-run-id* (make-log-run-id))
  (clrhash *subtask-start-times*)
  (clrhash *task-start-times*)
  *model-log-run-id*)

(defun ensure-log-run-id ()
  (or *model-log-run-id*
      (start-new-model-log-run)))

(defun subtask-timer-key (task subtask)
  (format nil "~a:~a" task subtask))

(defun task-timer-key (task)
  (format nil "~a" task))

(defun mark-subtask-start (task subtask)
  (setf (gethash (subtask-timer-key task subtask) *subtask-start-times*)
        (safe-model-time)))

(defun mark-subtask-complete (task subtask)
  (let* ((key (subtask-timer-key task subtask))
         (start (gethash key *subtask-start-times*))
         (end (safe-model-time))
         (duration (and start (- end start))))
    (append-csv-row *subtask-time-log-file*
                    (list (ensure-log-run-id) task subtask
                          (or start "") end (or duration "")))
    (remhash key *subtask-start-times*)
    duration))

(defun mark-task-start (task)
  (setf (gethash (task-timer-key task) *task-start-times*)
        (safe-model-time)))

(defun mark-task-complete (task)
  (let* ((key (task-timer-key task))
         (start (gethash key *task-start-times*))
         (end (safe-model-time))
         (duration (and start (- end start))))
    (append-csv-row *task-time-log-file*
                    (list (ensure-log-run-id) task
                          (or start "") end (or duration "")))
    (remhash key *task-start-times*)
    duration))

(defun prepare-task-and-subtask-logging (task)
  (when (= task 1)
    (start-new-model-log-run))
  (mark-task-start task)
  (mark-subtask-start task 1)
  t)

(defun log-keypress-event (expected typed delivered)
  (append-csv-row *keypress-log-file*
                  (list (ensure-log-run-id)
                        (safe-model-time)
                        expected typed delivered)))

(defun set-tcp-visitor-endpoint (host &optional (port *tcp-visitor-port*))
  (setf *tcp-visitor-host* host
        *tcp-visitor-port* port)
  (format nil "TCP endpoint set to ~a:~a" *tcp-visitor-host* *tcp-visitor-port*))

(defun detect-wsl-windows-host ()
  (handler-case
      (with-open-file (stream "/etc/resolv.conf" :direction :input)
        (loop for line = (read-line stream nil nil)
              while line
              when (search "nameserver" line :test #'char-equal)
                do (let* ((last-space (position #\Space line :from-end t))
                          (ip (and last-space
                                   (string-trim '(#\Space #\Tab)
                                                (subseq line (1+ last-space))))))
                     (when (and ip (> (length ip) 0))
                       (return ip)))))
    (error () nil)))

(defun set-tcp-endpoint-from-wsl (&optional (port *tcp-visitor-port*))
  (let ((host (detect-wsl-windows-host)))
    (if host
        (set-tcp-visitor-endpoint host port)
      "Could not detect Windows host IP from /etc/resolv.conf")))

(defun enable-uia-output (&optional visicon-json-path)
  (setf *tcp-use-uia-output* t)
  (when visicon-json-path
    (setf *tcp-uia-json-path* visicon-json-path))
  *tcp-use-uia-output*)

(defun disable-uia-output ()
  (setf *tcp-use-uia-output* nil)
  *tcp-use-uia-output*)

(defun enable-tcp-interactions ()
  (setf *tcp-interactions-enabled* t)
  *tcp-interactions-enabled*)

(defun disable-tcp-interactions ()
  (setf *tcp-interactions-enabled* nil)
  *tcp-interactions-enabled*)

(defun normalize-visitor-arg (value)
  (cond
   ((and (listp value) (= (length value) 1)) (normalize-visitor-arg (first value)))
   ((symbolp value) (string-downcase (symbol-name value)))
   (t value)))

(defun normalize-visitor-arglist (arglist)
  (cond
   ((null arglist) nil)
   ((listp arglist) (mapcar #'normalize-visitor-arg arglist))
   (t (list (normalize-visitor-arg arglist)))))

(defun send-tcp-command (payload)
  (tcp-debug-log "Connecting to ~a:~a" *tcp-visitor-host* *tcp-visitor-port*)
  (let ((socket (usocket:socket-connect *tcp-visitor-host* *tcp-visitor-port* :element-type 'character)))
    (unwind-protect
         (let* ((stream (usocket:socket-stream socket))
                (encoded (json:encode-json-to-string payload)))
           (tcp-debug-log "Sending payload: ~s" payload)
           (format stream "~a~%" encoded)
           (force-output stream)
           (let ((response (read-line stream nil "")))
             (tcp-debug-log "Received raw response: ~a" response)
             (if (string= response "")
                 (progn
                   (tcp-debug-log "Empty response from server")
                   nil)
               (handler-case
                   (json:decode-json-from-string response)
                 (error (e)
                   (tcp-debug-log "Failed to decode JSON response: ~a" e)
                   response)))))
      (progn
        (tcp-debug-log "Closing TCP socket")
        (usocket:socket-close socket)))))

(defun run-shell-command (command &optional arglist)
  (let* ((normalized-args (normalize-visitor-arglist arglist))
         (payload
          (cond
           ((string-equal command "whatisonscreen")
            `(("function" . ,command)
              ("kwargs" . ,(append
                              (list (cons "Dir" *directory*)
                                    (cons "arg2" normalized-args)
                                    (cons "use_uia" *tcp-use-uia-output*))
                              (if *tcp-uia-json-path*
                                  (list (cons "visicon_json" *tcp-uia-json-path*))
                                nil)))))
           ((string-equal command "movecursortopattern")
            `(("function" . ,command)
              ("kwargs" . ,(append
                             (list (cons "Dir" *directory*)
                                   (cons "arg2" normalized-args)
                                   (cons "use_uia" *tcp-use-uia-output*))
                             (if *tcp-uia-json-path*
                                 (list (cons "visicon_json" *tcp-uia-json-path*))
                               nil)))))
           ((string-equal command "whereis")
            `(("function" . ,command)
              ("kwargs" . (("Dir" . ,*directory*)
                           ("arg2" . ,normalized-args)))))
           (t
            `(("function" . ,command)
              ("args" . ,normalized-args))))))
      (tcp-debug-log "run-shell-command -> command=~a args=~s" command normalized-args)
      (let ((result (send-tcp-command payload)))
        (tcp-debug-log "run-shell-command <- result=~s" result)
        result)))
(defun check-excel-cell-format (x)
  "Return T only for strict Excel-style cell labels like A1, AA10.
Reject labels such as ROW_1, A_1, A1B, or plain numbers."
  (let* ((input-string (string-trim '(#\Space #\Tab #\Newline #\Return)
                                    (string x)))
         (len (length input-string)))
    (if (<= len 1)
        "nil"
      (let ((split-pos nil))
        ;; Find where trailing digits start.
        (loop for i from 0 below len do
              (when (digit-char-p (char input-string i))
                (setf split-pos i)
                (return)))
        (if (null split-pos)
            "nil"
          (let ((letters (subseq input-string 0 split-pos))
                (digits (subseq input-string split-pos)))
            (if (and (> (length letters) 0)
                     (> (length digits) 0)
                     (every #'alpha-char-p letters)
                     (every #'digit-char-p digits))
                T
              "nil")))))))
(defun breakdown-cell (cell)
  "Break down an Excel cell reference into its letter and number parts.
   Returns a list of the form (LETTER NUMBER)."
  (let* ((input-string (string cell))
         (letter (subseq input-string 0 1))
         (number (subseq input-string 1)))
    (list letter number)))
(
    defun what-is-on-screen (l)
  (tcp-debug-log "what-is-on-screen called with ~s" l)
  (let ((on-screen (if *tcp-interactions-enabled*
                       (run-shell-command "whatisonscreen" l)
                     (list :result "Trace-only mode: screen query suppressed"))))
    (maybe-act-r-output "what is on screen function ~A!!!" on-screen)
    on-screen)
)

(
    defun set-pattern (p)
  (setf *pattern-global* p)
  (maybe-act-r-output " Now we have ~s !!!!" *pattern-global*)
)
(defun move-attention-output-creator (x)
  (format nil "moving attention to ~A" x))

(
    defun respond-to-move-cursor ( z)
  (maybe-act-r-output "move-cursor to ~A!!!" z)
  (tcp-debug-log "respond-to-move-cursor target ~s" z)
  (let ((result-from-java (if *tcp-interactions-enabled*
                              (run-shell-command "movecursortopattern" z)
                            (list :result "Trace-only mode: cursor move suppressed"))))
    (tcp-debug-log "respond-to-move-cursor result ~s" result-from-java)
    result-from-java)
 )

(defun respond-to-move-cursor-xy (x y)
  (maybe-act-r-output "move-cursor to XY (~A, ~A)!!!" x y)
  (tcp-debug-log "respond-to-move-cursor-xy target (~s, ~s)" x y)
  (let ((result-from-java (if *tcp-interactions-enabled*
                              (run-shell-command "movecursorto" (list x y))
                            (list :result "Trace-only mode: cursor XY move suppressed"))))
    (tcp-debug-log "respond-to-move-cursor-xy result ~s" result-from-java)
    result-from-java))

(defun respond-to-move-cursor-monitor (model device loc)
  (declare (ignore model device))
  (let* ((x (and (listp loc) (first loc)))
         (y (and (listp loc) (second loc))))
    (if (and x y)
        (progn
          (record-typed-echo-location x y)
          (respond-to-move-cursor-xy x y))
      (progn
        (tcp-debug-log "respond-to-move-cursor-monitor received invalid loc ~s" loc)
        nil))))

(defun infer-current-visual-location-label ()
  (let ((loc (ignore-errors (buffer-read 'visual-location))))
    (when loc
      (or (location-name-from-chunk loc)
          (and (symbolp loc) (symbol-name loc))))))

(defun infer-current-task-subtask ()
  (let* ((goal (ignore-errors (buffer-read 'goal)))
         (task (and goal (chunk-slot-safe goal 'task)))
         (subtask (and goal (chunk-slot-safe goal 'subtask))))
    (values task subtask)))

(defun append-attention-shift-row (location-name x y source &optional task subtask)
  (multiple-value-bind (goal-task goal-subtask)
      (infer-current-task-subtask)
    (append-csv-row *attention-log-file*
                    (list (ensure-log-run-id)
                          (safe-model-time)
                          (or task goal-task "")
                          (or subtask goal-subtask "")
                          (or location-name "")
                          x
                          y
                          (or source "")))))

(defun respond-to-eye-move-xy (x y &optional location-name source task subtask)
  (let* ((resolved-name (or location-name (infer-current-visual-location-label) ""))
         (resolved-source (or source "direct-eye-move")))
    (append-attention-shift-row resolved-name x y resolved-source task subtask))
  (tcp-debug-log "respond-to-eye-move-xy target (~s, ~s)" x y)
  (let ((result-from-java (if *tcp-interactions-enabled*
                              (run-shell-command "moveeyeto" (list x y))
                            (list :result "Trace-only mode: eye move suppressed"))))
    (tcp-debug-log "respond-to-eye-move-xy result ~s" result-from-java)
    result-from-java))

(defun move-attention-location->xy (location)
  (when location
    (handler-case
        (let* ((x (chunk-slot-value-fct location 'screen-x))
               (y (chunk-slot-value-fct location 'screen-y)))
          (if (and (numberp x) (numberp y))
              (list x y)
            (let ((screen-pos (chunk-slot-value-fct location 'screen-pos)))
              (when screen-pos
                (let ((sx (chunk-slot-value-fct screen-pos 'screen-x))
                      (sy (chunk-slot-value-fct screen-pos 'screen-y)))
                  (when (and (numberp sx) (numberp sy))
                    (list sx sy)))))))
      (error () nil))))

(defun chunk-slot-safe (chunk slot)
  (handler-case
      (chunk-slot-value-fct chunk slot)
    (error () nil)))

(defun location-name-from-chunk (chunk)
  (let ((text-value (chunk-slot-safe chunk 'text-value))
        (value (chunk-slot-safe chunk 'value))
        (name (chunk-slot-safe chunk 'name)))
    (cond
      (text-value text-value)
      (value value)
      (name name)
      (t nil))))

(defun normalize-chunk-designator (value)
  (cond
   ((null value) nil)
   ((symbolp value) value)
   ((stringp value)
    (handler-case
        (read-from-string value)
      (error () nil)))
   (t nil)))

(defun maybe-xy-from-value (value)
  (or (move-attention-location->xy (normalize-chunk-designator value))
      (when (and (listp value)
                 (>= (length value) 2)
                 (numberp (first value))
                 (numberp (second value)))
        (list (first value) (second value)))))

(defun log-attention-shift-explicit (location &optional source task subtask)
  (let* ((xy (maybe-xy-from-value location))
         (chunk (normalize-chunk-designator location))
         (label (or (and chunk (location-name-from-chunk chunk))
                    (and (symbolp chunk) (symbol-name chunk))
                    (and (symbolp location) (symbol-name location))
                    ""))
         (src (or source "production-eval")))
    (when xy
  (append-attention-shift-row label (first xy) (second xy) src task subtask))
    t))

(defun extract-location-from-move-attention-args (args)
  (or
   ;; Event style payload: (:location <chunk> ...)
   (when (and args (listp (first args)) (keywordp (first (first args))))
     (maybe-xy-from-value (getf (first args) :location)))
   ;; If a plist was passed directly.
   (when (and args (keywordp (first args)))
     (maybe-xy-from-value (getf args :location)))
   ;; Robust fallback: scan all args and use the first one that resolves to XY.
   (loop for a in args
         for xy = (maybe-xy-from-value a)
         when xy do (return xy))
   ;; Final fallback: first 2 args are direct numbers.
   (when (and (>= (length args) 2)
              (numberp (first args))
              (numberp (second args)))
     (list (first args) (second args)))))

(defun extract-location-designator-from-move-attention-args (args)
  (or
   (when (and args (listp (first args)) (keywordp (first (first args))))
     (normalize-chunk-designator (getf (first args) :location)))
   (when (and args (keywordp (first args)))
     (normalize-chunk-designator (getf args :location)))
   (loop for a in args
         for chunk = (normalize-chunk-designator a)
         when (and chunk (move-attention-location->xy chunk)) do (return chunk))))

(defun log-attention-shift-event (location-designator xy args)
  (let* ((label (or (and location-designator
                         (location-name-from-chunk location-designator))
                    (and location-designator
                         (symbolp location-designator)
                         (symbol-name location-designator))
                    ""))
         (x (if xy (first xy) ""))
         (y (if xy (second xy) "")))
    (append-attention-shift-row label x y (princ-to-string args))))

(defun respond-to-move-attention-monitor (&rest args)
  (let* ((location-designator (extract-location-designator-from-move-attention-args args))
      (location-name (or (and location-designator
               (location-name-from-chunk location-designator))
             (and location-designator
               (symbolp location-designator)
               (symbol-name location-designator))
             ""))
         (xy (or (and location-designator
                      (move-attention-location->xy location-designator))
                 (extract-location-from-move-attention-args args))))
    (if xy
     (progn
       ;; When visual attention moves to the same place as the cursor, retain
       ;; the underlying visicon feature as the editable display object.  A
       ;; keypress will change that feature, allowing ACT-R's vision module to
       ;; re-encode the already-attended object in the normal way.
       (when (and *reuse-attended-typing-feature*
                  location-designator
                  (numberp *typed-echo-x*)
                  (numberp *typed-echo-y*)
                  (< (abs (- (first xy) *typed-echo-x*)) 0.5)
                  (< (abs (- (second xy) *typed-echo-y*)) 0.5))
         (let ((feature (ignore-errors
                          (chunk-visicon-entry location-designator))))
           (when feature
             (setf *typed-echo-feature* feature))))
       (respond-to-eye-move-xy (first xy) (second xy)
                location-name
                "move-attention-monitor"))
       (progn
        (tcp-debug-log "respond-to-move-attention-monitor could not resolve location from args ~s" args)
        nil))))

(
    defun respond-to-where-is ( z)
  (maybe-act-r-output "move-cursor to ~A!!!" z)
  (let ((result-from-java (if *tcp-interactions-enabled*
                              (run-shell-command "whereis" z)
                            (list :result "Trace-only mode: whereis suppressed"))))
    result-from-java)
 )

;; Per-keystroke typo injection rates.  *target-keypress-typo-rate* drives the
;; formula-typing path (checked in should-inject-typo-p at key delivery);
;; *word-keypress-typo-rate* drives the actual-word path
;; (choose-key-with-typo-rate in the model file) and falls back to the target
;; rate when NIL.  The standalone target rate defaults to 0.2; the ablation
;; harness can still override both rates for controlled runs.
(defparameter *target-keypress-typo-rate* 0.2)
(defparameter *word-keypress-typo-rate* nil)

(defparameter *non-typo-keys*
  '("enter" "return" "backspace" "tab" "escape" "esc"
    "shift" "ctrl" "control" "alt" "command"
    "left" "right" "up" "down" "home" "end" "delete"))

;; QWERTY-adjacent substitutions for every typeable key class.  Letters are
;; included so formula characters like the c/b in "=(C7*B13)" can be mistyped
;; too — the human keystroke data shows letters/digits are corrected at least
;; as often as symbols.
(defparameter *fallback-typo-map*
  '(("0" . "9") ("1" . "2") ("2" . "3") ("3" . "4") ("4" . "5")
    ("5" . "6") ("6" . "7") ("7" . "8") ("8" . "9") ("9" . "0")
    ("=" . "-") ("-" . "=") ("/" . ".") ("*" . "/")
    ("(" . ")") (")" . "(") (":" . ";") (";" . ":")
    ("." . "/") ("," . ".")
    ("a" . "s") ("b" . "n") ("c" . "v") ("d" . "f") ("e" . "r")
    ("f" . "g") ("g" . "h") ("h" . "j") ("i" . "o") ("j" . "k")
    ("k" . "l") ("l" . ";") ("m" . ",") ("n" . "m") ("o" . "p")
    ("p" . "[") ("q" . "w") ("r" . "t") ("s" . "d") ("t" . "y")
    ("u" . "i") ("v" . "b") ("w" . "e") ("x" . "c") ("y" . "u")
    ("z" . "x")))

(defparameter *pending-shift-keypress* nil)
(defparameter *keypress-override-expected* nil)
(defparameter *keypress-override-typed* nil)

(defvar *last-keypress-signature* nil)
(defvar *last-keypress-time* nil)

(defparameter *shift-output-map*
  '(("1" . "!") ("2" . "@") ("3" . "#") ("4" . "$") ("5" . "%")
    ("6" . "^") ("7" . "&") ("8" . "*") ("9" . "(") ("0" . ")")
    ("-" . "_") ("=" . "+") ("[" . "{") ("]" . "}") ("\\" . "|")
    (";" . ":") ("'" . "\"") ("," . "<") ("." . ">") ("/" . "?")
    ("`" . "~")))

(defun shift-key-name-p (key)
  (member (normalize-key-string key)
          '("shift" "left-shift" "right-shift")
          :test #'string-equal))

(defun clear-pending-shift-keypress ()
  (setf *pending-shift-keypress* nil))

(defun set-keypress-override (expected typed)
  (setf *keypress-override-expected* (normalize-key-string expected)
        *keypress-override-typed* (normalize-key-string typed))
  *keypress-override-typed*)

(defun clear-keypress-override ()
  (setf *keypress-override-expected* nil
        *keypress-override-typed* nil)
  nil)

(defun shifted-output-for-key (key)
  (let* ((k (normalize-key-string key))
         (pair (assoc k *shift-output-map* :test #'string-equal)))
    (if pair (cdr pair) k)))

(defun extract-keypress-token (k)
  (cond
   ((and (listp k) (>= (length k) 1)) (first k))
   (t k)))

(defun motor-typo-rate-for-current-entry ()
  ;; Error generation belongs to the keyboard/task interface, not to a
  ;; production which can then inspect the sampled key.  Select the calibrated
  ;; word rate only from the public goal type; formulas use the shared rate.
  (let* ((goal (ignore-errors (buffer-read 'goal)))
         (entry-type (and goal (chunk-slot-safe goal 'type))))
    (if (and entry-type
             (string-equal (princ-to-string entry-type) "actual-word")
             (numberp *word-keypress-typo-rate*))
        *word-keypress-typo-rate*
      *target-keypress-typo-rate*)))

(defun should-inject-typo-p (key)
  (let ((k (normalize-key-string key)))
    (and (> (length k) 0)
         (not (member k *non-typo-keys* :test #'string-equal))
         (< (random 1.0) (motor-typo-rate-for-current-entry)))))

(defun fallback-typo-key (expected)
  (let* ((k (normalize-key-string expected))
         (pair (assoc k *fallback-typo-map* :test #'string-equal)))
    (if pair (cdr pair) k)))

(defun inject-typo-if-needed (expected)
  (let ((e (normalize-key-string expected)))
    (if (should-inject-typo-p e)
        (let ((picked (sample-motor-typo-key e)))
          (if (string-equal picked e)
              (fallback-typo-key e)
            picked))
      e)))

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
                           ((listp shift-pending)
                            typed)
                           (shift-pending
                            (shifted-output-for-key typed))
                           (t typed)))
              ;; What WOULD have appeared on screen had the press been
              ;; error-free: same delivery mapping applied to the expected key.
              (expected-delivered (cond
                                    ((string-equal effective-expected "return") "enter")
                                    ((string-equal effective-expected "newline") "enter")
                                    ((string-equal effective-expected "delete") "backspace")
                                    ((listp shift-pending) effective-expected)
                                    (shift-pending (shifted-output-for-key effective-expected))
                                    (t effective-expected)))
              (payload (list delivered)))
         (setf *pending-shift-keypress* nil)
         (clear-keypress-override)
         ;; The keyboard output monitor is the single source of truth for
         ;; intended and delivered keys, which keeps typo generation and
         ;; checking aligned.
         (set-last-typed-keys effective-expected typed)
         (setf *last-delivered-key* (normalize-key-string delivered)
               *last-expected-delivered-key* (normalize-key-string expected-delivered))
         ;; Older variants draw once per delivered formula keystroke.  The
         ;; accumulated-entry variant draws at formula-token boundaries in
         ;; the model instead, so do not consume a second random value here.
         (when (and (visual-error-checking-p)
                    (not *accumulated-entry-percept*))
           (draw-formula-visual-check))
         ;; Entry tracking is keyboard/display bookkeeping.  In accumulated
         ;; mode it supplies the characters rendered in the editable field's
         ;; TEXT-VALUE; productions never consult these lists for a verdict.
         (entry-tracking-note-key delivered expected-delivered)
         ;; Keep the on-screen typed-text echo current so checking productions
         ;; can attend it.  Enter refreshes the whole visicon below, which
         ;; deletes the feature.  In accumulated-entry mode backspace must also
         ;; update the display, after ENTRY-TRACKING-NOTE-KEY has removed the
         ;; last character.
         ;; The 7-21 accumulated-entry model uses this editable-field percept
         ;; as the visual object that remains under attention while formula
         ;; typing advances.  Keep that real display state current even in a
         ;; no-check ablation; otherwise clearing the visual buffer after a key
         ;; leaves formula typing with no percept to re-encode and it stalls.
         ;; Older typed-echo variants still create/update an echo only while
         ;; visual checking is active.
         (if (string-equal delivered "enter")
             (setf *typed-echo-feature* nil)
           (when (and (or (visual-error-checking-p)
                          (and *reuse-attended-typing-feature*
                               *accumulated-entry-percept*))
                      (or (and *reuse-attended-typing-feature*
                               *accumulated-entry-percept*
                               (string-equal (normalize-key-string delivered)
                                             "backspace"))
                          (not (member (normalize-key-string delivered)
                                       '("backspace" "delete" "tab" "escape" "esc")
                                       :test #'string-equal))))
             (update-typed-echo-feature delivered)))
         (log-keypress-event effective-expected typed delivered)
         (when *tcp-interactions-enabled*
           (run-shell-command "Keypress" payload))
         (when (string-equal delivered "enter")
           (update-model-click)))))))

(defparameter *last-expected-key* nil)
(defparameter *last-typed-key* nil)

(defparameter *motor-model-path*
  (namestring
   (merge-pathnames #P"../MSR Spelling Correction Data/motor_model.json"
                    (make-pathname :name nil :type nil
                                   :defaults (or *load-truename* *load-pathname*)))))

(defparameter *motor-error-conditional-probabilities* (make-hash-table :test 'equal))
(defparameter *motor-error-rate* 0.0)

(defun normalize-key-string (x)
  (cond
   ((null x) "")
   ((stringp x) (string-downcase x))
   ((characterp x) (string-downcase (string x)))
   ((symbolp x) (string-downcase (symbol-name x)))
   ((and (listp x) (= (length x) 1)) (normalize-key-string (first x)))
   (t (string-downcase (princ-to-string x)))))

(defun choose-weighted-key (pairs)
  (let ((r (random 1.0))
        (acc 0.0)
        (choice nil))
    (dolist (pair pairs)
      (let ((k (car pair))
            (p (float (cdr pair) 1.0)))
        (setf acc (+ acc p))
        (when (and (null choice) (<= r acc))
          (setf choice k))))
    (or choice (and pairs (car (car (last pairs)))))))

(defun load-motor-error-model (&optional (path *motor-model-path*))
  (when (probe-file path)
    (with-open-file (stream path :direction :input)
      (let* ((data (json:decode-json stream))
             (rate (cdr (or (assoc :motor_error_rate data)
                            (assoc :|motor_error_rate| data)
                            (assoc "motor_error_rate" data :test #'equal))))
             (conditionals (cdr (or (assoc :conditional_probabilities data)
                                    (assoc :|conditional_probabilities| data)
                                    (assoc "conditional_probabilities" data :test #'equal)))))
        (setf *motor-error-rate* (or rate 0.0))
        (clrhash *motor-error-conditional-probabilities*)
        (dolist (entry conditionals)
          (let* ((intended (normalize-key-string (car entry)))
                 (neighbors (cdr entry))
                 (pairs nil))
            (dolist (n neighbors)
              (push (cons (normalize-key-string (car n)) (cdr n)) pairs))
            (setf (gethash intended *motor-error-conditional-probabilities*)
                  (nreverse pairs))))))
    t))

(defun sample-motor-typo-key (expected)
  (let* ((normalized (normalize-key-string expected))
         (pairs (gethash normalized *motor-error-conditional-probabilities*))
         (picked (and pairs (choose-weighted-key pairs))))
    (or picked normalized)))

(defun set-last-typed-keys (expected typed)
  (setf *last-expected-key* (normalize-key-string expected)
        *last-typed-key* (normalize-key-string typed))
  *last-typed-key*)

(load-motor-error-model)

;; --- Typed-text echo ---------------------------------------------------------
;; A single visicon feature that shows the most recent character delivered to
;; the screen, placed at the typing location (the cell last clicked).  Error
;; checking shifts visual attention to this feature and encodes its text
;; before deciding whether the typed and intended characters differ, instead
;; of consulting the keypress log directly.
(defparameter *typed-echo-x* 500)
(defparameter *typed-echo-y* 500)
;; Offset the echo from the exact cell coordinates so productions that request
;; a location by exact remembered SCREEN-X/SCREEN-Y never match the echo.
(defparameter *typed-echo-y-offset* 9)
(defvar *typed-echo-feature* nil)
(defvar *typed-echo-failures* 0)
(defparameter *last-delivered-key* nil)
(defparameter *last-expected-delivered-key* nil)

;; Master switch for the perceptual checking chain.  The correction-checking
;; ablation turns this off so the disabled variants neither look nor check.
;; 2026-07-18: default NIL — the perceptual chain (attend the typed-text echo,
;; encode, compare) raised Full-Realistic completion time to 760.6 s (+6.3%
;; vs human 715.4) versus 710.1 s (-0.7%) for the instant check, so the paper
;; keeps the instant-check model.  Set to T to re-enable the perceptual
;; mechanism (see Spreadsheet/Perceptual_Checking_Report_2026-07-18.md).
;; *visual-error-checking-default* is what ENABLE-SPREADSHEET-CORRECTION-
;; CHECKING restores; keep both in sync when re-enabling.
(defparameter *visual-error-checking-default* nil)
(defparameter *visual-error-checking-enabled* *visual-error-checking-default*)

(defun visual-error-checking-p ()
  (and *visual-error-checking-enabled* t))

;; --- Quick (no-reshift) perceptual checks (2026-07-21) -----------------------
;; While the model is attending the typed-text echo, every keystroke's echo
;; update is a change to the attended object, and the vision module re-encodes
;; it automatically (case [3] of UPDATE-ATTENDED-LOC in
;; actr7.x/core-modules/vision.lisp): the fresh percept arrives in the =visual
;; buffer with no find-location/move-attention chain, and the module is busy
;; from the instant of the change, so a production that waits for ?visual free
;; can never harvest the pre-keystroke text.  The -quick verify productions in
;; the model harvest that percept, recognizing it BY ITS CONTENT (the =visual
;; chunk carries type "typed-echo") -- all of the model's knowledge about
;; where its attention is lives in its own buffers, never in Lisp state.  The
;; full attend chain remains for checks where no echo percept is in hand
;; (first check after attention was elsewhere); the two paths compete at the
;; same goal state and the -quick variants win on utility when both match, so
;; a missing percept can never deadlock a run.
;; *quick-visual-check-enabled* is an ablation/A-B harness switch like the
;; other mechanism toggles: NIL restores the 2026-07-20 behavior exactly
;; (every check pays the full attend chain).  The counter is pure logging.
(defvar *quick-visual-check-count* 0)
(defvar *quick-visual-check-enabled* t)

(defun quick-visual-check-p ()
  (and *quick-visual-check-enabled* t))

(defun note-quick-visual-check (&optional label)
  (declare (ignore label))
  (incf *quick-visual-check-count*)
  t)

;; --- Formula-path visual check rate ------------------------------------------
;; Probability that a formula / learned-formula keystroke is verified through
;; the overt perceptual chain (attend the typed-echo, encode, compare) rather
;; than the instant TYPE-CHECK fallback.  The draw happens ONCE per delivered
;; keystroke, inside RESPOND-TO-KEY-PRESS, and is stashed here: !eval! LHS
;; guards are re-evaluated on every conflict-resolution cycle, so the guards
;; must read a stashed value, never (random ...) directly.
;;   1.0 -> perceptual check on every formula keystroke (2026-07-17 behavior)
;;   0.0 -> instant check on every formula keystroke (baseline timing;
;;          corrections identical at every rate, only the number of overt
;;          attention shifts changes)
;; The word path keeps its own independent knob
;; (*actual-word-immediate-check-probability*, default 0.85).
;; DEFVARs so per-run reloads never clobber a value set by a sweep harness
;; (this file is loaded once per sbcl session anyway, unlike the model file).
(defvar *formula-visual-check-probability* 1.0)
(defvar *formula-visual-check-now* t)

;; --- Practice-based formula learning (2026-07-21) ----------------------------
;; Humans get faster across the repeated formula rows of Tasks 7 and 9 (10
;; near-identical rows each); the July 20 model re-reads the instruction on
;; every row and shows a flat per-row time.  These switches activate the
;; model's existing (previously dormant) learned-formula pathway:
;;   *formula-practice-learning-enabled*   after a formula PATTERN has been
;;       typed *learned-formula-practice-threshold* times (default 2), later
;;       rows of the same pattern are typed from memory (no per-token
;;       instruction look-backs).  Consulted by FORMULA-TYPING-STRATEGY.
;;   *formula-practice-extended-patterns*  also register the Task 3/5 row
;;       patterns (=(Cx*B13)/100 and =(Bx*100)/B13) as learnable, not just
;;       the Task 7/9 patterns (len-cell, cell-times-cell).
;;   *formula-practice-check-probability*  when a number, practiced patterns
;;       use this per-keystroke visual check rate instead of
;;       *formula-visual-check-probability* (checking automaticity).
;; All default to off/nil so every published configuration is unchanged.
;; DEFVARs in this once-per-session file so per-run model reloads never
;; clobber a harness-set value.
(defvar *formula-practice-learning-enabled* nil)
(defvar *formula-practice-extended-patterns* nil)
(defvar *formula-practice-check-probability* nil)
(defvar *current-formula-word* nil)

(defun formula-practice-note-current-word (word)
  (setf *current-formula-word* (and word (string word))))

(defun formula-current-check-probability ()
  (if (and (numberp *formula-practice-check-probability*)
           *formula-practice-learning-enabled*
           *current-formula-word*
           (fboundp 'learned-formula-pattern-ready-p)
           (ignore-errors (learned-formula-pattern-ready-p *current-formula-word*)))
      *formula-practice-check-probability*
      *formula-visual-check-probability*))

(defun draw-formula-visual-check ()
  (setf *formula-visual-check-now*
        (< (random 1.0) (formula-current-check-probability))))

(defun formula-visual-check-now-p ()
  ;; True only when the perceptual chain is globally enabled AND this
  ;; keystroke's draw chose the overt check.  Its exact complement guards the
  ;; -direct productions, so exactly one of the two paths is eligible in
  ;; every verify phase.
  (and (visual-error-checking-p) *formula-visual-check-now* t))

(defun formula-skip-verdict ()
  ;; Verdict for the -direct verify productions.  With the perceptual chain
  ;; ON, a keystroke whose draw skipped the overt check is NOT verified at
  ;; all — an uncaught typo stays on screen until the guaranteed pre-Enter
  ;; final check (see formula-final-verdict).  With the chain OFF this is
  ;; the paper's instant check, so ablation variants are unchanged.
  (if (visual-error-checking-p) "true" (type-check)))

;; --- Formula-entry tracking for the guaranteed pre-Enter check ---------------
;; Ground truth of what the current cell entry looks like (delivered) versus
;; what the model meant to type (expected-delivered), maintained by the
;; keyboard output monitor: content keys push a pair, backspace pops one,
;; Enter resets.  This is background bookkeeping exactly like the word path's
;; maybe-store-delayed-error-position machinery — the overt cost the model
;; pays is the attention shift of the final check plus the repair keystrokes.
(defvar *formula-entry-delivered* nil)   ; reversed (most recent first)
(defvar *formula-entry-expected* nil)    ; reversed, same length
(defvar *formula-repair-target* nil)     ; snapshot, typing order

;; Diagnostic counter: number of times the FORMULA-FINAL-CHECK-DIRECT escape
;; hatch fired (a final check that bypassed the overt attend/encode chain).
;; With perceptual checking enabled this must stay 0 for a clean run; with
;; checking disabled it counts the instant final verdicts.  Reset per run by
;; APPLY-SPREADSHEET-FACTORIAL.
(defvar *formula-final-direct-count* 0)

(defun note-formula-final-direct-check ()
  (incf *formula-final-direct-count*))

(defparameter *entry-tracking-control-keys*
  '("enter" "return" "newline" "backspace" "delete" "tab" "escape" "esc"
    "shift" "ctrl" "control" "alt" "command"
    "left" "right" "up" "down" "home" "end"))

(defun entry-tracking-note-key (delivered expected-delivered)
  (let ((d (normalize-key-string delivered))
        (e (normalize-key-string expected-delivered)))
    (cond
      ((string-equal d "enter")
       (setf *formula-entry-delivered* nil
             *formula-entry-expected* nil
             *formula-repair-target* nil))
      ((string-equal d "backspace")
       (pop *formula-entry-delivered*)
       (pop *formula-entry-expected*))
      ((member d *entry-tracking-control-keys* :test #'string-equal)
       nil)
      (t
       (push d *formula-entry-delivered*)
       (push e *formula-entry-expected*)))))

(defun entry-tracking-delivered-string ()
  "Return the current delivered entry in screen order."
  (format nil "~{~a~}" (reverse *formula-entry-delivered*)))

(defun formula-entry-clean-p ()
  (equal *formula-entry-delivered* *formula-entry-expected*))

(defun formula-final-verdict (&optional seen)
  ;; Verdict of the always-run pre-Enter check.  The overt act is reading the
  ;; typed text (the attention shift to the echo delivers SEEN, the last
  ;; character); the verdict itself compares the tracked entry, mirroring how
  ;; the word path realizes stored delayed errors at its final-char check.
  (declare (ignore seen))
  (if (formula-entry-clean-p)
      (progn (setf *formula-repair-target* nil) "true")
    (progn
      (setf *formula-repair-target* (reverse *formula-entry-expected*))
      "false")))

(defun formula-repair-action ()
  ;; "delete" until the on-screen entry is a clean prefix of the repair
  ;; target, then "type" the missing tail, then "done".  Recomputed from the
  ;; live tracking state after every keystroke, so retype typos (the repair
  ;; keys go through the same 3.4% injection) simply extend the repair.
  (let* ((delivered (reverse *formula-entry-delivered*))
         (target *formula-repair-target*)
         (nd (length delivered))
         (nt (length target))
         (mm (mismatch delivered target :test #'string-equal)))
    (cond ((null target) "done")
          ((null mm) (setf *formula-repair-target* nil) "done")
          ((< mm nd) "delete")
          ((< nd nt) "type")
          (t "delete"))))

(defun formula-repair-next-char ()
  (nth (length *formula-entry-delivered*) *formula-repair-target*))

(defun formula-repair-next-char-shifted-p ()
  (let ((ch (formula-repair-next-char)))
    (and ch
         (fboundp 'shifted-formula-base-key)
         (boundp '*no-shift-base-key*)
         (not (string-equal (shifted-formula-base-key ch)
                            (symbol-value '*no-shift-base-key*))))))

(defun formula-repair-next-char-base ()
  (shifted-formula-base-key (formula-repair-next-char)))

(defun reset-formula-entry-tracking ()
  (setf *formula-entry-delivered* nil
        *formula-entry-expected* nil
        *formula-repair-target* nil
        *formula-visual-check-now* t))

(defun reset-perceptual-typing-environment ()
  "Clear keyboard/display bookkeeping which must not leak across model runs."
  (reset-formula-entry-tracking)
  (clear-pending-shift-keypress)
  (clear-keypress-override)
  (setf *typed-echo-feature* nil
        *typed-echo-failures* 0
        *last-delivered-key* nil
        *last-expected-delivered-key* nil
        *last-expected-key* nil
        *last-typed-key* nil
        *last-keypress-signature* nil
        *last-keypress-time* nil
        *quick-visual-check-count* 0
        *formula-final-direct-count* 0
        *current-formula-word* nil)
  t)

(defun configure-perceptual-typing-environment
    (&key (reuse-attended-feature nil)
          (accumulated-entry-percept nil)
          (typed-echo-offset 9)
          (visual-checking-default nil)
          (visual-checking-enabled visual-checking-default))
  "Install a complete variant configuration and clear per-run typing state.

Every model variant calls this explicitly.  That makes loading one model after
another in the same Lisp session deterministic instead of inheriting switches
left behind by the previously loaded variant.  Typo probabilities are run
parameters and are intentionally not reset here."
  (setf *reuse-attended-typing-feature* reuse-attended-feature
        *accumulated-entry-percept* accumulated-entry-percept
        *typed-echo-y-offset* typed-echo-offset
        *visual-error-checking-default* visual-checking-default
        *visual-error-checking-enabled* visual-checking-enabled)
  (reset-perceptual-typing-environment))

(defun record-typed-echo-location (x y)
  (when (and (numberp x) (numberp y))
    (setf *typed-echo-x* x
          *typed-echo-y* y)))

(defun currently-attended-visicon-feature ()
  "Return the visicon feature encoded in the visual buffer, if any."
  (when *reuse-attended-typing-feature*
    (let ((visual-object
           (or (ignore-errors (buffer-read 'visual))
               ;; A typing production deliberately clears the buffer so its
               ;; following check cannot inspect stale pre-keypress content.
               ;; Clearing the buffer does not move visual attention, so the
               ;; vision module still records the attended object here.
               (ignore-errors (currently-attended (get-module :vision))))))
      (and visual-object
           (ignore-errors (chunk-visicon-entry visual-object))))))

(defun update-typed-echo-feature (delivered)
  (handler-case
      (let ((val (normalize-key-string delivered))
            (text-val (if (and *reuse-attended-typing-feature*
                               *accumulated-entry-percept*)
                          (entry-tracking-delivered-string)
                        (normalize-key-string delivered)))
            (ey (+ *typed-echo-y* *typed-echo-y-offset*)))
        ;; In the 7-21 model the editable display is the object which is
        ;; already encoded in the visual buffer.  Resolving it here is task
        ;; environment bookkeeping, analogous to updating a GUI text field;
        ;; attention and the resulting re-encoding remain vision-module events.
        (when *reuse-attended-typing-feature*
          (let ((attended-feature (currently-attended-visicon-feature)))
            (when attended-feature
              (setf *typed-echo-feature* attended-feature))))
        (when (and *typed-echo-feature*
                   (null (ignore-errors
                           (modify-visicon-features
                            (if *reuse-attended-typing-feature*
                                ;; Reuse mode: the typed text appears where
                                ;; the model is already looking.  Never
                                ;; relocate the attended feature -- moving it
                                ;; to the recorded cursor position teleports
                                ;; it away from the attended location when
                                ;; the two differ, so the automatic re-encode
                                ;; finds some OTHER feature there and every
                                ;; verification fails (2026-07-21 runaway
                                ;; =/delete loop).
                                 (list *typed-echo-feature*
                                       'value val
                                      'text-value text-val)
                               (list *typed-echo-feature*
                                     'value val
                                    'text-value text-val
                                     'screen-x *typed-echo-x*
                                     'screen-y ey))))))
          (setf *typed-echo-feature* nil))
        (unless *typed-echo-feature*
          (let ((ids (ignore-errors
                       (add-visicon-features
                        `(screen-x ,*typed-echo-x* screen-y ,ey
                          height 18 width 24 type "typed-echo"
                          value ,val text-value ,text-val)))))
            (setf *typed-echo-feature* (if (listp ids) (first ids) ids)))))
    (error () (setf *typed-echo-feature* nil)))
  *typed-echo-feature*)

(defun ensure-typed-echo-feature ()
  ;; Recovery path used when a checking production finds no echo feature.
  ;; After repeated failures the visual chain disables itself so a run can
  ;; never deadlock waiting for a feature that cannot be created.
  (if *last-delivered-key*
      (progn
        (update-typed-echo-feature *last-delivered-key*)
        (if *typed-echo-feature*
            (setf *typed-echo-failures* 0)
          (when (> (incf *typed-echo-failures*) 3)
            (setf *visual-error-checking-enabled* nil)))
        t)
    (progn
      (when (> (incf *typed-echo-failures*) 3)
        (setf *visual-error-checking-enabled* nil))
      t)))

(defun check-string (x)
  (if (and (char-alpha-p (char x 0))
           (every #'digit-char-p (subseq x 1)))
      "cell"
      "text"))

;
;(defun type-check (key-string-temp)
;  (setf key-string (string-trim "#\\" key-string))
;  (let ((command "typecheck"))
;    (cond
;     ((string-equal key-string "*") (setf key-string "*"))
;     ((string-equal key-string "q") (setf key-string ":"))
;     ((string-equal key-string "]") (setf key-string ")"))
;     ((string-equal key-string "[") (setf key-string "(")))
;    (let ((on-screen (run-shell-command command key-string)))
;      (model-output on-screen)
;      on-screen)))
(
    defun type-check ()
  (if (or (null *last-expected-key*)
          (null *last-typed-key*)
          (string-equal *last-expected-key* *last-typed-key*))
      "true"
      "false")
)

(defun visual-type-check (seen)
  ;; Perceptual variant of TYPE-CHECK: the verdict comes from the text the
  ;; model encoded at the typing location, compared against the character it
  ;; intended to see there.  Falls back to TYPE-CHECK (which ablations may
  ;; override) when no usable percept is available.
  (let ((s (normalize-key-string seen)))
    (if (and *last-expected-delivered-key*
             (plusp (length s)))
        (if (string-equal s *last-expected-delivered-key*) "true" "false")
      (type-check))))
(
    defun respond-to-click-mouse (x y z)
  (declare (ignore x y z))
  (when *tcp-interactions-enabled*
    (run-shell-command "click" '("temp")))
  (setf *clicking-occurred* T)
    ;;  (sleep 0.1)
;(update-model-click)  ; Set the variable when clicking occurs

)

(
    defun get-key (l sublist)
  "Finds a key given the pair of values associated with it"
  (car (find-if (lambda (parts) (equal sublist (cadr parts))) l))
)
(
    defun concatenate-strings (num1 )
  (concatenate 'string
                "task"
               (write-to-string num1))
)
(
    defun concatenate-strings-subtask (num1 num2)
  (concatenate 'string
               "subtask"
               (write-to-string num1)
               "_"
               (write-to-string num2)
               "_list")
)
(
    defun get-element-from-list (num1 num2 which)
  (let ((desired_string (concatenate-strings-subtask num1 num2)))
    (case which
           (1 (car (read-from-string (concatenate 'string "(" desired_string ")"))))
           (2 (cadr (read-from-string (concatenate 'string "(" desired_string ")"))))
      (t nil)))
)

(
    defun get-chars-after-sequence-ci (char1 char2 char3 string)
  (let* ((seq (concatenate 'string char1 char2 char3))
         (pos (search seq string :test #'string-equal)))
    (if pos
        (let ((len (length string)))
          (list (if (< (+ pos (length seq)) len) (string (char string (+ pos (length seq)))) nil)
                (if (< (+ pos (length seq) 1) len) (string (char string (+ pos (length seq) 1))) nil)
                (if (< (+ pos (length seq) 2) len) (string (char string (+ pos (length seq) 2))) nil)))
        nil))
)
(
    defun replace-at-positions (lst vi txt)
  (let ((counter 0)) ; initialize counter to traverse the list
    (mapcar (lambda (x)
              (incf counter) ; increment the counter for each item
              (cond
               ((= counter 15) vi) ; 15th item in the list
               ((= counter 19) txt) ; 19th item in the list
               (t x))) ; for all other items, keep the original value
            lst))
)
;(defun read-json-file (filename)
;  "Reads a JSON file and converts it to a Lisp data structure."
;  ;; Implement JSON reading functionality here.
;  ;; This can be straightforward or complex based on the Lisp system and libraries you have.
;)
;
;(defun create-agi-elements (elements)
;  "Create AGI elements based on the provided list."
;  (loop for elem in elements do
;    (let ((name (getf elem 'name))
;          (position (getf elem 'position))
;          (color (getf elem 'color))
;          (text (getf elem 'text)))
;      ;; Use the appropriate AGI function based on the element type.
;      ;; This is an example for text elements.
;      (add-text-to-exp-window *my-agi-window* text :x (first position) :y (second position) :color color))))
;
;;; Example usage
;(defvar *elements* (read-json-file "visicons.json"))
;(create-agi-elements *elements*)
(defun clicking-occurred? (x)
  (declare (ignore x))
  *clicking-occurred*)
