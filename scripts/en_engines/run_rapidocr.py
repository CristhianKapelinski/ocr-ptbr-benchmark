"""Run RapidOCR (ONNXRuntime, English-capable) over EN images -> <base>.rapidocr.txt."""
import sys
from pathlib import Path

from rapidocr_onnxruntime import RapidOCR

EN = Path(sys.argv[1])
engine = RapidOCR()
for img in sorted(EN.glob("*.png")):
    result, _ = engine(str(img))
    lines = [r[1] for r in result] if result else []
    text = "\n".join(lines)
    (EN / f"{img.name}.rapidocr.txt").write_text(text, encoding="utf-8")
    print("rapidocr", img.name, len(text))
