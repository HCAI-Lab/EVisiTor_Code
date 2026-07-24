;;; ============================================================================
;;; generic_interface_model.lisp — interface-generic EVisiTor ACT-R model
;;;
;;; Author: derived from Amir Bagherzadeh's Excel model
;;;         "New_Error (3-5-2-TCP_4-23).lisp" by stripping every
;;;         Excel-specific mechanism. 2026-07-06.
;;;
;;; This model contains ONLY primitive interface activities:
;;;
;;;   * attention shift   (Goto / Move -> visual search + move-attention,
;;;                        with remembered-location memory and local/global
;;;                        search strategy choice)
;;;   * mouse movement    (move-cursor to the attended object)
;;;   * clicking          (Select -> click-mouse)
;;;   * right-clicking    (RightClick -> right-click-mouse: punch of the
;;;                        virtual mouse's right button / middle finger)
;;;   * drag primitives   (ClickDown -> hold-mouse, Move -> move-cursor
;;;                        with the button held [drag-slowed per
;;;                        :cursor-drag-delay], ClickUp -> release-mouse)
;;;   * scrolling         (Scroll -> scroll-wheel motor style, one
;;;                        execution event per wheel notch)
;;;   * typing            (Type -> character-by-character keypresses with
;;;                        probabilistic typo injection, immediate/delayed
;;;                        typing CHECK, and delete-and-retype repair)
;;;   * key commands      (Press -> Enter, named keys, and modifier chords
;;;                        such as "win+r" or "ctrl+shift+esc")
;;;
;;; It contains NO task knowledge and NO interface-specific productions
;;; (no spreadsheet cell/row/column resolution, no formula typing).
;;; All task knowledge arrives as declarative chunks from a task file
;;; (tasks/Wxx_*.lisp) which must be loaded BEFORE this file:
;;;
;;;   load order: fucntion_new_tcp.lisp -> generic_helpers.lisp
;;;               -> tasks/Wxx_*.lisp -> THIS FILE
;;;
;;; or simply use load_generic_task.lisp:  (load-generic-task "W01_run_notepad")
;;; ============================================================================

(reset)
(delete-model)
(require-extra "emma")
(require-extra "extended-motor-actions")  ; hold/release + release signals (drag, right-click)
(defvar *clicking-occurred* nil)

;; Predeclare generated subtask globals so top-level SETQ forms compile cleanly.
(eval-when (:compile-toplevel :load-toplevel :execute)
  (proclaim-subtask-specials 30 60))

(define-model GenericInterface-TCP

;;;; Monitoring commands: forward ACT-R eye/hand output to the TCP bridge.
(defvar *my-agi-window* (open-exp-window "Generic Interface Window" :visible t))
(add-act-r-command "my-move-cursor" 'respond-to-move-cursor-monitor "sth")
(monitor-act-r-command "move-cursor" "my-move-cursor")
(add-act-r-command "my-click-mouse" 'respond-to-click-mouse "temp" "temp" "sth")
(monitor-act-r-command "click-mouse" "my-click-mouse")
(add-act-r-command "my-release-mouse" 'respond-to-release-mouse "temp" "temp" "sth")
(monitor-act-r-command "release-mouse" "my-release-mouse")
(add-act-r-command "my-press-key" 'respond-to-key-press-monitor "sth")
(add-act-r-command "my-move-attention" 'respond-to-move-attention-monitor "sth")
(monitor-act-r-command "output-key" "my-press-key")
(monitor-act-r-command "move-attention" "my-move-attention")
(install-device '("motor" "cursor" "mouse"))
(install-device '("motor" "keyboard"))
(start-hand-at-mouse)

;;;; Chunk-types (identical to the Excel model where they overlap)
(chunk-type Task Number)
(chunk-type Subtask actions items)
(chunk-type action action item)
(chunk-type actionencode action meaning)
(chunk-type WORD TYPE (SPELLING SYMBOL))
(chunk-type intention job task subtask subsubtask sx sy item meaning type word)
(chunk-type remembered-location item sx sy)
(chunk-type typing word type correct check phase token-index char-index
            current-token target-cell formula-source source-marker next-char
            token-done error-position error-next-position last-position
            task subtask subsubtask item meaning job)
(chunk-type item word current after position next previous)
(chunk-type memory task subtask subsubtask action item meaning)
(chunk-type target-spec label lookup-text lookup-cell-type target-type)

(sgp :v t :needs-mouse t :show-focus t :trace-detail high :emma t)
(sgp
    :TT                          3
    :PCT                         NIL
    ;;--------------------------------
    ;; DECLARATIVE module
    ;;--------------------------------
    :MAS                         1.6
    :BLL                         0.1
    :RT                          0
    :LF                          0.05
    :LE                          1.0
    :BLC                         5.0
    :ANS                         0.005
    :MD                          -1.0
    :MS                          0.0
    :DECLARATIVE-NUM-FINSTS      4
    :DECLARATIVE-FINST-SPAN      3.0
    :OL                          T
    :ESC                         T
    :ER                          NIL
    :EGS                         0.1
    :UT                          NIL
    :NU                          20
    :UL                          T
    :ALPHA                       0.2
    :IU                          10
    :VISUAL-NUM-FINSTS           1000
    :VISUAL-FINST-SPAN           1000
    ;;--------------------------------
    ;; MOTOR extension (extended-motor-actions)
    ;;--------------------------------
    :CURSOR-DRAG-DELAY           T    ; slow cursor moves made with the button held (MacKenzie et al., 1991)
)

;;;; Action-verb interpretations: the ONLY built-in semantic knowledge.
(add-dm
 (Goto       ISA actionencode action Goto       meaning "attention-N-movecursor")
 (moveto     ISA actionencode action move       meaning "attention-N-movecursor")
 (type       ISA actionencode action type       meaning "type")
 (select     ISA actionencode action select     meaning "click")
 (press      ISA actionencode action press      meaning "keycommand")
 (rightclick ISA actionencode action rightclick meaning "rightclick")
 (scroll     ISA actionencode action scroll     meaning "scroll")
 (clickdown  ISA actionencode action clickdown  meaning "mousedown")
 (clickup    ISA actionencode action clickup    meaning "mouseup")
)

(sgp-fct (list :cmdt (no-output (car (sgp :v)))))

;;; ========================================================================
;;; 1. Main controller: read the instruction panel, walk task -> subtask ->
;;;    action, dispatch on the comprehended meaning.
;;; ========================================================================

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
    !output! (=y)
    !eval!  (what-is-on-screen '(=y))
    !eval! (respond-to-eye-move-xy =sx =sy)
    !eval! (log-attention-shift-explicit =visual-location "move-vision-to-task")
    =goal>
        isa     intention
        job     "retrieve-subtask"
    +visual>
        isa         move-attention
        screen-pos  =visual-location
)

(P 3-move-attention-to-task
    =goal>
        isa     intention
        job     "retrieve-subtask"
        task    =x
        subtask =y
    ?visual-location>
        state   free
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

;;; ========================================================================
;;; 2. Attention shift + mouse movement (Goto / Move / Select targets)
;;;
;;;    Every target is an ordinary visual object: resolve it through
;;;    declarative target knowledge (protected UIA labels), then search
;;;    memory for its location, else run a local/global visual search.
;;; ========================================================================

(P 7-1-item-categorization
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
    +retrieval>
        isa     target-spec
        label   =x
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

;; If target knowledge is genuinely missing, fall back to visual search on
;; the literal label.
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

(P ready-to-attention-to-do-task-not-cell
    =goal>
        isa     intention
        job     "do-action"
        meaning  "attention-N-movecursor"
        item    =x
        type    "nil"
    ?visual-location>
        state   free
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
    ==>
    !bind! =limit (instruction-panel-boundary)
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
    <   screen-x =limit
)

(P no-recalled-object-location
    =goal>
        isa     intention
        job     "checking-object-location-memory"
    ?retrieval>
        buffer  failure
    ==>
    !bind! =search-mode (choose-visual-search-mode)
    =goal>
        isa     intention
        job     "request-visual-search"
        type    =search-mode
)

(P request-local-neighbor-visual-search
    =goal>
        isa     intention
        job     "request-visual-search"
        type    "local"
    ?visual-location>
        state   free
    ==>
    !bind! =limit (instruction-panel-boundary)
    =goal>
        isa     intention
        job     "waiting-visual-search"
        type    "nil"
    +visual-location>
        isa     visual-location
        type    "text"
    -   text-value nil
    <   screen-x =limit
        :attended nil
        :nearest current
)

(P request-global-away-visual-search
    =goal>
        isa     intention
        job     "request-visual-search"
        type    "global"
    ?visual-location>
        state   free
    ==>
    !bind! =limit (instruction-panel-boundary)
    =goal>
        isa     intention
        job     "waiting-visual-search"
        type    "nil"
    +visual-location>
        isa     visual-location
        type    "text"
    -   text-value nil
    <   screen-x =limit
        :attended nil
)

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
    ==>
    !bind! =limit (instruction-panel-boundary)
    +visual-location>
        isa     visual-location
        :attended nil
    -   text-value nil
    <   screen-x =limit
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

;; Target found: remember its location and move the mouse cursor there.
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
    !eval! (snap-hand-to-mouse)
    +manual>
        isa     move-cursor
        loc     =visual
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask =y
)

;; Attended object is not the target: search again.
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

;;; ========================================================================
;;; 3. Clicking (Select)
;;; ========================================================================

(P clicking
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
   !eval! (snap-hand-to-mouse)
   +manual>
      isa        click-mouse
)

;;; ========================================================================
;;; 3b. Right-clicking (RightClick): punch of the virtual mouse's right
;;;     button (right middle finger); the cursor is already on the target
;;;     from the preceding Goto, exactly as with Select.
;;; ========================================================================

(P right-clicking
    =goal>
        isa     intention
        job     "do-action"
        meaning  "rightclick"
        subsubtask  =x
    ?manual>
        state       free
    ==>
    !bind! =y (+ 1 =x)
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =y
   !eval! (snap-hand-to-mouse)
   +manual>
      isa        right-click-mouse
)

;;; ========================================================================
;;; 3c. Drag primitives: ClickDown holds the left button on the current
;;;     target, Move (the ordinary attention+cursor pathway) then drags the
;;;     cursor with the button held (slowed per :cursor-drag-delay), and
;;;     ClickUp releases the button at the destination.
;;; ========================================================================

(P mouse-button-down
    =goal>
        isa     intention
        job     "do-action"
        meaning  "mousedown"
        subsubtask  =x
    ?manual>
        state       free
    ==>
    !bind! =y (+ 1 =x)
    !eval! (snap-hand-to-mouse)
    !eval! (setf *mouse-hold-pending* t)
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =y
   +manual>
      isa        hold-mouse
)

(P mouse-button-up
    =goal>
        isa     intention
        job     "do-action"
        meaning  "mouseup"
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
      isa        release-mouse
)

;;; ========================================================================
;;; 3d. Scrolling (Scroll): the scroll-wheel motor style delivers
;;;     *scroll-notches-per-action* wheel notches in the item's direction
;;;     ("down" or "up"); offline, the first scroll reveals any deferred
;;;     below-the-fold visicon features.
;;; ========================================================================

(P scrolling
    =goal>
        isa     intention
        job     "do-action"
        meaning  "scroll"
        item        =dir
        subsubtask  =x
    ?manual>
        state       free
    ==>
    !bind! =y (+ 1 =x)
    !bind! =d (normalize-scroll-direction =dir)
    !bind! =n *scroll-notches-per-action*
    !eval! (snap-hand-to-mouse)
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =y
        item        nil
   +manual>
      isa        scroll-wheel
      hand       right
      direction  =d
      notches    =n
)

;;; ========================================================================
;;; 4. Key commands (Press): Enter, named keys, and modifier chords.
;;;    The chord string is delivered to VisiTor as one payload via the
;;;    keypress override; the manual press of a surrogate key supplies the
;;;    motor timing. Command keys are exempt from typo injection.
;;; ========================================================================

(P 7-2-pressing-key-command
    =goal>
        isa     intention
        job     "do-action"
        meaning "keycommand"
        item    =key
        subsubtask =z
    ?manual>
        state   free
    ==>
    !eval! (clear-pending-shift-keypress)
    !eval! (snap-hands-to-home)
    !bind! =surrogate (key-command-surrogate =key)
    !eval! (prepare-key-command =key)
    +manual>
        cmd     press-key
        key     =surrogate
    !bind! =w (+ 1 =z)
    =goal>
        isa     intention
        job     "retrieve-actions-of-subtask"
        subsubtask  =w
        item        nil
)

;;; ========================================================================
;;; 5. Typing (Type) with typing CHECK and repair — identical machinery to
;;;    the Excel model's actual-word pathway, plus uppercase shift support
;;;    and an interface-generic visual anchor.
;;; ========================================================================

(P ready-to-type
    =goal>
        isa     intention
        job     "do-action"
        meaning  "type"
        type   "pending"
        item        =y
    ==>
    !eval! (snap-hands-to-home)
    =goal>
        isa     intention
        job     "typing"
        word    =y
    +retrieval>
        isa     word
        SPELLING    =y
)

(P retrieving-word
    =goal>
        isa     intention
        job     "typing"
        word    =w
        type   "pending"
        task      =x
        subtask   =y
        subsubtask =z
    =retrieval>
        type    =r
    ?visual-location>
        state    free
    ==>
    !bind!  =j  (typing-anchor-label =x =y =z)
    =goal>
        isa     typing
        word    =w
        type    "actual-word"
        CORRECT t
        check   "done"
        phase   nil
        token-index nil
        char-index nil
        current-token nil
        target-cell nil
        source-marker nil
        next-char nil
        token-done nil
        error-position none
        error-next-position none
        last-position nil
    +retrieval>
        isa     item
        word    =w
        position    first
    ;; shift attention to the typing anchor (last visual target, else the
    ;; instruction-panel label for this subtask)
    +visual-location>
        isa     visual-location
        Text    T
        text-value   =j
)

;; The anchor was not on screen (possible in live mode): fall back to the
;; instruction-panel label, which the model itself installs and is
;; therefore always present.
(P start-typing-anchor-fallback
    =goal>
        ISA       typing
        type      "actual-word"
        correct   t
        phase     nil
        task      =x
        subtask   =y
    ?visual-location>
        state   error
    ==>
    !bind! =lbl (concatenate-strings-subtask =x =y)
    +visual-location>
        isa     visual-location
        Text    T
        text-value   =lbl
)

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
    !bind! =typed-key (choose-key-with-typo-rate =l)
    !eval! (mark-keypress-for-check =l =typed-key)
    !bind! =check-mode (choose-actual-word-check-mode)
    !bind! =base (generic-shift-base-key =l =typed-key)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =typed-key))
    !bind! =next-phase (if (string-equal =needs-shift "yes")
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
    !bind! =check-mode (choose-actual-word-check-mode)
    !bind! =base (generic-shift-base-key =l =typed-key)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =typed-key))
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
   !eval! (snap-hands-to-home)
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
   !eval! (snap-hands-to-home)
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
    !bind! =base (generic-shift-base-key =l =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =l))
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
    !bind! =base (generic-shift-base-key =l =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =l))
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
    !bind! =base (generic-shift-base-key =l =typed-key)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =typed-key))
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

(p verify-final-typed-char
   =goal>
      ISA       typing
      word      =w
      type      "actual-word"
      phase     "verify-final-char"
      correct   "pending"
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
   !eval! (snap-hands-to-home)
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
    !bind! =base (generic-shift-base-key =l =l)
    !bind! =needs-shift (if (string-equal =base *no-shift-base-key*) "no" "yes")
    !bind! =press-key (if (string-equal =needs-shift "yes") "shift" (actr-key-for-char =l))
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

;; When typing is over, we move on to the next action.
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

;;; ========================================================================
;;; 6. Subtask / task bookkeeping and termination
;;; ========================================================================

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
    !bind! =limit (+ 1 *generic-total-tasks*)
    !eval! (when (< =y =limit) (mark-task-start =y))
    !eval! (when (< =y =limit) (mark-subtask-start =y 1))
    !bind! =next-job (if (< =y =limit) "retrieve-task" "done")
    !bind! =next-task (if (< =y =limit) =y =x)
    !bind! =next-subtask (if (< =y =limit) 1 =s)
    =goal>
        isa     intention
        job     =next-job
        task        =next-task
        subtask     =next-subtask
        subsubtask  1
)

(P stop-when-all-tasks-done
    =goal>
        isa     intention
        job     "done"
    ;; Wait for the motor module to be fully idle before stopping, otherwise the
    ;; run halts while the LAST action (e.g. the final "Press enter" that commits
    ;; an inline rename) is still mid-execution — its key-output never fires, so
    ;; the bridge never receives the enter and the rename is left uncommitted
    ;; (W03: folder stayed "New folder" with "Projects" typed but not confirmed).
    ?manual>
        state   free
    ==>
    !output! ("all tasks complete")
    !stop!)

)

;;; ========================================================================
;;; Instantiate the loaded task file's knowledge (chunks, panel, visicon,
;;; goal focus). Fails loudly if no task file was loaded first.
;;; ========================================================================
(install-generic-task-knowledge)
