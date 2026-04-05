#!/usr/bin/env python3
"""
Direct PDF extraction - find equations (3)-(11), (16)-(20), (28)-(33)
"""
import sys
import re
from pathlib import Path

pdf_path = Path("2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf")

if not pdf_path.exists():
    print(f"ERROR: PDF not found at {pdf_path}")
    sys.exit(1)

print("=" * 80)
print("TESTING PDF EXTRACTION LIBRARIES")
print("=" * 80 + "\n")

# Test all libraries
libraries_status = {}
pdf_text_by_lib = {}

# ===== PyMuPDF (fitz) =====
try:
    import fitz
    doc = fitz.open(str(pdf_path))
    num_pages = doc.page_count
    print(f"✓ PyMuPDF (fitz): SUCCESS - {num_pages} pages")
    libraries_status['PyMuPDF'] = 'OK'
    
    # Extract all text
    full_text = {}
    for pn in range(num_pages):
        full_text[pn] = doc[pn].get_text()
    pdf_text_by_lib['PyMuPDF'] = full_text
    doc.close()
except ImportError:
    print("✗ PyMuPDF (fitz): Not installed")
    libraries_status['PyMuPDF'] = 'NOT_INSTALLED'
except Exception as e:
    print(f"✗ PyMuPDF (fitz): ERROR - {e}")
    libraries_status['PyMuPDF'] = 'ERROR'

# ===== pdfplumber =====
try:
    import pdfplumber
    with pdfplumber.open(str(pdf_path)) as pdf:
        num_pages = len(pdf.pages)
        print(f"✓ pdfplumber: SUCCESS - {num_pages} pages")
        libraries_status['pdfplumber'] = 'OK'
        
        # Extract all text
        full_text = {}
        for pn, page in enumerate(pdf.pages):
            full_text[pn] = page.extract_text() or ""
        pdf_text_by_lib['pdfplumber'] = full_text
except ImportError:
    print("✗ pdfplumber: Not installed")
    libraries_status['pdfplumber'] = 'NOT_INSTALLED'
except Exception as e:
    print(f"✗ pdfplumber: ERROR - {e}")
    libraries_status['pdfplumber'] = 'ERROR'

# ===== pypdf =====
try:
    import pypdf
    with open(str(pdf_path), 'rb') as f:
        reader = pypdf.PdfReader(f)
        num_pages = len(reader.pages)
        print(f"✓ pypdf: SUCCESS - {num_pages} pages")
        libraries_status['pypdf'] = 'OK'
        
        # Extract all text
        full_text = {}
        for pn, page in enumerate(reader.pages):
            full_text[pn] = page.extract_text() or ""
        pdf_text_by_lib['pypdf'] = full_text
except ImportError:
    print("✗ pypdf: Not installed")
    libraries_status['pypdf'] = 'NOT_INSTALLED'
except Exception as e:
    print(f"✗ pypdf: ERROR - {e}")
    libraries_status['pypdf'] = 'ERROR'

# ===== pytesseract =====
try:
    import pytesseract
    import cv2
    print("✓ pytesseract: Available (OCR)")
    libraries_status['pytesseract'] = 'OK'
except ImportError:
    print("✗ pytesseract: Not installed")
    libraries_status['pytesseract'] = 'NOT_INSTALLED'
except Exception as e:
    print(f"✗ pytesseract: ERROR - {e}")
    libraries_status['pytesseract'] = 'ERROR'

print("\n" + "=" * 80)
print("EXTRACTION STATUS")
print("=" * 80 + "\n")

# Use the first successful library
best_lib = None
best_text = None
for lib in ['PyMuPDF', 'pdfplumber', 'pypdf']:
    if libraries_status.get(lib) == 'OK':
        best_lib = lib
        best_text = pdf_text_by_lib[lib]
        break

if not best_lib:
    print("ERROR: No PDF extraction library available")
    sys.exit(1)

print(f"Using: {best_lib}")
print(f"Total pages: {len(best_text)}\n")

