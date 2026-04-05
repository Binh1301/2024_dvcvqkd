#!/usr/bin/env python3
"""
PDF extraction script for CV-QKD satellite paper
"""
import os
import sys
import json
import re
from pathlib import Path

# Change to target directory
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# ============= STEP 1: Test Imports =============
import_results = {}
import_order = ['fitz', 'pdfplumber', 'pypdf', 'PyPDF2', 'pytesseract']

for lib in import_order:
    try:
        if lib == 'fitz':
            import fitz
        elif lib == 'pdfplumber':
            import pdfplumber
        elif lib == 'pypdf':
            import pypdf
        elif lib == 'PyPDF2':
            import PyPDF2
        elif lib == 'pytesseract':
            import pytesseract
        import_results[lib] = 'SUCCESS'
    except ImportError as e:
        import_results[lib] = f'FAILED: {str(e)}'

# ============= Locate PDF =============
pdf_name = "2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"
pdf_path = None

for f in os.listdir('.'):
    if f.endswith('.pdf'):
        print(f"Found PDF: {f}")
        if '2024' in f and 'QKD' in f and 'LEO' in f:
            pdf_path = f
            break

if not pdf_path:
    for f in os.listdir('.'):
        if 'CV-QKD' in f and f.endswith('.pdf'):
            pdf_path = f
            break

print(f"\nTarget PDF: {pdf_path}")
if not pdf_path or not os.path.exists(pdf_path):
    print(f"ERROR: PDF not found at {pdf_path}")
    print(f"Files in directory: {os.listdir('.')[:20]}")
    sys.exit(1)

# ============= STEP 2-3: Extract text page by page =============
method_evidence = []
pages_text = {}
page_count = 0

# Try FITZ
if import_results['fitz'] == 'SUCCESS':
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        method_evidence.append(f"fitz (PyMuPDF): Opened PDF with {page_count} pages")
        
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            pages_text[page_num + 1] = text
        
        print(f"FITZ: Extracted {page_count} pages")
    except Exception as e:
        method_evidence.append(f"fitz failed: {str(e)}")

# Try pdfplumber
if import_results['pdfplumber'] == 'SUCCESS':
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if not page_count:
                page_count = len(pdf.pages)
                method_evidence.append(f"pdfplumber: {page_count} pages detected")
            
            for page_num, page in enumerate(pdf.pages, 1):
                if page_num not in pages_text:
                    pages_text[page_num] = ""
                text = page.extract_text()
                if text:
                    pages_text[page_num] += text
        
        print(f"PDFPLUMBER: Enhanced text extraction")
    except Exception as e:
        method_evidence.append(f"pdfplumber failed: {str(e)}")

# Try pypdf
if import_results['pypdf'] == 'SUCCESS':
    try:
        import pypdf
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            if not page_count:
                page_count = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages, 1):
                if page_num not in pages_text:
                    pages_text[page_num] = ""
                text = page.extract_text()
                if text:
                    pages_text[page_num] += text
        
        print(f"PYPDF: Enhanced text extraction")
    except Exception as e:
        method_evidence.append(f"pypdf failed: {str(e)}")

# ============= STEP 3: Search for equation labels =============
target_equations = {
    str(i): None for i in list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
}

equations_found = {}

# Search patterns for equations
eq_patterns = {str(i): [f'\\({i}\\)', f'(Eq.{i})', f'Equation {i}'] for i in target_equations.keys()}

for page_num, text in sorted(pages_text.items()):
    # Search each equation
    for eq_num in target_equations.keys():
        if eq_num not in equations_found:
            # Search for equation label
            for pattern in eq_patterns[eq_num]:
                if pattern in text or pattern.replace('\\', '') in text:
                    # Find snippet around match
                    idx = text.find(pattern.replace('\\(', '(').replace('\\)', ')'))
                    if idx == -1:
                        idx = text.find(f"({eq_num})")
                    
                    if idx >= 0:
                        start = max(0, idx - 150)
                        end = min(len(text), idx + 200)
                        snippet = text[start:end].strip()
                        
                        equations_found[eq_num] = {
                            'status': 'FOUND',
                            'page': page_num,
                            'snippet': snippet,
                            'source': 'text_extraction'
                        }
                        break
            
            # Also search with looser pattern
            if eq_num not in equations_found:
                pattern = f"({eq_num})"
                if pattern in text:
                    idx = text.find(pattern)
                    start = max(0, idx - 150)
                    end = min(len(text), idx + 200)
                    snippet = text[start:end].strip()
                    
                    equations_found[eq_num] = {
                        'status': 'FOUND',
                        'page': page_num,
                        'snippet': snippet,
                        'source': 'text_extraction'
                    }

# ============= STEP 4: Search for special terms =============
search_terms = {
    'xi': r'\bxi\b|\bχ\b',
    'chi_line': r'χ.*line|chi.*line',
    'chi_tot': r'χ.*tot|chi.*tot',
    'homodyne_noise': r'homodyne.*noise',
    'heterodyne_noise': r'heterodyne.*noise',
    'detector_noise': r'detector.*noise'
}

definitions_found = []

for page_num, text in sorted(pages_text.items()):
    for term, pattern in search_terms.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            snippet = text[start:end].strip()
            
            definitions_found.append({
                'term': term,
                'page': page_num,
                'snippet': snippet,
                'source': 'text_extraction'
            })

# ============= STEP 5: OCR Fallback (if available) =============
ocr_uncertain = []

if import_results['pytesseract'] == 'SUCCESS':
    try:
        import pytesseract
        from PIL import Image
        
        # Try OCR on pages likely to have equations (if FITZ available)
        if import_results['fitz'] == 'SUCCESS':
            import fitz
            doc = fitz.open(pdf_path)
            
            # Pages known to have many equations
            likely_pages = [p for p in range(min(3, doc.page_count)) for _ in range(1)]  # First few pages
            
            for page_num in likely_pages[:3]:
                try:
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("ppm")
                    
                    from io import BytesIO
                    img = Image.open(BytesIO(img_data))
                    text = pytesseract.image_to_string(img)
                    
                    if text.strip():
                        ocr_uncertain.append(f"Page {page_num + 1} OCR: {text[:200]}")
                except Exception as e:
                    pass
    except Exception as e:
        pass

# ============= Build Results =============
result = {
    'method_evidence': import_results,
    'extraction_sources': method_evidence,
    'total_pages': page_count,
    'equations': {eq_num: equations_found.get(eq_num, {'status': 'UNVERIFIABLE', 'page': None, 'snippet': None, 'source': 'none'}) 
                  for eq_num in target_equations.keys()},
    'definitions': definitions_found[:50],  # Limit to 50
    'ocr_uncertain': ocr_uncertain,
    'missing': [eq_num for eq_num in target_equations.keys() if eq_num not in equations_found]
}

print("\n" + "="*60)
print("JSON RESULT:")
print("="*60)
print(json.dumps(result, indent=2, ensure_ascii=False))
