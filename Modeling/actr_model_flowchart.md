# ACT-R Model Production Flowchart

Source model: `New_Error (3-5-2-TCP).lisp`

This chart was built from the ACT-R production rules in the model. In ACT-R, the left side of a production tests buffer contents, and the right side after `==>` changes buffers or sends requests. Most movement between productions in this model is controlled by the `goal` buffer, especially `goal.job` for high-level control and `goal.phase` for typing.

## How To Read This

- Each box is a production rule from the Lisp file.
- Arrows show the next production family that becomes eligible after the current production changes `goal.job`, `goal.phase`, `goal.type`, or requests a visual/retrieval/manual buffer action.
- Branch labels describe the buffer result or condition that selects the path.
- The main action loop is `5-retrieve-meaning-subtask -> 6-comprehend-action -> action-specific productions -> 5-retrieve-meaning-subtask`.
- `end` moves to the next subtask. `endsub` moves to the next task. Task 15 stops the model.

## 1. Main Controller And Action Dispatch

```mermaid
flowchart TD
    G0([goal-focus first-goal<br/>job retrieve-task])
    P1["1-start-task<br/>job retrieve-task -> move-vision-task"]
    P2["2-move-vision-to-task<br/>attend task label"]
    P3["3-move-attention-to-task<br/>request subtask label"]
    P4["4-move-attention-to-subtask<br/>attend subtask label"]
    P5["5-retrieve-meaning-subtask<br/>read next action from subtask list"]
    P6["6-comprehend-action<br/>retrieval actionencode -> meaning"]

    PEndSubtask["on-to-the-next-subtask<br/>imaginal action end"]
    PEndTask["on-to-the-next-task<br/>imaginal action endsub"]
    PStop["stop-at-task-15<br/>job done"]

    P71["7-1-item-categorization<br/>meaning attention-N-movecursor"]
    P72["7-2-pressing-enter<br/>meaning enter"]
    PClick["clicking<br/>meaning click"]
    PReadyType["ready-to-type<br/>meaning type"]
    PRetrieveWord["retrieving-word<br/>lookup word type"]

    TargetFlow[[Visual target and cursor flow<br/>see chart 2]]
    ActualWordFlow[[Actual-word typing flow<br/>see chart 3]]
    FormulaFlow[[Formula typing flow<br/>see chart 4]]
    PNextTyping["on-to-the-next-typing<br/>typing complete"]

    G0 --> P1 --> P2 --> P3 --> P4 --> P5 --> P6

    P6 -->|normal action| P71
    P6 -->|action end| PEndSubtask
    P6 -->|action endsub| PEndTask

    PEndSubtask -->|subtask + 1| P3
    PEndTask -->|task less than 15| P1
    PEndTask -->|task 15| PStop

    P71 --> TargetFlow --> P5
    P6 -->|meaning enter| P72 --> P5
    P6 -->|meaning click| PClick --> P5
    P6 -->|meaning type| PReadyType --> PRetrieveWord
    PRetrieveWord -->|type actual-word| ActualWordFlow --> PNextTyping --> P5
    PRetrieveWord -->|type formula| FormulaFlow --> P5
```

## 2. Visual Target Search And Cursor Movement

This is the largest controller branch. It handles `Goto`, `Move`, and `Select` style actions whose meaning is `attention-N-movecursor`.

