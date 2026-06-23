"""Run docTR (default detector+recognizer) over EN images -> <base>.doctr.txt."""
import sys
from pathlib import Path

from doctr.io import DocumentFile
from doctr.models import ocr_predictor

EN = Path(sys.argv[1])
model = ocr_predictor(pretrained=True)
for img in sorted(EN.glob("*.png")):
    doc = DocumentFile.from_images(str(img))
    res = model(doc)
    lines = []
    for page in res.pages:
        for block in page.blocks:
            for line in block.lines:
                lines.append(" ".join(w.value for w in line.words))
    text = "\n".join(lines)
    (EN / f"{img.name}.doctr.txt").write_text(text, encoding="utf-8")
    print("doctr", img.name, len(text))