# ===== SEARCH FOR TARGET EQUATIONS =====
target_eq_nums = set(list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34)))

print("=" * 80)
print("SEARCHING FOR EQUATION NUMBERS (3-11, 16-20, 28-33)")
print("=" * 80 + "\n")

# Regex to find equation references like "(3)" "(28)" etc
eq_ref_pattern = re.compile(r'\((\d+)\)')

found_equations = {}  # eq_num -> [(page, context), ...]

for page_num, text in best_text.items():
    # Find all parenthesized numbers
    for match in eq_ref_pattern.finditer(text):
        eq_str = match.group(1)
        try:
            eq_num = int(eq_str)
            if eq_num in target_eq_nums:
                # Extract context: 200 chars before and 500 after
                start_idx = max(0, match.start() - 200)
                end_idx = min(len(text), match.end() + 500)
                context = text[start_idx:end_idx]
                
                if eq_num not in found_equations:
                    found_equations[eq_num] = []
                
                found_equations[eq_num].append({
                    'page': page_num + 1,
                    'context': context
                })
        except ValueError:
            pass

# Report findings
print(f"Found {len(found_equations)} distinct target equation numbers\n")

# Sort and display
for eq_num in sorted(found_equations.keys()):
    instances = found_equations[eq_num]
    pages = [str(inst['page']) for inst in instances]
    print(f"Eq. ({eq_num}): Found on page(s) {', '.join(pages)}")

if len(found_equations) < len(target_eq_nums):
    missing = target_eq_nums - set(found_equations.keys())
    print(f"\nMissing equations: {sorted(missing)}")

print("\n" + "=" * 80)
print("EQUATION DETAILS")
print("=" * 80 + "\n")

for eq_num in sorted(found_equations.keys()):
    instances = found_equations[eq_num]
    for idx, inst in enumerate(instances, 1):
        print(f"\n--- Eq. ({eq_num}) - Instance {idx} - Page {inst['page']} ---")
        # Clean up context for display
        context_clean = inst['context'].replace('\n', ' ').strip()
        # Limit length
        if len(context_clean) > 400:
            context_clean = context_clean[:400] + "..."
        print(context_clean)

# ===== SEARCH FOR KEY TERMS =====
print("\n" + "=" * 80)
print("SEARCHING FOR KEY TECHNICAL TERMS")
print("=" * 80 + "\n")

search_terms = {
    'χ (chi)': r'χ|\\chi',
    'ξ (xi)': r'ξ|\\xi',
    'homodyne': r'homodyne',
    'heterodyne': r'heterodyne',
    'χ_line': r'χ_line|χ_l|\\chi_l',
    'χ_tot': r'χ_tot|χ_t|\\chi_t',
    'detector noise': r'detector\s+noise|detector-noise',
    'thermal noise': r'thermal\s+noise'
}

term_locations = {}

for page_num, text in best_text.items():
    for term_name, pattern in search_terms.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if term_name not in term_locations:
                term_locations[term_name] = []
            
            # Extract context
            start_idx = max(0, match.start() - 150)
            end_idx = min(len(text), match.end() + 150)
            context = text[start_idx:end_idx]
            
            term_locations[term_name].append({
                'page': page_num + 1,
                'context': context
            })

for term_name in search_terms.keys():
    if term_name in term_locations:
        instances = term_locations[term_name]
        pages = [str(inst['page']) for inst in instances]
        print(f"✓ {term_name}: Found on page(s) {', '.join(set(pages))}")
        # Show first occurrence
        first = instances[0]
        ctx = first['context'].replace('\n', ' ').strip()[:200]
        print(f"  Context: {ctx}...\n")
    else:
        print(f"✗ {term_name}: Not found\n")

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Library used: {best_lib}")
print(f"Equations found: {len(found_equations)} / {len(target_eq_nums)}")
print(f"Success rate: {100 * len(found_equations) / len(target_eq_nums):.1f}%")
if len(found_equations) < len(target_eq_nums):
    print(f"Missing: {sorted(target_eq_nums - set(found_equations.keys()))}")