```mermaid
flowchart TD
    P71["7-1-item-categorization<br/>retrieve target-spec"]
    P73["7-3-resolve-direct-cell-target<br/>direct cell"]
    P74["7-4-resolve-aliased-visual-target<br/>row header alias"]

    P76["7-6-find-row-header-location-direct<br/>request row header"]
    PAttendHeader["attend-row-header-location-direct<br/>move attention to row header"]

    PColSpec["use-column-target-spec<br/>alias is column header"]
    PObjSpec["use-object-target-spec<br/>ordinary visual object"]
    PNoSpec["no-target-spec-found<br/>missing target-spec"]

    PReadyCell["ready-to-attention-to-do-task-cell<br/>split cell into column and row"]
    PFindCol["find-column-location<br/>retrieve remembered column"]
    PUseCol["use-recalled-column-location"]
    PNoCol["no-recalled-column-location-try-neighbor"]
    PUseNearCol["use-neighbor-column-location"]
    PNoNearCol["no-neighbor-column-location-fallback"]
    PAttendCol["attending-column-location<br/>attend column header"]
    PEncodeCol["encode-attended-column-location<br/>store column sx/sy"]

    PFindRow["find-row-location<br/>retrieve remembered row"]
    PUseRow["use-recalled-row-location"]
    PNoRow["no-recalled-row-location-try-neighbor"]
    PUseNearRow["use-neighbor-row-location"]
    PNoNearRow["no-neighbor-row-location-fallback"]
    PAttendRow["attending-row-location<br/>attend row header"]
    PEncodeRow["encode-attended-row-location<br/>store row sx/sy"]

    PIntersect["find-intersection<br/>request visual-location at sx/sy"]
    PShift["shift-to-intersection<br/>attend target cell"]
    PMoveCell["move-attention-N-cursor-cell<br/>move mouse to cell"]

    PReadyNonCell["ready-to-attention-to-do-task-not-cell<br/>retrieve object location"]
    PUseObj["use-recalled-object-location"]
    PNoObj["no-recalled-object-location<br/>choose local/global search"]
    PReqLocal["request-local-neighbor-visual-search"]
    PReqGlobal["request-global-away-visual-search"]
    PSearchOK["visual-search-request-succeeded<br/>candidate found"]
    PFallback["visual-search-request-fallback-local<br/>visual-location error"]
    PAssure["move-attention-to-assure<br/>move attention to candidate"]
    PMoveObj["move-attention-N-cursor<br/>candidate matches item"]
    PFail["move-attention-fail<br/>candidate does not match"]

    P5Back[[back to 5-retrieve-meaning-subtask]]

    P71 -->|cell target-spec| P73 --> PReadyCell
    P71 -->|row target-spec| P74 --> P76 --> PAttendHeader --> PMoveCell
    P71 -->|column target-spec| PColSpec --> PFindCol
    P71 -->|object target-spec| PObjSpec --> PReadyNonCell
    P71 -->|retrieval failure| PNoSpec --> PReadyNonCell

    PReadyCell --> PFindCol
    PFindCol -->|remembered column| PUseCol --> PAttendCol
    PFindCol -->|retrieval failure| PNoCol -->|remembered neighbor| PUseNearCol --> PAttendCol
    PNoCol -->|neighbor failure| PNoNearCol --> PAttendCol
    PAttendCol --> PEncodeCol --> PFindRow

    PFindRow -->|remembered row| PUseRow --> PAttendRow
    PFindRow -->|retrieval failure| PNoRow -->|remembered neighbor| PUseNearRow --> PAttendRow
    PNoRow -->|neighbor failure| PNoNearRow --> PAttendRow
    PAttendRow --> PEncodeRow --> PIntersect --> PShift --> PMoveCell --> P5Back

    PReadyNonCell -->|remembered object| PUseObj --> PSearchOK
    PReadyNonCell -->|retrieval failure| PNoObj
    PNoObj -->|local| PReqLocal --> PSearchOK
    PNoObj -->|global| PReqGlobal --> PSearchOK
    PSearchOK --> PAssure
    PSearchOK -->|visual-location error| PFallback --> PSearchOK
    PAssure -->|visual text matches item| PMoveObj --> P5Back
    PAssure -->|visual text differs| PFail
    PFail -->|choose local/global again| PReqLocal
    PFail -->|choose local/global again| PReqGlobal
```

## 3. Actual-Word Typing And Repair

This branch is used when `retrieving-word` finds `type "actual-word"`. The model types character by character, optionally checks immediately, sometimes delays error realization, and repairs errors by deleting and retyping.

