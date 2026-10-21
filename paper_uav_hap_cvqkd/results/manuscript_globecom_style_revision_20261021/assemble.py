"""Produce a single-file manuscript without changing its protected sections."""
from pathlib import Path

OUT=Path(__file__).resolve().parent


def main():
    if (OUT/'validation/final_receipt.json').exists():
        raise FileExistsError('Sealed manuscript is immutable')
    prefix=(OUT/'validation/protected_prefix.tex.txt').read_bytes()
    body=(OUT/'revised_sections.tex').read_bytes()
    bibliography=(OUT/'validation/protected_bibliography.tex.txt').read_bytes()
    assert body.count(b'\\section{')==4
    assert b'\\includegraphics' not in prefix+bibliography
    (OUT/'main.tex').write_bytes(prefix+body+bibliography)
    print('Single-file main.tex assembled; front matter, system model and bibliography preserved byte-for-byte')


if __name__=='__main__':main()
