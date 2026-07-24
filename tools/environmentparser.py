import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import comtypes
import comtypes.client
import win32gui
import win32process


# Generate/load UIAutomation COM wrappers
comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as UIA  # noqa: E402


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return default


def simplify_value(value: Any) -> Any:
    """Convert COM/ctypes values into JSON-safe values."""
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # SAFEARRAYs / COM arrays
    try:
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
            return [simplify_value(v) for v in value]
    except Exception:
        pass

    # RECT-like objects
    if all(hasattr(value, x) for x in ["left", "top", "right", "bottom"]):
        return {
            "left": int(value.left),
            "top": int(value.top),
            "right": int(value.right),
            "bottom": int(value.bottom),
        }

    try:
        return str(value)
    except Exception:
        return None


def get_prop(element: Any, prop_id: int) -> Any:
    try:
        return simplify_value(element.GetCurrentPropertyValue(prop_id))
    except Exception:
        return None


def get_rect(element: Any) -> Optional[Dict[str, int]]:
    try:
        r = element.CurrentBoundingRectangle
        return {
            "left": int(r.left),
            "top": int(r.top),
            "right": int(r.right),
            "bottom": int(r.bottom),
            "width": int(r.right - r.left),
            "height": int(r.bottom - r.top),
        }
    except Exception:
        return None


def rect_has_area(rect: Optional[Dict[str, int]]) -> bool:
    if not rect:
        return False
    return rect["width"] > 0 and rect["height"] > 0


def rect_intersects(a: Dict[str, int], b: Dict[str, int]) -> bool:
    return not (
        a["right"] <= b["left"]
        or a["left"] >= b["right"]
        or a["bottom"] <= b["top"]
        or a["top"] >= b["bottom"]
    )


def normalize_rect_to_window(
    rect: Optional[Dict[str, int]],
    window_rect: Dict[str, int],
) -> Optional[List[int]]:
    """
    Return [ymin, xmin, ymax, xmax] normalized 0-1000 relative to target window.
    This matches common visual-grounding coordinate format.
    """
    if not rect:
        return None

    ww = max(1, window_rect["right"] - window_rect["left"])
    wh = max(1, window_rect["bottom"] - window_rect["top"])

    ymin = round(((rect["top"] - window_rect["top"]) / wh) * 1000)
    xmin = round(((rect["left"] - window_rect["left"]) / ww) * 1000)
    ymax = round(((rect["bottom"] - window_rect["top"]) / wh) * 1000)
    xmax = round(((rect["right"] - window_rect["left"]) / ww) * 1000)

    return [ymin, xmin, ymax, xmax]


def get_runtime_id(element: Any) -> Optional[List[int]]:
    try:
        rid = element.GetRuntimeId()
        return [int(x) for x in rid]
    except Exception:
        return None


def const_value(name: str) -> Optional[int]:
    return safe_getattr(UIA, name, None)


def build_control_type_map() -> Dict[int, str]:
    names = [
        "Button",
        "Calendar",
        "CheckBox",
        "ComboBox",
        "Edit",
        "Hyperlink",
        "Image",
        "ListItem",
        "List",
        "Menu",
        "MenuBar",
        "MenuItem",
        "ProgressBar",
        "RadioButton",
        "ScrollBar",
        "Slider",
        "Spinner",
        "StatusBar",
        "Tab",
        "TabItem",
        "Text",
        "ToolBar",
        "ToolTip",
        "Tree",
        "TreeItem",
        "Custom",
        "Group",
        "Thumb",
        "DataGrid",
        "DataItem",
        "Document",
        "SplitButton",
        "Window",
        "Pane",
        "Header",
        "HeaderItem",
        "Table",
        "TitleBar",
        "Separator",
        "SemanticZoom",
        "AppBar",
    ]

    out = {}
    for name in names:
        cid = const_value(f"UIA_{name}ControlTypeId")
        if cid is not None:
            out[int(cid)] = name
    return out


CONTROL_TYPE_MAP = build_control_type_map()


def control_type_name(control_type_id: Optional[int]) -> Optional[str]:
    if control_type_id is None:
        return None
    return CONTROL_TYPE_MAP.get(int(control_type_id), f"Unknown({control_type_id})")


def build_pattern_map() -> Dict[int, str]:
    pattern_names = [
        "Invoke",
        "Selection",
        "Value",
        "RangeValue",
        "Scroll",
        "ExpandCollapse",
        "Grid",
        "GridItem",
        "MultipleView",
        "Window",
        "SelectionItem",
        "Dock",
        "Table",
        "TableItem",
        "Text",
        "Toggle",
        "Transform",
        "ScrollItem",
        "LegacyIAccessible",
        "ItemContainer",
        "VirtualizedItem",
        "SynchronizedInput",
        "ObjectModel",
        "Annotation",
        "TextPattern2",
        "Styles",
        "Spreadsheet",
        "SpreadsheetItem",
        "TransformPattern2",
        "TextChild",
        "Drag",
        "DropTarget",
        "TextEdit",
        "CustomNavigation",
        "SelectionPattern2",
    ]

    out = {}
    for name in pattern_names:
        pid = const_value(f"UIA_{name}PatternId")
        if pid is not None:
            out[int(pid)] = name
    return out


