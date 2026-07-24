"""Per-step UIA-grounded parse for the six live Windows tasks.

Promoted into the repo from the 2026-07-14 session scratchpad (was
scratchpad/run_perstep.py); extended 2026-07-15 with:
  - the Windows verb schema (UIAGroundedParser.W_SCHEMA) sent with every
    call, so RightClick/Scroll are actually emittable -- previously the
    Excel eval's 5-verb enum was baked into the structured-output schema
    and silently forbade them even though the prompt allowed them;
  - a --variant switch: "instruction" (the task_specs.json sentence) or
    "guide" (UIAGroundedParser.GUIDES step-by-step walk-through, so all
    models are pushed toward the same strategy);
  - artifact merge: a filtered --tasks re-run updates only the tasks it ran
    instead of clobbering the whole artifact;
  - stale-capture guard: tasks whose spec start state changed after their
    newest live capture (W02: File Explorer now opened by the model with
    budget.xlsx pinned to Quick access; W10: File Explorer now already
    open) are skipped until a re-capture exists, unless --include-stale.

Realism rule (2026-07-14, per user): the screen changes only when the model
ACTS. So we hold one captured scan fixed and ask the model for ONE action at a
time, showing only that scan's elements; we advance to the next captured scan
only when the model emits a screen-changing action (a click = Select/RightClick,
a Press = key/chord, or a Scroll). A Goto/Move is just looking and does NOT
advance the screen. This is exactly what the live ACT-R model perceives, with no
union / future-screen leakage.

Concurrency: (model x task) pairs run in a thread pool; the action loop within a
pair is sequential (each action's prompt includes the model's own prior actions).

Writes: llm_parsing_eval/<slug>__<variant>__per-step.json

Usage:
  python EnvironmentParsers/run_perstep.py                      # instruction
  python EnvironmentParsers/run_perstep.py --variant guide
  python EnvironmentParsers/run_perstep.py --tasks W02,W10 --include-stale
"""
from __future__ import annotations
import argparse
import json, os, sys, glob
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GI = os.path.join(ROOT, "EVisiTor2026", "NewInterfaces_PSAI", "GenericInterface")
EVAL = os.path.join(GI, "llm_parsing_eval")
sys.path.insert(0, HERE); sys.path.insert(0, GI)

import InstructionAcquisitionParser as iap
import uia_grounding_common as ugc
import UIAGroundedParser as uiap

TASKS = ["W01", "W02", "W03", "W04", "W09", "W10"]
# Newest completed captures of these tasks no longer match the current gold;
# skip until a fresh live capture exists, then remove them from this set.
# 2026-07-16: W02/W10 re-captured live (W02_20260716_181407 with the
# Explorer-opens-to-Downloads start state; W10_20260716_182427 with Explorer
# already open) and removed. W03 was briefly stale after its gold switched to
# Ctrl+Shift+N, then re-captured under the new gold late 2026-07-16
# (W03_20260716_234759: taskbar / Downloads / Desktop view / 'New folder'
# edit state / 'Projects' -- 5 step-aligned scans) and removed again.
STALE_CAPTURES = set()
# Tasks stale for the per-step protocol ONLY: their captured scan sequence no
# longer matches the gold path step-for-step, but the scan UNION remains a
# valid superset for the single-shot full-uia condition.
PERSTEP_ONLY_STALE = set()
MAXCONC = 8
CAP = 150
ADVANCING = {"Select", "RightClick", "ClickUp", "ClickDown", "Press", "Scroll"}
LOOK = {"Goto", "Move"}


def tnum(t): return int(t[1:])


def load_specs():
    return {t["id"]: t for t in uiap.load_specs()}


def scans_for(task_id):
    run = uiap.newest_completed_run(task_id)
    if not run:
        return []
    paths = sorted(glob.glob(os.path.join(run, "visicon_snapshots", "visicons_*.json")))
    out, last = [], None
    for p in paths:
        els = ugc.load_elements(p)
        names = ugc.element_names(els)
        if names == last:
            continue
        pruned, _ = ugc.prune_elements(els, cap=CAP)
        out.append((names, pruned))
        last = names
    return out


PROMPT = """\
You convert a natural-language Windows desktop task into a sequence of atomic
actions for a cognitive model that can ONLY see the current screen.

TASK INSTRUCTION: "{instr}"

ACTIONS YOU HAVE ALREADY TAKEN (in order):
{history}

UI_ELEMENTS below is a UIA scan of the screen RIGHT NOW -- this exact moment
only. Earlier or later screens are NOT shown:
UI_ELEMENTS = {elements}

Return the SINGLE next atomic action, as JSON: exactly one task, one subtask,
one action. Allowed verbs: Goto (look at an element, screen unchanged), Select
(left-click the thing you last looked at), RightClick (right-click the thing
you last looked at; opens its context menu), Type, Press (a key/chord
like "enter" or "win+r"), Scroll. For a Goto/Select/RightClick target: if the
element is in UI_ELEMENTS use its "name" EXACTLY; if the element you need is not
on THIS screen yet, use a short generic term (never invent a specific name not
listed). If the task is fully complete, return an action with verb "Press" and
target "done".
"""


def instr_for(variant, spec):
    if variant == "instruction":
        return spec["instruction"]
    if variant == "guide":
        steps = uiap.GUIDES[spec["id"]]
        return " ".join(f"({i}) {s}" for i, s in enumerate(steps, 1))
    raise ValueError(variant)


def build_prompt(instr, history, pruned):
    hist = "\n".join(history) if history else "(none yet)"
    elems = "[\n" + ",\n".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in pruned) + "\n]"
    return PROMPT.format(instr=instr, history=hist, elements=elems)


