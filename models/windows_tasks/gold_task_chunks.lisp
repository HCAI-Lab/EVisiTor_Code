;;; ============================================================================
;;; GOLD-STANDARD Subtask chunks for the Windows tasks selected from the
;;; PSAI computer-use dataset (huggingface.co/datasets/anaisleila/computer-use-data-psai)
;;;
;;; Authored 2026-07-11 by decomposing the VENDORS' OWN reasoning_steps
;;; (candidate_tasks_full.json / new_candidate_tasks_full.json) into the
;;; model's action vocabulary — one subtask per reasoning step, following
;;; the DEMONSTRATED method, not a modeler-preferred alternative. Where a
;;; recording has no reasoning_steps (W3, W10) the decomposition follows
;;; the event stream / video summary in selected_tasks.md.
;;;
;;; This file supersedes the implicit "gold" role of the specs that were
;;; derived from generated_task_chunks.lisp; score the LLM-generated file
;;; against THIS one with the Appendix G procedure.
;;;
;;; Vocabulary (extended 2026-07-11, matching generic_interface_model.lisp):
;;;   Goto / Move  attention + cursor       Select     left click
;;;   Type         char-by-char typing      Press      key or modifier chord
;;;   RightClick   right button click       Scroll     wheel, item = "down"|"up"
;;;   ClickDown    hold left button         ClickUp    release left button
;;;   (drag = ClickDown -> Move -> ClickUp; no task below needs it, but the
;;;    capability is exercised by tasks/T00_drag_selftest.lisp)
;;;
;;; REMOVED TASKS (2026-07-11):
;;;   W5 (screen resolution): reasoning steps skip the "Keep changes"
;;;      confirmation dialog and say "1920 x 1080" while the UIA literal is
;;;      "1920 × 1080" (multiplication sign); resolution changes also break
;;;      the recording geometry — hard to simulate faithfully.
;;;   W6 (Task Manager end process): "right-click on ANY of the running
;;;      tasks that are not required" is unresolvable — the target is
;;;      unspecified and machine-dependent (dynamic process list).
;;;   W8 (Excel macro): reasoning includes untraceable free choices
;;;      (optional shortcut key, macro storage location, 'highlight the data
;;;      range' without a stated range, 'test your macro') plus PSAI-portal
;;;      upload overhead; too under-determined for a gold reference.
;;; ============================================================================

;;; ----------------------------------------------------------------------------
;;; W1  (EASY, Run dialog)  cmaela4ed001gzr0xhfhqg921
;;; "Use the Run dialog (Win+R) to open Notepad on Windows."
;;; Reasoning steps: 1. Press Windows + R.  2. Type "notepad" and press
;;; enter.  3. Close the window once done.
;;; ----------------------------------------------------------------------------
(setq subtaskW1_1_list '((Press "win+r") (end)))
(setq subtaskW1_2_list '((Type "notepad") (Press "enter") (end)))
(setq subtaskW1_3_list '((Goto "Close") (Select "Close") (endsub)))          ; #VERIFY-UIA Notepad close button

;;; ----------------------------------------------------------------------------
;;; W2  (EASY, File Explorer)  cmaela4el00dezr0xar3kk07l
;;; "Rename the file 'budget.xlsx' to 'budget_2025.xlsx' using File Explorer."
;;; Reasoning steps: 1. Click budget.xlsx.  2. Click the rename icon on the
;;; top bar.  3. Change the name to "budget_2025.xlsx" and press Enter.
;;; NOTE: vendor APPENDED "_2025" (8 keypresses); Type cannot express
;;; within-text editing, so the gold chunk retypes the full name.
;;; ----------------------------------------------------------------------------
(setq subtaskW2_1_list '((Goto "budget.xlsx") (Select "budget.xlsx") (end)))
(setq subtaskW2_2_list '((Goto "Rename") (Select "Rename") (end)))           ; #VERIFY-UIA command-bar Rename button
(setq subtaskW2_3_list '((Type "budget_2025.xlsx") (Press "enter") (endsub)))

;;; ----------------------------------------------------------------------------
;;; W3  (EASY, File Explorer)  cm9egbfne005d0e0v3a0rw2pb
;;; "Create a new folder named 'Projects' on the Desktop using File Explorer."
;;; reasoning_steps empty; from the event stream: open File Explorer ->
;;; Desktop -> right-click empty area -> New -> Folder -> type Projects ->
;;; Enter. "Desktop background" = the folder view's empty region (no UIA
;;; text label; live runs map it to the view container's free area).
;;; ----------------------------------------------------------------------------
(setq subtaskW3_1_list '((Goto "File Explorer") (Select "File Explorer") (end)))  ; #VERIFY-UIA taskbar item
(setq subtaskW3_2_list '((Goto "Desktop") (Select "Desktop") (end)))              ; navigation-pane item
(setq subtaskW3_3_list '((Goto "Desktop background") (RightClick "Desktop background") (end)))  ; #VERIFY-UIA
(setq subtaskW3_4_list '((Goto "New") (Select "New") (Goto "Folder") (Select "Folder") (end)))  ; #VERIFY-UIA
(setq subtaskW3_5_list '((Type "Projects") (Press "enter") (endsub)))

;;; ----------------------------------------------------------------------------
;;; W4  (MEDIUM, File Explorer)  cmaela4el00dgzr0xvj1od7q9
;;; "Compress the folder 'Logs' into a ZIP archive."
;;; Reasoning steps: 1. Right-click the Logs folder.  2. Select "Show more
;;; options".  3. Select "Send to" then "Compressed (zipped) folder".
;;; 4. Name the .zip file and press Enter — the event stream shows a single
;;; keypress, i.e. the vendor accepted the default name "Logs.zip".
;;; ----------------------------------------------------------------------------
(setq subtaskW4_1_list '((Goto "Logs") (RightClick "Logs") (end)))
(setq subtaskW4_2_list '((Goto "Show more options") (Select "Show more options") (end)))  ; #VERIFY-UIA Win11 legacy menu
(setq subtaskW4_3_list '((Goto "Send to") (Select "Send to") (Goto "Compressed (zipped) folder") (Select "Compressed (zipped) folder") (end)))  ; #VERIFY-UIA
(setq subtaskW4_4_list '((Press "enter") (endsub)))

;;; ----------------------------------------------------------------------------
;;; W7  (MEDIUM, Command Prompt)  cmaela4em00ggzr0xbdq9jgok
;;; "Use Command Prompt to find your IP address (using ipconfig)."
;;; Reasoning steps: 1. Go to the Start menu and navigate to the search
;;; bar.  2. Type "cmd" and press Enter.  3. Type or paste "ipconfig" and
;;; press Enter.  4. SCROLL through the report and look for "IPv4 Address".
;;; ----------------------------------------------------------------------------
(setq subtaskW7_1_list '((Goto "Search") (Select "Search") (end)))           ; #VERIFY-UIA taskbar search box
(setq subtaskW7_2_list '((Type "cmd") (Press "enter") (end)))
(setq subtaskW7_3_list '((Type "ipconfig") (Press "enter") (end)))
(setq subtaskW7_4_list '((Scroll "down") (Goto "IPv4 Address") (endsub)))    ; #VERIFY-UIA terminal text exposure

;;; ----------------------------------------------------------------------------
;;; W9  (EASY, Start menu)  cma092ib400ghwu0v52t3qxia
;;; "Open the Calculator via the Windows Start menu search bar."
;;; Reasoning steps: 1. Go to the start menu and navigate to the search
;;; bar.  2. Type "calculator" and press Enter.  3. The calculator window
;;; opens (verification -> attention-only Goto).
;;; NOTE: the event stream shows a shortened query + a result click; the
;;; reasoning text says "press Enter" — the gold follows the reasoning text.
;;; ----------------------------------------------------------------------------
(setq subtaskW9_1_list '((Goto "Search") (Select "Search") (end)))           ; #VERIFY-UIA
(setq subtaskW9_2_list '((Type "calculator") (Press "enter") (end)))
(setq subtaskW9_3_list '((Goto "Calculator") (endsub)))                      ; #VERIFY-UIA window title

;;; ----------------------------------------------------------------------------
;;; W10 (EASY, File Explorer / Windows search)  cm9egbkl7005j0e0v774e8iqr
;;; "Search for a file named 'report.docx' in the Documents folder using
;;; Windows search."
;;; reasoning_steps empty; from the event stream: File Explorer from the
;;; taskbar -> Documents -> search box -> type report.docx -> Enter ->
;;; locate the result (attention-only).
;;; ----------------------------------------------------------------------------
(setq subtaskW10_1_list '((Goto "File Explorer") (Select "File Explorer") (end)))  ; #VERIFY-UIA taskbar item
(setq subtaskW10_2_list '((Goto "Documents") (Select "Documents") (end)))
(setq subtaskW10_3_list '((Goto "Search Documents") (Select "Search Documents") (end)))  ; #VERIFY-UIA
(setq subtaskW10_4_list '((Type "report.docx") (Press "enter") (end)))
(setq subtaskW10_5_list '((Goto "report.docx") (endsub)))

;;; ============================================================================
;;; Summary counts: 7 tasks -> 27 named subtask lists, 54 non-terminal
;;; atomic action items, decomposed from the vendors' demonstrations.
;;;
;;; Known divergences from generated_task_chunks.lisp (LLM baseline) that a
;;; scorer must classify as strategy/coverage differences, not label errors:
;;;   * W3: gold follows right-click > New > Folder and includes opening
;;;     File Explorer; generated used Ctrl+Shift+N and started inside
;;;     Explorer (5 vs 3 subtasks).
;;;   * W4: gold uses RightClick; generated used Select + Press "shift+f10".
;;;     Gold merges Send to + Compressed (zipped) folder into one subtask
;;;     (= vendor step 3); generated split them.
;;;   * W7: gold opens the search bar by mouse (Goto/Select Search) per the
;;;     reasoning text; generated used Press "win". Gold adds the Scroll
;;;     action the vendor demonstrated; generated had no way to express it.
;;; ============================================================================
