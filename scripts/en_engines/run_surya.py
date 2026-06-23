"""Run Surya (classic detection + recognition) over EN images -> <base>.surya.txt.

Targets surya-ocr 0.13.x, whose RecognitionPredictor()(images, langs,
det_predictor=...) returns one OCRResult per page with line-level text. This is
the lightweight detector+recognizer path that produced the committed RIB/HYB/IDs
Surya run of record (line-by-line text, not the 0.20 foundation-VLM HTML blocks),
so the EN cell is produced the same way as the rest of Surya's numbers.
"""
import sys
from pathlib import Path

from PIL import Image

from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor

EN = Path(sys.argv[1])
imgs = sorted(EN.glob("*.png"))

rec = RecognitionPredictor()
det = DetectionPredictor()

for img in imgs:
    im = Image.open(img).convert("RGB")
    preds = rec([im], [["en"]], det_predictor=det)
    lines = [ln.text for ln in preds[0].text_lines]
    text = "\n".join(lines)
    (EN / f"{img.name}.surya.txt").write_text(text, encoding="utf-8")
    print("surya", img.name, len(text), flush=True)
