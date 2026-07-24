"""Functional-correctness judge for the six live Windows tasks (2026-07-16).

Purpose (user request): many generated parses deviate from the gold action
sequence but are TECHNICALLY CAPABLE of getting the job done on a real
Windows 11 machine (e.g. renaming with F2 or the right-click context menu
instead of the toolbar Rename button, creating a folder via the context-menu
New > Folder path when the gold uses Ctrl+Shift+N (since 2026-07-16),
zipping with the modern "Compress to ZIP file" context item instead of the
legacy Send-to path, launching the Calculator by clicking the search result
instead of pressing Enter). Those parses should be FLAGGED as functionally
correct, not just marked as gold mismatches.

judge(tid, flat_actions) -> (verdict, detail)
  flat_actions : [(verb, target), ...] -- the model's flat action sequence,
                 post-task-cleanup actions (W01 close) already removed.
  verdict      : "MATCHES GOLD"            flat sequence == gold (Goto/Move
                                           equivalent, targets canonicalized)
                 "FUNCTIONAL (alt path)"   achieves the task via a known-valid
                                           alternative strategy from the
                                           task's REAL start state
                 "NOT FUNCTIONAL"          a required effect is missing
  detail       : which alternative features were used / which requirement
                 failed.

The rules are deliberately hand-written and conservative-but-charitable:
each task lists the effects that MUST occur (from its live start state) and
the known interchangeable ways of producing them. Generic-fallback names from
ungrounded parses are matched by substring (e.g. a click on "search box"
counts as focusing search).

Start states (2026-07-16 specs):
  W01 desktop; W02 desktop, Explorer closed, opens to a folder view (Downloads)
  containing budget.xlsx (Home tiles have Rename disabled, so the pin-to-Home
  plan was replaced); W03 desktop, Explorer closed; W04 Explorer open showing
  Logs; W09 desktop/taskbar; W10 Explorer already open, Documents in nav pane.
"""
from __future__ import annotations
import re
from typing import List, Tuple

ALIAS = {"this folder is empty.": "desktop background"}


def canon(s: str) -> str:
    t = str(s).strip().lower()
    m = re.fullmatch(r"row[ _](\d+)", t)
    if m:
        t = m.group(1)
    return ALIAS.get(t, t)


def _verbs_equiv(a: str, b: str) -> bool:
    nav = {"Goto", "Move"}
    return (a in nav and b in nav) or a == b


class Ops:
    """Effective operations extracted from a flat action sequence."""

    def __init__(self, seq: List[Tuple[str, str]]):
        self.seq = [(v, canon(t)) for v, t in seq]
        self.clicks = [t for v, t in self.seq if v == "Select"]
        self.rclicks = [t for v, t in self.seq if v == "RightClick"]
        self.lookups = [t for v, t in self.seq
                        if v in ("Goto", "Move", "Select")]
        self.types = [t for v, t in self.seq if v == "Type"]
        self.presses = [t for v, t in self.seq if v == "Press"]

    def clicked(self, *names):          # exact click
        return any(t in names for t in self.clicks)

    def clicked_like(self, *subs):      # substring click (generic fallbacks)
        return any(s in t for t in self.clicks for s in subs)

    def rclicked_like(self, *subs):
        return any(s in t for t in self.rclicks for s in subs)

    def typed_like(self, *subs):
        return any(s in t for t in self.types for s in subs)

    def pressed(self, *keys):
        return any(t in keys for t in self.presses)

    def looked_like(self, *subs):       # Goto/Move/Select (attention counts)
        return any(s in t for t in self.lookups for s in subs)


# ---------------------------------------------------------------------------
# Per-task functional rules. Each returns (ok, used_alts, missing).
# ---------------------------------------------------------------------------

def _w01(o: Ops):
    alts, missing = [], []
    if not o.pressed("win+r"):
        missing.append("never opens the Run dialog (Press win+r)")
    if o.typed_like("notepad"):
        if o.typed_like("notepad.exe"):
            alts.append("typed 'notepad.exe' (valid Run command)")
    else:
        missing.append("never types the notepad command")
    if o.pressed("enter"):
        pass
    elif o.clicked_like("ok"):
        alts.append("clicked OK instead of pressing Enter")
    else:
        missing.append("never submits the Run dialog (Enter/OK)")
    return not missing, alts, missing


def _w02(o: Ops):
    alts, missing = [], []
    if o.clicked_like("file explorer"):
        pass
    elif o.pressed("win+e"):
        alts.append("opened File Explorer with Win+E")
    else:
        missing.append("never opens File Explorer (start state: closed)")
    if not (o.clicked_like("budget.xlsx") or o.rclicked_like("budget.xlsx")):
        missing.append("never selects budget.xlsx")
    if o.clicked_like("rename"):
        if o.rclicked_like("budget.xlsx"):
            alts.append("context-menu Rename (right-click) instead of the "
                        "toolbar button")
    elif o.pressed("f2"):
        alts.append("renamed with F2 instead of the toolbar button")
    else:
        missing.append("never invokes Rename (toolbar / context menu / F2)")
    if not o.typed_like("budget_2025.xlsx"):
        missing.append("never types the new name 'budget_2025.xlsx'")
    if not o.pressed("enter"):
        missing.append("never commits the new name (Enter)")
    return not missing, alts, missing


