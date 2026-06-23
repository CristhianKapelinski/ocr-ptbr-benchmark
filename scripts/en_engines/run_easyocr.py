"""Run EasyOCR (English) over the EN control images -> <base>.easyocr.txt."""
import sys
from pathlib import Path

import easyocr

EN = Path(sys.argv[1])
reader = easyocr.Reader(["en"], gpu=False)
for img in sorted(EN.glob("*.png")):
    lines = reader.readtext(str(img), detail=0, paragraph=False)
    text = "\n".join(lines)
    (EN / f"{img.name}.easyocr.txt").write_text(text, encoding="utf-8")
    print("easyocr", img.name, len(text))
