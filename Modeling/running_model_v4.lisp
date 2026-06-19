(ql:quickload "cl-json")
(defparameter *my-agi-window* nil)

(defparameter *running-model-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun running-model-file (name)
  (namestring (merge-pathnames name *running-model-root*)))

(defparameter *visicon-source-mode* :uia-direct)
(defparameter *saved-visicon-dir* (merge-pathnames #P"visicons/" *running-model-root*))
(defparameter *saved-visicon-files* nil)
(defparameter *saved-visicon-index* 0)
(defparameter *current-visicon-json-path* (running-model-file "visicons.json"))
(defparameter *spreadsheet-model-source-file* (running-model-file "New_Error (3-5-2-TCP).lisp"))
(defparameter *batch-suppress-act-r-trace* t)
(defparameter *batch-quiet-output* t)

(defun ensure-run-agi-window ()
  (or *my-agi-window*
      (setf *my-agi-window*
            (ignore-errors
              (open-exp-window "My AGI Window" :visible t)))))

(defun batch-timestamp-string ()
  (multiple-value-bind (sec min hour day month year)
      (decode-universal-time (get-universal-time))
    (format nil "~4,'0d-~2,'0d-~2,'0d_~2,'0d-~2,'0d-~2,'0d"
            year month day hour min sec)))

(defun run-subdirectory-name (index)
  (format nil "run_~3,'0d/" index))

(defun default-batch-log-root ()
  (merge-pathnames (format nil "logs/batch_~a/" (batch-timestamp-string))
                   *running-model-root*))

(defun batch-summary-path (batch-root)
  (merge-pathnames #P"batch_summary.csv" batch-root))

(defun ensure-batch-summary-file (path)
  (ensure-csv-header path '("run_index" "status" "log_dir")))

(defun append-batch-summary-row (path run-index status log-dir)
  (append-csv-row path (list run-index status (namestring log-dir))))

(defun enable-batch-gc ()
  #+sbcl
  (progn
    (dolist (package-name '("SB-KERNEL" "SB-EXT"))
      (multiple-value-bind (gc-inhibit-sym status)
          (find-symbol "*GC-INHIBIT*" package-name)
        (when (and gc-inhibit-sym status (boundp gc-inhibit-sym))
          (setf (symbol-value gc-inhibit-sym) nil))))
    t)
  #-sbcl
  nil)

(defun maybe-run-full-gc ()
  #+sbcl
  (progn
    (enable-batch-gc)
    (sb-ext:gc :full t)
    t)
  #-sbcl
  nil)

(defun cleanup-run-state ()
  (when (and (boundp '*formula-token-cache*)
             (hash-table-p *formula-token-cache*))
    (clrhash *formula-token-cache*))
  (when (fboundp 'reset-model-log-state)
    (reset-model-log-state))
  (setf *saved-visicon-index* 0
        *saved-visicon-files* nil
        *clicking-occurred* nil
        *my-agi-window* nil)
  (when (ignore-errors (current-model))
    (ignore-errors (clear-buffer 'visual))
    (ignore-errors (clear-buffer 'visual-location))
    (ignore-errors (clear-buffer 'goal))
    (ignore-errors (clear-exp-window))
    (ignore-errors (delete-all-visicon-features)))
  ;; ACT-R's clear-all deletes all model structs, clears scheduler hooks, and
  ;; resets the meta-process.  That is stronger than reset + delete-model for
  ;; long reload-heavy batches.
  (ignore-errors (clear-all))
  (maybe-run-full-gc)
  t)

(defun rebuild-model-for-run ()
  ;; Reload the model source so each batch run starts from a clean ACT-R model
  ;; rather than accumulating state across repeated resets.
  (cleanup-run-state)
  (load *spreadsheet-model-source-file*)
  (ensure-run-agi-window)
  (when *batch-suppress-act-r-trace*
    (ignore-errors (sgp :v nil :trace-detail low :cmdt nil)))
  (maybe-run-full-gc)
  t)

(defun pathname-file-namestring (path)
  (file-namestring (pathname path)))

(defun sort-pathnames-by-name (paths)
  (sort (copy-list paths)
        #'string<
        :key #'pathname-file-namestring))

(defun refresh-saved-visicon-files (&optional (directory *saved-visicon-dir*))
  (setf *saved-visicon-files*
        (sort-pathnames-by-name
         (directory (merge-pathnames #P"visicons_*.json" directory))))
  *saved-visicon-files*)

(defun use-uia-direct-visicons (&optional (json-path (running-model-file "visicons.json")))
  (setf *visicon-source-mode* :uia-direct
        *current-visicon-json-path* json-path
        *saved-visicon-index* 0)
  (when (fboundp 'enable-uia-output)
    (enable-uia-output *current-visicon-json-path*))
  (when (fboundp 'enable-tcp-interactions)
    (enable-tcp-interactions))
  *visicon-source-mode*)

(defun use-saved-visicons-iteratively (&optional (directory *saved-visicon-dir*))
  (refresh-saved-visicon-files directory)
  (unless *saved-visicon-files*
    (error "No saved visicon snapshots found in ~a" (namestring directory)))
  (setf *visicon-source-mode* :saved-iterative
        *saved-visicon-dir* directory
        *saved-visicon-index* 0
        *current-visicon-json-path* (namestring (first *saved-visicon-files*)))
  (when (fboundp 'enable-uia-output)
    (enable-uia-output *current-visicon-json-path*))
  (when (fboundp 'disable-tcp-interactions)
    (disable-tcp-interactions))
  *visicon-source-mode*)

(defun active-visicon-json-path ()
  *current-visicon-json-path*)

(defun ensure-visicon-bridge-config ()
  ;; Keep the TCP bridge reading from the same JSON source that ACT-R loads.
  (when (fboundp 'enable-uia-output)
    (enable-uia-output (active-visicon-json-path))))

(defun advance-saved-visicon-snapshot ()
  (unless *saved-visicon-files*
    (refresh-saved-visicon-files))
  (unless *saved-visicon-files*
    (error "Saved visicon mode is active, but no visicon snapshots were found in ~a"
           (namestring *saved-visicon-dir*)))
  (when (< (1+ *saved-visicon-index*) (length *saved-visicon-files*))
    (incf *saved-visicon-index*))
  (setf *current-visicon-json-path*
        (namestring (nth *saved-visicon-index* *saved-visicon-files*)))
  (ensure-visicon-bridge-config)
  *current-visicon-json-path*)

(defun prepare-next-visicon-source ()
  (ecase *visicon-source-mode*
    (:uia-direct
     (setf *current-visicon-json-path* (running-model-file "visicons.json"))
     (ensure-visicon-bridge-config)
     (refresh-visicons-via-bridge)
     *current-visicon-json-path*)
    (:saved-iterative
     (advance-saved-visicon-snapshot))))

(defun visicon-field (visicon &rest keys)
  (loop for key in keys
        for pair = (assoc key visicon)
        when pair do (return (cdr pair))))

(defun infer-cell-type (name text vis-type cell-flag)
  (declare (ignore name text))
  (let ((is-cell (or (eq cell-flag t)
                     (string-equal (princ-to-string cell-flag) "true")
                     (string-equal (princ-to-string vis-type) "cell"))))
    (unless is-cell
      (return-from infer-cell-type nil)))
  ;; Avoid re-inferring row/column labels from raw text.
  ;; Numeric cell contents like "5" are common data values and should not
  ;; become row headers unless the upstream parser explicitly labels them.
  nil)

(defun normalize-ui-type (vis-type text position cell-flag)
  (declare (ignore text position))
  (if (or (eq cell-flag t)
          (string-equal (princ-to-string cell-flag) "true")
          (string-equal (princ-to-string vis-type) "cell"))
      "cell"
      "text"))

(defun json-true-p (value)
  (or (eq value t)
      (and (stringp value) (string-equal value "true"))
      (and (symbolp value) (string-equal (symbol-name value) "true"))))

(defun read-json-visicons (json-file)
  (with-open-file (stream json-file)
    (let ((json-data (cl-json:decode-json stream)))
      (mapcar #'(lambda (visicon)
              (let* ((name (visicon-field visicon :name :|name|))
                (text (visicon-field visicon :text :|text|))
                (raw-type (visicon-field visicon :type :|type|))
                (position (visicon-field visicon :position :|position|))
                (cell (visicon-field visicon :cell :|cell|))
                (type (normalize-ui-type raw-type text position cell))
                         (type-vlm type)
                         (cell-type-raw (visicon-field visicon :cell--type :cell-type :|cell-type|))
                         (cell-type (or (and cell-type-raw (string-downcase (princ-to-string cell-type-raw)))
                     (infer-cell-type name text type cell))))
                    (list :name name
                 :type type
                          :width (visicon-field visicon :width :|width|)
                          :height (visicon-field visicon :height :|height|)
                 :position position
                          :color (visicon-field visicon :color :|color|)
                          :text text
                          :highlighted (visicon-field visicon :highlighted :|highlighted|)
                          :type-vlm type-vlm
                          :text-vlm (visicon-field visicon :text--vlm :text-vlm :|text-vlm|)
                 :cell cell
                          :cell-type cell-type)))
              json-data))))

(defun create-visicon-chunk (visicon)
  (let* ((type (getf visicon :type))
         (name (getf visicon :name))
         (x (first (getf visicon :position)))
         (y (second (getf visicon :position)))
         (width (getf visicon :width))
         (height (getf visicon :height))
         (color (getf visicon :color))
         (actual-text (getf visicon :text))
         (highlighted (getf visicon :highlighted))
         (highlighted-value (if (json-true-p highlighted) 'T 'NIL))
         (type-vlm (getf visicon :type-vlm)) 
         (text-vlm (getf visicon :text-vlm))
         (cell (getf visicon :cell))
         (cell-value (if (json-true-p cell) 'T 'NIL))
         (cell-type (getf visicon :cell-type)))
    (add-visicon-features `(name ,name screen-x ,x screen-y ,y height ,height width ,width 
                           color ,color type ,type value ,actual-text text T Text-value ,actual-text 
                           highlighted ,highlighted-value type-vlm ,type-vlm text-vlm ,text-vlm
                           cell ,cell-value cell-type ,cell-type))))

(defun create-agi-element (visicon)
  (let* ((type (getf visicon :type))
         (name (getf visicon :name))
         (x (first (getf visicon :position)))
         (y (second (getf visicon :position)))
         (width (getf visicon :width))
         (height (getf visicon :height))
         (color (getf visicon :color))
         (text (getf visicon :text))
         (type-vlm (getf visicon :type-vlm))
         (text-vlm (getf visicon :text-vlm))
         (cell (getf visicon :cell))
         (cell-type (getf visicon :cell-type)))
    (declare (ignore type type-vlm text-vlm cell cell-type))
    (let ((window (ensure-run-agi-window)))
      (when window
        (add-text-to-exp-window window text :x x :y y :width width :height height :color color)))))

(defun create-agi-elements-from-visicons (visicons)
  (dolist (visicon visicons)
    (create-visicon-chunk visicon)
    (create-agi-element visicon)))

(defun main ()
  ; (let ((visicons (read-json-visicons (running-model-file "visicons_fixed.json"))))
  ;   (create-agi-elements-from-visicons visicons))
  (let ((visicons1 (read-json-visicons (active-visicon-json-path))))
    (create-agi-elements-from-visicons visicons1)))

(defun restore-model-control-markers ()
  ;; Recreate task/subtask markers defined in the model file so visual search
  ;; can continue across refreshes after Enter/click updates.
  (dotimes (i 14)
    (let ((name (format nil "task~d" (1+ i))))
      (add-visicon-features
       `(screen-x ,(+ 20 i) screen-y 20 value ,name text-value ,name text T))))

  (loop for task from 1 to 30 do
        (loop for sub from 1 to 200 do
              (let* ((label (format nil "subtask~d_~d_list" task sub))
                     (sym (read-from-string label)))
                (if (boundp sym)
                    (add-visicon-features
                     `(screen-x ,(+ 30 task) screen-y ,(+ 30 sub)
                       value ,label text-value ,label text T))
                  (return))))))

(defun refresh-visicons-via-bridge ()
  (if (and (fboundp 'run-shell-command)
           (boundp '*tcp-visitor-host*))
      (progn
        (act-r-output "Refreshing visicons via TCP bridge")
        (let ((response (run-shell-command "refreshvisicons" nil)))
          (let ((err (and (listp response) (cdr (assoc :error response)))))
            (when err
              (error "refreshvisicons failed through TCP: ~a" err)))
          response))
    (let* ((pkg (find-package "INFERIOR-SHELL"))
           (run-ss (and pkg (find-symbol "RUN/SS" pkg))))
      (if (and run-ss (fboundp run-ss))
          (funcall run-ss (list (running-model-file "visual_v3.py")))
        (error "Neither TCP bridge nor INFERIOR-SHELL RUN/SS is available to run visual_v3.py")))))

(main)

(defun update-model-click()
  (clear-exp-window)
  (delete-all-visicon-features)
  (prepare-next-visicon-source)
  (main)
  (restore-model-control-markers))

(defun current-goal-task-number ()
  (let ((goal (ignore-errors (buffer-read 'goal))))
    (when goal
      (ignore-errors (chunk-slot-value-fct goal 'task)))))

(defun current-goal-job-name ()
  (let ((goal (ignore-errors (buffer-read 'goal))))
    (when goal
      (ignore-errors (chunk-slot-value-fct goal 'job)))))

(defun model-finished-at-task-15-p ()
  (let ((task (current-goal-task-number))
        (job (current-goal-job-name)))
    (and (eql task 15)
         (or (null job)
             (string-equal (princ-to-string job) "done")))))

(defun initialize-visicons-from-json ()
  ;; Prime ACT-R from JSON without deleting model-seeded task markers (task1, subtask lists).
  (ensure-run-agi-window)
  (case *visicon-source-mode*
    (:uia-direct
     (setf *current-visicon-json-path* (running-model-file "visicons.json"))
     (ensure-visicon-bridge-config)
     (refresh-visicons-via-bridge))
    (:saved-iterative
     (unless *saved-visicon-files*
       (refresh-saved-visicon-files))
     (unless *saved-visicon-files*
       (error "Saved visicon mode is active, but no visicon snapshots were found in ~a"
              (namestring *saved-visicon-dir*)))
     (setf *saved-visicon-index* 0
           *current-visicon-json-path* (namestring (first *saved-visicon-files*)))
     (ensure-visicon-bridge-config)))
  (main)
  (restore-model-control-markers))

(defun run-model-loop ()
  (initialize-visicons-from-json)
  (loop
    (enable-batch-gc)
    (setf *clicking-occurred* nil)
    (run-until-condition 'clicking-occurred?)
    (enable-batch-gc)
    (when (model-finished-at-task-15-p)
      (return-from run-model-loop 'finished))
    ;; Let in-flight vision events settle before replacing the visicon.
    ; (run 0.05)
    (clear-buffer 'visual)
    (clear-buffer 'visual-location)
    (clear-exp-window)
    (delete-all-visicon-features)
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
;(add-visicon-features '(screen-x 295 screen-y 350 height 30 width 70 color white value "C6" Highlighted "blue" text-value "C6" Highlighted "blue" type "text" text T))
;(add-visicon-features '(screen-x 45 screen-y 135 height 30 width 70 color red value "open_file" text-value "open_file" type "text" text T))
(add-visicon-features '(screen-x 100 screen-y 245 height 30 width 70 color red value "WORKBOOKS" text-value "WORKBOOKS" type "text" text T))
(add-visicon-features '(screen-x 200 screen-y 340 height 30 width 70 color red value "NORMALIZATION_FILE" text-value "NORMALIZATION_FILE" type "text" text T))
(add-visicon-features '(screen-x 664 screen-y 153 height 30 width 70 color red value "file_name" text-value "file_name" type "text" text T))
;(add-visicon-features '(screen-x 86 screen-y 64 height 30 width 70 color red value "Home" text-value "Home" type "text" text T))
      

;(add-visicon-features '(screen-x 630 screen-y 129 height 30 width 70 color red value "Cells" text-value "Cells" type "text" text T))
;(add-visicon-features '(screen-x 141 screen-y 64 height 30 width 70 color red value "Insert" text-value "Insert" type "text" text T))
;(add-visicon-features '(screen-x 14 screen-y 250 height 30 width 70 color red value "ROW_1" text-value "ROW_1" type "text" text T))
;(add-visicon-features '(screen-x 78 screen-y 250 height 30 width 70 color red value "A1" text-value "A1" type "text" text T))
;(add-visicon-features '(screen-x 78 screen-y 270 height 30 width 70 color blue value "A2" text-value "A2" type "text" text T))
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

    (prepare-next-visicon-source)
    (main)))

(defun run-model-multiple-times (&optional (runs 25)
                                           (batch-root (default-batch-log-root))
                                           (retain-results nil))
  (let* ((root (ensure-directory-pathname batch-root))
         (summary-path (batch-summary-path root))
         (original-log-dir (and (boundp '*model-log-dir*) *model-log-dir*))
         (had-tcp-debug (boundp '*tcp-debug*))
         (original-tcp-debug (and had-tcp-debug *tcp-debug*))
         (had-quiet-output (boundp '*batch-quiet-output*))
         (original-quiet-output (and had-quiet-output *batch-quiet-output*))
         (results nil))
    (ensure-batch-summary-file summary-path)
    (enable-batch-gc)
    (when had-tcp-debug
      (setf *tcp-debug* nil))
    (when had-quiet-output
      (setf *batch-quiet-output* t))
    (unwind-protect
         (loop for run-index from 1 to runs do
               (let* ((run-dir (merge-pathnames (run-subdirectory-name run-index) root))
                      (status "finished")
                      (stop-batch nil))
                 (handler-case
                     (progn
                       (set-model-log-directory run-dir)
                       (rebuild-model-for-run)
                       (enable-batch-gc)
                       (run-model-loop))
                   (usocket:connection-refused-error (e)
                     (setf status (format nil "error: TCP bridge connection refused: ~a" e)
                           stop-batch t)
                     (act-r-output "Stopping batch early because TCP bridge is unavailable."))
                   (error (e)
                     (setf status (format nil "error: ~a" e))))
                 (cleanup-run-state)
                 (append-batch-summary-row summary-path run-index status run-dir)
                 (when retain-results
                   (push (list :run run-index :status status :log-dir run-dir) results))
                 (when stop-batch
                   (return))))
      (when original-log-dir
        (set-model-log-directory original-log-dir))
      (when had-tcp-debug
        (setf *tcp-debug* original-tcp-debug))
      (when had-quiet-output
        (setf *batch-quiet-output* original-quiet-output))
      (maybe-run-full-gc))
    (if retain-results
        (nreverse results)
      (list :runs runs
            :batch-root (namestring root)
            :summary-file (namestring summary-path)))))
