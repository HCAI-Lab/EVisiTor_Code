import ctypes
# Per-monitor DPI awareness BEFORE anything queries the screen: on a scaled
# 4K display, a non-aware process gets virtualized coordinates and every
# cursor move / UIA rectangle would land in the wrong physical place.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import socket
import json
from Functions import *
import threading
import os
import subprocess
import sys
import importlib

from knowledge_descipherer import VLLMClient

# Agent-in-the-loop UIA target resolution (enabled per-run via AGENT_RESOLVE=1).
try:
    import agent_resolver
except Exception as _agent_e:
    agent_resolver = None
    print(f"agent_resolver unavailable: {_agent_e}")

def auto_install(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        return __import__(module_name)
    except ImportError:
        print(f"Module '{module_name}' not found. Installing '{package_name}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            # The user specifically asked for "uv pip install", so let's try that if uv is available, 
            # but standard pip is more universal. Wait, the user said: automatically run "uv pip install ..."
            # I will use "uv pip install" as requested.
            subprocess.check_call(["uv", "pip", "install", package_name])
        except Exception as e:
            # Fallback to pip if uv fails or isn't installed
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            except Exception as e2:
                print(f"Failed to install {package_name}: {e2}")
                raise e2
        return __import__(module_name)

# Apply auto_install to dependencies that might be missing
# (socket, json, threading, os, subprocess, sys are stdlib)

from Functions import *

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

# Live tasks deliberately move the cursor to screen edges (windows are
# repositioned to the top-left search region, and UIA targets can sit at the
# very corner). pyautogui's corner fail-safe would abort those legitimate
# moves, so disable it here — the run's wall-clock timeout is the safety net.
pyautogui.FAILSAFE = False

LLM_CLIENT = VLLMClient()


def ask_llm(prompt, **kwargs):
    return LLM_CLIENT.ask(prompt, **kwargs)


def _safe_mouse_position():
    try:
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)
    except Exception:
        try:
            pos = win32api.GetCursorPos()
            return int(pos[0]), int(pos[1])
        except Exception:
            return None


def _set_cursor_pos_verified(x, y):
    target = (int(x), int(y))
    before = _safe_mouse_position()
    errors = []

    try:
        win32api.SetCursorPos(target)
    except Exception as e:
        errors.append(f"win32api.SetCursorPos failed: {e}")

    after = _safe_mouse_position()
    if after != target:
        try:
            pyautogui.moveTo(target[0], target[1], duration=0)
        except Exception as e:
            errors.append(f"pyautogui.moveTo failed: {e}")
        try:
            win32api.SetCursorPos(target)
        except Exception as e:
            errors.append(f"retry SetCursorPos failed: {e}")
        after = _safe_mouse_position()

    return {
        "target": [target[0], target[1]],
        "before": [before[0], before[1]] if before else None,
        "after": [after[0], after[1]] if after else None,
        "moved": after == target,
        "errors": errors,
    }


def _set_eye_pos_verified(x, y):
    target = (int(x), int(y))
    errors = []
    moved = False

    try:
        eye_tracker.naturaleyemove(target)
        moved = True
    except Exception as e:
        errors.append(f"eye_tracker.naturaleyemove failed: {e}")

    return {
        "target": [target[0], target[1]],
        "moved": moved,
        "errors": errors,
    }


def _click_verified():
    before = _safe_mouse_position()
    errors = []

    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    except Exception as e:
        errors.append(f"win32api.mouse_event failed: {e}")
        try:
            pyautogui.click()
        except Exception as e2:
            errors.append(f"pyautogui.click failed: {e2}")

    after = _safe_mouse_position()
    return {
        "position": [after[0], after[1]] if after else ([before[0], before[1]] if before else None),
        "errors": errors,
    }


def _button_event_verified(down_flag, up_flag=None, fallback=None):
    """Send raw mouse button events at the current cursor position, with a
    pyautogui fallback, mirroring _click_verified's return shape."""
    before = _safe_mouse_position()
    errors = []

    try:
        win32api.mouse_event(down_flag, 0, 0, 0, 0)
        if up_flag is not None:
            win32api.mouse_event(up_flag, 0, 0, 0, 0)
    except Exception as e:
        errors.append(f"win32api.mouse_event failed: {e}")
        if fallback is not None:
            try:
                fallback()
            except Exception as e2:
                errors.append(f"pyautogui fallback failed: {e2}")

    after = _safe_mouse_position()
    return {
        "position": [after[0], after[1]] if after else ([before[0], before[1]] if before else None),
        "errors": errors,
    }


def _scroll_one_notch(direction):
    """One wheel notch (the model sends one call per notch)."""
    amount = -120 if direction == 'down' else 120
    errors = []
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, amount, 0)
    except Exception as e:
        errors.append(f"win32api.mouse_event failed: {e}")
        try:
            pyautogui.scroll(amount)
        except Exception as e2:
            errors.append(f"pyautogui.scroll failed: {e2}")
    return errors


