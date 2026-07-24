"""agent_resolver.py — agent-in-the-loop UIA target resolution for the
generic-interface live runs.

Idea (per the 2026-07-13 request): instead of the model relying on hard-coded
chunk labels that must exactly match the live UIA Name, the live UIA scan is
shown to the agent, the agent decides which on-screen item each expected label
maps to, that decision drives the run, and it is persisted so future runs
auto-apply it.

Integration: TCP_VisiTor.py's `refreshvisicons` handler calls, when
AGENT_RESOLVE=1 in the environment:
    reposition_foreground_left()          # before the scan
    ... visual_v3 writes visicons.json ...
    apply(output_path, os.getenv("AGENT_TASK"))

`apply` rewrites visicons.json so each of the task's expected target labels
becomes one visicon entry, positioned at the *real* on-screen coordinates of
the element the agent (or an exact match, or a learned map) picked. Labels that
cannot be resolved are simply omitted (the model then waits / scrolls).

Handshake files live in GenericInterface/agent_resolution/:
    request_<seq>.json   written by this module, read by the agent
    response_<seq>.json  written by the agent, read by this module
    <task>.map.json      learned {expected_label: uia_name}, auto-applied
    transcript.log       human-readable record of every resolution
"""

import os
import re
import json
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_GI = os.path.abspath(os.path.join(_HERE, "..", "NewInterfaces_PSAI", "GenericInterface"))
RES_DIR = os.path.join(_GI, "agent_resolution")
SPECS = os.path.join(_GI, "task_specs.json")

VISUAL_VERBS = {"Goto", "Move", "Select", "RightClick", "ClickDown", "ClickUp"}
# Windows we must never reposition (our own tooling), matched case-insensitively.
_REPOS_DENY = ("visual studio code", "- code", "powershell", "windows terminal",
               "cmd.exe", "command prompt", "sbcl", "python", "control panel",
               "act-r", "acl ", "listener")

_seq = 0
_CAP_STAMP = None   # per-process capture run timestamp (set on first scan)
_CAP_N = {}         # task_id -> running scan counter


