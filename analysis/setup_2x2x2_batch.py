"""Set up the 2x2x2 factorial batch root: archived seed list + frozen source hashes.

Idempotent-by-refusal: if seed_list.txt or source_hashes.json already exist it
refuses to overwrite them (a batch's seeds and freeze record are immutable).
Run with --refreeze to recompute hashes BEFORE any runs exist (e.g. after a
reviewed source fix during smoke testing).
"""

import datetime
import json
import sys

import numpy as np

from ablation_2x2x2_common import (
    BATCH_ROOT, N_RUNS, N_RESERVE, SEED_RNG_SEED, CELLS, cell_label,
    compute_source_hashes,
)


def main() -> None:
    refreeze = "--refreeze" in sys.argv
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)

    seed_path = BATCH_ROOT / "seed_list.txt"
    if seed_path.exists():
        print(f"Seed list already exists, keeping it: {seed_path}")
    else:
        rng = np.random.default_rng(SEED_RNG_SEED)
        seeds = rng.integers(1, 2**31 - 1, size=N_RUNS + N_RESERVE)
        seed_path.write_text("\n".join(str(int(s)) for s in seeds) + "\n")
        print(f"Wrote {N_RUNS} primary + {N_RESERVE} reserve seeds to {seed_path}")

    hash_path = BATCH_ROOT / "source_hashes.json"
    if hash_path.exists() and not refreeze:
        print(f"Freeze record already exists, keeping it: {hash_path}")
        return
    if refreeze:
        assembled = [BATCH_ROOT / cell_label(w) for (_c, _v, _b, _k, w) in CELLS]
        if any(p.exists() for p in assembled):
            raise SystemExit("Refusing --refreeze: assembled cell folders already exist.")
    record = {
        "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "seed_rng_seed": SEED_RNG_SEED,
        "n_runs": N_RUNS,
        "n_reserve": N_RESERVE,
        "hashes": compute_source_hashes(),
    }
    hash_path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Froze {len(record['hashes'])} sources into {hash_path}")


if __name__ == "__main__":
    main()
