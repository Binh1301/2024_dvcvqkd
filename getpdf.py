try:
    import pymupdf as fitz  # PyMuPDF (preferred modern import)
except ModuleNotFoundError:
    try:
        import fitz  # PyMuPDF (legacy import)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "PyMuPDF is not available. Install it with: python -m pip install --upgrade pymupdf"
        ) from exc

input_pdf = "paper.pdf"
output_txt = "paper_text.txt"

doc = fitz.open(input_pdf)

with open(output_txt, "w", encoding="utf-8") as f:
    for i, page in enumerate(doc):
        text = page.get_text("text")
        f.write(f"\n--- Page {i+1} ---\n\n")
        f.write(text)

print(f"Saved extracted text to: {output_txt}")
