"""Shared helpers for the UIA-grounded LLM parsing evaluations.

Used by:
  - UIAGroundedParser.py          (Windows tasks W01-W10, three UIA conditions)
  - InstructionAcquisitionParser.py --uia-context initial   (Excel retrofit)

The scientific point: when the prompt contains the UIA element dump the
ACT-R model actually perceives, a grounded LLM should (a) copy real element
names character-for-character, and (b) fall back to a short generic term for
elements that are genuinely not visible yet.  These helpers prune the dumps
for prompting and score both behaviours.

Name-matching semantics mirror generic_live.lisp: a generated target
"resolves" iff target.lower() equals some element name.lower() in the scan
(full-name, case-insensitive equality).
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

VISUAL_VERBS = {"Goto", "Move", "Select"}


# ---------------------------------------------------------------------------
# UIA dump loading / pruning
# ---------------------------------------------------------------------------

def load_elements(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def element_names(elements: Iterable[Dict[str, Any]]) -> Set[str]:
    """Lowercased non-empty element names — the resolvability ground truth."""
    out: Set[str] = set()
    for e in elements:
        name = (e.get("name") or "").strip()
        if name:
            out.add(name.lower())
    return out


def prune_elements(elements: Iterable[Dict[str, Any]],
                   cap: int = 300) -> Tuple[List[Dict[str, str]], int]:
    """Reduce a raw UIA dump to prompt-sized records.

    Keeps name / control_type / parent_text, drops geometry and colors,
    dedupes by (name, control_type), drops empty names, caps the list.
    Returns (pruned_list, n_truncated). Truncation must be reported, never
    silent.
    """
    seen: Set[Tuple[str, str]] = set()
    out: List[Dict[str, str]] = []
    for e in elements:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        ctype = (e.get("control_type") or "").strip()
        key = (name.lower(), ctype.lower())
        if key in seen:
            continue
        seen.add(key)
        rec = {"name": name, "control_type": ctype}
        parent = (e.get("parent_text") or "").strip()
        if parent:
            rec["parent_text"] = parent
        out.append(rec)
    truncated = max(0, len(out) - cap)
    return out[:cap], truncated


def render_uia_block(pruned: List[Dict[str, str]], scope_phrase: str) -> str:
    """The grounding instruction + compact JSON element list for the prompt.

    scope_phrase: e.g. "at the start of the task" or "across the whole task".
    """
    lines = [json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
             for rec in pruned]
    body = "[\n" + ",\n".join(lines) + "\n]"
    return (
        f"The UI_ELEMENTS list below is an accessibility (UIA) scan of the "
        f"screen {scope_phrase}. When the object a step refers to appears in "
        "the list, use its \"name\" string EXACTLY (character-for-character) "
        "as the action target. If you cannot find a matching element, do not "
        "be afraid to use a short generic descriptive term instead — the "
        "element may simply not be visible on screen at that point in the "
        "task (for example, a window that has not been opened yet has no "
        "Close button). Never invent a specific-looking name that is not in "
        "the list.\n\n"
        f"UI_ELEMENTS = {body}\n"
    )


# ---------------------------------------------------------------------------
# Resolvability + generic-fallback metrics
# ---------------------------------------------------------------------------

def compute_uia_metrics(
    gen_eval: Dict[Tuple[int, int], List[Tuple[str, str]]],
    gold_eval: Dict[Tuple[int, int], List[Tuple[str, str]]],
    initial_names_for_task: Callable[[int], Set[str]],
    union_names_for_task: Optional[Callable[[int], Set[str]]] = None,
    exempt: Optional[Callable[[str], bool]] = None,
) -> Dict[str, Any]:
    """Score visual-verb targets in `gen_eval` against UIA name sets.

    - resolvability: fraction of (non-exempt) Goto/Move/Select targets whose
      lowercased text equals an element name in the task's initial snapshot
      (and, if given, in the union of all snapshots of the run).
    - fallback classification, for targets NOT resolving in the initial
      snapshot: align each with the gold action at the same (key, index)
      (falling back to the first visual gold action of the subtask).
        * gold target also absent from the initial snapshot
              -> "fallback_correct"   (element genuinely not visible yet;
                 using a generic term is the intended behaviour)
        * gold target present in the initial snapshot
              -> "grounding_failure"  (element was visible but misnamed)
        * no aligned gold visual action
              -> "unaligned"
    `exempt` marks targets outside UIA grounding (e.g. Excel cell
    coordinates); they are counted but excluded from the rates.
    """
    total = 0
    n_exempt = 0
    resolved_initial = 0
    resolved_union = 0
    fallback_correct = 0
    grounding_failure = 0
    unaligned = 0
    unresolved_detail: List[Dict[str, Any]] = []

    for key in sorted(gen_eval.keys()):
        task_id = key[0]
        initial_names = initial_names_for_task(task_id)
        union_names = (union_names_for_task(task_id)
                       if union_names_for_task else None)
        gold_actions = gold_eval.get(key, [])
        gold_visual = [(i, t) for i, (v, t) in enumerate(gold_actions)
                       if v in VISUAL_VERBS]
        for idx, (verb, target) in enumerate(gen_eval[key]):
            if verb not in VISUAL_VERBS:
                continue
            if exempt and exempt(target):
                n_exempt += 1
                continue
            total += 1
            t_low = target.strip().lower()
            in_initial = t_low in initial_names
            in_union = (t_low in union_names) if union_names is not None else None
            if in_initial:
                resolved_initial += 1
            if in_union:
                resolved_union += 1
            if not in_initial:
                # align with gold to classify the miss
                gold_target: Optional[str] = None
                if (idx < len(gold_actions)
                        and gold_actions[idx][0] in VISUAL_VERBS):
                    gold_target = gold_actions[idx][1]
                elif gold_visual:
                    gold_target = gold_visual[0][1]
                if gold_target is None:
                    cls = "unaligned"
                    unaligned += 1
                elif gold_target.strip().lower() in initial_names:
                    cls = "grounding_failure"
                    grounding_failure += 1
                else:
                    cls = "fallback_correct"
                    fallback_correct += 1
                unresolved_detail.append({
                    "key": f"task{key[0]}_sub{key[1]}",
                    "target": target,
                    "gold_target": gold_target,
                    "in_union": in_union,
                    "class": cls,
                })

    def pct(num: int, denom: int) -> float:
        return round(100.0 * num / denom, 2) if denom else 0.0

    unresolved = total - resolved_initial
    return {
        "visual_targets_scored": total,
        "visual_targets_exempt": n_exempt,
        "resolved_initial": resolved_initial,
        "resolvability_initial_pct": pct(resolved_initial, total),
        "resolved_union": resolved_union if union_names_for_task else None,
        "resolvability_union_pct": (pct(resolved_union, total)
                                    if union_names_for_task else None),
        "unresolved_initial": unresolved,
        "fallback_correct": fallback_correct,
        "grounding_failure": grounding_failure,
        "unaligned": unaligned,
        "fallback_correct_pct_of_unresolved": pct(fallback_correct, unresolved),
        "unresolved_detail": unresolved_detail,
    }