```mermaid
flowchart TD
    RW["retrieving-word<br/>goal becomes ISA typing<br/>type actual-word phase nil"]
    Start["start-typing<br/>first character"]
    Continue["continue-typing<br/>middle characters"]
    Finish["finish-typing<br/>final character"]

    ShiftNow["type-actual-word-shift-base<br/>shifted char, check now"]
    ShiftSkip["type-actual-word-shift-base-skip<br/>shifted char, check later"]
    Skip["skip-actual-word-check<br/>mark char accepted"]
    Check["check-letter<br/>type-check current char"]
    VisualCheck["continue-typing-with-visual-check<br/>TODO visual check path"]

    DelayedStart["realize-delayed-error-start<br/>stored error-position exists"]
    DeleteBack["delete-back-or-retype-delayed-error<br/>delete back until error"]
    DeleteFirst["delete-first-delayed-error-and-retype<br/>error was first char"]
    Correct["correct-letter<br/>delete latest bad char"]
    Retype["retype-corrected-letter"]
    RetypeFinal["retype-final-corrected-letter"]
    RetypeShift["retype-corrected-letter-shift-base"]
    RetypeFinalShift["retype-final-corrected-letter-shift-base"]

    FinalShift["type-final-char-shift-base"]
    VerifyFinal["verify-final-typed-char"]
    RepairFinalDelete["repair-final-typed-char-delete"]
    RepairFinalRetype["repair-final-typed-char-retype"]
    RepairFinalShift["repair-final-typed-char-retype-shift-base"]
    DoneTyping["on-to-the-next-typing<br/>correct done"]

    RW --> Start
    Start -->|unshifted and check now| Check
    Start -->|shifted and check now| ShiftNow --> Check
    Start -->|unshifted and check later| Skip
    Start -->|shifted and check later| ShiftSkip --> Skip

    Skip -->|more chars| Continue
    Skip -->|final char next| Finish

    Check -->|correct true and more chars| Continue
    Check -->|correct true and final char next| Finish
    Check -->|correct false| Correct
    Check -->|delayed error-position not none| DelayedStart
    VisualCheck -.-> Check

    Correct -->|retrieval has next| Retype
    Correct -->|retrieval next nil| RetypeFinal
    Retype -->|more chars, unshifted| Check
    Retype -->|more chars, shifted| RetypeShift --> Check
    RetypeFinal -->|final char, unshifted| VerifyFinal
    RetypeFinal -->|final char, shifted| RetypeFinalShift --> VerifyFinal

    DelayedStart --> DeleteBack
    DeleteBack -->|not at error yet| DeleteBack
    DeleteBack -->|at error and retrieval has next| Retype
    DeleteBack -->|at error and retrieval next nil| RetypeFinal
    DelayedStart -->|first char error| DeleteFirst
    DeleteFirst -->|retrieval has next| Retype
    DeleteFirst -->|retrieval next nil| RetypeFinal

    Continue -->|unshifted and check now| Check
    Continue -->|shifted and check now| ShiftNow
    Continue -->|unshifted and check later| Skip
    Continue -->|shifted and check later| ShiftSkip
    Continue -->|retrieval says next nil| Finish

    Finish -->|unshifted| VerifyFinal
    Finish -->|shifted| FinalShift --> VerifyFinal
    VerifyFinal -->|type-check done| DoneTyping
    VerifyFinal -->|type-check false| RepairFinalDelete --> RepairFinalRetype
    RepairFinalRetype -->|unshifted| VerifyFinal
    RepairFinalRetype -->|shifted| RepairFinalShift --> VerifyFinal
```

## 4. Formula Typing And Repair

This branch is used when `retrieving-word` finds `type formula`. Unlike actual-word typing, formula typing tokenizes the formula, looks back to the instruction/source between tokens, and then returns attention to the target cell.

