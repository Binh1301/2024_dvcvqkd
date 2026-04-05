#!/usr/bin/env python3
"""
Comprehensive PDF equation extraction for satellite QKD paper.
Target equations: (3)-(11), (16)-(20), (28)-(33)
"""

import sys
import re
import json
from pathlib import Path

# Determine which libraries are available
libs_available = {}
extraction_results = {}

print("=" * 80)
print("TESTING EXTRACTION LIBRARIES")
print("=" * 80)

# Test PyMuPDF (fitz)
try:
    import fitz
    libs_available['PyMuPDF'] = True
    print("✓ PyMuPDF (fitz) available")
except ImportError:
    libs_available['PyMuPDF'] = False
    print("✗ PyMuPDF (fitz) NOT available")

# Test pdfplumber
try:
    import pdfplumber
    libs_available['pdfplumber'] = True
    print("✓ pdfplumber available")
except ImportError:
    libs_available['pdfplumber'] = False
    print("✗ pdfplumber NOT available")

# Test pypdf
try:
    import pypdf
    libs_available['pypdf'] = True
    print("✓ pypdf available")
except ImportError:
    libs_available['pypdf'] = False
    print("✗ pypdf NOT available")

# Test pytesseract for OCR
try:
    import pytesseract
    import cv2
    libs_available['OCR'] = True
    print("✓ pytesseract (OCR) available")
except ImportError:
    libs_available['OCR'] = False
    print("✗ pytesseract (OCR) NOT available")

pdf_path = Path("2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf")

if not pdf_path.exists():
    print(f"\n✗ PDF file not found: {pdf_path}")
    sys.exit(1)

print(f"\n✓ PDF file found: {pdf_path}")
print(f"  File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")

# Target equations to find
target_equations = set(
    list(range(3, 12)) +  # 3-11
    list(range(16, 21)) + # 16-20
    list(range(28, 34))   # 28-33
)

print(f"\nTarget equation numbers: {sorted(target_equations)}")
print("\n" + "=" * 80)
print("EXTRACTION PHASE")
print("=" * 80)

# ==============================================================================
# PYMUPDF EXTRACTION
# ==============================================================================
if libs_available['PyMuPDF']:
    print("\n--- PyMuPDF (fitz) Extraction ---\n")
    try:
        doc = fitz.open(str(pdf_path))
        print(f"Total pages: {doc.page_count}\n")
        
        extraction_results['pymupdf'] = {}
        
        # Extract text from all pages
        all_text = {}
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            all_text[page_num] = text
        
        # Search for equation patterns and equation numbers
        equation_pattern = re.compile(r'\((\d+)\)')
        
        for page_num in range(doc.page_count):
            text = all_text[page_num]
            
            # Find all equation numbers on this page
            matches = equation_pattern.finditer(text)
            for match in matches:
                eq_num_str = match.group(1)
                try:
                    eq_num = int(eq_num_str)
                    if eq_num in target_equations:
                        start = max(0, match.start() - 200)
                        end = min(len(text), match.end() + 500)
                        context = text[start:end].strip()
                        
                        if eq_num not in extraction_results['pymupdf']:
                            extraction_results['pymupdf'][eq_num] = []
                        
                        extraction_results['pymupdf'][eq_num].append({
                            'page': page_num + 1,
                            'context': context[:600]  # Limit length
                        })
                except ValueError:
                    pass
        
        # Search for key terms
        print("Key terms search (PyMuPDF):")
        for page_num in range(doc.page_count):
            text = all_text[page_num]
            if any(term in text for term in ['χ', 'xi', 'χ_line', 'χ_tot', 'homodyne', 'heterodyne', 'detector noise']):
                print(f"  Page {page_num + 1}: Found relevant terms")
        
        print(f"\nPyMuPDF found {len(extraction_results['pymupdf'])} target equations")
        
        doc.close()
    except Exception as e:
        print(f"✗ PyMuPDF extraction failed: {e}")

