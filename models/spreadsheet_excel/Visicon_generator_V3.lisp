;; Added VLM features
(defvar *my-agi-window* (open-exp-window "My AGI Window" :visible t))
(ql:quickload "cl-json")

(defparameter *visicon-generator-root*
  (make-pathname :name nil :type nil :defaults (or *load-truename* *load-pathname*)))

(defun visicon-generator-file (name)
  (namestring (merge-pathnames name *visicon-generator-root*)))

(defun normalize-visicon-type (raw-type cell-flag)
  (if (or (and raw-type (string-equal raw-type "cell"))
          (equal cell-flag t)
          (and (stringp cell-flag) (string-equal cell-flag "t")))
      "cell"
      "text"))

(defun dedupe-visicons (visicons)
  (let ((seen (make-hash-table :test 'equal))
        (out nil))
    (dolist (visicon visicons)
      (let* ((pos (getf visicon :position))
             (x (first pos))
             (y (second pos))
             (key (list (getf visicon :type)
                        x
                        y
                        (getf visicon :text)
                        (getf visicon :cell)
                        (getf visicon :cell-type)
                        (getf visicon :width)
                        (getf visicon :height)
                        (getf visicon :color))))
        (unless (gethash key seen)
          (setf (gethash key seen) t)
          (push visicon out))))
    (nreverse out)))

(defun read-json-visicons (json-file)
  (with-open-file (stream json-file)
    (let ((json-data (cl-json:decode-json stream)))
      (dedupe-visicons
       (mapcar #'(lambda (visicon)
                   (let* ((raw-type (cdr (assoc :type visicon)))
                          (cell (cdr (assoc :cell visicon)))
                          (norm-type (normalize-visicon-type raw-type cell)))
                     (list :name (cdr (assoc :name visicon))
                           :type norm-type
                           :position (cdr (assoc :position visicon))
                           :width (cdr (assoc :width visicon))
                           :height (cdr (assoc :height visicon))
                           :color (cdr (assoc :color visicon))
                           :text (cdr (assoc :text visicon))
                           :highlighted (cdr (assoc :highlighted visicon))
                           :type-vlm norm-type
                           :text-vlm (cdr (assoc :text--vlm visicon))
                           :cell cell
                           :cell-type (cdr (assoc :cell--type visicon))
                           :cell-vlm (cdr (assoc :cell--vlm visicon))
                           :cell-type-vlm (cdr (assoc :cell--type--vlm visicon)))))
               json-data)))))

(defun create-agi-element (visicon)
  (let* ((type (getf visicon :type))
         (name (getf visicon :name))
         (x (first (getf visicon :position)))
         (y (second (getf visicon :position)))
         (width (getf visicon :width))
         (height (getf visicon :height))
         (color (getf visicon :color))
         (text (getf visicon :text))
         (highlighted (getf visicon :highlighted))
         (type-vlm (getf visicon :type-vlm))
         (text-vlm (getf visicon :text-vlm))
         (cell (getf visicon :cell))
         (cell-type (getf visicon :cell-type))
         (cell-vlm (getf visicon :cell-vlm))
         (cell-type-vlm (getf visicon :cell-type-vlm)))
    (cond
      ((string-equal type "text")
       (add-text-to-exp-window *my-agi-window* text 
                              :x x 
                              :y y 
                              :width width 
                              :height height 
                              :color color))
      ((string-equal type "cell")
       (add-text-to-exp-window *my-agi-window* text
                              :x x
                              :y y
                              :width width
                              :height height
                              :color color))
      (t (format t "Unknown type: ~A~%" type)))))

(defun create-agi-elements-from-visicons (visicons)
  (dolist (visicon visicons)
    (create-agi-element visicon)))

(defun main ()
  (let ((visicons (read-json-visicons (visicon-generator-file "visicons.json"))))
    (create-agi-elements-from-visicons visicons)))

(main)