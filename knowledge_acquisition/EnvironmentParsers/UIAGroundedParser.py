"""UIA-grounded LLM step-parsing evaluation for the ten Windows tasks.

Clone of the Excel RQ3 evaluation (InstructionAcquisitionParser.py) applied
to the W01-W10 generic-interface tasks, with one experimental manipulation:
whether the prompt contains the UIA element dump the ACT-R model actually
perceives, so the LLM can ground its action targets in the real element
names -- and gracefully fall back to a generic term for elements that are
not visible yet.

Design (see GenericInterface/HANDOFF_UIA_GROUNDED_PARSING_2026-07-08.md):

  models      : the MODELS list from InstructionAcquisitionParser (the
                paper's model set; call/retry layer is imported from there).
  variants    : instruction      - the task_specs.json instruction sentence
                paraphrase       - hand-written rewording (this file)
                guide            - step-by-step procedural walk-through
                                   (GUIDES in this file, added 2026-07-15) so
                                   all models follow the same strategy
                reasoning_steps  - the PSAI demonstration's reasoning_steps
                                   (cached in llm_parsing_eval/
                                   reasoning_steps_cache.json; five tasks
                                   have none and are skipped in that variant)
  conditions  : no-uia       - prompt without any UIA context (baseline)
                initial-uia  - pruned visicons_001.json of the newest
                               completed live run of the task (start-of-task
                               screen; later targets absent -> exercises the
                               generic-term fallback)
                full-uia     - deduped union of ALL snapshots of that run
                               (upper bound: every name the model ever saw)

  gold        : task_specs.json "subtasks" (already [(verb, target), ...]
                per subtask), keyed (task_number 1-10, subtask_index 1-N).

  metrics     : the five extraction metrics from the Excel eval, plus
                UIA-resolvability (initial + union) and generic-fallback
                correctness (uia_grounding_common.compute_uia_metrics),
                plus a spec-shape execution check that re-validates each
                generated parse with generate_task_models.validate_task.

Outputs (GenericInterface/llm_parsing_eval/):
  <model>__<variant>__<condition>.json   raw per-task LLM outputs
  metrics_report.json                    all metrics, checkpointed per model
  model_comparison.md                    summary tables

Usage:
  python EnvironmentParsers/UIAGroundedParser.py
  python EnvironmentParsers/UIAGroundedParser.py --providers openai --conditions initial-uia
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GI_DIR = os.path.join(ROOT, "EVisiTor2026", "NewInterfaces_PSAI",
                      "GenericInterface")
OUTPUT_DIR = os.path.join(GI_DIR, "llm_parsing_eval")

sys.path.insert(0, HERE)
sys.path.insert(0, GI_DIR)

import InstructionAcquisitionParser as iap  # noqa: E402  (call layer + metrics)
from uia_grounding_common import (  # noqa: E402
    compute_uia_metrics, element_names, load_elements, prune_elements,
    render_uia_block)
from analyze_task_times import completed_run_rows  # noqa: E402
from generate_task_models import validate_task  # noqa: E402

CONDITIONS = ["no-uia", "initial-uia", "full-uia"]
VARIANTS = ["instruction", "paraphrase", "reasoning_steps", "guide"]

UIA_PROMPT_CAP = 300  # elements per prompt; truncation is reported

# Windows-task verb vocabulary (2026-07-15): the generic model's runtime
# supports RightClick (context menus) and Scroll, and the gold uses RightClick
# in W03/W04. The structured-output schema sent with every call previously
# reused the Excel eval's 5-verb enum, which made it IMPOSSIBLE for a model to
# emit RightClick regardless of the prompt. The Windows eval now sends its own
# schema; the Excel eval (InstructionAcquisitionParser defaults) is unchanged.
W_ALLOWED_ACTIONS = ["Goto", "Move", "Select", "Type", "Press",
                     "RightClick", "Scroll"]
W_SCHEMA = iap.schema_for_actions(W_ALLOWED_ACTIONS)

# ---------------------------------------------------------------------------
# Instruction variants
# ---------------------------------------------------------------------------
# `instruction` comes from task_specs.json. `reasoning_steps` comes from the
# PSAI demonstration (reasoning_steps_cache.json). The hand-written
# paraphrases below reword the spec instruction without adding or removing
# information (in particular they do NOT mention steps the instruction leaves
# implicit, e.g. closing Notepad in W01).
# ---------------------------------------------------------------------------

PARAPHRASES: Dict[str, str] = {
    # Updated 2026-07-15 for the current six-task gold (W04=zip_logs_folder,
    # W09=open_calculator; W02/W10 reworded to match their amended
    # instructions/start states). The old 10-task paraphrases are preserved in
    # llm_parsing_eval_backup_pre6task_20260710/.
    "W01": "Launch the Run box with the Win+R keyboard shortcut and use it "
           "to start Notepad.",
    "W02": "Launch File Explorer, then change the name of the file "
           "'budget.xlsx' so that it becomes 'budget_2025.xlsx'.",
    "W03": "On the Desktop, make a new folder and call it 'Projects' "
           "(use File Explorer).",
    "W04": "Turn the folder 'Logs' into a compressed ZIP archive.",
    "W09": "Use the search bar of the Windows Start menu to find and open "
           "the Calculator.",
    "W10": "File Explorer is open already; use the search box in the "
           "Documents folder to look for a file called 'report.docx'.",
}


# ---------------------------------------------------------------------------
# Step-by-step guides (variant "guide", added 2026-07-15)
# ---------------------------------------------------------------------------
# Procedural walk-throughs that spell out the demonstrated interaction path,
# so every model is pushed toward the SAME strategy for the same problem
# (e.g. the legacy Send-to zip path for W04, not Compress-to or a third-party
# tool). One string per gold subtask, in gold order. These are the "steps"
# input, exactly like reasoning_steps.
# ---------------------------------------------------------------------------

GUIDES: Dict[str, List[str]] = {
    "W01": [
        "Press Win+R to open the Run dialog.",
        "Type 'notepad' and press Enter.",
    ],
    "W02": [
        "Click the File Explorer icon on the taskbar to open File Explorer.",
        "Click the file 'budget.xlsx' in the file list.",
        "Click the Rename button in the toolbar.",
        "Type 'budget_2025.xlsx' and press Enter.",
    ],
    "W03": [
        # 2026-07-16: guide + gold switched from "right-click the empty
        # background > New > Folder" to the Ctrl+Shift+N chord. The empty
        # folder-view region is not a UIA visual item (no scan exposes a
        # 'Desktop background' element; its only UIA text is 'This folder
        # is empty.'), so the old step could never be grounded.
        "Click the File Explorer icon on the taskbar to open File Explorer.",
        "Click 'Desktop' in the navigation pane.",
        "Press Ctrl+Shift+N to create a new folder.",
        "Type 'Projects' and press Enter.",
    ],
    "W04": [
        "Right-click the folder 'Logs'.",
        "Click 'Show more options' in the context menu.",
        "Click 'Send to', then click 'Compressed (zipped) folder' in the "
        "submenu that opens.",
        "Press Enter to accept the default archive name.",
    ],
    "W09": [
        "Click the Search box on the taskbar.",
        "Type 'calculator' and press Enter.",
        "Look at the Calculator window that opened.",
    ],
    "W10": [
        "File Explorer is already open. Click 'Documents' in the "
        "navigation pane.",
        "Click the search box labeled 'Search Documents'.",
        "Type 'report.docx' and press Enter.",
        "Look at the search result 'report.docx'.",
    ],
}


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
# Adapted from iap.PROMPT_HEADER: same 5-verb vocabulary, segmentation and
# pairing rules and a few-shot shape example from a different domain; the
# Excel cell-coordinate conventions are dropped and replaced by Windows
# key-command conventions (fixed-cost vocabulary documentation, mirroring the
# Excel prompt's naming-convention notes). {uia_block} is empty in the no-uia
# condition.
# ---------------------------------------------------------------------------

W_PROMPT_TEMPLATE = """\
You convert a natural-language Windows desktop task instruction into a
structured action representation for an ACT-R cognitive model that simulates
desktop UI use (File Explorer, Windows Settings, dialogs).

