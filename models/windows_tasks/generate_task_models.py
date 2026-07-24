"""Validate task_specs.json and generate the ACT-R task chunk files for the
generic-interface EVisiTor model.

For every task in task_specs.json this script:
  1. validates the normalized action lists against the model's vocabulary
     (Goto, Move, Select, Type, Press, RightClick, Scroll, ClickDown,
     ClickUp), the schema rules (one object per action, ordered, end/endsub
     terminators), the typeable character set, the allowed Press key-command
     grammar, the Scroll direction set, and the drag/right-click structure
     rules (target under the cursor, button released after being held);
  2. emits a complete, standalone chunk file  tasks/<ID>_<name>.lisp  that
     contains ALL declarative knowledge the generic model needs:
       - the subtaskN_M_list normalized action lists,
       - Task and first-goal chunks,
       - WORD + letter `item` chains for every Type target (with ordinal
         positions and inter-ordinal similarities),
       - target-spec chunks for every visual-action label,
       - placeholder visicon features for offline validation runs
         (labels listed in a task's `scroll_reveals` are deferred to
         *generic-scroll-reveal-features* and only enter the visicon when
         the model's first Scroll executes);
  3. emits tasks/ALL<N>_windows_tasks.lisp with all tasks in sequence
     for a single batch run;
  4. writes validation_report.md.

Usage:  python generate_task_models.py
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPECS = HERE / "task_specs.json"
TASKS_DIR = HERE / "tasks"
REPORT = HERE / "validation_report.md"

VERBS = {"Goto", "Move", "Select", "Type", "Press",
         "RightClick", "Scroll", "ClickDown", "ClickUp"}
# Verbs whose target is a visual object (gets a target-spec chunk and a
# placeholder visicon feature). Scroll's target is a direction, not an object.
VISUAL_VERBS = {"Goto", "Move", "Select", "RightClick", "ClickDown", "ClickUp"}
# Verbs that act on the object under the cursor and therefore must follow a
# Goto/Move of the same target within the subtask.
AT_CURSOR_VERBS = {"Select", "RightClick", "ClickDown"}
SCROLL_DIRECTIONS = {"down", "up"}

# Keyboard support mirrored from generic_helpers.lisp / fucntion_new_tcp.lisp
PLAIN_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | set("-=[];',./`")
SHIFTED_SYMBOLS = set('!@#$%^&*()_+{}|:"<>?~')
UPPER = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

PRESS_MODIFIERS = {"win", "ctrl", "alt", "shift"}
PRESS_FINAL_KEYS = (
    {"enter", "return", "esc", "escape", "tab", "delete", "del", "space",
     "end", "home", "pageup", "pagedown", "up", "down", "left", "right",
     "win"}  # bare "win" opens the Start menu
    | {f"f{i}" for i in range(1, 25)}
    | set("abcdefghijklmnopqrstuvwxyz0123456789")
)

ORDINALS = [
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
    "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
    "nineteenth", "twentieth", "twenty-first", "twenty-second",
    "twenty-third", "twenty-fourth", "twenty-fifth", "twenty-sixth",
    "twenty-seventh", "twenty-eighth", "twenty-ninth", "thirtieth",
]


def lisp_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_type_target(target: str, where: str, problems: list):
    if not target:
        problems.append(f"{where}: empty Type target")
        return
    for ch in target:
        if ch in PLAIN_KEYS or ch in SHIFTED_SYMBOLS or ch in UPPER:
            continue
        if ch == " ":
            problems.append(
                f"{where}: Type target {target!r} contains a space; the motor "
                "layer maps it to the space key but VisiTor delivery of ' ' "
                "is unverified — avoid if possible")
            continue
        problems.append(
            f"{where}: Type target {target!r} contains unsupported character {ch!r}")


def validate_press_target(target: str, where: str, problems: list):
    parts = target.lower().split("+")
    if len(parts) == 1:
        if parts[0] not in PRESS_FINAL_KEYS:
            problems.append(f"{where}: Press key {target!r} not in the allowed key set")
        return
    *mods, final = parts
    for m in mods:
        if m not in PRESS_MODIFIERS:
            problems.append(f"{where}: Press chord {target!r} has unknown modifier {m!r}")
    if final not in PRESS_FINAL_KEYS:
        problems.append(f"{where}: Press chord {target!r} has unknown final key {final!r}")


def validate_task(task: dict, problems: list, warnings: list):
    tid = task["id"]
    subtasks = task.get("subtasks", [])
    if not subtasks:
        problems.append(f"{tid}: no subtasks")
        return
    n_actions = 0
    for si, sub in enumerate(subtasks, start=1):
        if not sub:
            problems.append(f"{tid} subtask {si}: empty")
            continue
        seen_moves: list[str] = []   # Goto/Move targets so far in this subtask
        held_target = None           # ClickDown target awaiting ClickUp
        for ai, action in enumerate(sub, start=1):
            where = f"{tid} subtask {si} action {ai}"
            if (not isinstance(action, list)) or len(action) != 2:
                problems.append(f"{where}: action must be [Verb, \"Target\"], got {action!r}")
                continue
            verb, target = action
            if verb in ("end", "endsub"):
                problems.append(f"{where}: terminators are generator-added; remove {verb!r} from the spec")
                continue
            if verb not in VERBS:
                problems.append(f"{where}: unknown verb {verb!r} (vocabulary: {sorted(VERBS)})")
                continue
            if not isinstance(target, str) or not target:
                problems.append(f"{where}: target must be one non-empty string")
                continue
            n_actions += 1
            if verb == "Type":
                validate_type_target(target, where, problems)
            elif verb == "Press":
                validate_press_target(target, where, problems)
            elif verb == "Scroll":
                if target.lower() not in SCROLL_DIRECTIONS:
                    problems.append(
                        f"{where}: Scroll target must be one of "
                        f"{sorted(SCROLL_DIRECTIONS)}, got {target!r}")
            else:
                if len(target) > 64:
                    warnings.append(f"{where}: unusually long visual label")
            # structure rules for cursor-anchored and drag actions
            if verb in ("Goto", "Move"):
                seen_moves.append(target)
            if verb in AT_CURSOR_VERBS and (not seen_moves or seen_moves[-1] != target):
                warnings.append(
                    f"{where}: {verb} {target!r} is not immediately preceded by a "
                    f"Goto/Move of the same target; the click lands wherever the "
                    f"cursor currently is")
            if verb == "ClickDown":
                if held_target is not None:
                    problems.append(f"{where}: ClickDown while the button is already held (from {held_target!r})")
                held_target = target
            if verb == "ClickUp":
                if held_target is None:
                    problems.append(f"{where}: ClickUp without a preceding ClickDown in this subtask")
                held_target = None
        if held_target is not None:
            problems.append(f"{tid} subtask {si}: ClickDown {held_target!r} never released by a ClickUp")
        # attention-only subtasks (Goto with no Select) are allowed: W07/W09/W10
    action_labels = {
        a[1]
        for sub in subtasks for a in sub
        if isinstance(a, list) and len(a) == 2}
    for label in task.get("verify_uia", []):
        if label not in action_labels:
            warnings.append(f"{tid}: verify_uia label {label!r} not used by any action")
    for label in task.get("scroll_reveals", []):
        if label not in action_labels:
            problems.append(f"{tid}: scroll_reveals label {label!r} not used by any action")
    if task.get("scroll_reveals") and not any(
            a[0] == "Scroll"
            for sub in subtasks for a in sub
            if isinstance(a, list) and len(a) == 2):
        problems.append(f"{tid}: scroll_reveals given but the task has no Scroll action")
    return n_actions


# ---------------------------------------------------------------------------
# Chunk generation
# ---------------------------------------------------------------------------

def word_letter_chunks(word_idx: int, word: str) -> list[str]:
    """WORD chunk + character `item` chain, same shape as the Excel model."""
    if len(word) > len(ORDINALS):
        raise ValueError(f"word {word!r} longer than the ordinal inventory ({len(ORDINALS)})")
    lines = [f"    (word-{word_idx} ISA WORD TYPE \"actual-word\" SPELLING {lisp_string(word)})"]
    n = len(word)
    for i, ch in enumerate(word):
        pos = ORDINALS[i]
        nxt = ORDINALS[i + 1] if i + 1 < n else "nil"
        prev = ORDINALS[i - 1] if i > 0 else "nil"
        after = "t" if i + 1 < n else "nil"
        lines.append(
            f"    (w{word_idx}-l{i + 1} ISA item word {lisp_string(word)} "
            f"current {lisp_string(ch)} after {after} position {pos} "
            f"next {nxt} previous {prev})")
    return lines


def similarities_forms(max_len: int) -> str:
    pairs = [
        f"     ({ORDINALS[i]} {ORDINALS[i + 1]} -0.5)"
        for i in range(min(max_len, len(ORDINALS)) - 1)
    ]
    return "  (set-similarities-fct '(\n" + "\n".join(pairs) + "))"


def visicon_layout(labels: list[str]) -> list[tuple[str, int, int]]:
    xs = [120, 320, 520, 720]
    out = []
    for i, label in enumerate(labels):
        out.append((label, xs[i % 4], 120 + 70 * (i // 4)))
    return out


def emit_task_lisp(tasks: list[dict], total_tasks: int, header: str) -> str:
    """Emit one chunk file covering `tasks` numbered 1..total_tasks."""
    lines = [header]
    lines.append("(proclaim-subtask-specials 30 60)")
    lines.append("(clear-subtask-lists 30 60)")
    lines.append(f"(defparameter *generic-total-tasks* {total_tasks})")
    lines.append("")

    words: list[str] = []            # unique Type targets, in first-use order
    visual_labels: list[str] = []    # unique visual-action targets
    verify = {}
    reveal_labels: list[str] = []    # labels deferred until the first Scroll

    for tnum, task in enumerate(tasks, start=1):
        lines.append(f";;; --- Task {tnum}: {task['id']} ({task['app']}, {task['difficulty']})")
        lines.append(f";;; {task['instruction']}")
        lines.append(f";;; PSAI unique_data_id: {task['unique_data_id']}")
        subtasks = task["subtasks"]
        for si, sub in enumerate(subtasks, start=1):
            terminator = "endsub" if si == len(subtasks) else "end"
            steps = []
            for verb, target in sub:
                steps.append(f"({verb} {lisp_string(target)})")
                if verb == "Type" and target not in words:
                    words.append(target)
                if verb in VISUAL_VERBS and target not in visual_labels:
                    visual_labels.append(target)
            steps.append(f"({terminator})")
            lines.append(f"(setq subtask{tnum}_{si}_list '({' '.join(steps)}))")
        for label in task.get("verify_uia", []):
            verify[label] = task["id"]
        for label in task.get("scroll_reveals", []):
            if label not in reveal_labels:
                reveal_labels.append(label)
        lines.append("")

    # ---- declarative chunks -------------------------------------------------
    lines.append("(defun install-task-chunks ()")
    lines.append("  (add-dm-fct '(")
    for tnum in range(1, total_tasks + 1):
        lines.append(f"    (Task{tnum} ISA Task Number {tnum})")
    lines.append("    (first-goal ISA intention job \"retrieve-task\" task 1)")
    lines.append("")
    lines.append("    ;; Words to type: character chains with ordinal positions")
    for wi, word in enumerate(words, start=1):
        lines.extend(word_letter_chunks(wi, word))
        lines.append("")
    lines.append("    ;; Visual targets (protected UIA labels resolve to themselves)")
    for li, label in enumerate(visual_labels, start=1):
        flag = f"  ; #VERIFY-UIA ({verify[label]})" if label in verify else ""
        lines.append(
            f"    (ts-{li} ISA target-spec label {lisp_string(label)} "
            f"lookup-text {lisp_string(label)} lookup-cell-type \"object\" "
            f"target-type \"nil\"){flag}")
    lines.append("  ))")
    max_word = max((len(w) for w in words), default=2)
    lines.append(similarities_forms(max_word))
    lines.append("  t)")
    lines.append("")

    # ---- offline placeholder visicon ---------------------------------------
    lines.append(";; Placeholder UI features for offline validation runs (no live UIA).")
    lines.append(";; Coordinates are an arbitrary grid left of the instruction-panel")
    lines.append(";; boundary; a live run replaces these with the UIA->visicon converter.")
    layout = visicon_layout(visual_labels)
    feature = {
        label: (f"(screen-x {x} screen-y {y} height 30 width 70 "
                f"color red value {lisp_string(label)} text-value {lisp_string(label)} "
                f"type \"text\" text T)")
        for label, x, y in layout}
    lines.append("(defun install-task-visicon ()")
    for label, _, _ in layout:
        if label in reveal_labels:
            continue
        lines.append(f"  (add-visicon-features '{feature[label]})")
    lines.append("  t)")
    lines.append("")
    # Labels below the fold: enter the visicon only when the first Scroll
    # executes (generic_helpers.lisp scroll-wheel-action). Always emitted so
    # a reloaded task file clears any stale reveal list.
    if reveal_labels:
        lines.append(";; Deferred features that scrolling brings into view (offline stand-in")
        lines.append(";; for below-the-fold content).")
        lines.append("(defparameter *generic-scroll-reveal-features*")
        lines.append("  (list")
        for label in reveal_labels:
            lines.append(f"    '{feature[label]}")
        lines.append("  ))")
    else:
        lines.append("(defparameter *generic-scroll-reveal-features* nil)")
    lines.append("")
    return "\n".join(lines)


def file_header(title: str, extra: str = "") -> str:
    return (
        ";;; ============================================================================\n"
        f";;; {title}\n"
        ";;; GENERATED by generate_task_models.py from task_specs.json — do not edit\n"
        ";;; by hand; edit the spec and regenerate.\n"
        ";;; Load AFTER fucntion_new_tcp.lisp + generic_helpers.lisp and BEFORE\n"
        ";;; generic_interface_model.lisp (or use load_generic_task.lisp).\n"
        + (f";;; {extra}\n" if extra else "")
        + ";;; ============================================================================\n"
    )


def main() -> int:
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    tasks = spec["tasks"]
    problems: list[str] = []
    warnings: list[str] = []
    stats = []

    for task in tasks:
        n = validate_task(task, problems, warnings)
        n_sub = len(task.get("subtasks", []))
        stats.append((task["id"], task["app"], task["difficulty"], n_sub, n or 0))

    if problems:
        print("VALIDATION FAILED:")
        for p in problems:
            print("  -", p)

    TASKS_DIR.mkdir(exist_ok=True)
    written = []
    if not problems:
        for task in tasks:
            fname = f"{task['id']}_{task['name']}.lisp"
            header = file_header(
                f"Task chunks {task['id']}: {task['instruction']}",
                f"App: {task['app']} | difficulty: {task['difficulty']} | "
                f"PSAI id: {task['unique_data_id']}")
            (TASKS_DIR / fname).write_text(
                emit_task_lisp([task], 1, header), encoding="utf-8")
            written.append(fname)
        all_name = f"ALL{len(tasks)}_windows_tasks.lisp"
        all_header = file_header(
            f"ALL {len(tasks)} Windows tasks in sequence (tasks 1..{len(tasks)}) for a batch run")
        (TASKS_DIR / all_name).write_text(
            emit_task_lisp(tasks, len(tasks), all_header), encoding="utf-8")
        written.append(all_name)

    # ---- report -------------------------------------------------------------
    rep = ["# Generic-interface task chunk validation report", ""]
    rep.append(f"Spec: `task_specs.json` ({len(tasks)} tasks). "
               f"Generator: `generate_task_models.py`.")
    rep.append("")
    rep.append("| Task | App | Difficulty | Subtasks | Atomic actions |")
    rep.append("|------|-----|-----------|----------|----------------|")
    for tid, app, diff, n_sub, n_act in stats:
        rep.append(f"| {tid} | {app} | {diff} | {n_sub} | {n_act} |")
    rep.append("")
    total_sub = sum(s[3] for s in stats)
    total_act = sum(s[4] for s in stats)
    rep.append(f"**Totals: {len(tasks)} tasks, {total_sub} subtask lists, "
               f"{total_act} atomic actions.**")
    rep.append("")
    rep.append("## Checks performed")
    rep.append("- action verbs within the 9-verb vocabulary (Goto, Move, Select, Type, "
               "Press, RightClick, Scroll, ClickDown, ClickUp)")
    rep.append("- exactly one non-empty string object per action; order preserved")
    rep.append("- terminators (`end`/`endsub`) are generator-emitted: every subtask closes "
               "with `end`, the last subtask of a task with `endsub`")
    rep.append("- Type targets restricted to the supported keyboard character set "
               "(plain keys, shifted symbols, uppercase letters)")
    rep.append("- Press targets restricted to named keys and modifier chords over "
               "{win, ctrl, alt, shift}")
    rep.append("- Scroll targets restricted to {down, up}")
    rep.append("- Select/RightClick/ClickDown warned unless immediately preceded by a "
               "Goto/Move of the same target; every ClickDown must be released by a "
               "ClickUp within its subtask")
    rep.append("- `verify_uia` labels cross-checked against the action lists; "
               "`scroll_reveals` labels must be action targets in a task that scrolls")
    rep.append("")
    rep.append(f"## Result: {'FAILED' if problems else 'PASSED'}")
    if problems:
        rep.append("")
        rep.extend(f"- ERROR: {p}" for p in problems)
    if warnings:
        rep.append("")
        rep.extend(f"- warning: {w}" for w in warnings)
    if written:
        rep.append("")
        rep.append("## Generated files")
        rep.extend(f"- `tasks/{f}`" for f in written)
    REPORT.write_text("\n".join(rep) + "\n", encoding="utf-8")
    print(f"{'FAILED' if problems else 'PASSED'}: {len(tasks)} tasks, "
          f"{total_sub} subtasks, {total_act} actions; "
          f"{len(written)} lisp files written; report -> {REPORT.name}")
    for w in warnings:
        print("  warning:", w)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
