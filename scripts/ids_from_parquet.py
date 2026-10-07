#!/usr/bin/env python3
"""Materialize the identity-document axis from its public source.

The 50 identity documents scored in the paper are the 25 CNH and 25 RG rows of
the ``valid`` split of the Hugging Face dataset ``tech4humans/br-doc-extraction``
(whose images were sampled from the BID Dataset); the same split also holds 25
invoice (nota fiscal) rows, which are not identity documents and are skipped.
See the Erratum in README.md.

Each kept row becomes ``<out>/valid_<CNH|RG>_<NN>.<ext>`` plus a
``.fields.json`` gold in the list-of-``{"key", "value"}`` shape that
``ocr_bench.io.load_fvr_pairs`` reads. Field values are copied verbatim (dates
stay ``YYYY-MM-DD``; the scorer's date-aware matching expands them).

Usage: python3 scripts/ids_from_parquet.py <valid.parquet> <out_dir>
Requires pyarrow (e.g. ``pip install pyarrow`` or ``uv run --with pyarrow``).
"""
import json
import sys
from pathlib import Path


def _ext(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return "bin"


def main(parquet: str, out_dir: str) -> int:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        sys.stderr.write("pyarrow is required: pip install pyarrow "
                         "(or run with: uv run --with pyarrow ...)\n")
        return 2
    table = pq.read_table(parquet)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = {"cnh": 0, "rg": 0}
    for img, kind, resp in zip(table.column("image").to_pylist(),
                               table.column("type").to_pylist(),
                               table.column("response").to_pylist()):
        if kind not in count:          # invoices: not part of the identity axis
            continue
        data = img["bytes"]
        base = f"valid_{kind.upper()}_{count[kind]:02d}"
        count[kind] += 1
        (out / f"{base}.{_ext(data)}").write_bytes(data)
        rows = [{"key": k, "value": v} for k, v in json.loads(resp).items()
                if v not in (None, "")]
        (out / f"{base}.fields.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"identity axis: {count['cnh']} CNH + {count['rg']} RG -> {out}")
    return 0 if count == {"cnh": 25, "rg": 25} else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