For the task you receive:
  1. Split it into ordered "subtasks". A subtask is the smallest unit that
     has its own selection target or its own key command -- e.g. "click the
     Rename button" is ONE subtask (Goto Rename, Select Rename); "type
     budget_2025.xlsx and press Enter" is ONE subtask (Type "...",
     Press "enter"); a keyboard shortcut like Win+R is its own subtask
     (Press "win+r").
  2. Within each subtask, list atomic actions in order.

Allowed verbs (use these exactly): Goto, Move, Select, Type, Press,
RightClick, Scroll.
  - Goto/Move : shift visual attention to a UI element (an icon, a file in a
                list, a navigation-pane item, a button). Prefer Goto.
  - Select    : left-click/activate the element reached by the preceding
                Goto/Move. Pair every Goto with a matching Select for the
                same target, EXCEPT when the step only requires looking at /
                locating something without clicking it (then use Goto alone).
  - RightClick: right-click the element reached by the preceding Goto/Move
                (opens that element's context menu). Like Select, pair it
                with a preceding Goto for the same target.
  - Type      : type a literal string exactly as written (file names keep
                their extension and case).
  - Press     : one key or key chord. Lowercase, joined with "+": "enter",
                "win+r", "ctrl+shift+n", "ctrl+x". The physical Delete key
                is "forward-delete".
  - Scroll    : scroll the current view; the target is a direction, "down"
                or "up".

Conventions:
  - Action targets are the visible names of UI elements as a user reads them.
  - Context-menu entries opened by a RightClick (and their cascading
    submenu entries) are ordinary elements: pick each one with its own
    Goto + Select pair.
  - The Run dialog opens with Press "win+r"; the Windows Settings app opens
    with Press "win+i".
  - Standard file-manipulation chords are available: cut "ctrl+x", paste
    "ctrl+v", new folder "ctrl+shift+n".
  - When an instruction implies a repetition you MUST expand it into the
    full set of subtasks. Do not abbreviate.

Use the task_id given in the input; number subtasks starting at 1. Return
exactly one task.

Example (different domain, just to show output shape):

INPUT:
[
  {"task_id": 1, "task_name": "mute_system_sound",
   "steps": ["Open the sound mixer with Ctrl+M, click Mute, then close the mixer window."]}
]
OUTPUT:
{"tasks":[{"task_id":1,"task_name":"mute_system_sound","subtasks":[
  {"subtask_id":1,"actions":[
    {"action":"Press","target":"ctrl+m"}]},
  {"subtask_id":2,"actions":[
    {"action":"Goto","target":"Mute"},
    {"action":"Select","target":"Mute"}]},
  {"subtask_id":3,"actions":[
    {"action":"Goto","target":"Close"},
    {"action":"Select","target":"Close"}]}
]}]}

{uia_block}Now convert the following INPUT. Return JSON only, matching the schema.

INPUT:
"""


def build_w_prompt(task_input: List[Dict[str, Any]], uia_block: str) -> str:
    if uia_block:
        uia_block = uia_block.rstrip() + "\n\n"
    return (W_PROMPT_TEMPLATE.replace("{uia_block}", uia_block)
            + json.dumps(task_input, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Gold standard + task numbering
# ---------------------------------------------------------------------------

def load_specs() -> List[Dict[str, Any]]:
    with open(os.path.join(GI_DIR, "task_specs.json"), encoding="utf-8") as f:
        return json.load(f)["tasks"]


def task_number(tid: str) -> int:
    return int(tid[1:])  # "W01" -> 1


def gold_from_specs(specs: List[Dict[str, Any]]) \
        -> Dict[Tuple[int, int], List[Tuple[str, str]]]:
    gold: Dict[Tuple[int, int], List[Tuple[str, str]]] = {}
    for t in specs:
        n = task_number(t["id"])
        for si, sub in enumerate(t["subtasks"], start=1):
            gold[(n, si)] = [(verb, target) for verb, target in sub]
    return gold


# ---------------------------------------------------------------------------
# UIA snapshot sources
# ---------------------------------------------------------------------------

def newest_completed_run(task_id: str) -> Optional[str]:
    """Newest live_runs folder of this task whose task_times.csv has a data
    row (i.e. the model actually finished the task)."""
    candidates = sorted(glob.glob(os.path.join(GI_DIR, "live_runs",
                                               f"{task_id}_*")))
    for run_dir in reversed(candidates):  # timestamps sort lexicographically
        if completed_run_rows(run_dir):
            return run_dir
    return None


def load_task_uia(task_id: str) -> Optional[Dict[str, Any]]:
    """Initial + union element sets and pruned prompt lists for one task."""
    run_dir = newest_completed_run(task_id)
    if run_dir is None:
        return None
    snap_paths = sorted(glob.glob(os.path.join(run_dir, "visicon_snapshots",
                                               "visicons_*.json")))
    if not snap_paths:
        return None
    initial_elements = load_elements(snap_paths[0])
    union_elements: List[Dict[str, Any]] = []
    for p in snap_paths:
        union_elements.extend(load_elements(p))

    initial_pruned, initial_trunc = prune_elements(initial_elements,
                                                   cap=UIA_PROMPT_CAP)
    union_pruned, union_trunc = prune_elements(union_elements,
                                               cap=UIA_PROMPT_CAP)
    return {
        "run_dir": os.path.basename(run_dir),
        "n_snapshots": len(snap_paths),
        "initial_names": element_names(initial_elements),
        "union_names": element_names(union_elements),
        "initial_pruned": initial_pruned,
        "initial_truncated": initial_trunc,
        "union_pruned": union_pruned,
        "union_truncated": union_trunc,
    }


def uia_block_for(condition: str, uia: Optional[Dict[str, Any]]) -> str:
    if condition == "no-uia" or uia is None:
        return ""
    if condition == "initial-uia":
        return render_uia_block(
            uia["initial_pruned"],
            "at the START of the task, before any action has been taken")
    if condition == "full-uia":
        return render_uia_block(
            uia["union_pruned"],
            "across the WHOLE task (union of scans taken as the task "
            "progressed, so it includes elements that only appear later)")
    raise ValueError(condition)


# ---------------------------------------------------------------------------
# Execution check: generated parse -> spec shape -> generator validation
# ---------------------------------------------------------------------------

def generated_task_to_spec_shape(task_id: str, spec: Dict[str, Any],
                                 gen_task: Dict[str, Any]) -> Dict[str, Any]:
    subtasks = []
    for s in sorted(gen_task.get("subtasks", []),
                    key=lambda s: s.get("subtask_id", 0)):
        subtasks.append([[a["action"], a["target"]]
                        for a in s.get("actions", [])])
    return {
        "id": task_id,
        "name": spec["name"],
        "unique_data_id": spec["unique_data_id"],
        "app": spec["app"],
        "difficulty": spec["difficulty"],
        "instruction": spec["instruction"],
        "subtasks": subtasks,
        "verify_uia": [],
        "notes": "generated by UIAGroundedParser.py (LLM parse, not gold)",
    }


def exec_check(spec_shaped_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Re-validate generated parses with the generator's own validator: verb
    vocabulary, one-string targets, typeable character set, Press key-command
    grammar. A task that passes round-trips into a loadable tasks/*.lisp file
    via generate_task_models.py."""
    per_task = {}
    n_valid = 0
    for t in spec_shaped_tasks:
        problems: List[str] = []
        warnings: List[str] = []
        validate_task(t, problems, warnings)
        ok = not problems
        n_valid += ok
        per_task[t["id"]] = {"valid": ok, "problems": problems,
                             "warnings": warnings}
    return {
        "tasks_checked": len(spec_shaped_tasks),
        "tasks_valid": n_valid,
        "per_task": per_task,
    }


# ---------------------------------------------------------------------------
# One cell = model x variant x condition (10 task calls)
# ---------------------------------------------------------------------------

def variant_steps(variant: str, spec: Dict[str, Any],
                  reasoning: Dict[str, Any]) -> Optional[List[str]]:
    tid = spec["id"]
    if variant == "instruction":
        return [spec["instruction"]]
    if variant == "paraphrase":
        return [PARAPHRASES[tid]]
    if variant == "guide":
        steps = GUIDES.get(tid)
        return list(steps) if steps else None
    if variant == "reasoning_steps":
        steps = (reasoning.get(tid) or {}).get("reasoning_steps") or []
        return list(steps) if steps else None
    raise ValueError(variant)


def run_cell(provider: str, client: Any, model: str, variant: str,
             condition: str,
             specs: List[Dict[str, Any]],
             reasoning: Dict[str, Any],
             uia_by_task: Dict[str, Optional[Dict[str, Any]]],
             gold_eval: Dict[Tuple[int, int], List[Tuple[str, str]]],
             only_tasks: Set[str]) -> Dict[str, Any]:
    print(f"\n--- variant={variant} condition={condition} ---")
    model_slug = iap._slug(model)
    artifact = os.path.join(OUTPUT_DIR,
                            f"{model_slug}__{variant}__{condition}.json")

    per_task: Dict[str, Any] = {}
    merged_tasks: List[Dict[str, Any]] = []
    attempted_nums: List[int] = []
    call_errors = 0

    for spec in specs:
        tid = spec["id"]
        if only_tasks and tid not in only_tasks:
            continue
        steps = variant_steps(variant, spec, reasoning)
        if steps is None:
            per_task[tid] = {"skipped": "no reasoning_steps in PSAI demo"}
            continue
        n = task_number(tid)
        attempted_nums.append(n)
        uia = uia_by_task.get(tid)
        block = uia_block_for(condition, uia)
        if condition != "no-uia" and uia is None:
            per_task[tid] = {"skipped": "no completed live run for UIA context"}
            attempted_nums.pop()
            continue
        task_input = [{"task_id": n, "task_name": spec["name"],
                       "steps": steps}]
        prompt = build_w_prompt(task_input, block)
        raw, err = iap.call_model(provider, client, model, task_input,
                                  prompt=prompt, schema=W_SCHEMA)
        entry: Dict[str, Any] = {"prompt_chars": len(prompt),
                                 "call_error": err}
        if raw is None:
            call_errors += 1
            entry["schema_valid"] = False
            per_task[tid] = entry
            print(f"  {tid}: call failed ({str(err)[:80]})")
            time.sleep(1)
            continue
        ok, errs = iap.validate_semantic(raw, W_ALLOWED_ACTIONS)
        entry["raw"] = raw
        entry["schema_valid"] = ok
        entry["semantic_errors"] = errs
        if ok and raw["tasks"]:
            gen_task = raw["tasks"][0]
            if gen_task.get("task_id") != n:
                entry["task_id_corrected"] = gen_task.get("task_id")
                gen_task["task_id"] = n
            merged_tasks.append(gen_task)
        per_task[tid] = entry
        print(f"  {tid}: schema_valid={ok} "
              f"subtasks={len(raw['tasks'][0].get('subtasks', [])) if raw.get('tasks') else 0}")
        time.sleep(1)

    gold_subset = {k: v for k, v in gold_eval.items()
                   if k[0] in set(attempted_nums)}
    merged = {"tasks": merged_tasks}
    gen_eval = iap.generated_to_eval(merged) if merged_tasks else {}
    extraction = (iap.compute_extraction_metrics(gen_eval, gold_subset)
                  if merged_tasks else None)

    num_to_tid = {task_number(s["id"]): s["id"] for s in specs}

    def initial_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["initial_names"] if u else set()

    def union_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["union_names"] if u else set()

    uia_metrics = (compute_uia_metrics(gen_eval, gold_subset,
                                       initial_names, union_names)
                   if merged_tasks else None)

    spec_by_num = {task_number(s["id"]): s for s in specs}
    spec_shaped = [generated_task_to_spec_shape(num_to_tid[t["task_id"]],
                                                spec_by_num[t["task_id"]], t)
                   for t in merged_tasks]
    execution = exec_check(spec_shaped) if spec_shaped else None

    # Merge with a previously-saved artifact (2026-07-15): a --tasks-filtered
    # re-run updates only the tasks it actually ran instead of clobbering the
    # rest. Metrics above still cover only this run's subset; use --rescore to
    # rebuild full-artifact metrics afterwards.
    if os.path.exists(artifact):
        try:
            with open(artifact, "r", encoding="utf-8") as f:
                old = json.load(f)
            run_tids = set(per_task)
            for tid, entry in old.get("per_task", {}).items():
                if tid not in run_tids:
                    per_task[tid] = entry
            kept_shapes = [s for s in old.get("generated_spec_shape", [])
                           if s.get("id") not in run_tids]
            spec_shaped = sorted(kept_shapes + spec_shaped,
                                 key=lambda s: s.get("id", ""))
        except Exception:
            pass
    with open(artifact, "w", encoding="utf-8") as f:
        json.dump({
            "model": model, "provider": provider,
            "variant": variant, "condition": condition,
            "per_task": per_task,
            "generated_spec_shape": spec_shaped,
        }, f, indent=2, ensure_ascii=False)

    if extraction:
        print(f"  => coverage={extraction['subtask_coverage_pct']}%  "
              f"action={extraction['action_accuracy_pct']}%  "
              f"target={extraction['target_accuracy_pct']}%  "
              f"exact={extraction['exact_match_pct']}%  "
              f"resolv_init={uia_metrics['resolvability_initial_pct']}%  "
              f"resolv_union={uia_metrics['resolvability_union_pct']}%")

    return {
        "variant": variant,
        "condition": condition,
        "tasks_attempted": len(attempted_nums),
        "tasks_parsed": len(merged_tasks),
        "call_errors": call_errors,
        "extraction_metrics": extraction,
        "uia_metrics": uia_metrics,
        "execution_check": execution,
        "artifact": artifact,
    }


def rescore_cell(provider: str, model: str, variant: str, condition: str,
                 specs: List[Dict[str, Any]],
                 uia_by_task: Dict[str, Optional[Dict[str, Any]]],
                 gold_eval: Dict[Tuple[int, int], List[Tuple[str, str]]]) \
        -> Optional[Dict[str, Any]]:
    """Rebuild a cell's metrics from its saved artifact, without any LLM
    call. Used to recover completed cells after a mid-run crash/quota-out
    (the per-cell artifacts are written even when the report checkpoint for
    the model never happened)."""
    model_slug = iap._slug(model)
    artifact = os.path.join(OUTPUT_DIR,
                            f"{model_slug}__{variant}__{condition}.json")
    if not os.path.exists(artifact):
        return None
    with open(artifact, "r", encoding="utf-8") as f:
        saved = json.load(f)
    per_task = saved.get("per_task", {})

    merged_tasks: List[Dict[str, Any]] = []
    attempted_nums: List[int] = []
    call_errors = 0
    known = {s["id"] for s in specs}
    for tid, entry in per_task.items():
        if "skipped" in entry:
            continue
        if tid not in known:
            # artifact predates a task-set change (e.g. the removed W05-W08);
            # ignore entries for tasks that no longer exist in the gold
            continue
        attempted_nums.append(task_number(tid))
        if entry.get("call_error"):
            call_errors += 1
            continue
        if entry.get("schema_valid") and entry.get("raw", {}).get("tasks"):
            merged_tasks.append(entry["raw"]["tasks"][0])

    gold_subset = {k: v for k, v in gold_eval.items()
                   if k[0] in set(attempted_nums)}
    gen_eval = (iap.generated_to_eval({"tasks": merged_tasks})
                if merged_tasks else {})
    extraction = (iap.compute_extraction_metrics(gen_eval, gold_subset)
                  if merged_tasks else None)

    num_to_tid = {task_number(s["id"]): s["id"] for s in specs}

    def initial_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["initial_names"] if u else set()

    def union_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["union_names"] if u else set()

    uia_metrics = (compute_uia_metrics(gen_eval, gold_subset,
                                       initial_names, union_names)
                   if merged_tasks else None)
    spec_by_num = {task_number(s["id"]): s for s in specs}
    spec_shaped = [generated_task_to_spec_shape(num_to_tid[t["task_id"]],
                                                spec_by_num[t["task_id"]], t)
                   for t in merged_tasks]
    execution = exec_check(spec_shaped) if spec_shaped else None

    return {
        "variant": variant,
        "condition": condition,
        "tasks_attempted": len(attempted_nums),
        "tasks_parsed": len(merged_tasks),
        "call_errors": call_errors,
        "extraction_metrics": extraction,
        "uia_metrics": uia_metrics,
        "execution_check": execution,
        "artifact": artifact,
        "rescored_from_artifact": True,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _fmt(x: Any) -> str:
    return f"{x:.2f}" if isinstance(x, (int, float)) else "-"


def write_markdown(report: Dict[str, Any], path: str) -> None:
    lines: List[str] = []
    lines.append("# UIA-grounded step parsing: Windows tasks W01-W10\n")
    lines.append(f"- Gold: `task_specs.json` subtasks "
                 f"({report['gold_subtasks']} subtask lists over 10 tasks).")
    lines.append(f"- Variants: {', '.join(report['variants'])} "
                 "(reasoning_steps exists for only "
                 f"{report['reasoning_steps_tasks']} of 10 tasks; its metrics "
                 "are computed against that subset of the gold).")
    lines.append("- Conditions: no-uia (baseline), initial-uia "
                 "(visicons_001.json of the newest completed live run), "
                 "full-uia (deduped union of all snapshots of that run).")
    lines.append("- Resolvability: % of generated Goto/Select targets that "
                 "case-insensitively equal a UIA element name (matching "
                 "semantics of generic_live.lisp) in the initial snapshot / "
                 "in the union of all snapshots.")
    lines.append("- Fallback-correct: among targets NOT resolving in the "
                 "initial snapshot, those whose gold counterpart is also "
                 "absent from it (the element genuinely was not visible "
                 "yet); the complement, grounding failures, were visible "
                 "but misnamed.\n")

    g = report["gold_uia_reference"]
    lines.append(f"Gold reference: resolvability initial = "
                 f"{_fmt(g['resolvability_initial_pct'])}%, union = "
                 f"{_fmt(g['resolvability_union_pct'])}% "
                 f"({g['visual_targets_scored']} visual targets). Gold "
                 "targets absent from the union are cases where the live "
                 "scan never captured the element under that exact name.\n")

    trunc = report.get("uia_truncation") or {}
    if any(trunc.values()):
        lines.append("Prompt truncation (elements beyond the "
                     f"{UIA_PROMPT_CAP}-element cap were dropped): "
                     + ", ".join(f"{k}: {v}" for k, v in trunc.items()
                                 if v) + "\n")

    lines.append("## Summary (mean over variants, per condition)\n")
    lines.append("| Model | Condition | Cells OK | Coverage % | Action acc % "
                 "| Target acc % | Exact % | Resolv (initial) % | Resolv "
                 "(union) % | Fallback correct % of unresolved | Exec-valid "
                 "tasks |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m in report["per_model"]:
        cells = [c for c in m.get("cells", []) if c.get("extraction_metrics")]
        for condition in report["conditions"]:
            sub = [c for c in cells if c["condition"] == condition]
            n_all = len([c for c in m.get("cells", [])
                         if c["condition"] == condition])
            if not sub:
                lines.append(f"| `{m['model']}` | {condition} | 0/{n_all} "
                             "| - | - | - | - | - | - | - | - |")
                continue

            def em(k: str) -> float:
                return sum(c["extraction_metrics"][k] for c in sub) / len(sub)

            def um(k: str) -> float:
                vals = [c["uia_metrics"][k] for c in sub
                        if c.get("uia_metrics")
                        and c["uia_metrics"][k] is not None]
                return sum(vals) / len(vals) if vals else float("nan")

            ev = [c["execution_check"]["tasks_valid"] for c in sub
                  if c.get("execution_check")]
            et = [c["execution_check"]["tasks_checked"] for c in sub
                  if c.get("execution_check")]
            exec_cell = (f"{sum(ev)}/{sum(et)}" if et else "-")
            lines.append(
                f"| `{m['model']}` | {condition} | {len(sub)}/{n_all} | "
                f"{_fmt(em('subtask_coverage_pct'))} | "
                f"{_fmt(em('action_accuracy_pct'))} | "
                f"{_fmt(em('target_accuracy_pct'))} | "
                f"{_fmt(em('exact_match_pct'))} | "
                f"{_fmt(um('resolvability_initial_pct'))} | "
                f"{_fmt(um('resolvability_union_pct'))} | "
                f"{_fmt(um('fallback_correct_pct_of_unresolved'))} | "
                f"{exec_cell} |")

    lines.append("\n## Per-cell detail\n")
    for m in report["per_model"]:
        lines.append(f"### `{m['model']}` ({m['provider']})\n")
        if m.get("global_error"):
            lines.append(f"_global error: {m['global_error']}_\n")
            continue
        lines.append("| Variant | Condition | Tasks parsed | Coverage % | "
                     "Action % | Target % | Exact % | Resolv init % | "
                     "Resolv union % | Fallback ok | Grounding fail | "
                     "Exec valid |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for c in m.get("cells", []):
            e = c.get("extraction_metrics")
            u = c.get("uia_metrics")
            x = c.get("execution_check")
            if not e:
                lines.append(f"| {c['variant']} | {c['condition']} | "
                             f"{c.get('tasks_parsed', 0)}/{c.get('tasks_attempted', 0)} "
                             "| - | - | - | - | - | - | - | - | - |")
                continue
            lines.append(
                f"| {c['variant']} | {c['condition']} | "
                f"{c['tasks_parsed']}/{c['tasks_attempted']} | "
                f"{_fmt(e['subtask_coverage_pct'])} | "
                f"{_fmt(e['action_accuracy_pct'])} | "
                f"{_fmt(e['target_accuracy_pct'])} | "
                f"{_fmt(e['exact_match_pct'])} | "
                f"{_fmt(u['resolvability_initial_pct'])} | "
                f"{_fmt(u['resolvability_union_pct'])} | "
                f"{u['fallback_correct']} | {u['grounding_failure']} | "
                f"{x['tasks_valid']}/{x['tasks_checked']} |")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="UIA-grounded LLM parsing eval (Windows tasks)")
    ap.add_argument("--providers", default="",
                    help="comma list to restrict run, e.g. 'openai,gemini'")
    ap.add_argument("--models", default="",
                    help="comma list of exact model ids to restrict run")
    ap.add_argument("--variants", default="",
                    help=f"comma list from {VARIANTS}")
    ap.add_argument("--conditions", default="",
                    help=f"comma list from {CONDITIONS}")
    ap.add_argument("--tasks", default="",
                    help="comma list of task ids, e.g. 'W01,W05'")
    ap.add_argument("--or-retries", type=int, default=10)
    ap.add_argument("--or-backoff", type=int, default=60)
    ap.add_argument("--rescore", action="store_true",
                    help="rebuild the selected cells' metrics from their "
                         "saved artifacts instead of calling any LLM "
                         "(recovers completed cells after a mid-run crash)")
    args = ap.parse_args()

    only_providers = {p.strip() for p in args.providers.split(",") if p.strip()}
    only_models = {m.strip() for m in args.models.split(",") if m.strip()}
    only_variants = [v for v in VARIANTS
                     if not args.variants
                     or v in {x.strip() for x in args.variants.split(",")}]
    only_conditions = [c for c in CONDITIONS
                       if not args.conditions
                       or c in {x.strip() for x in args.conditions.split(",")}]
    only_tasks = {t.strip() for t in args.tasks.split(",") if t.strip()}

    iap.OR_RETRIES = args.or_retries
    iap.OR_BACKOFF_S = args.or_backoff

    iap._load_env_file(os.path.join(HERE, ".env"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    specs = load_specs()
    gold_eval = gold_from_specs(specs)
    print(f"gold subtask lists: {len(gold_eval)} over {len(specs)} tasks")

    reasoning_path = os.path.join(OUTPUT_DIR, "reasoning_steps_cache.json")
    with open(reasoning_path, encoding="utf-8") as f:
        reasoning = json.load(f)
    rs_tasks = [t for t in reasoning
                if reasoning[t].get("reasoning_steps")]
    print(f"reasoning_steps available for: {', '.join(sorted(rs_tasks))}")

    uia_by_task: Dict[str, Optional[Dict[str, Any]]] = {}
    trunc_report: Dict[str, int] = {}
    for spec in specs:
        uia = load_task_uia(spec["id"])
        uia_by_task[spec["id"]] = uia
        if uia is None:
            print(f"  WARNING {spec['id']}: no completed live run -> "
                  "UIA conditions will be skipped for this task")
        else:
            if uia["initial_truncated"]:
                trunc_report[f"{spec['id']} initial"] = uia["initial_truncated"]
            if uia["union_truncated"]:
                trunc_report[f"{spec['id']} union"] = uia["union_truncated"]
            print(f"  {spec['id']}: run={uia['run_dir']} "
                  f"snapshots={uia['n_snapshots']} "
                  f"initial={len(uia['initial_pruned'])}(+{uia['initial_truncated']} truncated) "
                  f"union={len(uia['union_pruned'])}(+{uia['union_truncated']} truncated)")

    num_to_tid = {task_number(s["id"]): s["id"] for s in specs}

    def initial_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["initial_names"] if u else set()

    def union_names(task_num: int) -> Set[str]:
        u = uia_by_task.get(num_to_tid[task_num])
        return u["union_names"] if u else set()

    gold_uia_reference = compute_uia_metrics(gold_eval, gold_eval,
                                             initial_names, union_names)
    print(f"gold resolvability: initial="
          f"{gold_uia_reference['resolvability_initial_pct']}% union="
          f"{gold_uia_reference['resolvability_union_pct']}%")

    selected = [
        (prov, mdl) for prov, mdl in iap.MODELS
        if (not only_providers or prov in only_providers)
        and (not only_models or mdl in only_models)
    ]
    if only_providers or only_models:
        print(f"filtered to {len(selected)} model(s): "
              f"{', '.join(m for _, m in selected) or '(none)'}")

    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = (os.environ.get("GEMINI_API_KEY")
                  or os.environ.get("GOOGLE_API_KEY"))
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    from openai import OpenAI
    openai_client = OpenAI(api_key=openai_key) if openai_key else None
    gemini_client = None
    if gemini_key and iap._HAS_GEMINI:
        from google import genai as google_genai
        from google.genai import types as google_genai_types
        # 120s request timeout: during "high demand" spells the API can hang
        # a request indefinitely; a timeout turns that into a retryable error.
        gemini_client = google_genai.Client(
            api_key=gemini_key,
            http_options=google_genai_types.HttpOptions(timeout=120_000))
    openrouter_client = (OpenAI(api_key=openrouter_key,
                                base_url=iap.OPENROUTER_BASE_URL)
                         if openrouter_key else None)
    clients = {"openai": openai_client, "gemini": gemini_client,
               "openrouter": openrouter_client}
    missing = {"openai": "OPENAI_API_KEY missing",
               "gemini": ("google-genai SDK not installed"
                          if not iap._HAS_GEMINI
                          else "GEMINI_API_KEY (or GOOGLE_API_KEY) missing"),
               "openrouter": "OPENROUTER_API_KEY missing"}

    json_path = os.path.join(OUTPUT_DIR, "metrics_report.json")
    md_path = os.path.join(OUTPUT_DIR, "model_comparison.md")

    # Retain previously-saved results we're NOT re-running (resumability).
    # kept: whole models outside the filter. prev_cells: cell-level results of
    # models we ARE re-running, so a filtered re-run (e.g. one failed
    # variant x condition) replaces only the cells it actually runs.
    kept: List[Dict[str, Any]] = []
    prev_cells: Dict[str, Dict[Tuple[str, str], Dict[str, Any]]] = {}
    if (only_providers or only_models or only_variants != VARIANTS
            or only_conditions != CONDITIONS or only_tasks) \
            and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                prev = json.load(f)
            fresh = {m for _, m in selected}
            kept = [m for m in prev.get("per_model", [])
                    if m["model"] not in fresh]
            for m in prev.get("per_model", []):
                if m["model"] in fresh:
                    prev_cells[m["model"]] = {
                        (c["variant"], c["condition"]): c
                        for c in m.get("cells", [])}
            print(f"retaining {len(kept)} previously-run model(s); "
                  f"cell-merging {len(prev_cells)} re-run model(s)")
        except Exception as e:
            print(f"could not read previous report ({e}); starting fresh")

    order = {m: i for i, (_, m) in enumerate(iap.MODELS)}

    def flush(per_model: List[Dict[str, Any]]) -> None:
        merged = sorted(per_model + kept,
                        key=lambda m: order.get(m["model"], 1_000))
        report = {
            "gold_subtasks": len(gold_eval),
            "variants": only_variants,
            "conditions": only_conditions,
            "reasoning_steps_tasks": len(rs_tasks),
            "uia_sources": {tid: (u["run_dir"] if u else None)
                            for tid, u in uia_by_task.items()},
            "uia_truncation": trunc_report,
            "gold_uia_reference": gold_uia_reference,
            "models_evaluated": [m["model"] for m in merged],
            "per_model": merged,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        write_markdown(report, md_path)

    per_model: List[Dict[str, Any]] = []
    for provider, model in selected:
        print(f"\n=== model: {model} ({provider}) ===")
        if args.rescore:
            ran = {}
            for variant in only_variants:
                for condition in only_conditions:
                    cell = rescore_cell(provider, model, variant, condition,
                                        specs, uia_by_task, gold_eval)
                    if cell is not None:
                        print(f"  rescored {variant} x {condition}: "
                              f"{cell['tasks_parsed']}/{cell['tasks_attempted']} tasks")
                        ran[(variant, condition)] = cell
                    else:
                        print(f"  no artifact for {variant} x {condition}; skipped")
            merged_cells = dict(prev_cells.get(model, {}))
            merged_cells.update(ran)
            cells = [merged_cells[(v, c)]
                     for v in VARIANTS for c in CONDITIONS
                     if (v, c) in merged_cells]
            per_model.append({"provider": provider, "model": model,
                              "cells": cells})
            flush(per_model)
            continue
        client = clients.get(provider)
        if client is None:
            per_model.append({"provider": provider, "model": model,
                              "global_error": missing.get(
                                  provider, f"unknown provider {provider}"),
                              "cells": []})
            flush(per_model)
            continue
        ran: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for variant in only_variants:
            for condition in only_conditions:
                ran[(variant, condition)] = run_cell(
                    provider, client, model, variant, condition, specs,
                    reasoning, uia_by_task, gold_eval, only_tasks)
        merged_cells = dict(prev_cells.get(model, {}))
        merged_cells.update(ran)
        cells = [merged_cells[(v, c)]
                 for v in VARIANTS for c in CONDITIONS
                 if (v, c) in merged_cells]
        per_model.append({"provider": provider, "model": model,
                          "cells": cells})
        flush(per_model)  # checkpoint after each model

    flush(per_model)
    print(f"\nwrote JSON -> {json_path}")
    print(f"wrote MD   -> {md_path}")


if __name__ == "__main__":
    main()