def _default_spreadsheet_dir():
    """Directory holding visual_v3.py. Search known locations rather than
    assuming one fixed relative path — the repo was relocated (Spreadsheet/
    is now at the repo root, two levels up from EVisiTor2026/VisiTor/), so the
    old EVisiTor2026/Spreadsheet guess no longer resolves."""
    here = os.path.dirname(__file__)
    candidates = [
        os.path.abspath(os.path.join(here, "..", "..", "Spreadsheet")),  # repo-root/Spreadsheet
        os.path.abspath(os.path.join(here, "..", "Spreadsheet")),         # legacy layout
    ]
    for cand in candidates:
        if os.path.isfile(os.path.join(cand, "visual_v3.py")):
            return cand
    return candidates[0]


def _default_visual_script_path():
    return os.path.join(_default_spreadsheet_dir(), "visual_v3.py")


def _import_visual_module(module_name="visual_v3"):
    spreadsheet_dir = _default_spreadsheet_dir()
    if spreadsheet_dir not in sys.path:
        sys.path.insert(0, spreadsheet_dir)
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


def _as_name_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def _first_name(value):
    items = _as_name_list(value)
    return items[0] if items else None


def _use_uia(kwargs):
    value = kwargs.get('use_uia') if kwargs else None
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _default_visicon_json_path():
    return os.path.join(_default_spreadsheet_dir(), "visicons.json")


def _visicon_json_path(kwargs):
    path = kwargs.get('visicon_json') if kwargs else None
    if not path:
        path = _default_visicon_json_path()
    return os.path.abspath(path)