PATTERN_MAP = build_pattern_map()


def get_supported_patterns(element: Any) -> List[str]:
    supported = []
    for pid, name in PATTERN_MAP.items():
        try:
            element.GetCurrentPattern(pid)
            supported.append(name)
        except Exception:
            pass
    return supported


def get_pattern_data(element: Any) -> Dict[str, Any]:
    """
    Extract selected useful pattern data.
    This intentionally avoids invoking actions. It only reads current values.
    """
    data: Dict[str, Any] = {}

    # ValuePattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_ValuePatternId)
        vp = p.QueryInterface(UIA.IUIAutomationValuePattern)
        data["Value"] = {
            "value": simplify_value(vp.CurrentValue),
            "is_read_only": simplify_value(vp.CurrentIsReadOnly),
        }
    except Exception:
        pass

    # RangeValuePattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_RangeValuePatternId)
        rp = p.QueryInterface(UIA.IUIAutomationRangeValuePattern)
        data["RangeValue"] = {
            "value": simplify_value(rp.CurrentValue),
            "minimum": simplify_value(rp.CurrentMinimum),
            "maximum": simplify_value(rp.CurrentMaximum),
            "small_change": simplify_value(rp.CurrentSmallChange),
            "large_change": simplify_value(rp.CurrentLargeChange),
            "is_read_only": simplify_value(rp.CurrentIsReadOnly),
        }
    except Exception:
        pass

    # TogglePattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_TogglePatternId)
        tp = p.QueryInterface(UIA.IUIAutomationTogglePattern)
        data["Toggle"] = {
            "toggle_state": simplify_value(tp.CurrentToggleState),
        }
    except Exception:
        pass

    # SelectionItemPattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_SelectionItemPatternId)
        sp = p.QueryInterface(UIA.IUIAutomationSelectionItemPattern)
        data["SelectionItem"] = {
            "is_selected": simplify_value(sp.CurrentIsSelected),
        }
    except Exception:
        pass

    # ExpandCollapsePattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_ExpandCollapsePatternId)
        ep = p.QueryInterface(UIA.IUIAutomationExpandCollapsePattern)
        data["ExpandCollapse"] = {
            "state": simplify_value(ep.CurrentExpandCollapseState),
        }
    except Exception:
        pass

    # ScrollPattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_ScrollPatternId)
        scp = p.QueryInterface(UIA.IUIAutomationScrollPattern)
        data["Scroll"] = {
            "horizontally_scrollable": simplify_value(scp.CurrentHorizontallyScrollable),
            "vertical_scrollable": simplify_value(scp.CurrentVerticallyScrollable),
            "horizontal_scroll_percent": simplify_value(scp.CurrentHorizontalScrollPercent),
            "vertical_scroll_percent": simplify_value(scp.CurrentVerticalScrollPercent),
            "horizontal_view_size": simplify_value(scp.CurrentHorizontalViewSize),
            "vertical_view_size": simplify_value(scp.CurrentVerticalViewSize),
        }
    except Exception:
        pass

    # GridPattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_GridPatternId)
        gp = p.QueryInterface(UIA.IUIAutomationGridPattern)
        data["Grid"] = {
            "row_count": simplify_value(gp.CurrentRowCount),
            "column_count": simplify_value(gp.CurrentColumnCount),
        }
    except Exception:
        pass

    # GridItemPattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_GridItemPatternId)
        gip = p.QueryInterface(UIA.IUIAutomationGridItemPattern)
        data["GridItem"] = {
            "row": simplify_value(gip.CurrentRow),
            "column": simplify_value(gip.CurrentColumn),
            "row_span": simplify_value(gip.CurrentRowSpan),
            "column_span": simplify_value(gip.CurrentColumnSpan),
        }
    except Exception:
        pass

    # TextPattern: pull limited document text if available
    try:
        p = element.GetCurrentPattern(UIA.UIA_TextPatternId)
        tp = p.QueryInterface(UIA.IUIAutomationTextPattern)
        text_range = tp.DocumentRange
        txt = text_range.GetText(500)  # limit to avoid huge dumps
        data["Text"] = {
            "document_text_first_500_chars": simplify_value(txt),
        }
    except Exception:
        pass

    # LegacyIAccessiblePattern
    try:
        p = element.GetCurrentPattern(UIA.UIA_LegacyIAccessiblePatternId)
        lp = p.QueryInterface(UIA.IUIAutomationLegacyIAccessiblePattern)
        data["LegacyIAccessible"] = {
            "name": simplify_value(lp.CurrentName),
            "value": simplify_value(lp.CurrentValue),
            "description": simplify_value(lp.CurrentDescription),
            "role": simplify_value(lp.CurrentRole),
            "state": simplify_value(lp.CurrentState),
            "default_action": simplify_value(lp.CurrentDefaultAction),
        }
    except Exception:
        pass

    return data


