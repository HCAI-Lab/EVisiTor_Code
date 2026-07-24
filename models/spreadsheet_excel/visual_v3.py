from pywinauto import Application
import numpy as np
from PIL import ImageGrab
import json
import time
import webcolors
from pywinauto.findwindows import find_elements
import win32gui
import win32process
import os
import re
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
VISICONS_OUTPUT_PATH = SCRIPT_DIR / "visicons.json"
VISICONS_SNAPSHOT_DIR = SCRIPT_DIR / "visicons"
DEFAULT_APP_TITLES = [
    "subject.xlsx - Excel",
    "normalization.xlsx - Excel",
    "normalization-excel-tasks-v2_AAAI2023.xlsx - Excel"
]

# Special scan-target tokens for generic (non-Excel) live runs. Instead of a
# literal window title, an app_titles entry may name a dynamic target:
#   __foreground__  the current foreground window (whatever the task opened)
#   __taskbar__     the Windows taskbar (Shell_TrayWnd), e.g. W9's Search box
FOREGROUND_TOKEN = "__foreground__"
TASKBAR_TOKEN = "__taskbar__"

# The visual-search region spans the primary screen; the virtual instruction
# panel sits just beyond its right edge (generic_live.lisp places the markers
# at screen-width + offsets). Repositioning below only pulls windows back
# when they extend past the primary monitor.
try:
    import win32api
    SEARCH_REGION_X_BOUNDARY = win32api.GetSystemMetrics(0)
    SEARCH_REGION_HEIGHT = win32api.GetSystemMetrics(1) - 60
except Exception:
    SEARCH_REGION_X_BOUNDARY = 1920
    SEARCH_REGION_HEIGHT = 1020

CONTAINER_TYPES = {"Pane", "Group", "Custom", "Window"}
ROW_LIKE_TYPES = {"DataItem", "ListItem", "MenuItem", "Button", "TabItem", "HeaderItem", "Text"}

def get_cursor_position():
    return win32gui.GetCursorPos()

def _normalize_color_name(name):
    return name.replace("-", "").replace("_", "").replace(" ", "").lower()

def _css3_names():
    try:
        return list(webcolors.names(spec="css3"))
    except Exception:
        pass
    try:
        return list(webcolors.CSS3_NAMES_TO_HEX.keys())
    except Exception:
        return []

def _name_to_rgb(name):
    try:
        return webcolors.name_to_rgb(name, spec="css3")
    except TypeError:
        return webcolors.name_to_rgb(name)

def closest_color(requested_color, available_colors):
    available_lookup = {_normalize_color_name(c): c for c in available_colors}
    min_distance = None
    best_name = None

    for css_name in _css3_names():
        normalized = _normalize_color_name(css_name)
        if normalized not in available_lookup:
            continue

        r_c, g_c, b_c = _name_to_rgb(css_name)
        distance = (
            (r_c - requested_color[0]) ** 2 +
            (g_c - requested_color[1]) ** 2 +
            (b_c - requested_color[2]) ** 2
        )

        if min_distance is None or distance < min_distance:
            min_distance = distance
            best_name = available_lookup[normalized]

    return best_name or "gray"

def get_average_color(rect):
    img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
    np_img = np.array(img)
    return np_img.mean(axis=(0, 1), dtype=int)

WS_CAPTION = 0x00C00000
GW_HWNDNEXT = 2