def _load_visicons(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


_INTERACTIVE_CONTROL_TYPES = {
    'Button', 'SplitButton', 'ComboBox', 'CheckBox', 'RadioButton',
    'ListItem', 'TreeItem', 'TabItem', 'MenuItem', 'Hyperlink', 'Edit',
    'Slider', 'ToggleSwitch',
}


def _find_visicon_by_name(visicons, target_name):
    target = str(target_name).strip().casefold()
    matches = [item for item in visicons
               if str(item.get('name', '')).strip().casefold() == target]
    if not matches:
        return None
    # A duplicated name is usually a text label plus its interactive control
    # (e.g. the Settings 'Display resolution' row label and its ComboBox).
    # Click the control, as a user would — clicking the label does nothing.
    for item in matches:
        if item.get('control_type') in _INTERACTIVE_CONTROL_TYPES:
            return item
    return matches[0]

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    with conn:
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode('utf-8')

            while '\n' in buffer:
                raw_message, buffer = buffer.split('\n', 1)
                raw_message = raw_message.strip()

                if not raw_message:
                    continue

                try:
                    command = json.loads(raw_message)
                    result = execute_command(command)
                    conn.sendall((json.dumps(result) + "\n").encode('utf-8'))
                    if result.get("quit"):
                        print("Quitting server...")
                        os._exit(0)
                except json.JSONDecodeError:
                    conn.sendall((json.dumps({"error": "Invalid JSON"}) + "\n").encode('utf-8'))
                except Exception as e:
                    conn.sendall((json.dumps({"error": str(e)}) + "\n").encode('utf-8'))

def _menu_settle_after_click():
    """Win11 context menus render a few hundred ms after the click, but the
    model requests its visicon refresh immediately -- so without a settle the
    scan can run before the menu exists and the popup capture finds nothing
    (the same race AGENT_KEY_SETTLE_MS already covers for enter/chords).
    Gated by AGENT_RESOLVE so the Excel path is unchanged. Waits a minimum
    beat (a menu-to-submenu click closes one popup before opening the next),
    then polls until a menu is visible or the budget runs out."""
    if not (os.getenv("AGENT_RESOLVE") and agent_resolver is not None):
        return
    total = float(os.getenv("AGENT_CLICK_SETTLE_MS", "1800")) / 1000.0
    sleep(min(0.6, total))
    waited = 0.6
    try:
        while waited < total and not agent_resolver.menu_is_open():
            sleep(0.15)
            waited += 0.15
        if agent_resolver.menu_is_open():
            sleep(0.4)  # let the menu items finish populating
    except Exception:
        pass


def execute_command(command):
    raw_function = command.get('function', '')
    function = raw_function.lower() if isinstance(raw_function, str) else ''
    args = command.get('args', [])
    kwargs = command.get('kwargs', {})

    if args is None:
        args = []

    if function == 'click':
        click_info = _click_verified()
        _menu_settle_after_click()
        return {"result": "Click executed", "details": click_info}
    elif function == 'rightclick':
        click_info = _button_event_verified(win32con.MOUSEEVENTF_RIGHTDOWN,
                                            win32con.MOUSEEVENTF_RIGHTUP,
                                            fallback=pyautogui.rightClick)
        _menu_settle_after_click()
        return {"result": "Right click executed", "details": click_info}
    elif function == 'mousedown':
        click_info = _button_event_verified(win32con.MOUSEEVENTF_LEFTDOWN,
                                            fallback=pyautogui.mouseDown)
        return {"result": "Left button down", "details": click_info}
    elif function == 'mouseup':
        click_info = _button_event_verified(win32con.MOUSEEVENTF_LEFTUP,
                                            fallback=pyautogui.mouseUp)
        return {"result": "Left button up", "details": click_info}
    elif function == 'scroll':
        direction = str(args[0]).lower() if args else 'down'
        if direction not in ('up', 'down'):
            direction = 'down'
        errors = _scroll_one_notch(direction)
        if errors:
            return {"result": f"Scrolled {direction} one notch", "details": {"errors": errors}}
        return {"result": f"Scrolled {direction} one notch"}
    elif function == 'keypress':
        key = str(args[0]) if args else ''
        if '+' in key and len(key) > 1:
            # Modifier chord, e.g. "win+r", "ctrl+shift+n", "shift+f10".
            parts = [p.strip().lower() for p in key.split('+') if p.strip()]
            aliases = {'win': 'winleft', 'esc': 'escape', 'del': 'delete'}
            pyautogui.hotkey(*[aliases.get(p, p) for p in parts])
        elif len(key) == 1 and key.isalpha() and key.isupper():
            # Shift-typed letter: keyDown('P') would type lowercase.
            pyautogui.hotkey('shift', key.lower())
        else:
            # Legacy single-key path (Excel study compatibility).
            aliases = {'win': 'winleft'}
            keypress(aliases.get(key.lower(), key), *args[1:], **kwargs)
        # Live runs: let the real UI catch up after a key that opens a dialog or
        # launches an app (a chord like win+r/win+i, or Enter in Run/search) so
        # the model's next scan sees the result. Gated -> Excel path unchanged.
        if os.getenv("AGENT_RESOLVE"):
            _k = key.strip().lower()
            if ('+' in _k and len(_k) > 1) or _k in ('enter', 'return'):
                sleep(float(os.getenv("AGENT_KEY_SETTLE_MS", "1400")) / 1000.0)
        return {"result": "Keypress executed"}
    elif function == 'longkeypress':
        longkeypress(*args)
        return {"result": "Long keypress started"}
    elif function == 'continuouspresskey':
        key = kwargs.get('key') if kwargs else None
        if key is None:
            key = args[0] if args else None
        if not key:
            return {"error": "continuouspresskey requires a key"}
        longkeypress(key)
        return {"result": f"Continuous key press started for '{key}'"}
    elif function in {'askllm', 'queryllm', 'llm', 'chat'}:
        prompt = kwargs.get('prompt') if kwargs else None
        if prompt is None and args:
            prompt = args[0]
        if prompt is None:
            return {"error": "askllm requires a prompt"}

        llm_kwargs = dict(kwargs) if isinstance(kwargs, dict) else {}
        llm_kwargs.pop('prompt', None)

        # Allow per-request endpoint/model override without restarting TCP_VisiTor.
        url_override = llm_kwargs.pop('url', None)
        model_override = llm_kwargs.pop('model', None)
        timeout_override = llm_kwargs.get('timeout')

        client = LLM_CLIENT
        if url_override or model_override or timeout_override:
            client = VLLMClient(
                url=url_override or LLM_CLIENT.url,
                model=model_override or LLM_CLIENT.model,
                timeout_seconds=timeout_override or LLM_CLIENT.timeout_seconds,
            )

        return client.ask(prompt, **llm_kwargs)
    elif function == 'whereis':
        # Supports both whereis(path) and Shell style whereis(dir, filename)
        directory = kwargs.get('Dir') if kwargs else None
        if directory is None and kwargs:
            directory = kwargs.get('dir')

        pattern_name = kwargs.get('pattern') if kwargs else None
        if pattern_name is None and kwargs:
            pattern_name = kwargs.get('arg2')

        if directory and pattern_name:
            if isinstance(pattern_name, list):
                pattern_name = pattern_name[0] if pattern_name else None
            path = find_file(directory, str(pattern_name))
            result = whereis(path)
        elif len(args) >= 2:
            path = find_file(args[0], args[1])
            result = whereis(path)
        else:
            result = whereis(*args)
        return {"result": result}
    elif function == 'find_file':
        result = find_file(*args)
        return {"result": result}
    elif function == 'addressfinder':
        result = addressfinder()
        return {"result": result}
    elif function == 'naturalmove':
        naturalmove(*args, **kwargs)
        return {"result": "Cursor moved"}
    elif function == 'movecursorto':
        x = kwargs.get('x') if kwargs else None
        y = kwargs.get('y') if kwargs else None
        if x is None or y is None:
            if len(args) >= 2:
                x, y = args[0], args[1]
            elif len(args) == 1 and isinstance(args[0], (list, tuple)) and len(args[0]) == 2:
                x, y = args[0][0], args[0][1]
            else:
                return {"error": "movecursorto requires x and y coordinates"}
        move_info = _set_cursor_pos_verified(x, y)
        target = move_info["target"]
        if move_info["moved"]:
            return {"result": f"Cursor moved to {target[0]}, {target[1]}", "details": move_info}
        return {
            "error": f"Cursor did not reach target {target[0]}, {target[1]}",
            "details": move_info,
        }
    elif function == 'moveeyeto':
        x = kwargs.get('x') if kwargs else None
        y = kwargs.get('y') if kwargs else None
        if x is None or y is None:
            if len(args) >= 2:
                x, y = args[0], args[1]
            elif len(args) == 1 and isinstance(args[0], (list, tuple)) and len(args[0]) == 2:
                x, y = args[0][0], args[0][1]
            else:
                return {"error": "moveeyeto requires x and y coordinates"}

        # While a context menu is open, do NOT physically move the gaze-
        # visualization window: it is topmost, and dragging it around (e.g. the
        # model glancing at its off-screen instruction panel between subtasks)
        # disturbs the transient Win11 menu the model is about to click. The eye
        # move is pure visualization, so suppressing it doesn't affect cognition.
        if os.getenv("AGENT_RESOLVE") and agent_resolver is not None:
            try:
                if agent_resolver.menu_is_open():
                    return {"result": f"Eye move suppressed (menu open) {int(x)}, {int(y)}"}
            except Exception:
                pass
        move_info = _set_eye_pos_verified(x, y)
        target = move_info["target"]
        if move_info["moved"]:
            return {"result": f"Eye moved to {target[0]}, {target[1]}", "details": move_info}
        return {
            "error": f"Eye did not reach target {target[0]}, {target[1]}",
            "details": move_info,
        }
    elif function == 'movecursortopattern':
        use_uia = _use_uia(kwargs)

        directory = kwargs.get('Dir') if kwargs else None
        if directory is None and kwargs:
            directory = kwargs.get('dir')
        if directory is None:
            directory = args[1] if len(args) >= 2 else None
        if directory is None:
            directory = addressfinder()

        pattern_name = kwargs.get('pattern') if kwargs else None
        if pattern_name is None and kwargs:
            pattern_name = kwargs.get('arg2')
        if pattern_name is None:
            pattern_name = args[0] if args else None

        pattern_name = _first_name(pattern_name)
        if not pattern_name:
            return {"error": "movecursortopattern requires a pattern name"}

        if use_uia:
            visicon_path = _visicon_json_path(kwargs)
            if not os.path.isfile(visicon_path):
                return {"error": f"UIA visicon JSON not found: {visicon_path}"}

            try:
                visicons = _load_visicons(visicon_path)
            except Exception as e:
                return {"error": f"Failed reading UIA visicon JSON: {e}"}

            target = _find_visicon_by_name(visicons, pattern_name)
            if not target:
                return {"error": f"UIA item '{pattern_name}' not found in {visicon_path}"}

            position = target.get('position')
            if not isinstance(position, (list, tuple)) or len(position) != 2:
                return {"error": f"UIA item '{pattern_name}' has invalid position: {position}"}

            x, y = int(position[0]), int(position[1])
            naturalmove((x, y))
            return {"result": f"Cursor moved to UIA item '{pattern_name}' at ({x}, {y})"}

        path = find_file(directory, str(pattern_name).lower())
        coor_choice = whereis(path)
        if isinstance(coor_choice, tuple):
            naturalmove((int(coor_choice[0]), int(coor_choice[1])))
            return {"result": f"Cursor moved to pattern '{pattern_name}' at {coor_choice}"}
        return {"error": str(coor_choice)}
    elif function == 'whatisonscreen':
        use_uia = _use_uia(kwargs)

        directory = kwargs.get('Dir') if kwargs else None
        if directory is None and kwargs:
            directory = kwargs.get('dir')
        if directory is None:
            directory = args[0] if args else None
        if not directory:
            return {"error": "whatisonscreen requires a directory"}

        modules = kwargs.get('modules') if kwargs else None
        if modules is None and kwargs:
            modules = kwargs.get('arg2')
        if modules is None:
            modules = args[1:] if len(args) > 1 else []
        modules = _as_name_list(modules)
        if not modules:
            return {"error": "whatisonscreen requires one or more module names"}

        if use_uia:
            visicon_path = _visicon_json_path(kwargs)
            if not os.path.isfile(visicon_path):
                return {"error": f"UIA visicon JSON not found: {visicon_path}"}

            try:
                visicons = _load_visicons(visicon_path)
            except Exception as e:
                return {"error": f"Failed reading UIA visicon JSON: {e}"}

            found_modules = []
            for module in modules:
                if _find_visicon_by_name(visicons, module):
                    found_modules.append(module)

            if not found_modules:
                return {"result": [], "message": "crap"}
            return {"result": found_modules}

        found_modules = []
        for module in modules:
            path = find_file(directory, module)
            coor_choice = whereis(path)
            if isinstance(coor_choice, tuple):
                found_modules.append(module)

        if not found_modules:
            return {"result": [], "message": "crap"}
        return {"result": found_modules}
    elif function == 'refreshvisicons':
        try:
            visual_v3 = _import_visual_module("visual_v3")
        except Exception as e:
            return {"error": f"Failed to import visual_v3 module: {e}"}

        app_titles = kwargs.get('app_titles') if kwargs else None
        if isinstance(app_titles, str):
            app_titles = [app_titles]

        output_path = kwargs.get('output_path') if kwargs else None

        try:
            if hasattr(visual_v3, "refresh_visicons"):
                _agent_on = agent_resolver is not None and os.getenv("AGENT_RESOLVE")
                if _agent_on:
                    # The generic model sends no app_titles, so scan the live
                    # target app + taskbar instead of DEFAULT_APP_TITLES (which
                    # are the Excel-study windows). AGENT_TARGET_TITLE pins the
                    # scan+reposition to a specific window by title so it works
                    # regardless of which window holds the foreground -- on this
                    # machine permission dialogs keep pulling focus back to the
                    # IDE, which would otherwise make the model scan/click that.
                    _target_title = os.getenv("AGENT_TARGET_TITLE")
                    # Don't move any window while a context menu is open -- that
                    # dismisses the menu before we can capture its items.
                    _menu_open = agent_resolver.menu_is_open()
                    if _target_title:
                        # Float the target window into the search region, then
                        # pin the scan to its CURRENT full title (it changes as
                        # the app navigates, e.g. Explorer 'Documents' ->
                        # 'report.docx - Search Results in Documents').
                        if not _menu_open:
                            agent_resolver.reposition_title_left(_target_title)
                        if not app_titles:
                            _full = agent_resolver.current_target_title(_target_title)
                            app_titles = [_full or _target_title, "__taskbar__"]
                    else:
                        if not app_titles:
                            app_titles = ["__foreground__", "__taskbar__"]
                        if not _menu_open:
                            agent_resolver.reposition_foreground_left()
                            # 2026-07-16: fresh Explorer windows restore the
                            # nav pane scrolled down, leaving quick-access
                            # rows (e.g. 'Start of Quick Access - Desktop')
                            # virtualized with rect [0,0,0,0] -- unclickable
                            # and unresolvable. Scrolling the pane to top
                            # BEFORE the scan (deterministic, no race) makes
                            # them realized. Gated so other tasks/Excel are
                            # unaffected.
                            if os.getenv("AGENT_NAV_SCROLL_TOP"):
                                try:
                                    agent_resolver.scroll_nav_pane_top()
                                except Exception:
                                    pass
                    sleep(float(os.getenv("AGENT_SCAN_SETTLE_MS", "900")) / 1000.0)
                refresh_result = visual_v3.refresh_visicons(app_titles=app_titles, output_path=output_path)
                if _agent_on and output_path:
                    try:
                        # Capture any open context-menu popups (visual_v3 can't
                        # traverse the XAML menu islands) before resolving.
                        agent_resolver.append_popup_menu_features(output_path)
                    except Exception as _e:
                        print(f"append_popup_menu_features failed: {_e}")
                    try:
                        agent_resolver.apply(output_path, os.getenv("AGENT_TASK"))
                    except Exception as _e:
                        print(f"agent_resolver.apply failed: {_e}")
                return {"result": "visicons refreshed", "details": refresh_result}

            if app_titles is None and hasattr(visual_v3, "DEFAULT_APP_TITLES"):
                app_titles = visual_v3.DEFAULT_APP_TITLES

            if app_titles is None:
                return {"error": "visual_v3 has no refresh_visicons and no default app titles available"}

            extract_result = visual_v3.extract_ui_elements(app_titles)
            visicons = extract_result[0] if isinstance(extract_result, tuple) else extract_result
            return {
                "result": "visicons refreshed",
                "details": {"visicons_count": len(visicons)},
            }
        except Exception as e:
            return {"error": f"visual_v3 refresh failed: {e}"}
    elif function == 'getmouselocation':
        pos = pyautogui.position()
        return {"result": f"Mouse position: {pos.x}, {pos.y}"}
    elif function == 'quit':
        return {"result": "Quitting server", "quit": True}
    else:
        return {"error": f"Unknown function: {raw_function}"}

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            # Tk-based eye overlay operations must run on the main thread.
            # Handling requests synchronously here avoids calling EyeTracker from worker threads.
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()
