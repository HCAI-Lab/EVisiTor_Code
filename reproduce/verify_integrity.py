"""Verify the published factorial models and the archived draft34 sources."""

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "analysis" / "batch_provenance"
DRAFT34 = PROVENANCE / "draft34_20260722_checkprob_sweep"


def verify(directory: Path, manifest: Path, key: str) -> bool:
    hashes = json.loads(manifest.read_bytes())[key]
    mismatches = []
    for name, expected in hashes.items():
        path = directory / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            mismatches.append(path.relative_to(ROOT))

    for path in mismatches:
        print(f"Missing or mismatched: {path}", file=sys.stderr)
    matched = len(hashes) - len(mismatches)
    print(f"{directory.relative_to(ROOT)}: {matched}/{len(hashes)} match")
    return not mismatches


if __name__ == "__main__":
    models_ok = verify(
        ROOT / "models" / "spreadsheet_excel",
        PROVENANCE / "draft36_check090_factorial" / "source_hashes.json",
        "hashes",
    )
    archive_ok = verify(
        DRAFT34 / "frozen_sources", DRAFT34 / "design_manifest.json", "source_sha256"
    )
    sys.exit(0 if models_ok and archive_ok else 1)
