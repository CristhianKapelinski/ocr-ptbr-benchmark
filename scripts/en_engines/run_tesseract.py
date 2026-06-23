"""Run Tesseract over the EN control images, writing <base>.tesseract.txt.

Mirrors the from-scratch classical entry: vendor-default Tesseract on CPU,
English model, full-page transcription. Output is the raw page text; the FVR
scorer alphanumeric-normalizes it, so line layout is irrelevant.
"""
import sys
from pathlib import Path

import pytesseract
from PIL import Image

EN = Path(sys.argv[1])
for img in sorted(EN.glob("*.png")):
    if "." in img.stem:  # skip prediction txt-derived names; png stems are pure ids
        pass
    text = pytesseract.image_to_string(Image.open(img), lang="eng")
    (EN / f"{img.name}.tesseract.txt").write_text(text, encoding="utf-8")
    print("tesseract", img.name, len(text))
