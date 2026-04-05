#!/usr/bin/env python
"""
Direct PDF Extraction Task - One-shot analysis
Requirements: Extract equations (3-11, 16-20, 28-33), special definitions, and OCR status
Libraries: fitz/pdfplumber/pypdf/PyPDF2 - direct extraction only
"""

import sys
import os
import re
from pathlib import Path

# ============================================================================
# PART 1: Library Import Status
# ============================================================================
print("=" * 80)
print("PART 1: LIBRARY IMPORT STATUS")
print("=" * 80)

libraries_status = {}
fitz_available = False
pdfplumber_available = False
pypdf_available = False
PyPDF2_available = False

try:
    import fitz
    fitz_available = True
    libraries_status['fitz (PyMuPDF)'] = f'✓ AVAILABLE v{fitz.version[0]}'
    print(f"✓ fitz (PyMuPDF): {fitz.version}")
except ImportError as e:
    libraries_status['fitz (PyMuPDF)'] = f'✗ MISSING'
    print(f"✗ fitz (PyMuPDF): NOT INSTALLED - {e}")

try:
    import pdfplumber
    pdfplumber_available = True
    ver = getattr(pdfplumber, '__version__', 'unknown')
    libraries_status['pdfplumber'] = f'✓ AVAILABLE v{ver}'
    print(f"✓ pdfplumber: v{ver}")
except ImportError as e:
    libraries_status['pdfplumber'] = f'✗ MISSING'
    print(f"✗ pdfplumber: NOT INSTALLED - {e}")

try:
    import PyPDF2
    PyPDF2_available = True
    ver = getattr(PyPDF2, '__version__', 'unknown')
    libraries_status['PyPDF2'] = f'✓ AVAILABLE v{ver}'
    print(f"✓ PyPDF2: v{ver}")
except ImportError as e:
    libraries_status['PyPDF2'] = f'✗ MISSING'
    print(f"✗ PyPDF2: NOT INSTALLED - {e}")

try:
    import pypdf
    pypdf_available = True
    ver = getattr(pypdf, '__version__', 'unknown')
    libraries_status['pypdf'] = f'✓ AVAILABLE v{ver}'
    print(f"✓ pypdf: v{ver}")
except ImportError as e:
    libraries_status['pypdf'] = f'✗ MISSING'
    print(f"✗ pypdf: NOT INSTALLED - {e}")

# ============================================================================
# PART 2: Find PDF file
# ============================================================================
print("\n" + "=" * 80)
print("PART 2: PDF FILE LOCATION")
print("=" * 80)

pdf_files = list(Path(".").glob("*.pdf"))
if not pdf_files:
    print("✗ NO PDF FILES FOUND IN CURRENT DIRECTORY")
    sys.exit(1)

pdf_path = str(pdf_files[0])
print(f"✓ PDF Found: {pdf_path}")
print(f"  File Size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")

# ============================================================================
# PART 3: Extraction attempts with each library
# ============================================================================
print("\n" + "=" * 80)
print("PART 3: DIRECT EXTRACTION BY LIBRARY")
print("=" * 80)

extraction_results = {}

# --- FITZ EXTRACTION ---
if fitz_available:
    print("\n[FITZ - PyMuPDF]")
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"✓ Opened successfully: {total_pages} pages")
        
        fitz_text = ""
        ocr_detected_fitz = False
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            fitz_text += f"\n[PAGE {page_num + 1}]\n{text}\n"
        
        doc.close()
        
        # Check for OCR markers
        if "confidence" in fitz_text.lower() or "ocr" in fitz_text.lower():
            ocr_detected_fitz = True
        
        extraction_results['fitz'] = {
            'status': 'SUCCESS',
            'total_pages': total_pages,
            'text_length': len(fitz_text),
            'ocr_detected': ocr_detected_fitz,
            'text': fitz_text[:5000]  # First 5000 chars
        }
        print(f"  Total text extracted: {len(fitz_text)} chars")
        print(f"  OCR detected: {ocr_detected_fitz}")
        
    except Exception as e:
        extraction_results['fitz'] = {'status': 'FAILED', 'error': str(e)}
        print(f"✗ Error: {e}")

