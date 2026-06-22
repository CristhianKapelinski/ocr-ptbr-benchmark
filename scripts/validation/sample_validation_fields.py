#!/usr/bin/env python3
"""Reproducible random sample of reconstructed-gold form fields for human validation.

Draws a SEED-fixed sample of N fields from the scored (non-empty value) fields across
all forms, so a human can estimate the field-level accuracy of the image-reconstructed
forms gold with a Wilson confidence interval. Same seed -> identical sample.

The pool is sorted deterministically before sampling, so the draw does not depend on the
filesystem's glob order. Output: validation_sample.json (the sampled fields grouped by
form). The field values carry PII, so this file stays local; only the resulting accuracy
and CI (PII-free) go in the paper.
"""
import glob
import json
import os
import random
import re

SEED = 0
N = 250
HERE = os.path.dirname(os.path.abspath(__file__))
GOLD_DIR = os.path.join(HERE, "gold_rebuilt")


def idx_of(path):
    m = re.search(r"pt_val_(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else -1


def build_pool():
    """All scored fields (non-empty stripped value), matching the FVR scorer's rule."""
    pool = []
    for fp in glob.glob(os.path.join(GOLD_DIR, "*.fields.json")):
        form = idx_of(fp)
        with open(fp, encoding="utf-8") as fh:
            fields = json.load(fh)
        for pos, f in enumerate(fields):
            value = str(f.get("value", "")).strip()
            if not value:
                continue
            pool.append({"form": form, "pos": pos, "key": f.get("key", ""), "value": value})
    pool.sort(key=lambda r: (r["form"], r["pos"]))  # deterministic order before sampling
    return pool


def main():
    pool = build_pool()
    rng = random.Random(SEED)
    sample = rng.sample(pool, min(N, len(pool)))

    forms = {}
    for r in sorted(sample, key=lambda r: (r["form"], r["pos"])):
        forms.setdefault(str(r["form"]), []).append(
            {"pos": r["pos"], "key": r["key"], "value": r["value"]}
        )

    out = {
        "seed": SEED,
        "n_target": N,
        "n_pool": len(pool),
        "n_sampled": len(sample),
        "n_forms_touched": len(forms),
        "forms": forms,
    }
    with open(os.path.join(HERE, "validation_sample.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    n_forms_pool = len({r["form"] for r in pool})
    print(
        f"pool={len(pool)} scored fields across {n_forms_pool} forms; "
        f"sampled {len(sample)} across {len(forms)} forms; seed={SEED}"
    )


if __name__ == "__main__":
    main()
