;;; Generic live driver for the agent-in-the-loop runs.
;;; Reads the task file name from the GENERIC_LIVE_TASK environment variable,
;;; loads ACT-R + the generic harness LIVE (:offline nil), and runs 300 s.
;;; The TCP bridge (TCP_VisiTor.py, with AGENT_RESOLVE=1) must already be up.
;;;
;;; Run headless:
;;;   set GENERIC_LIVE_TASK=W02_rename_budget_file   (PowerShell: $env:GENERIC_LIVE_TASK=...)
;;;   sbcl --non-interactive --disable-debugger --load run_live_task.lisp
(setf *load-verbose* nil *compile-verbose* nil)
(let ((task (sb-ext:posix-getenv "GENERIC_LIVE_TASK"))
      (root "g:/ACT-RModels/EVisiTor2026/"))
  (unless task
    (format t "~&### ERROR: set GENERIC_LIVE_TASK to a task file name~%")
    (sb-ext:exit :code 2))
  (handler-case
      (progn
        (load (concatenate 'string root "Draft20_Frontiers_Code_Package_2026-06-19/actr7.x/load-single-threaded-act-r.lisp"))
        (load (concatenate 'string root "NewInterfaces_PSAI/GenericInterface/load_generic_task.lisp"))
        (format t "~&### loading task ~a LIVE (:offline nil)~%" task)
        (funcall (intern "LOAD-GENERIC-TASK" :cl-user) task :offline nil)
        (format t "~&### running (run 300)...~%")
        (funcall (intern "RUN" :cl-user) 300)
        (format t "~&### RUN COMPLETE~%")
        (finish-output)
        (sb-ext:exit :code 0))
    (error (e)
      (format t "~&### DRIVER ERROR: ~a~%" e)
      (finish-output)
      (sb-ext:exit :code 3))))