# --- PDFPLUMBER EXTRACTION ---
if pdfplumber_available:
    print("\n[PDFPLUMBER]")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"✓ Opened successfully: {total_pages} pages")
            
            pdfplumber_text = ""
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pdfplumber_text += f"\n[PAGE {page_num + 1}]\n{text}\n"
                else:
                    pdfplumber_text += f"\n[PAGE {page_num + 1}]\n[NO TEXT]\n"
            
            # Check for OCR
            ocr_detected_pp = page.extract_text_simple() != page.extract_text() if hasattr(page, 'extract_text_simple') else False
            
            extraction_results['pdfplumber'] = {
                'status': 'SUCCESS',
                'total_pages': total_pages,
                'text_length': len(pdfplumber_text),
                'ocr_detected': ocr_detected_pp,
                'text': pdfplumber_text[:5000]
            }
            print(f"  Total text extracted: {len(pdfplumber_text)} chars")
            print(f"  OCR detected: {ocr_detected_pp}")
            
    except Exception as e:
        extraction_results['pdfplumber'] = {'status': 'FAILED', 'error': str(e)}
        print(f"✗ Error: {e}")

# --- PYPDF EXTRACTION ---
if pypdf_available:
    print("\n[PYPDF]")
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            print(f"✓ Opened successfully: {total_pages} pages")
            
            pypdf_text = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pypdf_text += f"\n[PAGE {page_num + 1}]\n{text}\n"
                else:
                    pypdf_text += f"\n[PAGE {page_num + 1}]\n[NO TEXT]\n"
            
            extraction_results['pypdf'] = {
                'status': 'SUCCESS',
                'total_pages': total_pages,
                'text_length': len(pypdf_text),
                'ocr_detected': False,
                'text': pypdf_text[:5000]
            }
            print(f"  Total text extracted: {len(pypdf_text)} chars")
            
    except Exception as e:
        extraction_results['pypdf'] = {'status': 'FAILED', 'error': str(e)}
        print(f"✗ Error: {e}")

# --- PYPDF2 EXTRACTION ---
if PyPDF2_available:
    print("\n[PyPDF2]")
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            print(f"✓ Opened successfully: {total_pages} pages")
            
            pypdf2_text = ""
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    pypdf2_text += f"\n[PAGE {page_num + 1}]\n{text}\n"
                else:
                    pypdf2_text += f"\n[PAGE {page_num + 1}]\n[NO TEXT]\n"
            
            extraction_results['PyPDF2'] = {
                'status': 'SUCCESS',
                'total_pages': total_pages,
                'text_length': len(pypdf2_text),
                'ocr_detected': False,
                'text': pypdf2_text[:5000]
            }
            print(f"  Total text extracted: {len(pypdf2_text)} chars")
            
    except Exception as e:
        extraction_results['PyPDF2'] = {'status': 'FAILED', 'error': str(e)}
        print(f"✗ Error: {e}")

# ============================================================================
# PART 4: Coverage Statistics & Best Library Selection
# ============================================================================
print("\n" + "=" * 80)
print("PART 4: COVERAGE STATISTICS & BEST LIBRARY")
print("=" * 80)

successful_libs = [lib for lib, res in extraction_results.items() if res.get('status') == 'SUCCESS']

if successful_libs:
    print(f"\n✓ Successful extractions: {', '.join(successful_libs)}")
    
    coverage_stats = {}
    for lib in successful_libs:
        text_len = extraction_results[lib]['text_length']
        coverage_stats[lib] = text_len
    
    best_lib = max(coverage_stats.items(), key=lambda x: x[1])
    print(f"\n✓ BEST LIBRARY: {best_lib[0]} ({best_lib[1]} chars)")
    
    for lib in sorted(coverage_stats.keys()):
        chars = coverage_stats[lib]
        print(f"  - {lib}: {chars} characters")
else:
    print("✗ NO SUCCESSFUL EXTRACTIONS")
    sys.exit(1)

# ============================================================================
# PART 5: Equation Extraction (3-11, 16-20, 28-33)
# ============================================================================
print("\n" + "=" * 80)
print("PART 5: EQUATION EXTRACTION")
print("=" * 80)

# Use the best library's text
best_text = extraction_results[best_lib[0]]['text']