def element_to_dict(
    element: Any,
    depth: int,
    index_path: str,
    window_rect: Dict[str, int],
) -> Dict[str, Any]:
    control_type_id = get_prop(element, UIA.UIA_ControlTypePropertyId)
    rect = get_rect(element)

    item = {
        "index_path": index_path,
        "depth": depth,
        "runtime_id": get_runtime_id(element),
        "name": get_prop(element, UIA.UIA_NamePropertyId),
        "automation_id": get_prop(element, UIA.UIA_AutomationIdPropertyId),
        "class_name": get_prop(element, UIA.UIA_ClassNamePropertyId),
        "control_type_id": control_type_id,
        "control_type": control_type_name(control_type_id),
        "localized_control_type": get_prop(element, UIA.UIA_LocalizedControlTypePropertyId),
        "framework_id": get_prop(element, UIA.UIA_FrameworkIdPropertyId),
        "process_id": get_prop(element, UIA.UIA_ProcessIdPropertyId),
        "native_window_handle": get_prop(element, UIA.UIA_NativeWindowHandlePropertyId),
        "is_control_element": get_prop(element, UIA.UIA_IsControlElementPropertyId),
        "is_content_element": get_prop(element, UIA.UIA_IsContentElementPropertyId),
        "is_enabled": get_prop(element, UIA.UIA_IsEnabledPropertyId),
        "is_keyboard_focusable": get_prop(element, UIA.UIA_IsKeyboardFocusablePropertyId),
        "has_keyboard_focus": get_prop(element, UIA.UIA_HasKeyboardFocusPropertyId),
        "is_offscreen": get_prop(element, UIA.UIA_IsOffscreenPropertyId),
        "bounding_rect_screen": rect,
        "bbox_normalized_window_ymin_xmin_ymax_xmax": normalize_rect_to_window(rect, window_rect),
        "supported_patterns": get_supported_patterns(element),
        "pattern_data": get_pattern_data(element),
        "children": [],
    }

    return item


def find_window_by_title(title_substring: str) -> Optional[int]:
    matches: List[Tuple[int, str]] = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if title and title_substring.lower() in title.lower():
            matches.append((hwnd, title))

    win32gui.EnumWindows(callback, None)

    if not matches:
        return None

    # Prefer the longest title because browser windows often include page title.
    matches.sort(key=lambda x: len(x[1]), reverse=True)
    return matches[0][0]


def get_window_rect(hwnd: int) -> Dict[str, int]:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return {
        "left": int(left),
        "top": int(top),
        "right": int(right),
        "bottom": int(bottom),
        "width": int(right - left),
        "height": int(bottom - top),
    }


def get_window_title(hwnd: int) -> str:
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def get_window_pid(hwnd: int) -> Optional[int]:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return int(pid)
    except Exception:
        return None


def should_include_element(
    element_dict: Dict[str, Any],
    window_rect: Dict[str, int],
    include_offscreen: bool,
    include_empty_rect: bool,
) -> bool:
    rect = element_dict.get("bounding_rect_screen")
    is_offscreen = element_dict.get("is_offscreen")

    if not include_offscreen and is_offscreen is True:
        return False

    if not include_empty_rect and not rect_has_area(rect):
        return False

    if rect and not rect_intersects(rect, window_rect):
        return False

    return True


