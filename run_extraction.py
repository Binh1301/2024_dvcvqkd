#!/usr/bin/env python3
"""
DIRECT PDF EXTRACTION - Test libraries and extract equations
User requirement: Extract directly from PDF, not from code files
Target: Eq. (3)-(11), (16)-(20), (28)-(33)
"""

import sys
import os

# Set working directory
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

pdf_file = "2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

print("=" * 90)
print("DIRECT PDF EXTRACTION TEST")
print("=" * 90)
print(f"\nWorking directory: {os.getcwd()}")
print(f"PDF file: {pdf_file}")
print(f"PDF exists: {os.path.exists(pdf_file)}")
print(f"PDF size: {os.path.getsize(pdf_file) / (1024*1024):.2f} MB\n")

# STEP 1: TEST AVAILABLE LIBRARIES
print("=" * 90)
print("STEP 1: TESTING PDF EXTRACTION LIBRARIES")
print("=" * 90)

libraries_ok = []

try:
    import fitz
    print("✓ PyMuPDF (fitz) - available")
    libraries_ok.append('fitz')
except ImportError:
    print("✗ PyMuPDF (fitz) - NOT installed")

try:
    import pdfplumber
    print("✓ pdfplumber - available")
    libraries_ok.append('pdfplumber')
except ImportError:
    print("✗ pdfplumber - NOT installed")

try:
    import pypdf
    print("✓ pypdf - available")
    libraries_ok.append('pypdf')
except ImportError:
    print("✗ pypdf - NOT installed")

try:
    import pytesseract
    print("✓ pytesseract (OCR) - available")
    libraries_ok.append('pytesseract')
except ImportError:
    print("✗ pytesseract (OCR) - NOT installed")

if not libraries_ok:
    print("\n✗ ERROR: No PDF libraries available!")
    sys.exit(1)

print(f"\n✓ Proceeding with available libraries: {libraries_ok}\n")

# STEP 2: EXTRACT TEXT USING FITZ IF AVAILABLE
if 'fitz' in libraries_ok:
    print("=" * 90)
    print("STEP 2: EXTRACTING TEXT WITH PYMUPDF")
    print("=" * 90 + "\n")
    
    import fitz
    import re
    
    doc = fitz.open(pdf_file)
    print(f"PDF opened successfully")
    print(f"Number of pages: {doc.page_count}\n")
    
    # Extract all text from all pages
    all_pages_text = {}
    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        text = page.get_text()
        all_pages_text[page_idx] = text
        print(f"  Page {page_idx + 1}: {len(text)} characters")
    
    doc.close()
    
    # STEP 3: SEARCH FOR EQUATION NUMBERS
    print("\n" + "=" * 90)
    print("STEP 3: SEARCHING FOR EQUATION NUMBERS")
    print("=" * 90 + "\n")
    
    target_eqs = set(list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34)))
    print(f"Target equations: {sorted(target_eqs)}")
    print(f"Total target: {len(target_eqs)} equations\n")
    
    # Find equations using regex pattern for "(N)"
    eq_pattern = re.compile(r'\((\d+)\)')
    found_equations = {}  # eq_num -> [(page, context), ...]
    
    for page_idx, text in all_pages_text.items():
        for match in eq_pattern.finditer(text):
            try:
                eq_num = int(match.group(1))
                if eq_num in target_eqs:
                    # Extract context around match
                    start = max(0, match.start() - 250)
                    end = min(len(text), match.end() + 600)
                    context = text[start:end]
                    
                    if eq_num not in found_equations:
                        found_equations[eq_num] = []
                    
                    found_equations[eq_num].append({
                        'page': page_idx + 1,
                        'match_pos': match.start(),
                        'context': context
                    })
            except ValueError:
                pass
    
    print(f"Found {len(found_equations)} distinct equation numbers\n")
    
    for eq_num in sorted(found_equations.keys()):
        instances = found_equations[eq_num]
        pages_list = [str(inst['page']) for inst in instances]
        print(f"  Eq. ({eq_num}): Page(s) {', '.join(pages_list)} - {len(instances)} instance(s)")
    
    # STEP 4: REPORT MISSING EQUATIONS
    missing_eqs = target_eqs - set(found_equations.keys())
    if missing_eqs:
        print(f"\n✗ MISSING equations: {sorted(missing_eqs)}")
    else:
        print(f"\n✓ ALL target equations found!")
    
    # STEP 5: SEARCH FOR KEY TERMS
    print("\n" + "=" * 90)
    print("STEP 4: SEARCHING FOR KEY TECHNICAL TERMS")
    print("=" * 90 + "\n")
    
    key_terms = {
        'chi symbol': r'χ|χ_|\\chi',
        'xi symbol': r'ξ|\\xi|xi',
        'chi_line': r'χ_line|χ_l|chi_line',
        'chi_tot': r'χ_tot|χ_t|chi_tot',
        'homodyne': r'homodyne|Homodyne',
        'heterodyne': r'heterodyne|Heterodyne',
        'detector noise': r'detector\s+noise|detector\s+-\s+noise',
        'thermal noise': r'thermal\s+noise'
    }
    
    term_matches = {}
    
    for page_idx, text in all_pages_text.items():
        for term_name, pattern in key_terms.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                if term_name not in term_matches:
                    term_matches[term_name] = []
                
                for match in matches:
                    start = max(0, match.start() - 150)
                    end = min(len(text), match.end() + 150)
                    context = text[start:end]
                    
                    term_matches[term_name].append({
                        'page': page_idx + 1,
                        'context': context
                    })
    
    for term_name in sorted(key_terms.keys()):
        if term_name in term_matches:
            pages = set([m['page'] for m in term_matches[term_name]])
            print(f"✓ '{term_name}': Found on page(s) {sorted(pages)}")
        else:
            print(f"✗ '{term_name}': Not found")
    
    # STEP 5: DETAILED EQUATION EXTRACTION
    print("\n" + "=" * 90)
    print("STEP 5: DETAILED EQUATION EXTRACTION")
    print("=" * 90)
    
    for eq_num in sorted(found_equations.keys()):
        instances = found_equations[eq_num]
        for idx, inst in enumerate(instances, 1):
            print(f"\n--- EQ. ({eq_num}) - Instance {idx} - PAGE {inst['page']} ---")
            context = inst['context'].replace('\n', ' ').strip()
            # Limit output
            if len(context) > 500:
                context = context[:500] + " ..."
            print(context)
    
    # STEP 6: SUMMARY
    print("\n" + "=" * 90)
    print("EXTRACTION SUMMARY")
    print("=" * 90)
    print(f"\nLibrary used: PyMuPDF (fitz)")
    print(f"Total pages processed: {len(all_pages_text)}")
    print(f"Equations found: {len(found_equations)} / {len(target_eqs)}")
    print(f"Success rate: {100 * len(found_equations) / len(target_eqs):.1f}%")
    if missing_eqs:
        print(f"Missing: {sorted(missing_eqs)}")
    print(f"Key terms found: {len(term_matches)} / {len(key_terms)}")
    print(f"OCR fallback needed: NO")
    
    # Save raw extracted text for reference
    output_file = "extracted_pdf_raw_text.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for page_idx in sorted(all_pages_text.keys()):
            f.write(f"\n\n{'=' * 80}\n")
            f.write(f"PAGE {page_idx + 1}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(all_pages_text[page_idx])
    
    print(f"\n✓ Raw extracted text saved to: {output_file}")

print("\n" + "=" * 90)
print("EXTRACTION COMPLETE")
print("=" * 90)