# Pattern to find equations
equation_pattern = re.compile(r'Eq\.\s*\(?(\d+)\)?', re.IGNORECASE)

target_equations = list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
target_equations = sorted(set(target_equations))

print(f"\nTarget equations: {target_equations}")
print(f"\nSearching in {best_lib[0]} extraction...")

found_equations = {}

for eq_num in target_equations:
    pattern = rf'Eq\.?\s*\(?\s*{eq_num}\s*\)?|equation\s*{eq_num}|({eq_num})\s*[=:]'
    matches = re.finditer(pattern, best_text, re.IGNORECASE)
    
    match_count = 0
    snippets = []
    for match in matches:
        match_count += 1
        start = max(0, match.start() - 100)
        end = min(len(best_text), match.end() + 200)
        snippet = best_text[start:end].strip()
        snippets.append(snippet)
    
    if snippets:
        found_equations[eq_num] = {'count': match_count, 'snippets': snippets[:1]}
    else:
        found_equations[eq_num] = {'status': 'UNVERIFIABLE'}

print("\nEquation Detection Summary:")
verified_count = sum(1 for v in found_equations.values() if 'count' in v)
print(f"✓ Verified equations: {verified_count}/{len(target_equations)}")
print(f"✗ Unverifiable: {len(target_equations) - verified_count}")

print("\nDetailed results:")
for eq_num in sorted(target_equations):
    if eq_num in found_equations:
        if 'count' in found_equations[eq_num]:
            print(f"  Eq.({eq_num}): FOUND ({found_equations[eq_num]['count']} matches)")
            if found_equations[eq_num]['snippets']:
                snippet = found_equations[eq_num]['snippets'][0][:150]
                print(f"    Preview: {snippet}...")
        else:
            print(f"  Eq.({eq_num}): UNVERIFIABLE")
    else:
        print(f"  Eq.({eq_num}): NOT FOUND")

# ============================================================================
# PART 6: Special Definitions (xi, χ_line, χ_tot, detector-noise)
# ============================================================================
print("\n" + "=" * 80)
print("PART 6: SPECIAL DEFINITIONS")
print("=" * 80)

special_defs = {
    'xi': r'\bxi\b|\ξ',
    'χ_line': r'χ.*?line|χ_line|\χ_line',
    'χ_tot': r'χ.*?tot|χ_tot|\χ_tot',
    'detector-noise': r'detector.*?noise|noise.*?detector'
}

print("\nSearching for special definitions...")
found_defs = {}

for def_name, pattern in special_defs.items():
    matches = list(re.finditer(pattern, best_text, re.IGNORECASE))
    if matches:
        found_defs[def_name] = len(matches)
        print(f"✓ {def_name}: FOUND ({len(matches)} occurrences)")
        
        # Get first occurrence with context
        match = matches[0]
        start = max(0, match.start() - 80)
        end = min(len(best_text), match.end() + 80)
        context = best_text[start:end].strip()
        print(f"  Context: {context[:120]}...")
    else:
        found_defs[def_name] = 0
        print(f"✗ {def_name}: NOT FOUND")

# ============================================================================
# PART 7: OCR Usage Detection
# ============================================================================
print("\n" + "=" * 80)
print("PART 7: OCR USAGE DETECTION")
print("=" * 80)

ocr_results = {}
for lib in successful_libs:
    ocr_status = extraction_results[lib].get('ocr_detected', False)
    ocr_results[lib] = "YES" if ocr_status else "NO (direct text extraction)"
    print(f"  {lib}: OCR = {ocr_results[lib]}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("FINAL SUMMARY REPORT")
print("=" * 80)

print(f"\n1. Library Import Status:")
for lib, status in libraries_status.items():
    print(f"   {lib}: {status}")

print(f"\n2. Best Library for Extraction: {best_lib[0]}")
print(f"   Coverage: {best_lib[1]} characters extracted")

print(f"\n3. Equations Found: {verified_count}/{len(target_equations)}")

print(f"\n4. Special Definitions Found: {len([v for v in found_defs.values() if v > 0])}/4")

print(f"\n5. OCR Status:")
for lib, status in ocr_results.items():
    print(f"   {lib}: {status}")

print("\n" + "=" * 80)
