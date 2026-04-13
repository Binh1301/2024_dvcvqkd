import re
try:
    import pymupdf as fitz  # PyMuPDF (preferred modern import)
except ModuleNotFoundError:
    try:
        import fitz  # PyMuPDF (legacy import)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "PyMuPDF is not available. Install it with: python -m pip install --upgrade pymupdf"
        ) from exc

pdf_path = "paper.pdf"
out_path = "formulas.txt"

doc = fitz.open(pdf_path)
results = []

for pno, page in enumerate(doc, 1):
    text = page.get_text("text")
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Dòng có số công thức (1), (2)... và chứa ký hiệu toán
        if re.search(r"\(\d+\)\s*$", s) and re.search(r"[=+\-*/^_<>≤≥∑∫]", s):
            results.append(f"[Page {pno}] {s}")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"Saved {len(results)} formulas to {out_path}")
