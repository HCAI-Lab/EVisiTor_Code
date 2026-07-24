"""Build the W6 model-IO workbook: gold chunks, exact model inputs (prompts +
UIA scans), every model's outputs per variant x condition, side-by-side
comparisons, and the summary metrics.

Promoted into the repo from the 2026-07-14 session scratchpad
(was scratchpad/build_w6_excel.py). 2026-07-15 changes:
  - two instruction variants: "instruction" (task_specs.json sentence) and
    "guide" (step-by-step walk-through, UIAGroundedParser.GUIDES);
  - W02/W10 spec change is flagged: their newest captures predate the new
    start states (W02 opens File Explorer w/ budget.xlsx pinned; W10 starts
    with File Explorer already open), so their UIA-condition cells read
    "stale capture" until a live re-capture exists;
  - gold counts computed from task_specs.json instead of hard-coded.

Output:
  GenericInterface/llm_parsing_eval/W6_model_IO_and_gold_2026-07-15.xlsx
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GI = os.path.join(ROOT, "EVisiTor2026", "NewInterfaces_PSAI", "GenericInterface")
EVAL = os.path.join(GI, "llm_parsing_eval")
sys.path.insert(0, HERE); sys.path.insert(0, GI)

import InstructionAcquisitionParser as iap
import uia_grounding_common as ugc
import UIAGroundedParser as uiap
import run_perstep  # scans_for + PROMPT template + STALE_CAPTURES
import functional_check  # alt-path judge (user 2026-07-16)

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

TASKS = ["W01", "W02", "W03", "W04", "W09", "W10"]
VARIANTS = ["instruction", "guide"]
# Per-step stale: captured scan SEQUENCE no longer matches the gold path.
# Single-shot stale: even the scan UNION is unusable (start state changed).
# 2026-07-16: W02/W10 re-captured (no longer stale anywhere); W03 per-step
# stale only -- its 2026-07-14 union is a valid superset for full-uia, but the
# scan sequence contains context-menu screens the Ctrl+Shift+N gold never
# opens.
PS_STALE = run_perstep.STALE_CAPTURES
STALE = run_perstep.STALE_CAPTURES - run_perstep.PERSTEP_ONLY_STALE
STALE_NOTE = "STALE capture (gold/start state changed; re-capture needed)"
ALIAS = {"this folder is empty.": "desktop background"}
OUT_NAME = "W6_model_IO_and_gold_2026-07-16.xlsx"

HDR = Font(bold=True)
HDRFILL = PatternFill("solid", fgColor="D9E1F2")
GOLDFILL = PatternFill("solid", fgColor="FFF2CC")
BADFILL = PatternFill("solid", fgColor="FFC7CE")
OKFILL = PatternFill("solid", fgColor="C6EFCE")
STALEFILL = PatternFill("solid", fgColor="D9D9D9")
WRAP = Alignment(wrap_text=True, vertical="top")


def canon(t):
    n = iap._norm_target(t)
    return ALIAS.get(n, n)


# Post-task cleanup excused from scoring (user, 2026-07-15): W01's gold no
# longer includes closing Notepad. Parses that still close the window (guide
# cells generated before the change, or models being tidy) are NOT penalized:
# their close actions are ignored in the match column and dropped from the
# gold-aligned Compare sequences instead of showing up red.
IGNORED_CLEANUP = {("W01", "close")}


def is_ignored(tid, verb, target):
    return (verb in ("Goto", "Move", "Select")
            and (tid, canon(str(target))) in IGNORED_CLEANUP)


def vsuffix(variant):
    return "" if variant == "instruction" else " guide"


def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HDR
        cell.fill = HDRFILL
    ws.freeze_panes = f"A{row + 1}"


def load_gold():
    specs = uiap.load_specs()
    return {t["id"]: t for t in specs}


def steps_for(variant, spec):
    if variant == "instruction":
        return [spec["instruction"]]
    return list(uiap.GUIDES[spec["id"]])


def gen_single_shot(model, variant, cond):
    slug = iap._slug(model)
    p = os.path.join(EVAL, f"{slug}__{variant}__{cond}.json")
    if not os.path.exists(p):
        return None
    data = json.load(open(p, encoding="utf-8"))
    per = data.get("per_task", {})
    out = {}
    for tid in TASKS:
        e = per.get(tid)
        if not e:
            note = STALE_NOTE if (cond != "no-uia" and tid in STALE) \
                else "not attempted"
            out[tid] = {"status": note, "subtasks": None}
        elif e.get("skipped"):
            out[tid] = {"status": f"skipped: {e['skipped']}", "subtasks": None}
        elif e.get("call_error"):
            out[tid] = {"status": f"call failed: {str(e['call_error'])[:120]}",
                        "subtasks": None}
        elif not e.get("schema_valid") or not e.get("raw", {}).get("tasks"):
            out[tid] = {"status": "invalid schema", "subtasks": None}
        else:
            task = e["raw"]["tasks"][0]
            subs = []
            for s in sorted(task.get("subtasks", []),
                            key=lambda s: s.get("subtask_id", 0)):
                subs.append((s.get("subtask_id"),
                             [(a["action"], a["target"]) for a in s.get("actions", [])]))
            out[tid] = {"status": "ok", "subtasks": subs}
    return out


def load_perstep(model, variant):
    slug = iap._slug(model)
    p = os.path.join(EVAL, f"{slug}__{variant}__per-step.json")
    if not os.path.exists(p):
        return None
    data = json.load(open(p, encoding="utf-8"))
    per = data.get("per_task", {})
    out = {}
    for tid in TASKS:
        if tid in PS_STALE:
            # older per-step streams for these tasks were driven by
            # captures that no longer match the gold; withhold them
            out[tid] = {"stream": [], "n_scans": 0, "targets": 0,
                        "resolved": 0, "error": STALE_NOTE}
            continue
        d = per.get(tid) or {}
        stream = []
        for entry in d.get("stream", []):
            entry = list(entry) + [None] * (4 - len(entry))
            stream.append(tuple(entry[:4]))  # verb, target, scan, resolved
        out[tid] = {"stream": stream, "n_scans": d.get("n_scans", 0),
                    "targets": d.get("targets", 0), "resolved": d.get("resolved", 0),
                    "error": d.get("error")}
    return out


def main():
    gold = load_gold()
    n_sub = sum(len(gold[t]["subtasks"]) for t in TASKS)
    n_act = sum(len(s) for t in TASKS for s in gold[t]["subtasks"])
    scans = {tid: ([] if tid in PS_STALE else run_perstep.scans_for(tid))
             for tid in TASKS}
    uia = {tid: (None if tid in STALE else uiap.load_task_uia(tid))
           for tid in TASKS}
    models = [(p, m) for p, m in iap.MODELS]

    # initial-uia dropped from the workbook (user 2026-07-16: only the union
    # matters for single-shot); its artifacts remain on disk.
    ss = {m: {v: {c: gen_single_shot(m, v, c)
                  for c in ("no-uia", "full-uia")}
              for v in VARIANTS} for _, m in models}
    ps = {m: {v: load_perstep(m, v) for v in VARIANTS} for _, m in models}

    def model_ok(m):
        for v in VARIANTS:
            a = ss[m][v]["no-uia"]
            if a and any(x["status"] == "ok" for x in a.values()):
                return True
            d = ps[m].get(v)
            if d and any(d[t]["stream"] for t in TASKS):
                return True
        return False

    ok_models = [m for _, m in models if model_ok(m)]

    wb = Workbook()

    # ---------------- README ----------------
    ws = wb.active; ws.title = "README"
    rows = [
        ["W6 instruction-to-chunk evaluation: model inputs, outputs, and gold", ""],
        ["Generated", "2026-07-16"],
        ["Gold", f"task_specs.json (6 live Windows tasks, {n_sub} subtasks / {n_act} actions)"],
        ["Gold changes 2026-07-15", "W02: instruction + gold now OPEN File Explorer first (start state: Explorer closed, budget.xlsx pinned to Quick access). W10: open-File-Explorer subtask REMOVED (start state: Explorer already open); instruction states the precondition."],
        ["Gold change 2026-07-16", "W03: gold + guide switched from 'right-click the empty background > New > Folder' to the Ctrl+Shift+N chord. The unoccupied folder-view region is NOT a UIA visual item (no scan contains a 'Desktop background' element; its only UIA text is 'This folder is empty.'), so the old gold step could never be grounded in the perceived interface. With Ctrl+Shift+N (or clicking New > Folder), the model performs the task perfectly."],
        ["Captures", "live ACT-R runs; W04/W09 step-aligned re-captures of 2026-07-14; W02/W10 re-captured 2026-07-16 under the new start states (W02: Explorer closed, opens to a folder view containing budget.xlsx; W10: Explorer already open). W03 re-captured 2026-07-16 under the revised Ctrl+Shift+N gold (W03_20260716_234759, 12.4 s live, 5 step-aligned scans: taskbar / Explorer at Downloads / Desktop view / 'New folder' edit state / 'Projects'); the folder was verified on the real Desktop."],
        ["Schema fix 2026-07-15", "the structured-output JSON schema sent with every call previously hard-coded the Excel eval's 5 verbs (Goto/Move/Select/Type/Press), so models could NOT emit RightClick/Scroll even where the prompt allowed them. The Windows eval now sends a 7-verb schema (adds RightClick, Scroll) and documents both verbs in the prompt."],
        ["", ""],
        ["Variants", ""],
        ["instruction", "the task_specs.json instruction sentence"],
        ["guide", "step-by-step walk-through of the demonstrated path (one step per gold subtask), so every model is pushed toward the SAME strategy -- e.g. W04: right-click Logs > Show more options > Send to > Compressed (zipped) folder"],
        ["", ""],
        ["Conditions", ""],
        ["no-uia", "one whole-task parse from the instruction alone (no element list)"],
        ["full-uia", "one whole-task parse; prompt includes the UNION of all UIA scans of the task's live run (per user 2026-07-15: single-shot LLM parses get the union; only the step-wise condition gets step-specific scans). All six tasks use captures that match the current gold (W03: the 2026-07-16 Ctrl+Shift+N re-capture)."],
        ["per-step", "one action per call; model sees ONLY the scan for the current step; screen advances on click/Press/Scroll"],
        ["(initial-uia)", "dropped from this workbook (user 2026-07-16); artifacts remain on disk"],
        ["", ""],
        ["Functional check", "per model x variant x condition x task, the Functional sheet judges whether the parse GETS THE JOB DONE from the task's real start state even when it deviates from gold: MATCHES GOLD (flat sequence identical) / FUNCTIONAL (alt path) (known-valid alternative, e.g. F2 or context-menu Rename, Ctrl+Shift+N, modern 'Compress to ZIP file', clicking the Calculator result, Win+E) / NOT FUNCTIONAL (a required effect is missing, stated in Detail). Deterministic rules in EnvironmentParsers/functional_check.py."],
        ["per-step caveat", "a per-step episode ends when the captured scans run out, so NOT FUNCTIONAL there often means the episode was cut short by a thin capture (e.g. W09 has only 2 distinct scans), not that the model chose wrong actions -- read the Detail column."],
        ["", ""],
        ["Sheets", ""],
        ["Gold", "gold chunks: one row per gold action"],
        ["Guides", "the exact step-by-step guide text given to the models in the guide variant"],
        ["Functional", "the functional-correctness verdicts (see above)"],
        ["Inputs", "exact steps input per variant + full prompts (no-uia / initial-uia) + per-step prompt template"],
        ["UIA_Scans", "the per-step element lists (what the model saw at each step); W02/W10 omitted as stale"],
        ["Out_* / Out_* guide", "every model's generated actions, one row per action, per variant"],
        ["Out_perstep*", "per-step actions with the scan shown and on-screen resolution"],
        ["Compare_*", "side-by-side: gold column vs each model, aligned by action index; red = differs from gold"],
        ["Summary", "resolvability + gold-recall per model per variant per condition"],
        ["", ""],
        ["Model availability", ""],
        ["gemini-3.5-flash", "NOT scored: Google 503/504 'model overloaded' (2026-07-14; unchanged)"],
        ["openai/gpt-oss-120b:free, deepseek/deepseek-v4-flash:free", "NOT scored: free slugs withdrawn (404); paid equivalents scored"],
        ["nvidia/nemotron-3-super-120b-a12b (paid)", "unstable under one-action-per-call schema; per-step numbers are a floor"],
        ["Aliases", "historical: the pre-2026-07-16 W03 gold target 'Desktop background' had no UIA name; the scan names the region 'This folder is empty.' (alias kept in scoring for old artifacts; the current gold uses Ctrl+Shift+N and needs no alias)"],
        ["W01 close excused", "W01's gold ends when Notepad opens (closing removed 2026-07-15). Model actions that close Notepad (Goto/Select 'Close') are marked 'ignored (post-task close)' and excluded from Compare alignment and Summary metrics -- not penalized, not rerun."],
        ["Flat-order matching", "gold-vs-run matching ignores the Subtask and Action # columns (user 2026-07-15): the model's k-th non-ignored action is compared to the gold's k-th action, so a model that segments subtasks differently but produces the right action sequence scores YES throughout."],
    ]
    for r in rows:
        ws.append(r)
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 110
    for row in ws.iter_rows():
        row[1].alignment = WRAP
        if row[0].value and not row[1].value:
            row[0].font = HDR

    # ---------------- Gold ----------------
    ws = wb.create_sheet("Gold")
    ws.append(["Task", "PSAI id", "Instruction", "Subtask", "Action #", "Verb", "Target"])
    style_header(ws, 7)
    for tid in TASKS:
        t = gold[tid]
        for si, sub in enumerate(t["subtasks"], 1):
            for ai, (v, tg) in enumerate(sub, 1):
                ws.append([tid, t["unique_data_id"], t["instruction"], si, ai, v, tg])
    for col, w in zip("ABCDEFG", (6, 28, 60, 8, 9, 11, 34)):
        ws.column_dimensions[col].width = w

    # ---------------- Guides ----------------
    ws = wb.create_sheet("Guides")
    ws.append(["Task", "Step #", "Guide step (verbatim model input, "
               "guide variant)"])
    style_header(ws, 3)
    for tid in TASKS:
        for i, step in enumerate(uiap.GUIDES[tid], 1):
            ws.append([tid, i, step])
    for col, w in zip("ABC", (6, 8, 110)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        row[2].alignment = WRAP

    # ---------------- Inputs ----------------
    ws = wb.create_sheet("Inputs")
    ws.append(["Task", "Variant", "Condition", "Steps input (NL)", "UIA context source",
               "Full prompt text (truncated at 32k)"])
    style_header(ws, 6)
    for tid in TASKS:
        t = gold[tid]
        n = int(tid[1:])
        u = uia[tid]
        for variant in VARIANTS:
            steps = steps_for(variant, t)
            steps_txt = "\n".join(steps)
            task_input = [{"task_id": n, "task_name": t["name"], "steps": steps}]
            for cond in ("no-uia", "full-uia"):
                if cond != "no-uia" and tid in STALE:
                    ws.append([tid, variant, cond, steps_txt, STALE_NOTE, "-"])
                    continue
                block = uiap.uia_block_for(cond, u) if cond != "no-uia" else ""
                prompt = uiap.build_w_prompt(task_input, block)
                src = "-" if cond == "no-uia" else \
                    (f"{u['run_dir']} union of all scans "
                     f"({len(u['union_pruned'])} elements)")
                ws.append([tid, variant, cond, steps_txt, src, prompt[:32700]])
            if tid in PS_STALE:
                ws.append([tid, variant, "per-step", steps_txt, STALE_NOTE, "-"])
            else:
                ws.append([tid, variant, "per-step", steps_txt,
                           f"{u['run_dir']}: {len(scans[tid])} distinct scans (see UIA_Scans)",
                           "template below; per call: history = model's own prior actions, "
                           "UI_ELEMENTS = the current step's scan only"])
    ws.append(["", "", "per-step TEMPLATE", "", "", run_perstep.PROMPT[:32700]])
    for col, w in zip("ABCDEF", (6, 12, 14, 55, 44, 120)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        row[5].alignment = WRAP
        row[3].alignment = WRAP

    # ---------------- UIA_Scans ----------------
    ws = wb.create_sheet("UIA_Scans")
    ws.append(["Task", "Run", "Scan #", "Element #", "Name", "Control type"])
    style_header(ws, 6)
    for tid in TASKS:
        if tid in PS_STALE:
            ws.append([tid, STALE_NOTE, "", "", "", ""])
            ws.cell(row=ws.max_row, column=2).fill = STALEFILL
            continue
        run = uia[tid]["run_dir"] if uia[tid] else "-"
        for k, (_names, pruned) in enumerate(scans[tid], 1):
            for i, rec in enumerate(pruned, 1):
                ws.append([tid, run, k, i, rec.get("name", ""),
                           rec.get("control_type", "")])
    for col, w in zip("ABCDEF", (6, 40, 7, 10, 60, 16)):
        ws.column_dimensions[col].width = w

    # ---------------- Output sheets (single-shot) ----------------
    for variant in VARIANTS:
        for cond, base in (("no-uia", "Out_noUIA"), ("full-uia", "Out_fullUIA")):
            ws = wb.create_sheet(base + vsuffix(variant))
            ws.append(["Model", "Provider", "Task", "Status", "Subtask", "Action #",
                       "Verb", "Target",
                       "Matches gold (flat order; Subtask/Action # ignored)"])
            style_header(ws, 9)
            for provider, model in models:
                data = ss[model][variant][cond]
                if data is None:
                    ws.append([model, provider, "-", "no artifact", "", "", "", "", ""])
                    continue
                for tid in TASKS:
                    d = data[tid]
                    if d["subtasks"] is None:
                        ws.append([model, provider, tid, d["status"], "", "", "", "", ""])
                        if d["status"] == STALE_NOTE:
                            ws.cell(row=ws.max_row, column=4).fill = STALEFILL
                        continue
                    # Flat-order comparison (user, 2026-07-15): the model's
                    # k-th non-ignored action vs the gold's k-th action --
                    # subtask segmentation and action numbering do NOT matter.
                    gold_flat = [(gv, gt) for sub in gold[tid]["subtasks"]
                                 for gv, gt in sub]
                    k = 0
                    for si, actions in d["subtasks"]:
                        for ai, (v, tg) in enumerate(actions, 1):
                            if is_ignored(tid, v, tg):
                                gm = "ignored (post-task close)"
                            elif k < len(gold_flat):
                                gv, gt = gold_flat[k]
                                gm = "YES" if (iap._verbs_equiv(gv, v)
                                               and canon(gt) == canon(tg)) else "no"
                                k += 1
                            else:
                                gm = "extra (beyond gold)"
                                k += 1
                            ws.append([model, provider, tid, "ok", si, ai, v, tg, gm])
                            if gm == "no":
                                ws.cell(row=ws.max_row, column=9).fill = BADFILL
                            elif gm == "YES":
                                ws.cell(row=ws.max_row, column=9).fill = OKFILL
                            elif gm.startswith("ignored"):
                                ws.cell(row=ws.max_row, column=9).fill = STALEFILL
            for col, w in zip("ABCDEFGHI", (34, 11, 6, 26, 8, 9, 11, 40, 24)):
                ws.column_dimensions[col].width = w

    # ---------------- Out_perstep ----------------
    for variant in VARIANTS:
        ws = wb.create_sheet("Out_perstep" + vsuffix(variant))
        ws.append(["Model", "Provider", "Task", "Step #", "Scan shown", "Verb",
                   "Target", "Target on that screen?"])
        style_header(ws, 8)
        for provider, model in models:
            data = ps[model].get(variant)
            if not data or not any(data[t]["stream"] for t in TASKS):
                ws.append([model, provider, "-", "", "", "no per-step parse", "", ""])
                continue
            for tid in TASKS:
                if not data[tid]["stream"] and data[tid].get("error"):
                    ws.append([model, provider, tid, "", "", data[tid]["error"], "", ""])
                    ws.cell(row=ws.max_row, column=6).fill = STALEFILL
                    continue
                for i, (v, tg, scan, resolved) in enumerate(data[tid]["stream"], 1):
                    res = "" if resolved is None else ("YES" if resolved else "NO")
                    ws.append([model, provider, tid, i, scan, v, str(tg)[:200], res])
                    if res == "NO":
                        ws.cell(row=ws.max_row, column=8).fill = BADFILL
                    elif res == "YES":
                        ws.cell(row=ws.max_row, column=8).fill = OKFILL
        for col, w in zip("ABCDEFGH", (34, 11, 6, 7, 11, 12, 46, 20)):
            ws.column_dimensions[col].width = w

    # ---------------- Compare sheets ----------------
    def flat_gold(tid):
        return [f'({v} "{t}")' for sub in gold[tid]["subtasks"] for v, t in sub]

    def flat_ss(model, variant, cond, tid):
        d = ss[model][variant][cond]
        if not d or d[tid]["subtasks"] is None:
            return None
        return [f'({v} "{t}")' for _si, acts in d[tid]["subtasks"]
                for v, t in acts if not is_ignored(tid, v, t)]

    def flat_ps(model, variant, tid):
        d = ps[model].get(variant)
        if not d or not d[tid]["stream"]:
            return None
        return [f'({v} "{str(t)[:60]}")' for v, t, _s, _r in d[tid]["stream"]
                if v != "<error>" and not is_ignored(tid, v, t)]

    def gold_pair(cell):  # "(Verb \"target\")" -> canonical tuple
        try:
            v, rest = cell[1:-1].split(" ", 1)
            t = rest.strip().strip('"')
            return ("GOTO" if v in ("Goto", "Move") else v, canon(t))
        except Exception:
            return (cell, "")

    for variant in VARIANTS:
        for cond, base in (("no-uia", "Compare_noUIA"),
                           ("full-uia", "Compare_fullUIA"),
                           ("per-step", "Compare_perstep")):
            ws = wb.create_sheet(base + vsuffix(variant))
            r = 1
            for tid in TASKS:
                cols = ["GOLD"] + ok_models
                seqs = {"GOLD": flat_gold(tid)}
                for m in ok_models:
                    seqs[m] = (flat_ps(m, variant, tid) if cond == "per-step"
                               else flat_ss(m, variant, cond, tid))
                title = f"{tid} — {gold[tid]['instruction']}"
                stale_here = (tid in PS_STALE if cond == "per-step"
                              else (cond != "no-uia" and tid in STALE))
                if stale_here:
                    title += f"  [{STALE_NOTE}]"
                ws.cell(row=r, column=1, value=title).font = HDR
                r += 1
                for c, name in enumerate(cols, 1):
                    cell = ws.cell(row=r, column=c, value=name)
                    cell.font = HDR; cell.fill = HDRFILL
                r += 1
                nmax = max(len(s) for s in seqs.values() if s) if any(seqs.values()) else 0
                for i in range(nmax):
                    gval = seqs["GOLD"][i] if i < len(seqs["GOLD"]) else ""
                    gc = ws.cell(row=r, column=1, value=gval)
                    gc.fill = GOLDFILL
                    for c, m in enumerate(ok_models, 2):
                        s = seqs[m]
                        val = ("(no parse)" if s is None
                               else (s[i] if i < len(s) else ""))
                        cell = ws.cell(row=r, column=c, value=val)
                        if val and val not in ("(no parse)",) and gval:
                            if gold_pair(val) != gold_pair(gval):
                                cell.fill = BADFILL
                    r += 1
                r += 2
            ws.column_dimensions["A"].width = 44
            for c in range(2, len(ok_models) + 2):
                ws.column_dimensions[get_column_letter(c)].width = 40

    # ---------------- Functional (alt-path judge, user 2026-07-16) --------
    ws = wb.create_sheet("Functional")
    ws.append(["Model", "Variant", "Condition", "Task", "Verdict", "Detail"])
    style_header(ws, 6)
    FUNCFILL = PatternFill("solid", fgColor="FFE699")

    def raw_ss(model, variant, cond, tid):
        d = ss[model][variant][cond]
        if not d or d[tid]["subtasks"] is None:
            return None
        return [(v, t) for _si, acts in d[tid]["subtasks"]
                for v, t in acts if not is_ignored(tid, v, t)]

    def raw_ps(model, variant, tid):
        d = ps[model].get(variant)
        if not d or not d[tid]["stream"]:
            return None
        return [(v, t) for v, t, _s, _r in d[tid]["stream"]
                if v != "<error>" and not is_ignored(tid, v, t)]

    func_counts = {}   # (model, variant, cond) -> [n_gets_job_done, n_judged]
    for provider, model in models:
        if model not in ok_models:
            continue
        for variant in VARIANTS:
            for cond in ("no-uia", "full-uia", "per-step"):
                for tid in TASKS:
                    seq = (raw_ps(model, variant, tid) if cond == "per-step"
                           else raw_ss(model, variant, cond, tid))
                    if seq is None:
                        continue
                    gf = [(gv, gt) for sub in gold[tid]["subtasks"]
                          for gv, gt in sub]
                    verdict, detail = functional_check.judge(tid, seq, gf)
                    ws.append([model, variant, cond, tid, verdict, detail])
                    c = ws.cell(row=ws.max_row, column=5)
                    if verdict == "MATCHES GOLD":
                        c.fill = OKFILL
                    elif verdict.startswith("FUNCTIONAL"):
                        c.fill = FUNCFILL
                    else:
                        c.fill = BADFILL
                    k = (model, variant, cond)
                    n = func_counts.setdefault(k, [0, 0])
                    n[1] += 1
                    n[0] += verdict != "NOT FUNCTIONAL"
    for col, w in zip("ABCDEF", (34, 12, 10, 6, 24, 100)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        row[5].alignment = WRAP

    # ---------------- Summary ----------------
    num_to_tid = {int(t[1:]): t for t in TASKS}

    def inames(n):
        u = uia.get(num_to_tid[n]); return u["initial_names"] if u else set()

    def unames(n):
        u = uia.get(num_to_tid[n]); return u["union_names"] if u else set()

    goldset = set()
    gold_eval = {}
    for tid in TASKS:
        n = int(tid[1:])
        for si, sub in enumerate(gold[tid]["subtasks"], 1):
            gold_eval[(n, si)] = [(v, t) for v, t in sub]
            goldset |= {canon(t) for v, t in sub if v not in ("Press", "Type", "Scroll")}

    ws = wb.create_sheet("Summary")
    ws.append(["Model", "Provider", "Variant",
               "no-UIA resolv (vs union) %", "full-UIA resolv %",
               "per-step resolv %",
               "no-UIA gold recall %", "full-UIA gold recall %",
               "per-step gold recall %",
               "gets job done: no-UIA", "gets job done: full-UIA",
               "gets job done: per-step"])
    style_header(ws, 12)
    for provider, model in models:
        for variant in VARIANTS:
            row = [model, provider, variant]
            vals = {}
            for cond, rkey in (("no-uia", "resolvability_union_pct"),
                               ("full-uia", "resolvability_union_pct")):
                data = ss[model][variant][cond]
                if not data or all(d["subtasks"] is None for d in data.values()):
                    vals[cond] = (None, None); continue
                gen = {}
                gl = set()
                for tid in TASKS:
                    d = data[tid]
                    if d["subtasks"] is None:
                        continue
                    n = int(tid[1:])
                    for si, acts in d["subtasks"]:
                        kept = [(v, t) for v, t in acts
                                if not is_ignored(tid, v, t)]
                        if not kept:
                            continue
                        gen[(n, si)] = kept
                        gl |= {canon(t) for v, t in kept
                               if v not in ("Press", "Type", "Scroll")}
                um = ugc.compute_uia_metrics(gen, gold_eval, inames, unames)
                rec = round(100.0 * len(goldset & gl) / len(goldset), 1)
                vals[cond] = (um[rkey], rec)
            d = ps[model].get(variant)
            if d and any(d[t]["stream"] for t in TASKS):
                tt = sum(d[t]["targets"] for t in TASKS)
                rr = sum(d[t]["resolved"] for t in TASKS)
                gl = set()
                for tid in TASKS:
                    gl |= {canon(t) for v, t, _s, _r in d[tid]["stream"]
                           if v not in ("Press", "Type", "Scroll", "<error>")
                           and not is_ignored(tid, v, t)}
                vals["per-step"] = (round(100.0 * rr / tt, 1) if tt else None,
                                    round(100.0 * len(goldset & gl) / len(goldset), 1))
            else:
                vals["per-step"] = (None, None)
            row += [vals["no-uia"][0], vals["full-uia"][0], vals["per-step"][0],
                    vals["no-uia"][1], vals["full-uia"][1], vals["per-step"][1]]
            if all(x is None for x in row[3:]):
                continue
            for cond in ("no-uia", "full-uia", "per-step"):
                n = func_counts.get((model, variant, cond))
                row.append(f"{n[0]}/{n[1]}" if n else None)
            ws.append([x if x is not None else "—" for x in row])
    for col, w in zip("ABCDEFGHIJKL",
                      (34, 11, 12, 24, 18, 18, 20, 18, 20, 18, 18, 18)):
        ws.column_dimensions[col].width = w

    out = os.path.join(EVAL, OUT_NAME)
    try:
        wb.save(out)
    except PermissionError:
        # The canonical workbook is open in Excel (Windows lock). Save to a
        # sibling so a fresh build is still available; the next unlocked
        # rebuild updates the canonical file again.
        out = os.path.join(EVAL, OUT_NAME.replace(".xlsx", "_live.xlsx"))
        wb.save(out)
        print("canonical workbook locked (open in Excel); saved fallback")
    print("wrote", out)
    print("sheets:", ", ".join(wb.sheetnames))
    print("models with output columns:", len(ok_models))


if __name__ == "__main__":
    main()
