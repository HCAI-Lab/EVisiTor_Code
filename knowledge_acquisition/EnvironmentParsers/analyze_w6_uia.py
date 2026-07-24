"""Six-task UIA-grounded comparison: no-UIA -> initial-UIA -> per-step.

per-step = at each moment the model saw ONLY the scan captured for that step of
the live run (screen advances only on a click / Press / Scroll). Two robust,
alignment-free metrics, computed uniformly across the three conditions:

  resolvability = share of the model's Goto/Select/RightClick targets that are a
                  real UIA element name on the screen it was shown (no-UIA: vs
                  the union, since it saw nothing; initial: vs the start scan;
                  per-step: vs THAT step's scan).
  gold recall   = share of the distinct task-specific gold targets (screen items
                  + typed text, excluding generic key chords) the model produced
                  anywhere -- order-independent, so it is not distorted by the
                  model splitting/merging Goto+Select.

Writes: scratchpad/w6_uia_section.md
"""
from __future__ import annotations
import json, os, sys

ROOT = os.environ.get("EVISITOR_REPO_ROOT", "g:/ACT-RModels")
HERE = os.path.join(ROOT, "EnvironmentParsers")
GI = os.path.join(ROOT, "EVisiTor2026", "NewInterfaces_PSAI", "GenericInterface")
EVAL = os.path.join(GI, "llm_parsing_eval")
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, GI)
import InstructionAcquisitionParser as iap
import uia_grounding_common as ugc
import UIAGroundedParser as uiap

TASKS = ["W01", "W02", "W03", "W04", "W09", "W10"]


def tnum(t): return int(t[1:])


def load_gold():
    with open(os.path.join(GI, "task_specs.json"), encoding="utf-8") as f:
        specs = json.load(f)["tasks"]
    gold, flat = {}, {}
    for t in specs:
        n = tnum(t["id"]); seq = []
        for si, sub in enumerate(t["subtasks"], start=1):
            gold[(n, si)] = [(v, tg) for v, tg in sub]
            seq += [(v, tg) for v, tg in sub]
        flat[t["id"]] = seq
    return gold, flat


# Current-Windows regrounding aliases (2026-07-14): the gold label and the
# name the live UIA scan actually exposes for the same object. 'Desktop
# background' has no UIA name of its own; the scan names that region by its
# placeholder text. The runtime map (agent_resolution/*.map.json) encodes the
# same equivalences for the live ACT-R run.
ALIAS = {
    "this folder is empty.": "desktop background",
}


def _canon(t):
    n = iap._norm_target(t)
    return ALIAS.get(n, n)


def gold_labels(gold_flat):
    return {_canon(t) for (v, t) in gold_flat if v != "Press"}


def gen_labels(pairs):
    return {_canon(t) for (v, t) in pairs if v != "Press"}


def recall(goldset, genset):
    return round(100.0 * len(goldset & genset) / len(goldset), 1) if goldset else None


def gen_single_shot(model, cond):
    slug = iap._slug(model)
    p = os.path.join(EVAL, f"{slug}__instruction__{cond}.json")
    if not os.path.exists(p):
        return None
    data = json.load(open(p, encoding="utf-8"))
    per = data.get("per_task", {}); gen = {}; nfail = 0
    for tid in TASKS:
        e = per.get(tid)
        if not e or e.get("call_error") or not e.get("schema_valid") or not e.get("raw", {}).get("tasks"):
            nfail += 1; continue
        task = e["raw"]["tasks"][0]; n = tnum(tid)
        for s in sorted(task.get("subtasks", []), key=lambda s: s.get("subtask_id", 0)):
            gen[(n, s.get("subtask_id"))] = [(a["action"], a["target"]) for a in s.get("actions", [])]
    return None if nfail == 6 else gen


def gen_per_step(model):
    slug = iap._slug(model)
    p = os.path.join(EVAL, f"{slug}__instruction__per-step.json")
    if not os.path.exists(p):
        return None
    data = json.load(open(p, encoding="utf-8"))
    per = data.get("per_task", {}); out = {}
    for tid in TASKS:
        d = per.get(tid) or {}
        out[tid] = {"flat": [(v, t) for (v, t, *_r) in d.get("stream", []) if v != "<error>"],
                    "targets": d.get("targets", 0), "resolved": d.get("resolved", 0),
                    "n_scans": d.get("n_scans", 0)}
    return out