# ==============================================================================
# PDFPLUMBER EXTRACTION
# ==============================================================================
if libs_available['pdfplumber']:
    print("\n--- pdfplumber Extraction ---\n")
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            print(f"Total pages: {len(pdf.pages)}\n")
            
            extraction_results['pdfplumber'] = {}
            
            all_text = {}
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text[page_num] = text
            
            equation_pattern = re.compile(r'\((\d+)\)')
            
            for page_num in range(len(pdf.pages)):
                if page_num in all_text:
                    text = all_text[page_num]
                    matches = equation_pattern.finditer(text)
                    
                    for match in matches:
                        eq_num_str = match.group(1)
                        try:
                            eq_num = int(eq_num_str)
                            if eq_num in target_equations:
                                start = max(0, match.start() - 200)
                                end = min(len(text), match.end() + 500)
                                context = text[start:end].strip()
                                
                                if eq_num not in extraction_results['pdfplumber']:
                                    extraction_results['pdfplumber'][eq_num] = []
                                
                                extraction_results['pdfplumber'][eq_num].append({
                                    'page': page_num + 1,
                                    'context': context[:600]
                                })
                        except ValueError:
                            pass
            
            print(f"pdfplumber found {len(extraction_results['pdfplumber'])} target equations")
    except Exception as e:
        print(f"✗ pdfplumber extraction failed: {e}")

# ==============================================================================
# PYPDF EXTRACTION
# ==============================================================================
if libs_available['pypdf']:
    print("\n--- pypdf Extraction ---\n")
    try:
        with open(str(pdf_path), 'rb') as f:
            reader = pypdf.PdfReader(f)
            print(f"Total pages: {len(reader.pages)}\n")
            
            extraction_results['pypdf'] = {}
            
            all_text = {}
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    all_text[page_num] = text
            
            equation_pattern = re.compile(r'\((\d+)\)')
            
            for page_num in range(len(reader.pages)):
                if page_num in all_text:
                    text = all_text[page_num]
                    matches = equation_pattern.finditer(text)
                    
                    for match in matches:
                        eq_num_str = match.group(1)
                        try:
                            eq_num = int(eq_num_str)
                            if eq_num in target_equations:
                                start = max(0, match.start() - 200)
                                end = min(len(text), match.end() + 500)
                                context = text[start:end].strip()
                                
                                if eq_num not in extraction_results['pypdf']:
                                    extraction_results['pypdf'][eq_num] = []
                                
                                extraction_results['pypdf'][eq_num].append({
                                    'page': page_num + 1,
                                    'context': context[:600]
                                })
                        except ValueError:
                            pass
            
            print(f"pypdf found {len(extraction_results['pypdf'])} target equations")
    except Exception as e:
        print(f"✗ pypdf extraction failed: {e}")

# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "=" * 80)
print("EXTRACTION SUMMARY")
print("=" * 80)

print("\nLibraries available:", {k: v for k, v in libs_available.items() if v})
print("Libraries that succeeded:", [k for k, v in extraction_results.items() if v])

# Consolidate results
all_equations = {}
for lib_name, equations in extraction_results.items():
    for eq_num, instances in equations.items():
        if eq_num not in all_equations:
            all_equations[eq_num] = []
        for instance in instances:
            all_equations[eq_num].append({
                'lib': lib_name,
                'page': instance['page'],
                'context': instance['context']
            })

if all_equations:
    print(f"\nFound {len(all_equations)} distinct target equations across {len(extraction_results)} libraries")
    print("\nEquations found:")
    for eq_num in sorted(all_equations.keys()):
        instances = all_equations[eq_num]
        print(f"  Eq. ({eq_num}): {len(instances)} instance(s) at page(s) {', '.join(str(i['page']) for i in instances)}")
else:
    print("\n⚠ No target equations found in direct extraction")

# Save detailed results
output_file = Path("extraction_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'libraries_available': libs_available,
        'target_equations': sorted(list(target_equations)),
        'found_equations': {str(k): v for k, v in all_equations.items()}
    }, f, indent=2, ensure_ascii=False)

print(f"\nDetailed results saved to: {output_file}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
if not all_equations or len(all_equations) < len(target_equations):
    print("\n⚠ Some equations were not found or text is unreadable.")
    print("Consider running OCR extraction on specific pages if OCR library is available.")
