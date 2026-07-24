;;; ============================================================================
;;; T00_drag_selftest.lisp — HAND-WRITTEN capability self-test (not a PSAI
;;; task; excluded from task_specs.json and the ALL batch).
;;;
;;; Exercises every 2026-07-11 vocabulary extension in one run:
;;;   subtask 1: drag       — ClickDown on "DragSource", Move (cursor drag
;;;              with the button held, slowed per :cursor-drag-delay) to
;;;              "DropTarget", ClickUp there
;;;   subtask 2: right-click — Goto + RightClick on "DropTarget"
;;;   subtask 3: scroll     — Scroll "down" reveals the deferred feature
;;;              "Revealed Item" (offline stand-in for below-the-fold
;;;              content), then attention-only Goto of it.
;;;
;;; Expected mouse_events.csv sequence: mousedown, mouseup, rightclick,
;;; scroll-down x3.
;;;
;;; Load AFTER fucntion_new_tcp.lisp + generic_helpers.lisp and BEFORE
;;; generic_interface_model.lisp (or use load_generic_task.lisp):
;;;   (load-generic-task "T00_drag_selftest")  (run 60)
;;; ============================================================================

(proclaim-subtask-specials 30 60)
(clear-subtask-lists 30 60)
(defparameter *generic-total-tasks* 1)

;;; --- Task 1: T00 (synthetic, capability self-test)
(setq subtask1_1_list '((Goto "DragSource") (ClickDown "DragSource") (Move "DropTarget") (ClickUp "DropTarget") (end)))
(setq subtask1_2_list '((Goto "DropTarget") (RightClick "DropTarget") (end)))
(setq subtask1_3_list '((Scroll "down") (Goto "Revealed Item") (endsub)))

(defun install-task-chunks ()
  (add-dm-fct '(
    (Task1 ISA Task Number 1)
    (first-goal ISA intention job "retrieve-task" task 1)

    ;; Visual targets
    (ts-1 ISA target-spec label "DragSource" lookup-text "DragSource" lookup-cell-type "object" target-type "nil")
    (ts-2 ISA target-spec label "DropTarget" lookup-text "DropTarget" lookup-cell-type "object" target-type "nil")
    (ts-3 ISA target-spec label "Revealed Item" lookup-text "Revealed Item" lookup-cell-type "object" target-type "nil")
  ))
  (set-similarities-fct '(
     (first second -0.5)))
  t)

;; Placeholder UI features for offline validation runs (no live UIA).
(defun install-task-visicon ()
  (add-visicon-features '(screen-x 120 screen-y 120 height 30 width 70 color red value "DragSource" text-value "DragSource" type "text" text T))
  (add-visicon-features '(screen-x 520 screen-y 320 height 30 width 70 color red value "DropTarget" text-value "DropTarget" type "text" text T))
  t)

;; Deferred feature that scrolling brings into view.
(defparameter *generic-scroll-reveal-features*
  (list
    '(screen-x 320 screen-y 480 height 30 width 70 color red value "Revealed Item" text-value "Revealed Item" type "text" text T)
  ))