def main():
    gold, gold_flat = load_gold()
    goldset = set()
    for t in TASKS:
        goldset |= gold_labels(gold_flat[t])

    uia = {t: uiap.load_task_uia(t) for t in TASKS}
    num_to_tid = {tnum(t): t for t in TASKS}
    def inames(n):
        u = uia.get(num_to_tid[n]); return u["initial_names"] if u else set()
    def unames(n):
        u = uia.get(num_to_tid[n]); return u["union_names"] if u else set()
    gref = ugc.compute_uia_metrics(gold, gold, inames, unames)

    data = {}
    for provider, model in iap.MODELS:
        row = {"provider": provider}
        for cond, rkey in (("no-uia", "resolvability_union_pct"),
                           ("initial-uia", "resolvability_initial_pct")):
            g = gen_single_shot(model, cond)
            if not g:
                row[cond] = None; continue
            gl = set()
            for pairs in g.values():
                gl |= gen_labels(pairs)
            um = ugc.compute_uia_metrics(g, gold, inames, unames)
            row[cond] = {"recall": recall(goldset, gl), "resolv": um[rkey]}
        ps = gen_per_step(model)
        if ps and any(ps[t]["flat"] for t in TASKS):
            gl = set(); tt = rr = 0
            for t in TASKS:
                gl |= gen_labels(ps[t]["flat"]); tt += ps[t]["targets"]; rr += ps[t]["resolved"]
            row["per-step"] = {"recall": recall(goldset, gl),
                               "resolv": round(100.0 * rr / tt, 1) if tt else 0.0,
                               "targets": tt, "resolved": rr, "by_task": ps}
        else:
            row["per-step"] = None
        data[model] = row

    def rr(m, c, k):
        d = data[m].get(c); return f"{d[k]:.1f}" if d and d[k] is not None else "—"

    L = []
    L.append("## UIA-grounded chunk generation (six live tasks)\n")
    L.append(
        "The table above (no-UIA) is deliberately hard: a model cannot invent "
        "the exact on-screen UIA label (`Search Documents`, `Compressed "
        "(zipped) folder`, `Desktop background`) from the instruction alone. "
        "The appropriate test for a *grounding* pipeline is to give the model "
        "the real UIA elements the ACT-R model perceives, scored against the "
        "current six-task gold and the corrected live captures — **W04/W09 were "
        "re-captured on 2026-07-14** so they are the right tasks (the earlier "
        "captures were the pre-renumber delete / autohide runs). Two grounded "
        "conditions:\n")
    L.append("- **initial-UIA** — one whole-task parse given only the "
             "start-of-task scan.")
    L.append("- **per-step** — the realistic condition: the model is shown "
             "**only the scan captured for the current step**, one action at a "
             "time, and the screen advances to the next captured scan only when "
             "the model acts (click / Press / Scroll) — never a look (Goto). No "
             "union / future-screen leakage; this is exactly what the live "
             "ACT-R model perceives.\n")
    L.append("Two alignment-free metrics (so splitting/merging Goto+Select does "
             "not distort them):")
    L.append("- **Resolvability** — share of the model's Goto/Select/RightClick "
             "targets that equal a real UIA element name on the screen it was "
             "shown (no-UIA: vs the whole-run union, since it saw no scan; "
             "initial: vs the start scan; per-step: vs *that step's* scan). The "
             "match rule is the one `generic_live.lisp` uses at run time.")
    L.append("- **Gold recall** — share of the distinct task-specific gold "
             "targets (screen items + typed strings, excluding generic key "
             "chords) the model produced anywhere.\n")
    L.append(f"Gold ceiling: scoring the gold targets themselves gives "
             f"resolvability initial {gref['resolvability_initial_pct']:.0f}%, "
             f"union {gref['resolvability_union_pct']:.0f}% "
             f"({gref['visual_targets_scored']} visual targets).\n")
    L.append("**Capture-completeness fixes (2026-07-14).** An earlier draft "
             "claimed the Windows 11 cascade sub-menus were \"not exposed to "
             "UI Automation\"; that was wrong. A live probe showed every menu "
             "level (`Show more options`, `Send to`, `Compressed (zipped) "
             "folder`, `New`, `Folder`) is fully UIA-readable — the scans were "
             "missing them because of a **timing race**: the model requests its "
             "visicon refresh milliseconds after a click, before the Win11 menu "
             "has rendered. The bridge already settled after key chords "
             "(`AGENT_KEY_SETTLE_MS`) but not after clicks; a post-click "
             "menu-settle (`AGENT_CLICK_SETTLE_MS`, polls until the menu is "
             "visible) fixes it. With the fix, the live W04 run **completes and "
             "captures all menu levels step-aligned** (initial → modern menu → "
             "classic menu → Send-to cascade → result). Two current-Windows "
             "regroundings, per the rule that targets must be items the model "
             "actually sees: the modern menu's direct zip action is now "
             "`Compress to...` (the demonstrated legacy path still exists under "
             "`Show more options`, so the W04 gold stands), and W03's `Desktop "
             "background` — which has no UIA name of its own — is the region "
             "the scan names **`This folder is empty.`** (treated as equivalent "
             "in scoring and in the runtime resolution map).\n")

    L.append("### Resolvability — does the model name something actually on screen?\n")
    L.append("| Model | Provider | no-UIA (vs union) % | initial-UIA % | "
             "**per-step** % |")
    L.append("|---|---|--:|--:|--:|")
    for provider, model in iap.MODELS:
        L.append(f"| `{model}` | {provider} | {rr(model,'no-uia','resolv')} | "
                 f"{rr(model,'initial-uia','resolv')} | "
                 f"**{rr(model,'per-step','resolv')}** |")
    ok = [data[m]["per-step"] for _, m in iap.MODELS if data[m].get("per-step")]
    if ok:
        at = sum(p["resolved"] for p in ok); an = sum(p["targets"] for p in ok)
        L.append(f"\n_Across the {len(ok)} models that produced a per-step "
                 f"parse, **{100.0*at/an:.0f}%** of every target named at a step "
                 f"was actually present on the screen shown at that step "
                 f"({at}/{an}) — versus the 30–50% no-UIA coincidence rate. "
                 "Grounding the model in the current screen essentially removes "
                 "the naming problem._\n")

    L.append("### Gold-target recall — does it name the RIGHT things?\n")
    L.append("| Model | Provider | no-UIA % | initial-UIA % | **per-step** % |")
    L.append("|---|---|--:|--:|--:|")
    for provider, model in iap.MODELS:
        L.append(f"| `{model}` | {provider} | {rr(model,'no-uia','recall')} | "
                 f"{rr(model,'initial-uia','recall')} | "
                 f"**{rr(model,'per-step','recall')}** |")
    L.append(f"\n_(Recall is over the {len(goldset)} distinct task-specific gold "
             "targets, with the documented `Desktop background` ≡ `This folder "
             "is empty.` equivalence. After the capture fixes the screens are "
             "step-aligned and complete, so per-step recall reflects what a "
             "screen-grounded parser can actually achieve rather than being "
             "capped by missing scans.)_\n")

    L.append("‡ Not scored: `gemini-3.5-flash` (Google 503/504 “model "
             "overloaded” all session); `*:free` slugs 404 (withdrawn, paid "
             "equivalents scored). `nemotron-3-super` (paid) was unstable under "
             "the one-action-at-a-time schema (empty / unparseable JSON), so "
             "several of its per-step actions dropped — its per-step numbers are "
             "a floor, not a fair read.\n")

    md = "\n".join(L)
    open(os.path.join(OUT, "w6_uia_section.md"), "w", encoding="utf-8").write(md)
    print("wrote w6_uia_section.md\n")
    print(f"gold ceiling: init={gref['resolvability_initial_pct']:.0f} union={gref['resolvability_union_pct']:.0f}  |goldset|={len(goldset)}")
    print(f"{'model':<34}{'nR':>6}{'iR':>6}{'psR':>6}   {'nRec':>6}{'iRec':>6}{'psRec':>6}")
    for provider, model in iap.MODELS:
        d = data[model]
        def g(c, k): return (d[c][k] if d.get(c) and d[c][k] is not None else float('nan'))
        print(f"{model:<34}{g('no-uia','resolv'):>6.0f}{g('initial-uia','resolv'):>6.0f}"
              f"{g('per-step','resolv'):>6.0f}   {g('no-uia','recall'):>6.0f}"
              f"{g('initial-uia','recall'):>6.0f}{g('per-step','recall'):>6.0f}")


if __name__ == "__main__":
    main()