def walk_uia_tree(
    root_element: Any,
    automation: Any,
    window_rect: Dict[str, int],
    max_depth: int,
    max_nodes: int,
    include_offscreen: bool,
    include_empty_rect: bool,
) -> Tuple[Dict[str, Any], int, int]:
    walker = automation.ControlViewWalker

    visited = 0
    included = 0

    def recurse(element: Any, depth: int, index_path: str) -> Optional[Dict[str, Any]]:
        nonlocal visited, included

        if visited >= max_nodes:
            return None

        visited += 1

        current_dict = element_to_dict(
            element=element,
            depth=depth,
            index_path=index_path,
            window_rect=window_rect,
        )

        include_current = should_include_element(
            current_dict,
            window_rect=window_rect,
            include_offscreen=include_offscreen,
            include_empty_rect=include_empty_rect,
        )

        child_dicts: List[Dict[str, Any]] = []

        if depth < max_depth:
            try:
                child = walker.GetFirstChildElement(element)
            except Exception:
                child = None

            child_index = 0
            while child is not None and visited < max_nodes:
                child_path = f"{index_path}.{child_index}"
                child_result = recurse(child, depth + 1, child_path)
                if child_result is not None:
                    child_dicts.append(child_result)

                try:
                    child = walker.GetNextSiblingElement(child)
                except Exception:
                    child = None

                child_index += 1

        current_dict["children"] = child_dicts

        # Keep parent if it itself is visible OR if it has visible descendants.
        if include_current or child_dicts:
            included += 1
            return current_dict

        return None

    tree = recurse(root_element, 0, "0")

    if tree is None:
        tree = {
            "index_path": "0",
            "warning": "No visible UIA elements passed the filters.",
            "children": [],
        }

    return tree, visited, included


def flatten_tree(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    flat = []

    def rec(n: Dict[str, Any]):
        copy = {k: v for k, v in n.items() if k != "children"}
        flat.append(copy)
        for c in n.get("children", []):
            rec(c)

    rec(node)
    return flat


def main():
    parser = argparse.ArgumentParser(
        description="Dump visible Microsoft UI Automation elements from a target window to JSON."
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help='Substring of target window title, e.g. "Google Sheets" or the spreadsheet file name.',
    )
    parser.add_argument(
        "--active",
        action="store_true",
        help="Use the currently active foreground window.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="uia_visible_dump.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=12,
        help="Maximum UIA tree depth to traverse.",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=5000,
        help="Maximum number of UIA nodes to visit.",
    )
    parser.add_argument(
        "--include-offscreen",
        action="store_true",
        help="Include UIA elements where IsOffscreen is true.",
    )
    parser.add_argument(
        "--include-empty-rect",
        action="store_true",
        help="Include elements with empty or missing bounding rectangles.",
    )
    parser.add_argument(
        "--flat-only",
        action="store_true",
        help="Save only a flat list instead of hierarchy + flat list.",
    )

    args = parser.parse_args()

    if args.active:
        hwnd = win32gui.GetForegroundWindow()
    elif args.title:
        hwnd = find_window_by_title(args.title)
        if hwnd is None:
            print(f'No visible window found containing title: "{args.title}"')
            sys.exit(1)
    else:
        print('Use either --active or --title "some window title".')
        sys.exit(1)

    if not hwnd:
        print("Could not identify target window.")
        sys.exit(1)

    window_title = get_window_title(hwnd)
    window_rect = get_window_rect(hwnd)
    window_pid = get_window_pid(hwnd)

    automation = comtypes.client.CreateObject(
        UIA.CUIAutomation,
        interface=UIA.IUIAutomation,
    )

    try:
        root_element = automation.ElementFromHandle(hwnd)
    except Exception as e:
        print(f"Failed to get UIA element from hwnd={hwnd}: {e}")
        sys.exit(1)

    started = time.time()

    tree, visited_count, included_count = walk_uia_tree(
        root_element=root_element,
        automation=automation,
        window_rect=window_rect,
        max_depth=args.max_depth,
        max_nodes=args.max_nodes,
        include_offscreen=args.include_offscreen,
        include_empty_rect=args.include_empty_rect,
    )

    flat = flatten_tree(tree)

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "target_hwnd": hwnd,
        "target_title": window_title,
        "target_process_id": window_pid,
        "target_window_rect_screen": window_rect,
        "filters": {
            "include_offscreen": args.include_offscreen,
            "include_empty_rect": args.include_empty_rect,
            "max_depth": args.max_depth,
            "max_nodes": args.max_nodes,
        },
        "counts": {
            "visited_nodes": visited_count,
            "included_nodes": included_count,
            "flat_nodes": len(flat),
        },
        "elapsed_seconds": round(time.time() - started, 3),
        "notes": [
            "Bounding boxes are screen coordinates.",
            "Normalized boxes are [ymin, xmin, ymax, xmax] relative to the target window.",
            "UIA exposes the accessibility/control tree, not the raw DOM.",
            "Google Sheets may expose only a subset of visually rendered grid/cell information through UIA.",
        ],
    }

    if args.flat_only:
        output = {
            "metadata": metadata,
            "elements": flat,
        }
    else:
        output = {
            "metadata": metadata,
            "tree": tree,
            "elements_flat": flat,
        }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved UIA dump to: {args.output}")
    print(f"Visited nodes: {visited_count}")
    print(f"Included nodes: {included_count}")
    print(f"Flat elements: {len(flat)}")
    print(f"Target title: {window_title}")


if __name__ == "__main__":
    main()