def _w03(o: Ops):
    alts, missing = [], []
    on_desktop = (o.clicked_like("desktop")
                  or o.rclicked_like("desktop", "empty"))
    if o.rclicked_like("desktop", "empty") and not o.clicked_like("file explorer"):
        alts.append("right-clicked the desktop directly (no Explorer needed)")
    if not on_desktop:
        missing.append("never navigates to / acts on the Desktop")
    # 2026-07-16: gold switched to the Ctrl+Shift+N chord (the old gold's
    # right-click target -- the folder view's empty background -- is not a
    # UIA visual item, so it could never be grounded). The context-menu
    # New > Folder path is now the accepted alternative.
    if o.pressed("ctrl+shift+n"):
        pass
    elif o.clicked_like("new") and o.clicked_like("folder"):
        alts.append("created the folder via the context-menu New > Folder "
                    "path instead of Ctrl+Shift+N")
    elif o.clicked_like("new folder"):
        alts.append("used a 'New folder' button/menu item")
    else:
        missing.append("never creates a new folder (New>Folder / "
                       "Ctrl+Shift+N / New folder button)")
    if not o.typed_like("projects"):
        missing.append("never types the folder name 'Projects'")
    if not o.pressed("enter"):
        missing.append("never commits the folder name (Enter)")
    return not missing, alts, missing


def _w04(o: Ops):
    alts, missing = [], []
    acts_on_logs = o.rclicked_like("logs") or o.clicked_like("logs")
    if not acts_on_logs:
        missing.append("never acts on the Logs folder")
    legacy = (o.clicked_like("show more options")
              and o.clicked_like("send to")
              and o.clicked_like("compressed (zipped) folder"))
    modern = o.clicked_like("compress to", "compress folder", "compress to zip")
    ribbon = o.clicked_like("zip") and not legacy
    if legacy:
        pass
    elif modern:
        alts.append("modern context item 'Compress to ZIP file' instead of "
                    "the legacy Send-to path")
    elif ribbon:
        alts.append("a toolbar/ribbon ZIP action instead of the Send-to path")
    else:
        missing.append("never triggers compression (Send to > Compressed "
                       "(zipped) folder, or Compress to ZIP file)")
    # accepting the default archive name needs no Enter on the modern path;
    # on the legacy path Windows also creates 'Logs.zip' if the name edit is
    # simply left alone, so Enter is not required for functionality.
    return not missing, alts, missing


def _w09(o: Ops):
    alts, missing = [], []
    if o.clicked_like("search", "start"):
        pass
    elif o.pressed("win", "win+s"):
        alts.append("opened Start search with the keyboard (Win / Win+S)")
    else:
        missing.append("never opens the Start menu search")
    if o.typed_like("calc"):
        if not o.typed_like("calculator"):
            alts.append("typed the shortened query 'calc'")
    else:
        missing.append("never types a calculator query")
    if o.pressed("enter"):
        pass
    elif o.clicked_like("calculator", "open"):
        alts.append("clicked the Calculator search result instead of "
                    "pressing Enter")
    else:
        missing.append("never launches the result (Enter or click)")
    return not missing, alts, missing


def _w10(o: Ops):
    alts, missing = [], []
    if not o.clicked_like("documents"):
        missing.append("never opens the Documents folder (Explorer is "
                       "already open; nav-pane click required)")
    if o.clicked_like("search"):
        pass
    elif o.pressed("ctrl+e", "ctrl+f", "f3"):
        alts.append("focused the search box with a keyboard shortcut")
    else:
        missing.append("never focuses the Explorer search box")
    if o.typed_like("report"):
        if not o.typed_like("report.docx"):
            alts.append("searched a partial query ('report') -- still finds "
                        "report.docx")
    else:
        missing.append("never types a search query for the report file")
    if o.pressed("enter") or o.looked_like("report.docx"):
        if not o.pressed("enter"):
            alts.append("located the result without pressing Enter "
                        "(search-as-you-type)")
    else:
        missing.append("never executes the search / locates the result")
    return not missing, alts, missing


RULES = {"W01": _w01, "W02": _w02, "W03": _w03, "W04": _w04,
         "W09": _w09, "W10": _w10}


def matches_gold(gold_flat, seq) -> bool:
    if len(gold_flat) != len(seq):
        return False
    return all(_verbs_equiv(gv, v) and canon(gt) == canon(t)
               for (gv, gt), (v, t) in zip(gold_flat, seq))


def judge(tid: str, flat_actions: List[Tuple[str, str]], gold_flat=None):
    """-> (verdict, detail)."""
    if gold_flat is not None and matches_gold(gold_flat, flat_actions):
        return "MATCHES GOLD", ""
    rule = RULES.get(tid)
    if rule is None:
        return "NOT FUNCTIONAL", f"no rules for {tid}"
    ok, alts, missing = rule(Ops(flat_actions))
    if ok:
        detail = "; ".join(alts) if alts else \
            "same strategy as gold, minor sequence differences"
        return "FUNCTIONAL (alt path)", detail
    return "NOT FUNCTIONAL", "; ".join(missing)
