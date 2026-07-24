"""Shared definitions for the 2x2x2 spreadsheet ablation factorial.

Cells in canonical order 000, 100, 010, 001, 110, 101, 011, 111 with
V = visual search, B = batched formula typing (look-backs), C = error +
correction/checking package (July 20 perceptual/final-check model).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

SPREADSHEET = Path(__file__).resolve().parent
REPO = SPREADSHEET.parent

# Released layout: the model .lisp sources live under
# models/spreadsheet_excel/, not next to these analysis scripts (they were
# flat in the original monorepo). Override with EVISITOR_MODELS_DIR.
MODELS_DIR = Path(os.environ.get(
    "EVISITOR_MODELS_DIR", str(REPO / "models" / "spreadsheet_excel")))
# Human data root (IRB-restricted; request access -- see REPRODUCE.md).
HUMAN_DATA_ROOT = Path(os.environ.get(
    "EVISITOR_HUMAN_DATA_ROOT", r"G:\ExcelDataAnalysis"))

BATCH_ROOT = Path(os.environ.get(
    "ABLATION_BATCH_ROOT",
    str(SPREADSHEET / "logs" /
        "ablation_2x2x2_150_july20_correct_typo_rates"),
))

# A batch can pin a newer production model without rewriting the reusable
# factorial wrappers.  The historical July-20 source remains the default so
# archived analysis commands continue to work when the environment is unset.
BASE_MODEL_SOURCE = os.environ.get(
    "ABLATION_MODEL_SOURCE", "New_Error (3-5-2-TCP).lisp")

# (code, V, B, C, wrapper file)
CELLS = [
    ("000", 0, 0, 0, "Ablation_Perfect.lisp"),
    ("100", 1, 0, 0, "Ablation_Visual_Search_Only.lisp"),
    ("010", 0, 1, 0, "Ablation_Batched_Formula_Typing.lisp"),
    ("001", 0, 0, 1, "Ablation_Correction_Checking.lisp"),
    ("110", 1, 1, 0, "Ablation_Visual_Plus_Batched.lisp"),
    ("101", 1, 0, 1, "Ablation_Visual_Plus_Checking.lisp"),
    ("011", 0, 1, 1, "Ablation_Batched_Plus_Checking.lisp"),
    ("111", 1, 1, 1, "Ablation_Full_Realistic.lisp"),
]

def cell_label(wrapper: str) -> str:
    return wrapper[:-len(".lisp")]

N_RUNS = int(os.environ.get("ABLATION_N_RUNS", "150"))
N_RESERVE = 50
SEED_RNG_SEED = 20260720
SUBTASKS = list(range(1, 15))

# Human-calibrated configuration every C=1 manifest must show.
# The formula visual-check probability defaults to the historical 0.40 so
# archived analysis commands still validate; a batch run at a different rate
# (e.g. the 0.90 human-backspace-fit build) sets ABLATION_CHECK_PROB so the
# manifest validator expects the value that was actually run.
C1_FORMULA_TYPO_RATE = 0.034
C1_WORD_TYPO_RATE = 0.063
C1_CHECK_PROBABILITY = float(os.environ.get("ABLATION_CHECK_PROB", "0.40"))
C1_WORD_IMMEDIATE = 0.85

# Frozen source files hashed into source_hashes.json.
FROZEN_SOURCES = [
    BASE_MODEL_SOURCE,
    "fucntion_new_tcp.lisp",
    "Ablation_support.lisp",
    "running_model_v4.lisp",
    "Complete_error_model_tcp.lisp",
    "Visicon_generator_V3.lisp",
    "Run_Ablation_2x2x2_Shard.lisp",
] + [wrapper for (_c, _v, _b, _k, wrapper) in CELLS]

# Human data (see analyze_ablation_fc.py / w1_per_task_check_rate.py)
HUMAN_MEANS_CSV = HUMAN_DATA_ROOT / "HumanCompletionTime.csv"
HUMAN_WINDOWS_CSV = (HUMAN_DATA_ROOT / "Human Data" / "eye_tracking_analysis"
                     / "task_time_windows_from_breakdown.csv")
HUMAN_EXCLUDED_SUBJECTS = ["Subject1", "Subject14"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_source_hashes() -> dict:
    return {name: sha256_file(MODELS_DIR / name) for name in FROZEN_SOURCES}


def load_source_hashes(root: Path = BATCH_ROOT) -> dict:
    with open(root / "source_hashes.json") as f:
        return json.load(f)["hashes"]


def check_sources_frozen(root: Path = BATCH_ROOT) -> None:
    """Raise if any frozen source changed since the batch was set up."""
    recorded = load_source_hashes(root)
    current = compute_source_hashes()
    drift = {k: (recorded.get(k), current.get(k))
             for k in set(recorded) | set(current)
             if recorded.get(k) != current.get(k)}
    if drift:
        raise SystemExit(
            "Source drift since freeze — batch is not a clean test:\n"
            + "\n".join(f"  {k}: recorded {a} != current {b}"
                        for k, (a, b) in sorted(drift.items())))


def load_seeds(root: Path = BATCH_ROOT) -> list[int]:
    with open(root / "seed_list.txt") as f:
        return [int(line) for line in f if line.strip()]


def expected_manifest(code: str, v: int, b: int, c: int) -> dict:
    exp = {
        "visual_search": bool(v),
        "formula_lookback": bool(b),
        "error_correction": bool(c),
        "visual_error_checking_enabled": bool(c),
        "visual_error_checking_default": bool(c),
        "guaranteed_final_check_enabled": bool(c),
    }
    if c:
        exp.update(
            formula_visual_check_probability=C1_CHECK_PROBABILITY,
            formula_typo_rate=C1_FORMULA_TYPO_RATE,
            word_typo_rate=C1_WORD_TYPO_RATE,
            forced_typing_error_rate=None,
            word_immediate_check_probability=C1_WORD_IMMEDIATE,
        )
    else:
        exp.update(
            formula_visual_check_probability=0.0,
            formula_typo_rate=0.0,
            word_typo_rate=0.0,
            forced_typing_error_rate=None,
            word_immediate_check_probability=0.0,
        )
    return exp


def manifest_matches(manifest: dict, code: str, v: int, b: int, c: int,
                     tol: float = 1e-6) -> list[str]:
    """Return a list of mismatch descriptions (empty if the manifest is clean)."""
    problems = []
    for key, want in expected_manifest(code, v, b, c).items():
        got = manifest.get(key, "<missing>")
        if isinstance(want, float):
            ok = isinstance(got, (int, float)) and abs(got - want) <= tol
        else:
            ok = got == want
        if not ok:
            problems.append(f"{key}: expected {want!r}, got {got!r}")
    return problems
