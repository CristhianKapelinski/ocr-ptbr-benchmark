"""Run PaddleOCR (PP-OCR, English) over EN images -> <base>.paddleocr.txt."""
import sys
from pathlib import Path

from paddleocr import PaddleOCR

EN = Path(sys.argv[1])
ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
for img in sorted(EN.glob("*.png")):
    result = ocr.ocr(str(img), cls=True)
    lines = []
    for page in result or []:
        for det in page or []:
            lines.append(det[1][0])
    text = "\n".join(lines)
    (EN / f"{img.name}.paddleocr.txt").write_text(text, encoding="utf-8")
    print("paddleocr", img.name, len(text))