def run_pair(provider, client, model, spec, variant):
    tid = spec["id"]; instr = instr_for(variant, spec)
    scans = scans_for(tid)
    if not scans:
        return tid, {"n_scans": 0, "stream": [], "targets": 0, "resolved": 0,
                     "error": "no scans"}
    i = 0
    stream = []            # [(verb, target, scan_index, resolved_bool_or_None)]
    history = []
    n_tgt = n_res = 0
    consecutive_look = 0
    cap = len(scans) * 2 + 6
    while i < len(scans) and len(stream) < cap:
        names, pruned = scans[i]
        prompt = build_prompt(instr, history, pruned)
        raw, err = iap.call_model(provider, client, model,
                                  [{"task_id": tnum(tid), "task_name": spec["name"],
                                    "steps": [instr]}], prompt=prompt,
                                  schema=uiap.W_SCHEMA)
        if not raw or not raw.get("tasks"):
            stream.append(("<error>", err or "no-parse", i + 1, None)); break
        subs = raw["tasks"][0].get("subtasks", [])
        acts = subs[0].get("actions", []) if subs else []
        if not acts:
            break
        verb, target = acts[0]["action"], acts[0]["target"]
        if verb == "Press" and str(target).strip().lower() == "done":
            break
        resolved = None
        if verb in ("Goto", "Move", "Select", "RightClick"):
            resolved = target.strip().lower() in names
            n_tgt += 1; n_res += 1 if resolved else 0
        stream.append((verb, target, i + 1, resolved))
        history.append(f'{len(history)+1}. ({verb} "{target}")')
        if verb in ADVANCING:
            i += 1
            consecutive_look = 0
        else:
            consecutive_look += 1
            if consecutive_look >= 2:      # avoid staring/looping on one screen
                i += 1
                consecutive_look = 0
    return tid, {"n_scans": len(scans), "stream": stream,
                 "targets": n_tgt, "resolved": n_res}


def main():
    ap = argparse.ArgumentParser(description="per-step UIA-grounded parse")
    ap.add_argument("--variant", default="instruction",
                    choices=["instruction", "guide"])
    ap.add_argument("--tasks", default="",
                    help="comma list of task ids to (re-)run; default all "
                         "non-stale tasks")
    ap.add_argument("--models", default="",
                    help="comma list of exact model ids to restrict run")
    ap.add_argument("--include-stale", action="store_true",
                    help=f"also run {sorted(STALE_CAPTURES)} even though their "
                         "captures predate the 2026-07-15 spec change")
    args = ap.parse_args()

    only = [t.strip() for t in args.tasks.split(",") if t.strip()] or TASKS
    tasks = [t for t in only
             if args.include_stale or t not in STALE_CAPTURES]
    skipped_stale = [t for t in only if t not in tasks]
    if skipped_stale:
        print(f"skipping stale captures (re-capture needed): "
              f"{', '.join(skipped_stale)}")

    iap._load_env_file(os.path.join(HERE, ".env"))
    specs = load_specs()
    from openai import OpenAI
    ok = os.environ.get("OPENAI_API_KEY")
    gk = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    ork = os.environ.get("OPENROUTER_API_KEY")
    openai_client = OpenAI(api_key=ok) if ok else None
    gemini_client = None
    if gk and iap._HAS_GEMINI:
        from google import genai as gg
        from google.genai import types as ggt
        gemini_client = gg.Client(api_key=gk, http_options=ggt.HttpOptions(timeout=60_000))
    orc = OpenAI(api_key=ork, base_url=iap.OPENROUTER_BASE_URL) if ork else None
    clients = {"openai": openai_client, "gemini": gemini_client, "openrouter": orc}

    SKIP = {"gemini-3.5-flash"}
    only_models = {m.strip() for m in args.models.split(",") if m.strip()}
    models = [(p, m) for p, m in iap.MODELS
              if m not in SKIP and ":free" not in m and clients.get(p)
              and (not only_models or m in only_models)]
    print(f"variant: {args.variant}")
    print("models:", ", ".join(m for _, m in models))
    print("tasks:", ", ".join(tasks))

    results = {m: {} for _, m in models}
    with ThreadPoolExecutor(max_workers=MAXCONC) as ex:
        futmap = {}
        for provider, model in models:
            for tid in tasks:
                f = ex.submit(run_pair, provider, clients[provider], model,
                              specs[tid], args.variant)
                futmap[f] = model
        for fut in as_completed(futmap):
            model = futmap[fut]
            try:
                tid, data = fut.result()
                results[model][tid] = data
                print(f"  {model:<34} {tid}: scans={data['n_scans']} "
                      f"acts={len(data['stream'])} resolv={data['resolved']}/{data['targets']}")
            except Exception as e:
                print(f"  {model} pair failed: {repr(e)[:120]}")

    for provider, model in models:
        slug = iap._slug(model)
        art = os.path.join(EVAL, f"{slug}__{args.variant}__per-step.json")
        per_task = {}
        if os.path.exists(art):        # merge: keep tasks not re-run this time
            try:
                with open(art, encoding="utf-8") as f:
                    per_task = json.load(f).get("per_task", {})
            except Exception:
                per_task = {}
        per_task.update(results.get(model, {}))
        for tid in skipped_stale:
            per_task.setdefault(tid, {"n_scans": 0, "stream": [], "targets": 0,
                                      "resolved": 0,
                                      "error": "stale capture (spec start "
                                               "state changed 2026-07-15); "
                                               "re-capture needed"})
        with open(art, "w", encoding="utf-8") as f:
            json.dump({"model": model, "provider": provider,
                       "variant": args.variant,
                       "condition": "per-step", "per_task": per_task},
                      f, indent=2, ensure_ascii=False)
    print(f"\nwrote {len(models)} per-step artifacts (variant={args.variant})")


if __name__ == "__main__":
    main()
