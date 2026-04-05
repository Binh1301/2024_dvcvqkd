#!/usr/bin/env python3
"""
PDF Equation and Variable Extractor
Extracts specific equations and variable definitions from CV-QKD paper
"""

import os
import sys

# Try different PDF libraries
pdf_text = None

# Try PyMuPDF first (fitz)
try:
    import fitz
    pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"
    doc = fitz.open(pdf_path)
    pdf_text = {}
    for page_num in range(len(doc)):
        page = doc[page_num]
        pdf_text[page_num] = page.get_text()
    print("SUCCESS: PDF extracted using PyMuPDF")
    print(f"Total pages: {len(doc)}")
except ImportError:
    print("PyMuPDF not available, trying pdfplumber...")
except Exception as e:
    print(f"PyMuPDF error: {e}")

# Try pdfplumber if PyMuPDF failed
if pdf_text is None:
    try:
        import pdfplumber
        pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"
        with pdfplumber.open(pdf_path) as pdf:
            pdf_text = {}
            for page_num, page in enumerate(pdf.pages):
                pdf_text[page_num] = page.extract_text()
        print("SUCCESS: PDF extracted using pdfplumber")
        print(f"Total pages: {len(pdf.pages)}")
    except ImportError:
        print("pdfplumber not available, trying PyPDF...")
    except Exception as e:
        print(f"pdfplumber error: {e}")

# Try PyPDF as last resort
if pdf_text is None:
    try:
        from pypdf import PdfReader
        pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"
        reader = PdfReader(pdf_path)
        pdf_text = {}
        for page_num, page in enumerate(reader.pages):
            pdf_text[page_num] = page.extract_text()
        print("SUCCESS: PDF extracted using PyPDF")
        print(f"Total pages: {len(reader.pages)}")
    except ImportError:
        print("PyPDF not available")
    except Exception as e:
        print(f"PyPDF error: {e}")

# If we have text, search for equations
if pdf_text:
    print("\n" + "="*80)
    print("SEARCHING FOR TARGET EQUATIONS")
    print("="*80)
    
    # Define equation numbers to find
    target_equations = {
        'group1': list(range(28, 34)),      # 28-33: channel model
        'group2': list(range(3, 12)),        # 3-11: covariance matrix
        'group3': [4, 6, 16, 17, 18, 19, 20], # key-rate formulas
        'noise': []                          # noise terms
    }
    
    all_equations = {}
    
    # Search all pages
    for page_num, text in pdf_text.items():
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for eq_num in [3,4,5,6,7,8,9,10,11,16,17,18,19,20,28,29,30,31,32,33]:
                # Look for equation markers like "Eq.", "Equation", "(28)", etc.
                if f"Eq.{eq_num}" in line or f"Equation {eq_num}" in line or f"({eq_num})" in line:
                    # Capture context
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 10)
                    context = '\n'.join(lines[context_start:context_end])
                    all_equations[eq_num] = {
                        'page': page_num,
                        'line_num': i,
                        'context': context
                    }
    
    # Print found equations
    if all_equations:
        print(f"\nFound {len(all_equations)} equations:")
        for eq_num in sorted(all_equations.keys()):
            info = all_equations[eq_num]
            print(f"\nEq. {eq_num} (Page {info['page']+1}, Line ~{info['line_num']}):")
            print("-" * 60)
            print(info['context'])
            print("-" * 60)
    else:
        print("\nNo equation markers found in direct text. May need OCR.")
        print("\nSample text from page 0:")
        if 0 in pdf_text:
            print(pdf_text[0][:1000])

else:
    print("ERROR: Could not extract PDF text with any available library")
    print("Available libraries to try: PyMuPDF, pdfplumber, PyPDF")
    sys.exit(1)
