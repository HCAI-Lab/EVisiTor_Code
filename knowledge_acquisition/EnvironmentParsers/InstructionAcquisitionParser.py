"""
Instruction -> ACT-R chunk pipeline (knowledge acquisition).

Converts natural-language spreadsheet task instructions into ACT-R compatible
subtask action lists in the same shape used by
Spreadsheet/Complete_Excel_Model.lisp, e.g.:

    (setq subtask3_1_list '((Goto "B7") (Select "B7") (end)))
    (setq subtask3_2_list '((Type "=(c7*b13)/100") (Press "enter") (end)))

Implements the RQ3 evaluation plan:

  (1) Schema-validity rate         -- structural correctness of generated output
  (2) Action-item extraction       -- action / target / sequence / exact-match
                                      accuracy vs. a gold-standard decomposition
  (3) Execution success            -- requires running the ACT-R model with the
                                      generated chunks; see run_execution_check()
                                      stub at the bottom.
  (4) Robustness to paraphrasing   -- pipeline is run on N paraphrased variants
                                      of the same task; metrics are reported per
                                      variant and aggregated.
  (5) Manual-authoring reduction   -- counts of chunks/action-pairs that would
                                      otherwise have to be hand-authored.

Outputs:
  Spreadsheet/generated_chunks/<variant>.lisp        -- one Lisp file per variant
  Spreadsheet/generated_chunks/<variant>.json        -- raw structured output
  Spreadsheet/generated_chunks/metrics_report.json   -- all metrics, all variants
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI, RateLimitError

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join("Spreadsheet", "generated_chunks")

# (provider, model_id) pairs to evaluate.
# Provider must be "openai", "gemini", or "openrouter".
MODELS: List[Tuple[str, str]] = [
    ("openai", "gpt-5.5"),
    ("openai", "gpt-5.4-mini"),
    ("openai", "gpt-5.4-nano"),
    ("gemini", "gemini-3.5-flash"),
    ("gemini", "gemini-3.1-flash-lite"),
    ("openrouter", "openai/gpt-oss-120b:free"),
    ("openrouter", "deepseek/deepseek-v4-flash:free"),
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
    # Paid slugs of the same three models, added 2026-07-10: the :free pool
    # was congested/withdrawn (deepseek :free now 404s) and credits were
    # purchased to complete the UIA-grounded evaluation runs.
    ("openrouter", "openai/gpt-oss-120b"),
    ("openrouter", "deepseek/deepseek-v4-flash"),
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b"),
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Tunable at runtime via --or-retries / --or-backoff.
OR_RETRIES = 10
OR_BACKOFF_S = 60

ALLOWED_ACTIONS = ["Goto", "Move", "Select", "Type", "Press"]
ALLOWED_TERMINATORS = ["end", "endsub"]


# ---------------------------------------------------------------------------
# Inputs: natural-language instruction sets
# ---------------------------------------------------------------------------
# Each variant is a list of {task_id, task_name, steps[]}. The "original"
# variant is the instruction text from the spreadsheet task booklet. The two
# paraphrased variants probe robustness (plan item #4) without adding new
# information.
# ---------------------------------------------------------------------------

ORIGINAL_INSTRUCTIONS: List[Dict[str, Any]] = [
    {"task_id": 1, "task_name": "OPEN FILE", "steps": [
        "Go to and select File",
        "Go to and select Open",
        "Go to Under Workbook and select normalization.xlsx",
    ]},
    {"task_id": 2, "task_name": "SAVE AS", "steps": [
        "Go to and select File",
        "Go to and select Save as",
        "Go to file name area",
        "Type subject",
        "Go to and select Save",
    ]},
    {"task_id": 3, "task_name": "CALCULATE FREQUENCY (B7 to B11)", "steps": [
        "Move and Select B7",
        "Type =(C7*B13)/100, press Enter",
        "Repeat the same Move-Select-Type-Enter pattern for B8, B9, B10, B11, "
        "using =(C8*B13)/100 ... =(C11*B13)/100 respectively",
    ]},
    {"task_id": 4, "task_name": "CALCULATE TOTAL FREQUENCY (B14)", "steps": [
        "Move and Select B14",
        "Type =sum(b2:b11), press Enter",
    ]},
    {"task_id": 5, "task_name": "CALCULATE NORMALIZATION (C2 to C6)", "steps": [
        "Move and Select C2",
        "Type =(B2*100)/b13, press Enter",
        "Repeat for C3 through C6 with =(B3*100)/b13 ... =(B6*100)/b13",
    ]},
    {"task_id": 6, "task_name": "CALCULATE TOTAL NORMALIZATION (C14)", "steps": [
        "Move and Select C14",
        "Type =sum(c2:c11), press Enter",
    ]},
    {"task_id": 7, "task_name": "CALCULATE LENGTH (D2 to D11)", "steps": [
        "Move and Select D2",
        "Type =len(a2), press Enter",
        "Repeat for D3 through D11 with =len(a3) ... =len(a11)",
    ]},
    {"task_id": 8, "task_name": "CALCULATE TOTAL LENGTH (D14)", "steps": [
        "Move and Select D14",
        "Type =sum(d2:d11), press Enter",
    ]},
    {"task_id": 9, "task_name": "CALCULATE TYPED CHARACTERS (E2 to E11)", "steps": [
        "Move and Select E2",
        "Type =d2*b2, press Enter",
        "Repeat for E3 through E11 with =d3*b3 ... =d11*b11",
    ]},
    {"task_id": 10, "task_name": "CALCULATE TOTAL TYPED CHARACTERS (E14)", "steps": [
        "Move and Select E14",
        "Type =sum(e2:e11), press Enter",
    ]},
    {"task_id": 11, "task_name": "INSERT TWO ROWS", "steps": [
        "Move to and Select Row 1",
        "Go to and select Home",
        "Go to and select Cells",
        "Go to and select Insert",
        "Go to and select Insert-cell",
        "Repeat the entire five-step sequence one more time",
    ]},
    {"task_id": 12, "task_name": "TYPE IN NAME (A1)", "steps": [
        "Move to and Select A1",
        "Type subject, press Enter",
    ]},
    {"task_id": 13, "task_name": "INSERT CURRENT DATE (A2)", "steps": [
        "Move to and Select A2",
        "Type =today(), press Enter",
    ]},
    {"task_id": 14, "task_name": "SAVE AS WITH NEW NAME", "steps": [
        "Go to and select File Tab",
        "Go to and select Save",
        "Go to the file name area",
        "Type normalization-subject, press Enter",
    ]},
]

PARAPHRASE_1: List[Dict[str, Any]] = [
    {"task_id": 1, "task_name": "OPEN FILE", "steps": [
        "Click the File tab.",
        "Click Open.",
        "Under Workbook, select the file called normalization.xlsx.",
    ]},
    {"task_id": 2, "task_name": "SAVE AS", "steps": [
        "Open the File tab.",
        "Choose Save as.",
        "Click into the file-name input.",
        """Enter the text "subject".""",
        "Click Save.",
    ]},
    {"task_id": 3, "task_name": "FILL FREQUENCY COLUMN B7-B11", "steps": [
        "Navigate to cell B7 and activate it.",
        "Enter the formula =(C7*B13)/100 and press the Enter key.",
        "Do the same for B8 through B11, substituting C8..C11 in the formula.",
    ]},
    {"task_id": 4, "task_name": "TOTAL FREQUENCY IN B14", "steps": [
        "Navigate to cell B14 and activate it.",
        "Enter =sum(b2:b11) and press Enter.",
    ]},
    {"task_id": 5, "task_name": "FILL NORMALIZATION COLUMN C2-C6", "steps": [
        "Navigate to C2 and activate it.",
        "Enter the formula =(B2*100)/b13 and press Enter.",
        "Repeat for C3 through C6 with =(B3*100)/b13 .. =(B6*100)/b13.",
    ]},
    {"task_id": 6, "task_name": "TOTAL NORMALIZATION IN C14", "steps": [
        "Navigate to C14 and activate it.",
        "Enter =sum(c2:c11) and press Enter.",
    ]},
    {"task_id": 7, "task_name": "FILL LENGTH COLUMN D2-D11", "steps": [
        "Navigate to D2 and activate it.",
        "Enter =len(a2) and press Enter.",
        "Repeat for D3 through D11 with =len(a3) .. =len(a11).",
    ]},
    {"task_id": 8, "task_name": "TOTAL LENGTH IN D14", "steps": [
        "Navigate to D14 and activate it.",
        "Enter =sum(d2:d11) and press Enter.",
    ]},
    {"task_id": 9, "task_name": "FILL TYPED-CHARS COLUMN E2-E11", "steps": [
        "Navigate to E2 and activate it.",
        "Enter =d2*b2 and press Enter.",
        "Repeat for E3 through E11 with =d3*b3 .. =d11*b11.",
    ]},
    {"task_id": 10, "task_name": "TOTAL TYPED-CHARS IN E14", "steps": [
        "Navigate to E14 and activate it.",
        "Enter =sum(e2:e11) and press Enter.",
    ]},
    {"task_id": 11, "task_name": "INSERT TWO ROWS AT THE TOP", "steps": [
        "Click on Row 1 to select the whole row.",
        "Open the Home ribbon.",
        "Open the Cells group.",
        "Click Insert.",
        "Choose Insert-cell.",
        "Carry out the same five clicks a second time.",
    ]},
    {"task_id": 12, "task_name": "ENTER A NAME IN A1", "steps": [
        "Navigate to A1 and activate it.",
        "Enter the text subject and press Enter.",
    ]},
    {"task_id": 13, "task_name": "ENTER TODAY'S DATE IN A2", "steps": [
        "Navigate to A2 and activate it.",
        "Enter =today() and press Enter.",
    ]},
    {"task_id": 14, "task_name": "RESAVE WITH A NEW NAME", "steps": [
        "Open the File tab.",
        "Choose Save.",
        "Click into the file-name input.",
        "Enter normalization-subject and press Enter.",
    ]},
]

PARAPHRASE_2: List[Dict[str, Any]] = [
    {"task_id": 1, "task_name": "OPEN FILE", "steps": [
        "Use File > Open. From the workbook list, pick normalization.xlsx.",
    ]},
    {"task_id": 2, "task_name": "SAVE AS", "steps": [
        "Use File > Save as. Type subject into the file-name field, then choose Save.",
    ]},
    {"task_id": 3, "task_name": "FREQUENCY B7..B11", "steps": [
        "For each row i in 7..11: jump to cell B{i}, type =(C{i}*B13)/100, hit Enter.",
    ]},
    {"task_id": 4, "task_name": "TOTAL FREQUENCY B14", "steps": [
        "Jump to B14, type =sum(b2:b11), hit Enter.",
    ]},
    {"task_id": 5, "task_name": "NORMALIZATION C2..C6", "steps": [
        "For each row i in 2..6: jump to C{i}, type =(B{i}*100)/b13, hit Enter.",
    ]},
    {"task_id": 6, "task_name": "TOTAL NORMALIZATION C14", "steps": [
        "Jump to C14, type =sum(c2:c11), hit Enter.",
    ]},
    {"task_id": 7, "task_name": "LENGTH D2..D11", "steps": [
        "For each row i in 2..11: jump to D{i}, type =len(a{i}), hit Enter.",
    ]},
    {"task_id": 8, "task_name": "TOTAL LENGTH D14", "steps": [
        "Jump to D14, type =sum(d2:d11), hit Enter.",
    ]},
    {"task_id": 9, "task_name": "TYPED CHARS E2..E11", "steps": [
        "For each row i in 2..11: jump to E{i}, type =d{i}*b{i}, hit Enter.",
    ]},
    {"task_id": 10, "task_name": "TOTAL TYPED CHARS E14", "steps": [
        "Jump to E14, type =sum(e2:e11), hit Enter.",
    ]},
    {"task_id": 11, "task_name": "INSERT TWO BLANK ROWS AT TOP", "steps": [
        "Twice in a row: pick Row 1, then Home, then Cells, then Insert, then Insert-cell.",
    ]},
    {"task_id": 12, "task_name": "NAME IN A1", "steps": [
        "In cell A1 type subject and press Enter.",
    ]},
    {"task_id": 13, "task_name": "DATE IN A2", "steps": [
        "In cell A2 type =today() and press Enter.",
    ]},
    {"task_id": 14, "task_name": "RESAVE", "steps": [
        "File > Save. In the file-name area type normalization-subject and press Enter.",
    ]},
]

INSTRUCTION_SETS: Dict[str, List[Dict[str, Any]]] = {
    "original": ORIGINAL_INSTRUCTIONS,
    "paraphrase_1": PARAPHRASE_1,
    "paraphrase_2": PARAPHRASE_2,
}


# ---------------------------------------------------------------------------
# Gold standard (verbatim from Spreadsheet/Complete_Excel_Model.lisp lines 10-125)
# ERRATUM 2026-07-10: subtask14_1 (Select "File ab") corrected to
# (Select "File Tab") — a typo in the source lisp (harmless at model runtime,
# but it cost every LLM one impossible target slot). Numbers published before
# this date used the uncorrected gold; the mean effect is +0.43 pts target
# accuracy / +0.86 pts full-subtask rate across the saved artifacts.
# ERRATUM 2026-07-11: task 2 restructured to match its own instruction text
# ("Go to and select Save" is the final step). Old gold ended subtask2_4 with
# (Press "enter") and had no Save click; corrected gold is
# subtask2_4 = (Type "subject") only, plus new subtask2_5 =
# (Goto "Save") (Select "Save"). Gold subtask count is now 94 (was 93).
# Also 2026-07-11: subtask2_2 target "Save" -> "Save a Copy": current Excel
# (AutoSave era) has no backstage "Save"/"Save As" item; the real element is
# "Save a Copy" (verified in the UIA scans), matching
# *spreadsheet-ablation-known-object-targets* in Ablation_support.lisp.
# Numbers published before this date used the old task-2 gold.
# ---------------------------------------------------------------------------

GOLD_LISP = r"""
(setq subtask1_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask1_2_list '((Goto "open") (Select "open") (end)))
(setq subtask1_3_list '((Goto "normalization") (Select "normalization") (endsub)))
(setq subtask2_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask2_2_list '((Goto "Save a Copy") (Select "Save a Copy") (end)))
(setq subtask2_3_list '((Goto "file_name") (Select "file_name") (end)))
(setq subtask2_4_list '((Type "subject") (end)))
(setq subtask2_5_list '((Goto "Save") (Select "Save") (endsub)))
(setq subtask3_1_list '((Goto "B7") (Select "B7") (end)))
(setq subtask3_2_list '((Type "=(c7*b13)/100") (Press "enter") (end)))
(setq subtask3_3_list '((Goto "B8") (Select "B8") (end)))
(setq subtask3_4_list '((Type "=(c8*b13)/100") (Press "enter") (end)))
(setq subtask3_5_list '((Goto "B9") (Select "B9") (end)))
(setq subtask3_6_list '((Type "=(c9*b13)/100") (Press "enter") (end)))
(setq subtask3_7_list '((Goto "B10") (Select "B10") (end)))
(setq subtask3_8_list '((Type "=(c10*b13)/100") (Press "enter") (end)))
(setq subtask3_9_list '((Goto "B11") (Select "B11") (end)))
(setq subtask3_10_list '((Type "=(c11*b13)/100") (Press "enter") (endsub)))
(setq subtask4_1_list '((Goto "B14") (Select "B14") (end)))
(setq subtask4_2_list '((Type "=sum(b2:b11)") (Press "enter") (endsub)))
(setq subtask5_1_list '((Goto "C2") (Select "C2") (end)))
(setq subtask5_2_list '((Type "=(b2*100)/b13") (Press "enter") (end)))
(setq subtask5_3_list '((Goto "C3") (Select "C3") (end)))
(setq subtask5_4_list '((Type "=(b3*100)/b13") (Press "enter") (end)))
(setq subtask5_5_list '((Goto "C4") (Select "C4") (end)))
(setq subtask5_6_list '((Type "=(b4*100)/b13") (Press "enter") (end)))
(setq subtask5_7_list '((Goto "C5") (Select "C5") (end)))
(setq subtask5_8_list '((Type "=(b5*100)/b13") (Press "enter") (end)))
(setq subtask5_9_list '((Goto "C6") (Select "C6") (end)))
(setq subtask5_10_list '((Type "=(b6*100)/b13") (Press "enter") (endsub)))
(setq subtask6_1_list '((Goto "c14") (Select "c14") (end)))
(setq subtask6_2_list '((Type "=sum(c2:c11)") (Press enter) (endsub)))
(setq subtask7_1_list '((Goto "D2") (Select "D2") (end)))
(setq subtask7_2_list '((Type "=len(a2)") (Press enter) (end)))
(setq subtask7_3_list '((Goto "d3") (Select "d3") (end)))
(setq subtask7_4_list '((Type "=len(a3)") (Press enter) (end)))
(setq subtask7_5_list '((Goto "d4") (Select "d4") (end)))
(setq subtask7_6_list '((Type "=len(a4)") (Press enter) (end)))
(setq subtask7_7_list '((Goto "d5") (Select "d5") (end)))
(setq subtask7_8_list '((Type "=len(a5)") (Press enter) (end)))
(setq subtask7_9_list '((Goto "d6") (Select "d6") (end)))
(setq subtask7_10_list '((Type "=len(a6)") (Press enter) (end)))
(setq subtask7_11_list '((Goto "d7") (Select "d7") (end)))
(setq subtask7_12_list '((Type "=len(a7)") (Press enter) (end)))
(setq subtask7_13_list '((Goto "d8") (Select "d8") (end)))
(setq subtask7_14_list '((Type "=len(a8)") (Press enter) (end)))
(setq subtask7_15_list '((Goto "d9") (Select "d9") (end)))
(setq subtask7_16_list '((Type "=len(a9)") (Press enter) (end)))
(setq subtask7_17_list '((Goto "d10") (Select "d10") (end)))
(setq subtask7_18_list '((Type "=len(a10)") (Press enter) (end)))
(setq subtask7_19_list '((Goto "d11") (Select "d11") (end)))
(setq subtask7_20_list '((Type "=len(a11)") (Press enter) (endsub)))
(setq subtask8_1_list '((Goto "d14") (Select "d14") (end)))
(setq subtask8_2_list '((Type "=sum(d2:d11)") (Press enter) (endsub)))
(setq subtask9_1_list '((Goto "e2") (Select "e2") (end)))
(setq subtask9_2_list '((Type "=d2*b2") (Press enter) (end)))
(setq subtask9_3_list '((Goto "e3") (Select "e3") (end)))
(setq subtask9_4_list '((Type "=d3*b3") (Press enter) (end)))
(setq subtask9_5_list '((Goto "e4") (Select "e4") (end)))
(setq subtask9_6_list '((Type "=d4*b4") (Press enter) (end)))
(setq subtask9_7_list '((Goto "e5") (Select "e5") (end)))
(setq subtask9_8_list '((Type "=d5*b5") (Press enter) (end)))
(setq subtask9_9_list '((Goto "e6") (Select "e6") (end)))
(setq subtask9_10_list '((Type "=d6*b6") (Press enter) (end)))
(setq subtask9_11_list '((Goto "e7") (Select "e7") (end)))
(setq subtask9_12_list '((Type "=d7*b7") (Press enter) (end)))
(setq subtask9_13_list '((Goto "e8") (Select "e8") (end)))
(setq subtask9_14_list '((Type "=d8*b8") (Press enter) (end)))
(setq subtask9_15_list '((Goto "e9") (Select "e9") (end)))
(setq subtask9_16_list '((Type "=d9*b9") (Press enter) (end)))
(setq subtask9_17_list '((Goto "e10") (Select "e10") (end)))
(setq subtask9_18_list '((Type "=d10*b10") (Press enter) (end)))
(setq subtask9_19_list '((Goto "e11") (Select "e11") (end)))
(setq subtask9_20_list '((Type "=d11*b11") (Press enter) (endsub)))
(setq subtask10_1_list '((Move "e14") (Select "e14") (end)))
(setq subtask10_2_list '((Type "=sum(e2:e11)") (Press enter) (endsub)))
(setq subtask11_1_list '((Goto "Row_1") (Select "Row_1") (end)))
(setq subtask11_2_list '((Goto "Home") (Select "Home") (end)))
(setq subtask11_3_list '((Goto "Cells") (Select "Cells") (end)))
(setq subtask11_4_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_5_list '((Goto "Insert-cell") (Select "Insert-cell") (end)))
(setq subtask11_6_list '((Goto "Row_1") (Select "Row_1") (end)))
(setq subtask11_7_list '((Goto "Home") (Select "Home") (end)))
(setq subtask11_8_list '((Goto "Cells") (Select "Cells") (end)))
(setq subtask11_9_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_10_list '((Goto "Insert-cell") (Select "Insert-cell") (endsub)))
(setq subtask12_1_list '((Goto "A1") (Select "A1") (end)))
(setq subtask12_2_list '((Type "subject") (Press enter) (endsub)))
(setq subtask13_1_list '((Goto "A2") (Select "A2") (end)))
(setq subtask13_2_list '((Type "=today()") (Press enter) (endsub)))
(setq subtask14_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask14_2_list '((Goto "Save") (Select "Save") (end)))
(setq subtask14_3_list '((Goto "file_name") (Select "file_name") (end)))
(setq subtask14_4_list '((Type "normalization-subject") (Press enter) (endsub)))
"""


SUBTASK_LINE_RE = re.compile(
    r"\(setq\s+subtask(\d+)_(\d+)_list\s+'\(\s*(.*?)\s*\)\)",
    re.DOTALL,
)
ACTION_RE = re.compile(
    r"\(\s*(\w[\w-]*)(?:\s+\"([^\"]*)\"|\s+([\w-]+))?\s*\)"
)


def parse_lisp_subtasks(text: str) -> Dict[Tuple[int, int], List[Tuple[str, Optional[str]]]]:
    """Parse all `(setq subtask{i}_{j}_list '(...))` forms into a dict keyed by
    (task_id, subtask_id). Each value is the ordered list of (verb, target)
    tuples; terminators (`end`, `endsub`) appear as (verb, None)."""
    out: Dict[Tuple[int, int], List[Tuple[str, Optional[str]]]] = {}
    for m in SUBTASK_LINE_RE.finditer(text):
        task = int(m.group(1))
        sub = int(m.group(2))
        body = m.group(3)
        actions: List[Tuple[str, Optional[str]]] = []
        for am in ACTION_RE.finditer(body):
            verb = am.group(1)
            target = am.group(2) if am.group(2) is not None else am.group(3)
            actions.append((verb, target))
        out[(task, sub)] = actions
    return out


# ---------------------------------------------------------------------------
# JSON schema for the LLM structured output
# ---------------------------------------------------------------------------

ACTION_ITEM_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "task_id": {"type": "integer", "minimum": 1},
                    "task_name": {"type": "string"},
                    "subtasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "subtask_id": {"type": "integer", "minimum": 1},
                                "actions": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "action": {
                                                "type": "string",
                                                "enum": ALLOWED_ACTIONS,
                                            },
                                            "target": {"type": "string"},
                                        },
                                        "required": ["action", "target"],
                                    },
                                },
                            },
                            "required": ["subtask_id", "actions"],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["task_id", "task_name", "subtasks"],
            },
        },
    },
    "required": ["tasks"],
}


def schema_for_actions(actions: List[str]) -> Dict[str, Any]:
    """ACTION_ITEM_SCHEMA with a different verb enum. Lets a caller (e.g. the
    Windows-task eval, whose vocabulary includes RightClick/Scroll) extend the
    structured-output constraint without touching the published Excel schema."""
    schema = json.loads(json.dumps(ACTION_ITEM_SCHEMA))
    (schema["properties"]["tasks"]["items"]["properties"]["subtasks"]["items"]
     ["properties"]["actions"]["items"]["properties"]["action"]["enum"]) = list(actions)
    return schema


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
# Few-shot example uses a *different* task (Word/Outlook style) to avoid leaking
# any of the spreadsheet inputs. It only demonstrates output format.
# ---------------------------------------------------------------------------

PROMPT_HEADER = """\
You convert step-by-step task instructions into a structured action representation
for an ACT-R cognitive model that simulates desktop UI use.

For each numbered task you receive:
  1. Split it into ordered "subtasks". A subtask is the smallest unit that has
     its own selection target -- e.g. "move and select cell B7" is ONE subtask
     (Goto B7, Select B7); "type =SUM(...) and press Enter" is a separate
     subtask (Type "...", Press "enter").
  2. Within each subtask, list atomic actions in order.

Allowed verbs (use these exactly): Goto, Move, Select, Type, Press.
  - Goto/Move : navigate to a UI target (a cell, a menu item, a row header,
                the file-name input, a button, etc.). Prefer Goto.
  - Select    : click/activate the target reached by the preceding Goto/Move.
                Pair every Goto with a matching Select for the same target.
  - Type      : type a literal string. Preserve formulas EXACTLY, including
                parentheses, casing as written, and the leading "=".
  - Press     : a single key press. Use "enter" for the Enter key, "tab" for
                Tab, "ctrl-b" for Ctrl+B, etc. (lowercase, hyphenated).

Pairing conventions:
  - "Move and select X"           -> 2 actions in 1 subtask:
                                     (Goto X), (Select X)
  - "Type ..., press Enter"       -> 2 actions in 1 subtask:
                                     (Type "..."), (Press "enter")
  - Cell coordinates: keep the exact letter+digit notation from the instruction
    (e.g. "B7", "c14"). Do not invent cells.
  - Menu / UI items: keep the displayed name (e.g. "File Tab", "Save", "Home",
    "Insert", "Cells", "Insert-cell", "file_name", "Row_1").
  - When an instruction says "repeat for X..Y" you MUST expand the repetition
    into the full set of subtasks. Do not abbreviate.

Number tasks starting at 1 in input order; number subtasks starting at 1 within
each task. Do not skip or merge tasks.

Example (different domain, just to show output shape):

INPUT:
[
  {"task_id": 1, "task_name": "BOLD TITLE",
   "steps": ["Move and select cell A1", "Press Ctrl+B"]}
]
OUTPUT:
{"tasks":[{"task_id":1,"task_name":"BOLD TITLE","subtasks":[
  {"subtask_id":1,"actions":[
    {"action":"Goto","target":"A1"},
    {"action":"Select","target":"A1"}]},
  {"subtask_id":2,"actions":[
    {"action":"Press","target":"ctrl-b"}]}
]}]}

Now convert the following INPUT. Return JSON only, matching the schema.

INPUT:
"""


# --uia-context initial sets this to a rendered UIA element block (see
# uia_grounding_common.render_uia_block). None (the default) leaves the
# prompt byte-identical to the published evaluation.
UIA_CONTEXT_BLOCK: Optional[str] = None

# Suffix appended to per-variant artifact filenames so a --uia-context run
# never clobbers the published (none-condition) artifacts.
ARTIFACT_SUFFIX: str = ""

_UIA_INSERT_MARKER = "Now convert the following INPUT."


def build_prompt(instructions: List[Dict[str, Any]]) -> str:
    header = PROMPT_HEADER
    if UIA_CONTEXT_BLOCK:
        header = header.replace(
            _UIA_INSERT_MARKER,
            UIA_CONTEXT_BLOCK.rstrip() + "\n\n" + _UIA_INSERT_MARKER,
        )
    return header + json.dumps(instructions, indent=2)


# ---------------------------------------------------------------------------
# OpenAI call
# ---------------------------------------------------------------------------

def call_openai(client: OpenAI, model: str,
                instructions: List[Dict[str, Any]],
                max_retries: int = 8,
                prompt: Optional[str] = None,
                schema: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if prompt is None:
        prompt = build_prompt(instructions)
    if schema is None:
        schema = ACTION_ITEM_SCHEMA
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "action_items",
                        "strict": True,
                        "schema": schema,
                    },
                },
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(resp.choices[0].message.content), None
        except RateLimitError as e:
            if "insufficient_quota" in str(e):
                # Account out of credit -- not transient, retrying is pointless.
                print("  insufficient_quota (account out of credit); giving up")
                return None, "insufficient_quota"
            print(f"  rate-limited, sleeping 60s (attempt {attempt + 1}/{max_retries})")
            time.sleep(60)
        except Exception as e:
            msg = str(e)
            if "insufficient_quota" in msg:
                print("  insufficient_quota (account out of credit); giving up")
                return None, "insufficient_quota"
            if "429" in msg or "quota" in msg.lower():
                print(f"  quota issue, sleeping 60s (attempt {attempt + 1}/{max_retries})")
                time.sleep(60)
            else:
                print(f"  call failed: {e}")
                return None, msg
    return None, "max_retries_exceeded"


# Gemini's response_schema doesn't accept `additionalProperties`. Build a stripped
# variant of ACTION_ITEM_SCHEMA on demand.

def _strip_for_gemini(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {k: _strip_for_gemini(v) for k, v in schema.items()
                if k != "additionalProperties"}
    if isinstance(schema, list):
        return [_strip_for_gemini(x) for x in schema]
    return schema


def call_gemini(client: Any, model: str,
                instructions: List[Dict[str, Any]],
                max_retries: int = 20,
                backoff_s: int = 60,
                prompt: Optional[str] = None,
                schema: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if prompt is None:
        prompt = build_prompt(instructions)
    schema = _strip_for_gemini(schema if schema is not None
                               else ACTION_ITEM_SCHEMA)
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=google_genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return json.loads(resp.text), None
        except Exception as e:
            msg = str(e)
            lowered = msg.lower()
            if "perday" in lowered.replace("_", "").replace("-", ""):
                # Free-tier per-day quota exhausted -- resets at midnight PT,
                # retrying within this run is pointless.
                print("  per-day quota exhausted (not transient); giving up")
                return None, "per_day_quota_exhausted"
            transient = (
                "429" in msg or "rate" in lowered or "quota" in lowered
                or "resource_exhausted" in lowered
                or "503" in msg or "unavailable" in lowered
                or "500" in msg or "overloaded" in lowered
            )
            if transient and attempt < max_retries - 1:
                print(f"  transient error ({msg[:80]}); waiting {backoff_s}s "
                      f"then retrying (attempt {attempt + 1}/{max_retries})")
                time.sleep(backoff_s)
            else:
                print(f"  call failed: {e}")
                return None, msg
    return None, "max_retries_exceeded"


def _extract_json(text: str) -> Dict[str, Any]:
    """Parse JSON, tolerating a leading/trailing markdown code fence that some
    OpenRouter models wrap their output in."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[A-Za-z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return json.loads(t)


def call_openrouter(client: OpenAI, model: str,
                    instructions: List[Dict[str, Any]],
                    max_retries: Optional[int] = None,
                    backoff_s: Optional[int] = None,
                    prompt: Optional[str] = None,
                    schema: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """OpenRouter is OpenAI-API-compatible. Not every routed model supports
    strict json_schema, so try response_format strategies in decreasing order
    of strictness and fall back automatically: json_schema -> json_object ->
    none (prompt-only). Rate limits are retried; format rejections (and empty
    completions, which usually mean the chosen format wasn't honored) downgrade
    without consuming a retry."""
    if max_retries is None:
        max_retries = OR_RETRIES
    if backoff_s is None:
        backoff_s = OR_BACKOFF_S
    if prompt is None:
        prompt = build_prompt(instructions)
    rf_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "action_items",
            "strict": True,
            "schema": schema if schema is not None else ACTION_ITEM_SCHEMA,
        },
    }
    rf_object = {"type": "json_object"}
    strategies: List[Optional[Dict[str, Any]]] = [rf_schema, rf_object, None]
    strat_idx = 0

    def downgrade(reason: str) -> bool:
        nonlocal strat_idx
        if strat_idx < len(strategies) - 1:
            strat_idx += 1
            print(f"  {reason}; downgrading strategy -> {strategies[strat_idx]}")
            return True
        return False

    attempt = 0
    while attempt < max_retries:
        rf = strategies[strat_idx]
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if rf is not None:
            kwargs["response_format"] = rf
        try:
            resp = client.chat.completions.create(**kwargs)

            # Throttled / malformed responses can come back with no choices.
            choices = getattr(resp, "choices", None)
            if not choices:
                err = getattr(resp, "error", None) or "empty response (no choices)"
                lowered = str(err).lower()
                if "rate" in lowered or "quota" in lowered or "429" in lowered:
                    attempt += 1
                    print(f"  throttled (no choices), sleeping {backoff_s}s "
                          f"(attempt {attempt}/{max_retries})")
                    time.sleep(backoff_s)
                    continue
                if downgrade("empty response"):
                    continue
                return None, str(err)

            content = choices[0].message.content
            if content is None or not content.strip():
                if downgrade("empty completion content"):
                    continue
                return None, "empty completion content after all strategies"

            return _extract_json(content), None

        except RateLimitError as e:
            lowered_e = str(e).lower()
            if "per day" in lowered_e or "free-models-per-day" in lowered_e:
                # Free-model daily cap (50/day without purchased credits) --
                # resets at midnight UTC, retrying within this run is pointless.
                print("  free-model daily cap reached; giving up")
                return None, "free_models_daily_cap"
            attempt += 1
            print(f"  rate-limited, sleeping {backoff_s}s (attempt {attempt}/{max_retries})")
            time.sleep(backoff_s)
        except json.JSONDecodeError:
            if downgrade("unparseable JSON"):
                continue
            return None, "unparseable JSON after all strategies"
        except Exception as e:
            msg = str(e)
            lowered = msg.lower()
            fmt_rejected = (
                "response_format" in lowered or "json_schema" in lowered
                or "schema" in lowered or "json_object" in lowered
                or "not support" in lowered
            )
            if fmt_rejected and downgrade("response_format rejected"):
                continue
            if "429" in msg or "rate" in lowered or "quota" in lowered:
                attempt += 1
                print(f"  rate/quota issue, sleeping {backoff_s}s "
                      f"(attempt {attempt}/{max_retries})")
                time.sleep(backoff_s)
                continue
            print(f"  call failed: {e}")
            return None, msg
    return None, "max_retries_exceeded"


def call_model(provider: str, client: Any, model: str,
               instructions: List[Dict[str, Any]],
               prompt: Optional[str] = None,
               schema: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if provider == "openai":
        return call_openai(client, model, instructions, prompt=prompt,
                           schema=schema)
    if provider == "gemini":
        return call_gemini(client, model, instructions, prompt=prompt,
                           schema=schema)
    if provider == "openrouter":
        return call_openrouter(client, model, instructions, prompt=prompt,
                               schema=schema)
    return None, f"unknown_provider:{provider}"


# ---------------------------------------------------------------------------
# Schema validation (plan item #1)
# ---------------------------------------------------------------------------
# OpenAI's strict json_schema mode already guarantees structural validity, so
# this layer mainly catches semantic violations the schema cannot express
# (e.g. duplicate subtask ids, empty targets) -- the kind of "repair required"
# bucket from the metrics table.
# ---------------------------------------------------------------------------

def validate_semantic(data: Optional[Dict[str, Any]],
                      allowed_actions: Optional[List[str]] = None
                      ) -> Tuple[bool, List[str]]:
    if allowed_actions is None:
        allowed_actions = ALLOWED_ACTIONS
    errors: List[str] = []
    if not isinstance(data, dict) or "tasks" not in data:
        return False, ["missing 'tasks' root"]
    seen_tasks = set()
    for t in data["tasks"]:
        tid = t.get("task_id")
        if tid in seen_tasks:
            errors.append(f"duplicate task_id {tid}")
        seen_tasks.add(tid)
        seen_subs = set()
        for s in t.get("subtasks", []):
            sid = s.get("subtask_id")
            if sid in seen_subs:
                errors.append(f"task {tid}: duplicate subtask_id {sid}")
            seen_subs.add(sid)
            if not s.get("actions"):
                errors.append(f"task {tid} subtask {sid}: empty action list")
            for a in s.get("actions", []):
                if a.get("action") not in allowed_actions:
                    errors.append(
                        f"task {tid} subtask {sid}: illegal action "
                        f"{a.get('action')!r}"
                    )
                if not isinstance(a.get("target"), str) or not a["target"].strip():
                    errors.append(
                        f"task {tid} subtask {sid}: empty/non-string target"
                    )
    return not errors, errors


# ---------------------------------------------------------------------------
# Emit Lisp in the Complete_Excel_Model.lisp format
# ---------------------------------------------------------------------------

def to_lisp(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    for t in data["tasks"]:
        lines.append(f';;; Task {t["task_id"]}: {t["task_name"]}')
        subs = t["subtasks"]
        last_idx = len(subs) - 1
        for i, s in enumerate(subs):
            terminator = "endsub" if i == last_idx else "end"
            pieces = []
            for a in s["actions"]:
                pieces.append(f'({a["action"]} "{a["target"]}")')
            pieces.append(f"({terminator})")
            sym = f"subtask{t['task_id']}_{s['subtask_id']}_list"
            lines.append(f"(setq {sym} '({' '.join(pieces)}))")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convert generated data into the (task, subtask) -> [(verb, target), ...]
# shape used for metric comparison. Terminators are stripped because they're
# computed by to_lisp(), not produced by the model.
# ---------------------------------------------------------------------------

def generated_to_eval(data: Dict[str, Any]) -> Dict[Tuple[int, int], List[Tuple[str, str]]]:
    out: Dict[Tuple[int, int], List[Tuple[str, str]]] = {}
    for t in data["tasks"]:
        for s in t["subtasks"]:
            key = (t["task_id"], s["subtask_id"])
            out[key] = [(a["action"], a["target"]) for a in s["actions"]]
    return out


def gold_to_eval(gold_raw: Dict[Tuple[int, int], List[Tuple[str, Optional[str]]]]) \
        -> Dict[Tuple[int, int], List[Tuple[str, str]]]:
    """Strip terminator markers ((end)/(endsub)) from the gold side."""
    out: Dict[Tuple[int, int], List[Tuple[str, str]]] = {}
    for key, actions in gold_raw.items():
        kept: List[Tuple[str, str]] = []
        for verb, target in actions:
            if verb in ALLOWED_TERMINATORS:
                continue
            kept.append((verb, target if target is not None else ""))
        out[key] = kept
    return out


# ---------------------------------------------------------------------------
# Metric computation (plan item #2)
# ---------------------------------------------------------------------------

def _norm_target(s: str) -> str:
    t = s.strip().lower()
    # Row-header references are equivalent under all observed spellings:
    # gold legacy "Row_1", instruction wording "Row 1", UIA element name "1".
    # The runtime model resolves all three via target-spec aliases
    # (New_Error (3-5-2-TCP).lisp), so the comparator must not split them.
    m = re.fullmatch(r"row[ _](\d+)", t)
    if m:
        return m.group(1)
    return t


def _verbs_equiv(a: str, b: str) -> bool:
    # Treat Goto/Move as equivalent navigation verbs (gold uses both).
    nav = {"Goto", "Move"}
    if a in nav and b in nav:
        return True
    return a == b


def compute_extraction_metrics(
    generated: Dict[Tuple[int, int], List[Tuple[str, str]]],
    gold: Dict[Tuple[int, int], List[Tuple[str, str]]],
) -> Dict[str, Any]:
    gold_keys = set(gold.keys())
    gen_keys = set(generated.keys())

    matched_keys = gold_keys & gen_keys
    missing_keys = sorted(gold_keys - gen_keys)
    extra_keys = sorted(gen_keys - gold_keys)

    total_action_pairs = 0
    action_correct = 0
    target_correct = 0
    exact_correct = 0
    full_subtask_correct = 0
    per_subtask_detail: List[Dict[str, Any]] = []

    for key in sorted(matched_keys):
        g = gold[key]
        h = generated[key]
        n = max(len(g), len(h))
        all_exact = (len(g) == len(h))
        sub_action_ok = sub_target_ok = sub_exact = 0
        for i in range(n):
            total_action_pairs += 1
            if i < len(g) and i < len(h):
                gv, gt = g[i]
                hv, ht = h[i]
                a_ok = _verbs_equiv(gv, hv)
                t_ok = _norm_target(gt) == _norm_target(ht)
                if a_ok:
                    action_correct += 1
                    sub_action_ok += 1
                if t_ok:
                    target_correct += 1
                    sub_target_ok += 1
                if a_ok and t_ok:
                    exact_correct += 1
                    sub_exact += 1
                else:
                    all_exact = False
            else:
                all_exact = False
        if all_exact:
            full_subtask_correct += 1
        per_subtask_detail.append({
            "key": f"subtask{key[0]}_{key[1]}",
            "gold_len": len(g),
            "gen_len": len(h),
            "action_correct": sub_action_ok,
            "target_correct": sub_target_ok,
            "exact_correct": sub_exact,
            "sequence_match": all_exact,
        })

    def pct(num: int, denom: int) -> float:
        return round(100.0 * num / denom, 2) if denom else 0.0

    return {
        "subtasks_in_gold": len(gold_keys),
        "subtasks_generated": len(gen_keys),
        "subtasks_matched": len(matched_keys),
        "subtasks_missing": missing_keys,
        "subtasks_extra": extra_keys,
        "subtask_coverage_pct": pct(len(matched_keys), len(gold_keys)),
        "action_pairs_compared": total_action_pairs,
        "action_accuracy_pct": pct(action_correct, total_action_pairs),
        "target_accuracy_pct": pct(target_correct, total_action_pairs),
        "exact_match_pct": pct(exact_correct, total_action_pairs),
        "full_subtask_sequence_pct": pct(full_subtask_correct, len(gold_keys)),
        "per_subtask": per_subtask_detail,
    }


# ---------------------------------------------------------------------------
# Manual-authoring reduction (plan item #5)
# ---------------------------------------------------------------------------

def authoring_reduction_metrics(
    instructions: List[Dict[str, Any]],
    generated: Dict[str, Any],
) -> Dict[str, Any]:
    # "Traditional": every subtask + every action chunk is hand-authored.
    # "VisiTor pipeline": author the schema + verbs once; instructions in the
    # NL text are the only per-task human input.
    n_generated_subtasks = sum(len(t["subtasks"]) for t in generated["tasks"])
    n_generated_action_items = sum(
        len(s["actions"]) for t in generated["tasks"] for s in t["subtasks"]
    )
    n_nl_lines = sum(len(t["steps"]) for t in instructions)
    return {
        "natural_language_lines_authored": n_nl_lines,
        "generated_subtask_chunks": n_generated_subtasks,
        "generated_action_items": n_generated_action_items,
        "chunks_avoided_vs_manual": n_generated_subtasks + n_generated_action_items,
        # The schema-and-verb vocabulary is the only fixed-cost authoring:
        "fixed_cost_authoring": {
            "schema_definitions": 1,
            "verb_vocabulary_size": len(ALLOWED_ACTIONS),
        },
    }


# ---------------------------------------------------------------------------
# Execution success (plan item #3) -- stub
# ---------------------------------------------------------------------------
# Filling this in requires loading the generated .lisp into the ACT-R model
# (e.g. via Spreadsheet/running_model_v4.lisp) and inspecting the run trace.
# Wire it up by replacing the body with a subprocess call to your runner and
# parsing its log for completion / failure per subtask.
# ---------------------------------------------------------------------------

def run_execution_check(lisp_path: str) -> Dict[str, Any]:
    return {
        "implemented": False,
        "lisp_path": lisp_path,
        "note": (
            "Plug your ACT-R runner here. Recommended: load this file in place "
            "of the hand-authored subtask*_list setqs in Complete_Excel_Model.lisp "
            "and run the model; record completed_subtasks / failed_subtasks / "
            "manual_interventions."
        ),
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")


# Lowercased UIA element names from Spreadsheet/visicons.json; set only when
# --uia-context initial is active (None keeps the default path untouched).
EXCEL_UIA_NAMES: Optional[set] = None

_CELL_REF_RE = re.compile(r"^[A-Za-z]{1,2}\d{1,3}$")


def _is_cell_ref(target: str) -> bool:
    """Cell coordinates resolve through the grid, not the UIA scan."""
    return bool(_CELL_REF_RE.match(target.strip()))


def _excel_uia_metrics(gen_eval, gold_eval):
    from uia_grounding_common import compute_uia_metrics
    return compute_uia_metrics(
        gen_eval, gold_eval,
        initial_names_for_task=lambda _t: EXCEL_UIA_NAMES,
        exempt=_is_cell_ref,
    )


def run_variant(provider: str,
                client: Any,
                model: str,
                label: str,
                instructions: List[Dict[str, Any]],
                gold_eval: Dict[Tuple[int, int], List[Tuple[str, str]]]) -> Dict[str, Any]:
    print(f"\n--- variant={label} ---")
    raw, call_err = call_model(provider, client, model, instructions)
    model_slug = _slug(model)
    json_path = os.path.join(OUTPUT_DIR, f"{model_slug}__{label}{ARTIFACT_SUFFIX}.json")
    lisp_path = os.path.join(OUTPUT_DIR, f"{model_slug}__{label}{ARTIFACT_SUFFIX}.lisp")

    if raw is None:
        print(f"  call_failed: {call_err}")
        return {
            "variant": label,
            "schema_valid": False,
            "semantic_errors": [],
            "extraction_metrics": None,
            "authoring_reduction": None,
            "execution_check": None,
            "call_error": call_err,
            "artifacts": {"json": None, "lisp": None},
        }

    ok, errs = validate_semantic(raw)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
    if ok:
        with open(lisp_path, "w", encoding="utf-8") as f:
            f.write(to_lisp(raw))

    gen_eval = generated_to_eval(raw) if ok else {}
    extraction = compute_extraction_metrics(gen_eval, gold_eval) if ok else None
    authoring = authoring_reduction_metrics(instructions, raw) if ok else None
    execution = run_execution_check(lisp_path) if ok else None

    # UIA grounding metrics (only under --uia-context initial). Also score the
    # published none-condition artifact of the same model/variant, so the
    # report carries the with/without-context comparison without re-calling
    # any LLM on the baseline.
    uia_metrics = None
    uia_metrics_baseline_none = None
    if ok and EXCEL_UIA_NAMES is not None:
        uia_metrics = _excel_uia_metrics(gen_eval, gold_eval)
        base_path = os.path.join(OUTPUT_DIR, f"{model_slug}__{label}.json")
        if os.path.exists(base_path):
            try:
                with open(base_path, "r", encoding="utf-8") as f:
                    base_raw = json.load(f)
                if validate_semantic(base_raw)[0]:
                    uia_metrics_baseline_none = _excel_uia_metrics(
                        generated_to_eval(base_raw), gold_eval)
            except Exception as e:
                print(f"  baseline uia scoring skipped ({e})")

    print(f"  schema_valid={ok}  errors={len(errs)}")
    if extraction:
        print(
            f"  coverage={extraction['subtask_coverage_pct']}%  "
            f"action_acc={extraction['action_accuracy_pct']}%  "
            f"target_acc={extraction['target_accuracy_pct']}%  "
            f"exact_match={extraction['exact_match_pct']}%"
        )

    result = {
        "variant": label,
        "schema_valid": ok,
        "semantic_errors": errs,
        "extraction_metrics": extraction,
        "authoring_reduction": authoring,
        "execution_check": execution,
        "call_error": None,
        "artifacts": {"json": json_path, "lisp": lisp_path if ok else None},
    }
    if uia_metrics is not None:
        result["uia_metrics"] = uia_metrics
        result["uia_metrics_baseline_none"] = uia_metrics_baseline_none
    return result


def aggregate_robustness(per_variant: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Plan item #4: how stable are the metrics across paraphrases?"""
    ok = [v for v in per_variant if v.get("extraction_metrics")]
    if not ok:
        return {"variants_considered": 0}
    def col(name: str) -> List[float]:
        return [v["extraction_metrics"][name] for v in ok]
    def stats(xs: List[float]) -> Dict[str, float]:
        return {
            "min": round(min(xs), 2),
            "max": round(max(xs), 2),
            "mean": round(sum(xs) / len(xs), 2),
            "spread": round(max(xs) - min(xs), 2),
        }
    return {
        "variants_considered": len(ok),
        "subtask_coverage_pct": stats(col("subtask_coverage_pct")),
        "action_accuracy_pct": stats(col("action_accuracy_pct")),
        "target_accuracy_pct": stats(col("target_accuracy_pct")),
        "exact_match_pct": stats(col("exact_match_pct")),
        "full_subtask_sequence_pct": stats(col("full_subtask_sequence_pct")),
    }


def _load_env_file(path: str) -> None:
    """Tiny .env loader; only sets vars that aren't already in os.environ."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            os.environ[k] = v


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def _fmt_pct(x: Any) -> str:
    return f"{x:.2f}" if isinstance(x, (int, float)) else "-"


def write_markdown_report(report: Dict[str, Any], path: str) -> None:
    lines: List[str] = []
    lines.append("# Instruction -> ACT-R chunk pipeline: model comparison\n")
    lines.append(f"- Gold subtasks: **{report['gold_subtasks']}**")
    lines.append(f"- Variants per model: **{len(INSTRUCTION_SETS)}** "
                 f"({', '.join(INSTRUCTION_SETS.keys())})")
    lines.append(f"- Verbs: `{', '.join(ALLOWED_ACTIONS)}`")
    lines.append("- Targets compared lower-cased + stripped; `Goto` ≡ `Move`; "
                 "row references `Row_N` ≡ `Row N` ≡ `N`.\n")

    # Summary: mean across variants per model
    lines.append("## Summary (mean across variants)\n")
    lines.append("| Model | Provider | Variants OK | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for model_entry in report["per_model"]:
        ok_variants = [v for v in model_entry["per_variant"] if v.get("extraction_metrics")]
        if not ok_variants:
            err = model_entry.get("global_error") or (
                model_entry["per_variant"][0].get("call_error") if model_entry["per_variant"] else None
            )
            lines.append(
                f"| `{model_entry['model']}` | {model_entry['provider']} | "
                f"0/{len(model_entry['per_variant'])} | - | - | - | - | - "
                f"<br/>_error: {err or 'unknown'}_ |"
            )
            continue
        def m(k: str) -> float:
            return sum(v["extraction_metrics"][k] for v in ok_variants) / len(ok_variants)
        lines.append(
            f"| `{model_entry['model']}` | {model_entry['provider']} | "
            f"{len(ok_variants)}/{len(model_entry['per_variant'])} | "
            f"{_fmt_pct(m('subtask_coverage_pct'))} | "
            f"{_fmt_pct(m('action_accuracy_pct'))} | "
            f"{_fmt_pct(m('target_accuracy_pct'))} | "
            f"{_fmt_pct(m('exact_match_pct'))} | "
            f"{_fmt_pct(m('full_subtask_sequence_pct'))} |"
        )

    # Per-model, per-variant table
    lines.append("\n## Per-variant detail\n")
    for model_entry in report["per_model"]:
        lines.append(f"### `{model_entry['model']}` ({model_entry['provider']})\n")
        if model_entry.get("global_error"):
            lines.append(f"_global error: {model_entry['global_error']}_\n")
            continue
        lines.append("| Variant | Schema valid | Coverage % | Action acc % | Target acc % | Exact match % | Full subtask % | Mismatched subtasks |")
        lines.append("|---|:---:|---:|---:|---:|---:|---:|---|")
        for v in model_entry["per_variant"]:
            if v.get("extraction_metrics"):
                em = v["extraction_metrics"]
                misses = [d["key"] for d in em["per_subtask"] if not d["sequence_match"]]
                miss_cell = ", ".join(misses) if misses else "_none_"
                lines.append(
                    f"| {v['variant']} | {'OK' if v['schema_valid'] else 'NO'} | "
                    f"{_fmt_pct(em['subtask_coverage_pct'])} | "
                    f"{_fmt_pct(em['action_accuracy_pct'])} | "
                    f"{_fmt_pct(em['target_accuracy_pct'])} | "
                    f"{_fmt_pct(em['exact_match_pct'])} | "
                    f"{_fmt_pct(em['full_subtask_sequence_pct'])} | {miss_cell} |"
                )
            else:
                err = v.get("call_error") or ", ".join(v.get("semantic_errors", [])) or "-"
                lines.append(
                    f"| {v['variant']} | NO | - | - | - | - | - | _error: {err}_ |"
                )

        rob = model_entry.get("robustness")
        if rob and rob.get("variants_considered", 0) >= 2:
            lines.append("\n_Robustness across paraphrases (min / max / mean / spread):_\n")
            lines.append("| Metric | min | max | mean | spread |")
            lines.append("|---|---:|---:|---:|---:|")
            for key in ("subtask_coverage_pct", "action_accuracy_pct",
                        "target_accuracy_pct", "exact_match_pct",
                        "full_subtask_sequence_pct"):
                s = rob[key]
                lines.append(
                    f"| {key} | {_fmt_pct(s['min'])} | {_fmt_pct(s['max'])} | "
                    f"{_fmt_pct(s['mean'])} | {_fmt_pct(s['spread'])} |"
                )
        lines.append("")

    # Authoring reduction (same for every successful run on a given variant,
    # so pull from any model that succeeded on `original`).
    lines.append("## Authoring reduction (variant = original)\n")
    for model_entry in report["per_model"]:
        for v in model_entry["per_variant"]:
            if v["variant"] == "original" and v.get("authoring_reduction"):
                ar = v["authoring_reduction"]
                lines.append(f"_From `{model_entry['model']}`:_")
                lines.append(
                    f"- NL lines authored: **{ar['natural_language_lines_authored']}**"
                )
                lines.append(
                    f"- Generated subtask chunks: **{ar['generated_subtask_chunks']}**"
                )
                lines.append(
                    f"- Generated action items: **{ar['generated_action_items']}**"
                )
                lines.append(
                    f"- Chunks/items avoided vs manual authoring: "
                    f"**{ar['chunks_avoided_vs_manual']}**\n"
                )
                break
        else:
            continue
        break

    # UIA-grounding section — emitted only when uia_metrics exist (i.e. the
    # report came from a --uia-context initial run); the default report stays
    # byte-identical.
    has_uia = any(v.get("uia_metrics")
                  for m in report["per_model"]
                  for v in m.get("per_variant", []))
    if has_uia:
        lines.append("\n## UIA grounding (context = initial Excel scan)\n")
        lines.append("Resolvability: % of generated Goto/Select targets that "
                     "case-insensitively equal a UIA element name in "
                     "`Spreadsheet/visicons.json`. Cell references (letter+digit) "
                     "are exempt — they resolve through the grid, not the scan. "
                     "The no-context column re-scores the published baseline "
                     "artifacts of the same model/variant.\n")
        gold_ref = report.get("gold_uia_reference")
        lines.append("| Model | Variant | Resolvability (UIA ctx) % | Resolvability (no ctx) % | Fallback correct | Grounding failures | Unresolved |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        if gold_ref:
            lines.append(
                f"| _gold reference_ | - | {_fmt_pct(gold_ref['resolvability_initial_pct'])} | "
                f"{_fmt_pct(gold_ref['resolvability_initial_pct'])} | "
                f"{gold_ref['fallback_correct']} | {gold_ref['grounding_failure']} | "
                f"{gold_ref['unresolved_initial']} |")
        for m in report["per_model"]:
            for v in m.get("per_variant", []):
                um = v.get("uia_metrics")
                if not um:
                    continue
                base = v.get("uia_metrics_baseline_none")
                base_pct = _fmt_pct(base["resolvability_initial_pct"]) if base else "-"
                lines.append(
                    f"| `{m['model']}` | {v['variant']} | "
                    f"{_fmt_pct(um['resolvability_initial_pct'])} | {base_pct} | "
                    f"{um['fallback_correct']} | {um['grounding_failure']} | "
                    f"{um['unresolved_initial']} |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Instruction -> ACT-R chunk pipeline")
    parser.add_argument("--providers", default="",
                        help="comma list to restrict run, e.g. 'openrouter' or 'openai,gemini'")
    parser.add_argument("--models", default="",
                        help="comma list of exact model ids to restrict run")
    parser.add_argument("--prune-failed", action="store_true",
                        help="drop models with zero successful variants from the report")
    parser.add_argument("--or-retries", type=int, default=10,
                        help="OpenRouter max retries per call")
    parser.add_argument("--or-backoff", type=int, default=60,
                        help="OpenRouter backoff seconds between retries")
    parser.add_argument("--uia-context", choices=["none", "initial"],
                        default="none",
                        help="'initial' injects the pruned Spreadsheet/visicons.json "
                             "(Excel-open UIA scan) into the prompt with a grounding "
                             "instruction, and writes artifacts/reports with a "
                             "__uia-initial / _uia-initial suffix. 'none' (default) "
                             "reproduces the published evaluation unchanged.")
    args = parser.parse_args()
    only_providers = {p.strip() for p in args.providers.split(",") if p.strip()}
    only_models = {m.strip() for m in args.models.split(",") if m.strip()}

    global OR_RETRIES, OR_BACKOFF_S
    OR_RETRIES = args.or_retries
    OR_BACKOFF_S = args.or_backoff

    _load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    gold_raw = parse_lisp_subtasks(GOLD_LISP)
    gold_eval = gold_to_eval(gold_raw)
    print(f"gold subtasks parsed: {len(gold_eval)}")

    global UIA_CONTEXT_BLOCK, ARTIFACT_SUFFIX, EXCEL_UIA_NAMES
    report_suffix = ""
    gold_uia_reference = None
    if args.uia_context == "initial":
        from uia_grounding_common import (
            element_names, load_elements, prune_elements, render_uia_block)
        vis_path = os.path.join("Spreadsheet", "visicons.json")
        elements = load_elements(vis_path)
        pruned, truncated = prune_elements(elements)
        if truncated:
            print(f"uia context: {truncated} element(s) truncated from the prompt")
        block = render_uia_block(
            pruned, "at the start of the task (Excel is open on the workbook)")
        block += (
            "\nNote: spreadsheet CELL references (e.g. \"B7\") are grid "
            "coordinates that resolve through a different mechanism — keep "
            "them exactly as written in the instructions. The UI_ELEMENTS "
            "grounding applies to menu / ribbon / dialog items only.\n")
        UIA_CONTEXT_BLOCK = block
        ARTIFACT_SUFFIX = "__uia-initial"
        EXCEL_UIA_NAMES = element_names(elements)
        report_suffix = "_uia-initial"
        gold_uia_reference = _excel_uia_metrics(gold_eval, gold_eval)
        print(f"uia context: {len(pruned)} pruned elements in prompt, "
              f"{len(EXCEL_UIA_NAMES)} distinct names for scoring; gold "
              f"resolvability {gold_uia_reference['resolvability_initial_pct']}%")

    selected = [
        (prov, mdl) for prov, mdl in MODELS
        if (not only_providers or prov in only_providers)
        and (not only_models or mdl in only_models)
    ]
    if only_providers or only_models:
        print(f"filtered to {len(selected)} model(s): "
              f"{', '.join(m for _, m in selected) or '(none)'}")

    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    openai_client = OpenAI(api_key=openai_key) if openai_key else None
    gemini_client = (
        # 300s request timeout: "high demand" spells can hang a request
        # indefinitely; a timeout turns that into a retryable error. The
        # all-14-task Excel prompt regularly needs >120s under load.
        google_genai.Client(
            api_key=gemini_key,
            http_options=google_genai_types.HttpOptions(timeout=300_000))
        if (gemini_key and _HAS_GEMINI) else None
    )
    openrouter_client = (
        OpenAI(api_key=openrouter_key, base_url=OPENROUTER_BASE_URL)
        if openrouter_key else None
    )

    json_path = os.path.join(OUTPUT_DIR, f"metrics_report{report_suffix}.json")
    md_path = os.path.join(OUTPUT_DIR, f"model_comparison{report_suffix}.md")

    # When filtered, retain previously-saved models we're NOT re-running so a
    # partial/interrupted run never clobbers stable results.
    kept: List[Dict[str, Any]] = []
    if (only_providers or only_models) and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                prev = json.load(f)
            fresh = {m for _, m in selected}
            kept = [m for m in prev.get("per_model", []) if m["model"] not in fresh]
            print(f"retaining {len(kept)} previously-run model(s)")
        except Exception as e:
            print(f"could not read previous report ({e}); starting fresh")

    order = {m: i for i, (_, m) in enumerate(MODELS)}

    def has_success(m: Dict[str, Any]) -> bool:
        return any(v.get("extraction_metrics") for v in m.get("per_variant", []))

    def flush(per_model: List[Dict[str, Any]]) -> None:
        merged = sorted(per_model + kept, key=lambda m: order.get(m["model"], 1_000))
        if args.prune_failed:
            merged = [m for m in merged if has_success(m)]
        report = {
            "gold_subtasks": len(gold_eval),
            "models_evaluated": [m["model"] for m in merged],
            "variants": list(INSTRUCTION_SETS.keys()),
            "per_model": merged,
        }
        if args.uia_context != "none":
            report["uia_context"] = args.uia_context
            report["gold_uia_reference"] = gold_uia_reference
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        write_markdown_report(report, md_path)

    per_model: List[Dict[str, Any]] = []
    for provider, model in selected:
        print(f"\n=== model: {model} ({provider}) ===")
        if provider == "openai":
            client = openai_client
            if client is None:
                per_model.append({
                    "provider": provider, "model": model,
                    "global_error": "OPENAI_API_KEY missing",
                    "per_variant": [],
                })
                continue
        elif provider == "gemini":
            if not _HAS_GEMINI:
                per_model.append({
                    "provider": provider, "model": model,
                    "global_error": "google-genai SDK not installed",
                    "per_variant": [],
                })
                continue
            if gemini_client is None:
                per_model.append({
                    "provider": provider, "model": model,
                    "global_error": "GEMINI_API_KEY (or GOOGLE_API_KEY) missing",
                    "per_variant": [],
                })
                continue
            client = gemini_client
        elif provider == "openrouter":
            if openrouter_client is None:
                per_model.append({
                    "provider": provider, "model": model,
                    "global_error": "OPENROUTER_API_KEY missing",
                    "per_variant": [],
                })
                continue
            client = openrouter_client
        else:
            per_model.append({
                "provider": provider, "model": model,
                "global_error": f"unknown provider {provider}",
                "per_variant": [],
            })
            continue

        per_variant: List[Dict[str, Any]] = []
        for label, instr in INSTRUCTION_SETS.items():
            per_variant.append(
                run_variant(provider, client, model, label, instr, gold_eval)
            )
            time.sleep(1)

        per_model.append({
            "provider": provider,
            "model": model,
            "per_variant": per_variant,
            "robustness": aggregate_robustness(per_variant),
        })
        flush(per_model)  # checkpoint after each model so partial runs survive

    flush(per_model)
    print(f"\nwrote JSON  -> {json_path}")
    print(f"wrote MD    -> {md_path}")


if __name__ == "__main__":
    main()