def _own_process_window(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid == os.getpid()
    except Exception:
        return False


def _foreground_handle():
    """Foreground window handle, skipping this process's own windows (the
    eye-tracker overlay) and untitled/invisible handles."""
    hwnd = win32gui.GetForegroundWindow()
    tries = 0
    while hwnd and tries < 10 and (
        _own_process_window(hwnd)
        or not win32gui.IsWindowVisible(hwnd)
        or not win32gui.GetWindowText(hwnd)
    ):
        hwnd = win32gui.GetWindow(hwnd, GW_HWNDNEXT)
        tries += 1
    return hwnd or None


def _maybe_move_into_search_region(hwnd, boundary=SEARCH_REGION_X_BOUNDARY):
    """Move a window the model opened into the visual-search region (left of
    the instruction-panel boundary), mirroring how the Excel study positioned
    the target application. Caption-less popups (menus, Start search flyout)
    are left where they are."""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        if right <= boundary:
            return
        style = win32gui.GetWindowLong(hwnd, -16)  # GWL_STYLE
        if not (style & WS_CAPTION):
            return
        width = min(right - left, boundary - 10)
        height = min(bottom - top, SEARCH_REGION_HEIGHT)
        win32gui.MoveWindow(hwnd, 0, 0, width, height, True)
        time.sleep(0.3)
    except Exception as e:
        print(f"Window reposition skipped: {e}")


def _resolve_scan_handles(app_titles, reposition=True):
    """Turn app_titles entries (literal titles or __foreground__/__taskbar__
    tokens) into a deduplicated list of top-level window handles."""
    handles = []
    for app_title in app_titles:
        if app_title == FOREGROUND_TOKEN:
            hwnd = _foreground_handle()
            if hwnd:
                if reposition:
                    _maybe_move_into_search_region(hwnd)
                handles.append(hwnd)
        elif app_title == TASKBAR_TOKEN:
            hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
            if hwnd:
                handles.append(hwnd)
        else:
            elements = find_elements(title_re=re.escape(app_title), backend="uia")
            elements = _select_target_elements(elements)
            handles.extend(el.handle for el in elements)

    seen = set()
    ordered = []
    for handle in handles:
        if handle not in seen:
            seen.add(handle)
            ordered.append(handle)
    return ordered


def _select_target_elements(elements):
    if not elements:
        return []

    try:
        foreground = win32gui.GetForegroundWindow()
    except Exception:
        foreground = None

    if foreground is not None:
        foreground_matches = [el for el in elements if getattr(el, "handle", None) == foreground]
        if foreground_matches:
            return foreground_matches

    return [elements[0]]

TASKBAR_STATE_SUFFIXES = re.compile(
    r"(\s+-\s+\d+\s+running\s+windows?)?(\s+pinned)?$", re.IGNORECASE)

# State suffix Windows appends to pinned items anywhere (e.g. the File
# Explorer nav-pane TreeItem 'Documents (pinned)').
PINNED_SUFFIX = re.compile(r"\s*\(pinned\)$", re.IGNORECASE)


def _clean_taskbar_label(text):
    """Strip state suffixes from taskbar-button UIA names so task chunks can
    target the app name itself: 'File Explorer - 2 running windows pinned'
    -> 'File Explorer'."""
    return TASKBAR_STATE_SUFFIXES.sub("", text).strip()


def _clean_state_suffixes(text):
    """Strip generic state suffixes: 'Documents (pinned)' -> 'Documents'."""
    return PINNED_SUFFIX.sub("", text).strip()


def _safe_text(child):
    try:
        text = child.window_text()
        return text.strip() if text else ""
    except Exception:
        return ""

def _safe_control_type(child):
    try:
        return child.element_info.control_type
    except Exception:
        return None

def _safe_parent_text(child):
    try:
        parent = child.parent()
        return parent.window_text().strip() if parent and parent.window_text() else ""
    except Exception:
        return ""

def _safe_children_count(child):
    try:
        return len(child.children())
    except Exception:
        return 0

def _looks_like_cell_address(text):
    return bool(re.fullmatch(r"[A-Z]+[1-9]\d*", text))

def _looks_like_row_label(text):
    return bool(re.fullmatch(r"[1-9]\d*", text))

def _looks_like_column_label(text):
    return bool(re.fullmatch(r"[A-Z]+", text))

def _excel_col_to_number(label):
    number = 0
    for char in label:
        number = number * 26 + (ord(char) - ord("A") + 1)
    return number

def _has_aligned_neighbor(visicon, candidates, value_fn, axis):
    x, y = visicon["position"]
    width = visicon["width"]
    height = visicon["height"]
    value = value_fn(visicon)

    align_tol = max(8, int((width if axis == "vertical" else height) * 0.6))
    step_tol = max(10, int((height if axis == "vertical" else width) * 1.5))

    for other in candidates:
        if other is visicon:
            continue

        ox, oy = other["position"]
        other_value = value_fn(other)
        if abs(other_value - value) != 1:
            continue

        if axis == "vertical":
            if abs(ox - x) <= align_tol and abs(oy - y) <= step_tol:
                return True
        else:
            if abs(oy - y) <= align_tol and abs(ox - x) <= step_tol:
                return True

    return False

def _assign_header_cell_types(visicons):
    data_items = [v for v in visicons if v.get("control_type") == "DataItem"]
    if not data_items:
        return

    xs = [v["position"][0] for v in data_items]
    ys = [v["position"][1] for v in data_items]
    widths = [v["width"] for v in data_items]
    heights = [v["height"] for v in data_items]

    min_x = min(xs)
    min_y = min(ys)
    median_width = int(np.median(widths)) if widths else 0
    median_height = int(np.median(heights)) if heights else 0

    row_candidates = []
    column_candidates = []
    for visicon in data_items:
        text = visicon.get("text", "")
        if _looks_like_row_label(text):
            row_candidates.append(visicon)
        elif _looks_like_column_label(text):
            column_candidates.append(visicon)

    # Header strips are expected at the extreme left/top among same-type candidates.
    # This prevents numeric values inside normal data cells from being labeled as row headers.
    row_strip_x = min((v["position"][0] for v in row_candidates), default=min_x)
    col_strip_y = min((v["position"][1] for v in column_candidates), default=min_y)
    row_strip_tol = max(8, int(median_width * 0.45))
    col_strip_tol = max(8, int(median_height * 0.45))

    for visicon in row_candidates:
        x, _ = visicon["position"]
        if abs(x - row_strip_x) > row_strip_tol:
            continue

        if _has_aligned_neighbor(
            visicon,
            row_candidates,
            value_fn=lambda v: int(v["text"]),
            axis="vertical",
        ):
            visicon["cell-type"] = "row"

    for visicon in column_candidates:
        _, y = visicon["position"]
        if abs(y - col_strip_y) > col_strip_tol:
            continue

        if _has_aligned_neighbor(
            visicon,
            column_candidates,
            value_fn=lambda v: _excel_col_to_number(v["text"]),
            axis="horizontal",
        ):
            visicon["cell-type"] = "column"

def _should_skip_element(child, text, control_type, rect):
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    if not text:
        return True

    # Drop broad containers
    if control_type in CONTAINER_TYPES:
        return True

    # Drop extremely large text regions; these are usually section/pane labels
    if control_type == "Text" and height > 80:
        return True

    # Drop non-leaf text elements that usually act like wrappers/headers
    if control_type == "Text" and _safe_children_count(child) > 0:
        return True

    # Drop absurdly huge nodes
    if width * height > 250000:
        return True

    return False

def _map_item_type(control_type):
    if control_type == "DataItem":
        return "cell"
    if control_type == "MenuItem":
        return "menu"
    if control_type == "TabItem":
        return "ribbon"
    if control_type == "Button":
        return "button"
    if control_type == "ListItem":
        return "listitem"
    return "text"

def _next_snapshot_identifier(snapshot_dir):
    snapshot_dir = Path(snapshot_dir)
    max_index = 0

    if snapshot_dir.exists():
        for path in snapshot_dir.glob("visicons_*.json"):
            suffix = path.stem.removeprefix("visicons_")
            if suffix.isdigit():
                max_index = max(max_index, int(suffix))

    return f"{max_index + 1:03d}"

def _snapshot_dir_for_output(output_path):
    output_path = Path(output_path)
    if output_path.parent == SCRIPT_DIR:
        return VISICONS_SNAPSHOT_DIR
    return output_path.parent / "visicons"

def _write_visicon_outputs(visicons, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(visicons, file, indent=2)

    snapshot_dir = _snapshot_dir_for_output(output_path)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = _next_snapshot_identifier(snapshot_dir)
    snapshot_path = snapshot_dir / f"visicons_{snapshot_id}.json"

    with open(snapshot_path, "w", encoding="utf-8") as file:
        json.dump(visicons, file, indent=2)

    return snapshot_path

def extract_ui_elements(app_titles, output_path=VISICONS_OUTPUT_PATH, settle_ms=0, reposition=True):
    if settle_ms:
        # Give the UI time to settle after the action that triggered this
        # refresh (dialogs opening, menus animating in, windows launching).
        time.sleep(settle_ms / 1000.0)

    visicons = []
    seen = set()
    cursor_x, cursor_y = get_cursor_position()

    for handle in _resolve_scan_handles(app_titles, reposition=reposition):
        try:
            is_taskbar = win32gui.GetClassName(handle) == "Shell_TrayWnd"
            app = Application(backend="uia").connect(handle=handle)
            window = app.window(handle=handle)
            children = window.descendants()
        except Exception as e:
            print(f"Error connecting to window {handle}: {e}")
            continue

        actr_colors = [
            "black", "green", "dark-gray", "cyan", "light-blue", "yellow",
            "dark-yellow", "light-gray", "dark-blue", "dark-magenta", "white",
            "dark-cyan", "blue", "purple", "gray", "dark-green", "dark-red",
            "red", "brown", "pink", "magenta"
        ]

        for child in children:
            try:
                if not child.is_visible():
                    continue

                text = _safe_text(child)
                if is_taskbar:
                    text = _clean_taskbar_label(text)
                text = _clean_state_suffixes(text)
                control_type = _safe_control_type(child)
                rect = child.rectangle()

                if _should_skip_element(child, text, control_type, rect):
                    continue

                width = rect.right - rect.left
                height = rect.bottom - rect.top

                avg_color = get_average_color(rect)
                closest_color_name = closest_color(avg_color, actr_colors)
                highlighted = rect.left <= cursor_x <= rect.right and rect.top <= cursor_y <= rect.bottom

                item_type = _map_item_type(control_type)

                key = (text, control_type, rect.left, rect.top, rect.right, rect.bottom)
                if key in seen:
                    continue
                seen.add(key)

                visicon = {
                    "name": text,
                    "type": item_type,
                    "control_type": control_type,
                    "position": ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2),
                    "rect": [rect.left, rect.top, rect.right, rect.bottom],
                    "width": width,
                    "height": height,
                    "color": closest_color_name,
                    "text": text,
                    "highlighted": highlighted,
                    "parent_text": _safe_parent_text(child),
                    "children_count": _safe_children_count(child),
                }

                # Only mark as spreadsheet cell when it is actually a DataItem
                if control_type == "DataItem":
                    visicon["cell"] = True

                    if _looks_like_cell_address(text):
                        visicon["cell-address"] = text

                visicons.append(visicon)

            except Exception as e:
                print(f"Error processing element: {e}")

    _assign_header_cell_types(visicons)

    snapshot_path = _write_visicon_outputs(visicons, output_path)

    return visicons, snapshot_path

def refresh_visicons(app_titles=None, output_path=None, settle_ms=0, reposition=True):
    if app_titles is None:
        app_titles = DEFAULT_APP_TITLES
    if output_path is None:
        output_path = VISICONS_OUTPUT_PATH

    visicons, snapshot_path = extract_ui_elements(
        app_titles, output_path=output_path,
        settle_ms=settle_ms, reposition=reposition)
    return {
        "visicons_count": len(visicons),
        "output_path": str(Path(output_path)),
        "snapshot_path": str(snapshot_path),
    }

if __name__ == "__main__":
    refresh_visicons()