```mermaid
flowchart TD
    RWFormula["retrieving-word<br/>type formula"]
    StartFormula["start-typing-formula<br/>target-cell and first token"]
    Memorize["memorize-token-and-shift-to-target<br/>attend formula target"]
    Compute["compute-next-char-of-current-token<br/>phase typing-token"]

    TypeChar["type-next-char-of-current-token<br/>unshifted char"]
    TypeShiftPrefix["type-shifted-char-prefix<br/>press shift"]
    TypeShiftBase["type-shifted-char-base<br/>press base key"]
    Verify["verify-formula-char<br/>type-check"]

    DeleteBad["correct-formula-char-delete"]
    RetypeBad["correct-formula-char-retype<br/>unshifted repair"]
    RetypeShiftPrefix["correct-shifted-formula-char-retype-prefix"]
    RetypeShiftBase["correct-shifted-formula-char-retype-base"]

    TokenDone["finished-current-token-go-back-to-formula<br/>advance token-index"]
    LookBack["look-back-to-formula-before-next-token<br/>attend formula source"]
    ReturnTarget["return-attention-to-formula-target<br/>request target cell"]
    Resume["resume-formula-typing-after-lookback<br/>return to target"]
    EndFormula["end-of-formula<br/>back to action retrieval"]
    P5Back[[5-retrieve-meaning-subtask]]

    RWFormula --> StartFormula --> Memorize --> Compute
    Compute -->|token has unshifted char| TypeChar --> Verify
    Compute -->|token has shifted char| TypeShiftPrefix --> TypeShiftBase --> Verify
    Compute -->|end of current token| TokenDone

    Verify -->|correct true| Compute
    Verify -->|correct false| DeleteBad
    DeleteBad -->|unshifted char| RetypeBad --> Verify
    DeleteBad -->|shifted char| RetypeShiftPrefix --> RetypeShiftBase --> Verify

    TokenDone --> LookBack --> ReturnTarget --> Resume
    Resume -->|next token exists| Compute
    Resume -->|current-token __end_of_formula__| EndFormula --> P5Back
```

## Production Coverage

The charts above include the following production groups:

- Controller: `1-start-task`, `2-move-vision-to-task`, `3-move-attention-to-task`, `4-move-attention-to-subtask`, `5-retrieve-meaning-subtask`, `6-comprehend-action`, `on-to-the-next-subtask`, `on-to-the-next-task`, `stop-at-task-15`.
- Action dispatch: `7-1-item-categorization`, `7-2-pressing-enter`, `clicking`, `ready-to-type`, `retrieving-word`, `on-to-the-next-typing`.
- Visual target/cursor movement: `7-3-resolve-direct-cell-target`, `7-4-resolve-aliased-visual-target`, `7-6-find-row-header-location-direct`, `attend-row-header-location-direct`, `use-column-target-spec`, `use-object-target-spec`, `no-target-spec-found`, `ready-to-attention-to-do-task-not-cell`, `use-recalled-object-location`, `no-recalled-object-location`, `request-local-neighbor-visual-search`, `request-global-away-visual-search`, `visual-search-request-succeeded`, `visual-search-request-fallback-local`, `ready-to-attention-to-do-task-cell`, `find-column-location`, `use-recalled-column-location`, `no-recalled-column-location-try-neighbor`, `use-neighbor-column-location`, `no-neighbor-column-location-fallback`, `attending-column-location`, `encode-attended-column-location`, `find-row-location`, `use-recalled-row-location`, `no-recalled-row-location-try-neighbor`, `use-neighbor-row-location`, `no-neighbor-row-location-fallback`, `attending-row-location`, `encode-attended-row-location`, `find-intersection`, `shift-to-intersection`, `move-attention-N-cursor-cell`, `move-attention-to-assure`, `move-attention-N-cursor`, `move-attention-fail`.
- Actual-word typing: `start-typing`, `type-actual-word-shift-base`, `type-actual-word-shift-base-skip`, `continue-typing`, `continue-typing-with-visual-check`, `skip-actual-word-check`, `realize-delayed-error-start`, `delete-back-or-retype-delayed-error`, `delete-first-delayed-error-and-retype`, `check-letter`, `correct-letter`, `retype-corrected-letter`, `retype-final-corrected-letter`, `retype-corrected-letter-shift-base`, `retype-final-corrected-letter-shift-base`, `finish-typing`, `type-final-char-shift-base`, `verify-final-typed-char`, `repair-final-typed-char-delete`, `repair-final-typed-char-retype`, `repair-final-typed-char-retype-shift-base`.
- Formula typing: `start-typing-formula`, `memorize-token-and-shift-to-target`, `compute-next-char-of-current-token`, `type-next-char-of-current-token`, `type-shifted-char-prefix`, `type-shifted-char-base`, `verify-formula-char`, `correct-formula-char-delete`, `correct-formula-char-retype`, `correct-shifted-formula-char-retype-prefix`, `correct-shifted-formula-char-retype-base`, `finished-current-token-go-back-to-formula`, `look-back-to-formula-before-next-token`, `return-attention-to-formula-target`, `resume-formula-typing-after-lookback`, `end-of-formula`.