def _capture_scan(task, raw):
    """When env AGENT_CAPTURE_SCANS=1, save the FULL pre-prune UIA scan to
    live_runs/<task_id>_<runstamp>/visicon_snapshots/visicons_NNN.json so the
    UIA-grounded eval (UIAGroundedParser.py) can read a real element set for
    this task. Non-destructive and independent of the visicons.json rewrite;
    off by default so normal runs are unaffected."""
    if os.environ.get("AGENT_CAPTURE_SCANS") != "1":
        return
    try:
        global _CAP_STAMP
        if _CAP_STAMP is None:
            _CAP_STAMP = time.strftime("%Y%m%d_%H%M%S")
        task_id = (task or "task").split("_")[0]
        d = os.path.join(_GI, "live_runs", f"{task_id}_{_CAP_STAMP}",
                         "visicon_snapshots")
        os.makedirs(d, exist_ok=True)
        n = _CAP_N.get(task_id, 0) + 1
        _CAP_N[task_id] = n
        with open(os.path.join(d, f"visicons_{n:03d}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2, ensure_ascii=False)
        _log(f"captured full scan -> live_runs/{task_id}_{_CAP_STAMP}/"
             f"visicon_snapshots/visicons_{n:03d}.json ({len(raw)} elements)")
    except Exception as e:
        _log(f"scan capture skipped: {e!r}")


def _log(msg):
    try:
        os.makedirs(RES_DIR, exist_ok=True)
        with open(os.path.join(RES_DIR, "transcript.log"), "a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except Exception:
        pass
    print("[agent_resolver] " + msg)


def reposition_foreground_left(width=900, height=1000):
    """Move the current foreground window into the model's left search region
    (x < *instruction-panel-x-boundary* = 960) so its elements are visible to
    the model. Skips our own dev tooling."""
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return
        title = (win32gui.GetWindowText(hwnd) or "").lower()
        if any(d in title for d in _REPOS_DENY) or not title:
            return
        win32gui.MoveWindow(hwnd, 0, 0, width, height, True)
        _log(f"repositioned foreground '{title[:40]}' -> (0,0,{width},{height})")
    except Exception as e:  # never let repositioning break a scan
        _log(f"reposition skipped: {e!r}")


def scroll_nav_pane_top():
    """Scroll the foreground File Explorer window's navigation pane to the
    top via the UIA ScrollPattern (no mouse, no focus change). Win11 restores
    fresh Explorer windows with the pane scrolled down, which leaves the
    quick-access rows ('Start of Quick Access - Desktop', 'Documents
    (pinned)', ...) virtualized at rect [0,0,0,0] -- present in the UIA tree
    but unclickable and hence unresolvable (2026-07-16, W03). Called by the
    bridge between reposition and scan when AGENT_NAV_SCROLL_TOP=1."""
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd or win32gui.GetClassName(hwnd) != "CabinetWClass":
            return
        from pywinauto import Desktop as _PwDesktop
        w = _PwDesktop(backend="uia").window(handle=hwnd)
        trees = w.descendants(control_type="Tree")
        if not trees:
            return
        trees[0].iface_scroll.SetScrollPercent(-1, 0.0)
        _log("nav pane scrolled to top (AGENT_NAV_SCROLL_TOP)")
    except Exception as e:  # never let this break a scan
        _log(f"nav-pane scroll skipped: {e!r}")


def reposition_title_left(substr, width=900, height=1000, topmost=True):
    """Move the (first visible) window whose title contains `substr` into the
    model's left search region AND float it above other windows.

    This makes the target app scannable-by-title and clickable regardless of
    which window currently holds the foreground -- essential on a machine where
    permission dialogs keep stealing focus back to the IDE. Unlike
    reposition_foreground_left this does NOT depend on the target being
    foreground at scan time."""
    if not substr:
        return
    try:
        import win32gui
        import win32con
        subl = str(substr).lower()
        hit = [None]

        def cb(hwnd, _):
            if hit[0] is not None:
                return
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd) or ""
                if subl in t.lower():
                    hit[0] = (hwnd, t)

        win32gui.EnumWindows(cb, None)
        if hit[0] is None:
            _log(f"reposition_title: no visible window matching {substr!r}")
            return
        hwnd, title = hit[0]
        if win32gui.IsIconic(hwnd):   # restore if a taskbar toggle minimized it
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # If the window is already parked in the search region, do NOT call
        # SetWindowPos again: re-activating it dismisses any open context menu
        # (Win11 menus close on the slightest activation change). Positioning
        # once on the first scan and then leaving it alone is what lets the W04
        # right-click -> Show more options -> Send to cascade survive.
        try:
            l, t, _r, _b = win32gui.GetWindowRect(hwnd)
        except Exception:
            l = t = 10 ** 9
        if abs(l) <= 12 and abs(t) <= 12:
            return
        insert_after = win32con.HWND_TOPMOST if topmost else win32con.HWND_TOP
        win32gui.SetWindowPos(hwnd, insert_after, 0, 0, width, height,
                              win32con.SWP_SHOWWINDOW)
        _log(f"reposition_title '{title[:40]}' -> (0,0,{width},{height}) "
             f"topmost={topmost}")
    except Exception as e:
        _log(f"reposition_title skipped: {e!r}")


def current_target_title(substr):
    """Return the FULL current title of the first visible window whose title
    contains `substr` (case-insensitive), else None.

    The live scan pins to a window via an anchored title match, but an app's
    title text changes as it navigates (e.g. Explorer 'Documents - File
    Explorer' becomes 'report.docx - Search Results in Documents - File
    Explorer' once a search runs). Re-fetching the full title each scan lets us
    keep pinning to the same window across those changes -- reposition_title_left
    (substring) and this helper select the same window."""
    if not substr:
        return None
    try:
        import win32gui
        subl = str(substr).lower()
        hit = [None]

        def cb(hwnd, _):
            if hit[0] is not None:
                return
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd) or ""
                if subl in t.lower():
                    hit[0] = t

        win32gui.EnumWindows(cb, None)
        return hit[0]
    except Exception as e:
        _log(f"current_target_title skipped: {e!r}")
        return None


def _menu_popup_handles(min_height=120):
    """Handles of visible context-menu popups: Win11 modern XAML menus
    ('PopupHost' / Microsoft.UI.Content.PopupWindowSiteBridge) and classic
    Win32 menus (#32768). Small popups (tooltips) are excluded by height."""
    import win32gui
    out = []

    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return
        try:
            cls = win32gui.GetClassName(h) or ""
        except Exception:
            return
        t = win32gui.GetWindowText(h) or ""
        if "PopupWindowSiteBridge" in cls or cls == "#32768" or t == "PopupHost":
            try:
                l, tp, r, b = win32gui.GetWindowRect(h)
            except Exception:
                return
            if (b - tp) >= min_height:
                out.append(h)

    win32gui.EnumWindows(cb, None)
    return out


def menu_is_open():
    """True if a real context-menu popup (not a tooltip) is currently visible.
    The bridge uses this to skip repositioning mid-menu (which would dismiss it)."""
    try:
        return bool(_menu_popup_handles())
    except Exception:
        return False


def append_popup_menu_features(output_path):
    """Append visible context-menu items to the visicon JSON at output_path.

    visual_v3's window scan cannot traverse Win11's XAML content-island menus,
    but UIAElementInfo(hwnd).descendants() reads both those and classic #32768
    menus fine. W04 (right-click Logs -> Show more options -> Send to ->
    Compressed (zipped) folder) lives entirely in these popups."""
    try:
        import win32gui  # noqa: F401  (used by _menu_popup_handles)
        from pywinauto.uia_element_info import UIAElementInfo
    except Exception as e:
        _log(f"popup capture unavailable: {e!r}")
        return 0
    try:
        popups = _menu_popup_handles()
    except Exception as e:
        _log(f"popup enum failed: {e!r}")
        return 0
    if not popups:
        return 0
    try:
        data = json.load(open(output_path, encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    seen = set((str(e.get("name", "")).strip().casefold(),
                tuple(e.get("position") or [])) for e in data)
    menu_ctypes = {"MenuItem", "Button", "ListItem"}
    added = 0
    for h in popups:
        try:
            ds = UIAElementInfo(h).descendants()
        except Exception:
            continue
        for d in ds:
            try:
                nm = d.name or ""
                ct = d.control_type or ""
            except Exception:
                continue
            if not nm.strip() or ct not in menu_ctypes:
                continue
            try:
                r = d.rectangle
                l, tp, ri, b = r.left, r.top, r.right, r.bottom
            except Exception:
                continue
            if ri <= l or b <= tp:
                continue
            cx, cy = (l + ri) // 2, (tp + b) // 2
            key = (nm.strip().casefold(), (cx, cy))
            if key in seen:
                continue
            seen.add(key)
            data.append({
                "name": nm, "type": ct.lower(), "control_type": ct,
                "position": [cx, cy], "rect": [l, tp, ri, b],
                "width": ri - l, "height": b - tp, "color": None,
                "text": nm, "highlighted": False,
                "parent_text": "context-menu", "children_count": 0,
            })
            added += 1
    if added:
        json.dump(data, open(output_path, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        _log(f"appended {added} popup-menu feature(s) from {len(popups)} popup(s)")
    return added


def clear_topmost(substr):
    """Drop the always-on-top flag from the window matching `substr` (cleanup)."""
    if not substr:
        return
    try:
        import win32gui
        import win32con
        subl = str(substr).lower()

        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd) or ""
                if subl in t.lower():
                    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                                          win32con.SWP_SHOWWINDOW)

        win32gui.EnumWindows(cb, None)
    except Exception as e:
        _log(f"clear_topmost skipped: {e!r}")


def _task_labels(task):
    """Expected visual-target labels for a task id like 'W01_run_notepad'."""
    tid = task.split("_")[0].upper()
    try:
        specs = json.load(open(SPECS, encoding="utf-8"))
    except Exception as e:
        _log(f"could not read task_specs.json: {e!r}")
        return []
    for t in specs.get("tasks", []):
        if str(t.get("id", "")).upper() == tid:
            labels = []
            for sub in t.get("subtasks", []):
                for a in sub:
                    if isinstance(a, list) and len(a) == 2 and a[0] in VISUAL_VERBS:
                        if a[1] not in labels:
                            labels.append(a[1])
            return labels
    return []


def _map_path(task):
    return os.path.join(RES_DIR, f"{task}.map.json")


def _load_map(task):
    p = _map_path(task)
    if os.path.isfile(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_map(task, m):
    os.makedirs(RES_DIR, exist_ok=True)
    json.dump(m, open(_map_path(task), "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def _tokens(s):
    return set(re.findall(r"[a-z0-9]+", str(s).lower()))


def apply(output_path, task, timeout=240):
    """Rewrite visicons.json at output_path to the agent-resolved visicon."""
    global _seq
    if not task or not output_path or not os.path.isfile(output_path):
        return None
    try:
        raw = json.load(open(output_path, encoding="utf-8"))
    except Exception as e:
        _log(f"could not read scan {output_path}: {e!r}")
        return None

    _capture_scan(task, raw)

    labels = _task_labels(task)
    if not labels:
        return None
    learned = _load_map(task)

    named = [e for e in raw if str(e.get("name", "")).strip()]

    def _clickable(e):
        # Virtualized items (e.g. scrolled-out / collapsed nav-pane rows)
        # report rect [0,0,0,0]; resolving a label onto one makes the model
        # click the window corner (2026-07-16: W03 'Desktop' resolved to the
        # virtualized nav root and the click was a no-op). Only elements with
        # a real on-screen rectangle are resolvable.
        r = e.get("rect") or []
        if len(r) == 4 and not (r[2] - r[0] > 0 and r[3] - r[1] > 0):
            return False
        p = e.get("position") or []
        return bool(p) and isinstance(p[0], (int, float))

    def find_exact(name):
        if not name:
            return None
        nl = str(name).strip().casefold()
        matches = [e for e in named
                   if str(e.get("name", "")).strip().casefold() == nl
                   and _clickable(e)]
        if not matches:
            return None
        # Prefer an element inside the model's search region (x < 960); several
        # UI items can share a name (e.g. the Calculator window title at x=83 vs
        # its taskbar button at x=1293 which the model can never reach).
        def x_of(e):
            p = e.get("position") or [None]
            return p[0] if isinstance(p[0], (int, float)) else 10 ** 9
        in_region = [e for e in matches if x_of(e) < 960]
        return (in_region or matches)[0]

    resolved = {}        # label -> (uia_name, element)
    need_agent = []      # labels the agent must resolve
    # AGENT_ALWAYS_ASK routes every target through the agent (even exact matches)
    # so the human-in-the-loop resolution is exercised for demonstration/audit.
    always_ask = bool(os.getenv("AGENT_ALWAYS_ASK"))
    # AGENT_NEVER_ASK: auto-resolve exact/learned matches only, never block to
    # ask the agent. Essential for transient-menu tasks (e.g. W04) where the act
    # of servicing a resolution request steals focus and dismisses the open
    # context menu before the model can click it.
    never_ask = bool(os.getenv("AGENT_NEVER_ASK"))

    for lbl in labels:
        el = None
        src = None
        if learned.get(lbl):
            el = find_exact(learned[lbl])
            src = learned[lbl] if el is not None else None
        if el is None:
            el = find_exact(lbl)       # label already matches a live UIA name
            src = lbl if el is not None else None
        if el is not None and not always_ask:
            resolved[lbl] = (src, el)
        else:
            # bother the agent only if something plausibly related is on screen
            lt = _tokens(lbl)
            cands = [e for e in named
                     if _tokens(e.get("name")) & lt and _clickable(e)]
            if cands and not never_ask:
                need_agent.append(lbl)
            elif el is not None:
                resolved[lbl] = (src, el)

    if need_agent:
        _seq += 1
        seq = _seq
        os.makedirs(RES_DIR, exist_ok=True)
        request = {
            "seq": seq,
            "task": task,
            "instruction": ("For each label in unresolved_labels, choose the single "
                            "best-matching UIA element NAME from uia_elements (or null if "
                            "none fits). Return {\"seq\":<seq>,\"mapping\":{label:name|null}}."),
            "unresolved_labels": need_agent,
            "already_resolved": {k: v[0] for k, v in resolved.items()},
            "uia_elements": [
                {"name": e.get("name"), "control_type": e.get("control_type"),
                 "x": (e.get("position") or [None, None])[0],
                 "y": (e.get("position") or [None, None])[1],
                 "text": e.get("text")}
                for e in named
            ],
        }
        req_path = os.path.join(RES_DIR, f"request_{seq}.json")
        resp_path = os.path.join(RES_DIR, f"response_{seq}.json")
        json.dump(request, open(req_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        _log(f"seq {seq}: asking agent to resolve {need_agent}")
        waited = 0.0
        while not os.path.isfile(resp_path) and waited < timeout:
            time.sleep(0.5)
            waited += 0.5
        if os.path.isfile(resp_path):
            try:
                resp = json.load(open(resp_path, encoding="utf-8"))
                for lbl, uianame in (resp.get("mapping") or {}).items():
                    if uianame:
                        el = find_exact(uianame)
                        if el is not None:
                            resolved[lbl] = (uianame, el)
                            learned[lbl] = uianame
                _save_map(task, learned)
                _log(f"seq {seq}: agent resolved "
                     f"{ {k: v[0] for k, v in resolved.items() if k in need_agent} }")
            except Exception as e:
                _log(f"seq {seq}: bad response: {e!r}")
        else:
            _log(f"seq {seq}: TIMEOUT after {timeout}s; proceeding with what resolved")

    # Build the resolved visicon: one entry per resolved label at real coords,
    # named as the label the model searches for.
    out = []
    for lbl, (uianame, el) in resolved.items():
        entry = dict(el)
        entry["name"] = lbl
        entry["text"] = lbl
        entry["_resolved_from"] = uianame
        out.append(entry)
    json.dump(out, open(output_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    _log(f"visicon rewritten: {len(out)} feature(s) "
         f"{[l for l in resolved]}  (labels needing agent this pass: {need_agent})")
    return {"resolved": {k: v[0] for k, v in resolved.items()},
            "unresolved": [l for l in labels if l not in resolved]}
