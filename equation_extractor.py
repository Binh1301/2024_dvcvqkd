#!/usr/bin/env python3
"""
Direct extraction of equations from CV-QKD PDF using multiple libraries.
Focus: Equations 3-11, 16-20, 28-33, noise terms (xi, χ_line, χ_tot), detector-noise definitions.
"""

import sys
import os
from pathlib import Path

pdf_path = r"e:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

print("=" * 80)
print("EQUATION EXTRACTION - CV-QKD PDF")
print("=" * 80)
print(f"Target PDF: {pdf_path}")
print(f"File exists: {os.path.exists(pdf_path)}")

if not os.path.exists(pdf_path):
    print("ERROR: PDF file not found!")
    sys.exit(1)

results = {
    "method_used": [],
    "equations": {},
    "variables": {},
    "noise_terms": {},
    "unverifiable": [],
    "missing": []
}

# ============================================================================
# METHOD 1: PyMuPDF (fitz)
# ============================================================================
print("\n" + "=" * 80)
print("METHOD 1: PyMuPDF (fitz)")
print("=" * 80)

try:
    import fitz
    print("✓ PyMuPDF imported successfully")
    results["method_used"].append("PyMuPDF")
    
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    print(f"✓ PDF opened. Total pages: {total_pages}")
    
    # Target equations to find
    target_eqs = list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
    
    # Search for equation patterns
    equation_markers = {
        f"Eq. {i}": None for i in target_eqs
    } | {
        f"Equation {i}": None for i in target_eqs
    } | {
        f"({i})": None for i in target_eqs
    }
    
    extracted_text = {}
    
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        extracted_text[page_num + 1] = text
        
        # Search for equation markers
        for marker in equation_markers.keys():
            if marker in text and equation_markers[marker] is None:
                equation_markers[marker] = page_num + 1
    
    # Extract text around equations
    print("\n[EXTRACTING EQUATION CONTENT]")
    
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for equation markers
            for eq_num in target_eqs:
                patterns = [f"Eq. {eq_num}", f"({eq_num})", f"Equation {eq_num}", f"equ. {eq_num}"]
                
                for pattern in patterns:
                    if pattern in line:
                        # Capture context: current line + next 2 lines
                        context = '\n'.join(lines[i:min(i+3, len(lines))])
                        
                        if f"Eq{eq_num}" not in results["equations"]:
                            results["equations"][f"Eq{eq_num}"] = {
                                "text": context.strip(),
                                "page": page_num + 1
                            }
                            print(f"  Found: Eq. {eq_num} (page {page_num + 1})")
            
            # Look for noise terms
            for term in ["xi", "χ_line", "χ_tot", "detector-noise", "homodyne", "heterodyne"]:
                if term in line.lower():
                    if term not in results["noise_terms"]:
                        results["noise_terms"][term] = {
                            "text": lines[i:min(i+2, len(lines))],
                            "page": page_num + 1
                        }
    
    doc.close()
    print(f"✓ PyMuPDF extraction complete")
    
except ImportError:
    print("✗ PyMuPDF not available")
except Exception as e:
    print(f"✗ PyMuPDF error: {e}")

# ============================================================================
# METHOD 2: pdfplumber
# ============================================================================
print("\n" + "=" * 80)
print("METHOD 2: pdfplumber")
print("=" * 80)

try:
    import pdfplumber
    print("✓ pdfplumber imported successfully")
    results["method_used"].append("pdfplumber")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"✓ PDF opened. Pages: {len(pdf.pages)}")
        
        print("\n[EXTRACTING EQUATION CONTENT - pdfplumber]")
        
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if text:
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    # Enhanced equation detection
                    for eq_num in range(3, 34):
                        patterns = [f"Eq. {eq_num}", f"({eq_num})", f"Equation {eq_num}"]
                        
                        for pattern in patterns:
                            if pattern in line:
                                # Extract full context
                                start = max(0, i - 1)
                                end = min(len(lines), i + 3)
                                context = '\n'.join(lines[start:end]).strip()
                                
                                eq_key = f"Eq{eq_num}"
                                if eq_key not in results["equations"]:
                                    results["equations"][eq_key] = {
                                        "text": context,
                                        "page": page_idx + 1,
                                        "source": "pdfplumber"
                                    }
                                    print(f"  Found: Eq. {eq_num} (page {page_idx + 1})")
                    
                    # Noise terms
                    for term in ["ξ", "χ", "detector", "homodyne", "heterodyne"]:
                        if term.lower() in line.lower():
                            if term not in results["noise_terms"]:
                                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+2)])
                                results["noise_terms"][term] = {
                                    "text": context,
                                    "page": page_idx + 1
                                }
    
    print(f"✓ pdfplumber extraction complete")
    
except ImportError:
    print("✗ pdfplumber not available")
except Exception as e:
    print(f"✗ pdfplumber error: {e}")

# ============================================================================
# METHOD 3: PyPDF2
# ============================================================================
print("\n" + "=" * 80)
print("METHOD 3: PyPDF2/pypdf")
print("=" * 80)

try:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    
    print("✓ PyPDF2/pypdf imported successfully")
    results["method_used"].append("PyPDF2")
    
    reader = PdfReader(pdf_path)
    print(f"✓ PDF opened. Pages: {len(reader.pages)}")
    
    print("\n[EXTRACTING EQUATION CONTENT - PyPDF2]")
    
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        
        if text:
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                for eq_num in range(3, 34):
                    patterns = [f"Eq. {eq_num}", f"({eq_num})"]
                    
                    for pattern in patterns:
                        if pattern in line:
                            context = '\n'.join(lines[max(0, i-1):min(len(lines), i+2)]).strip()
                            eq_key = f"Eq{eq_num}"
                            
                            if eq_key not in results["equations"]:
                                results["equations"][eq_key] = {
                                    "text": context,
                                    "page": page_idx + 1,
                                    "source": "PyPDF2"
                                }
                                print(f"  Found: Eq. {eq_num} (page {page_idx + 1})")
    
    print(f"✓ PyPDF2 extraction complete")
    
except ImportError:
    print("✗ PyPDF2 not available")
except Exception as e:
    print(f"✗ PyPDF2 error: {e}")

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("EXTRACTION RESULTS SUMMARY")
print("=" * 80)

print(f"\nMethods Used: {', '.join(results['method_used'])}")
print(f"Equations Found: {len(results['equations'])}")
print(f"Noise Terms Found: {len(results['noise_terms'])}")

print("\n[EXTRACTED EQUATIONS]")
for eq_key in sorted(results["equations"].keys(), key=lambda x: int(x.replace("Eq", ""))):
    eq_data = results["equations"][eq_key]
    print(f"\n{eq_key} (Page {eq_data.get('page', '?')}):")
    print(f"  {eq_data['text'][:200]}{'...' if len(eq_data['text']) > 200 else ''}")

print("\n[NOISE TERMS]")
for term, data in results["noise_terms"].items():
    print(f"\n{term} (Page {data.get('page', '?')}):")
    if isinstance(data['text'], list):
        print(f"  {' '.join(data['text'][:150])}")
    else:
        print(f"  {data['text'][:150]}")

print("\n" + "=" * 80)
print("Extraction complete. Check above for results.")
print("=" * 80)
