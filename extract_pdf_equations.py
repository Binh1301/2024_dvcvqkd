#!/usr/bin/env python3
"""
Extract equations and variable definitions from CV-QKD PDF
Targets: Eq. 28-33, Eq. 3-11, noise terms, key-rate formulas
"""

import sys
import json
from pathlib import Path

# Try different PDF libraries
pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

extraction_result = {
    "pdf_file": str(pdf_path),
    "file_exists": Path(pdf_path).exists(),
    "equations": {},
    "variables": {},
    "noise_terms": {},
    "extraction_method": None,
    "errors": []
}

print(f"PDF file exists: {extraction_result['file_exists']}\n")

# Try PyMuPDF first
try:
    import fitz
    print("=" * 60)
    print("Method 1: PyMuPDF (fitz)")
    print("=" * 60)
    
    doc = fitz.open(pdf_path)
    extraction_result["extraction_method"] = "PyMuPDF"
    
    print(f"Total pages: {len(doc)}\n")
    
    # Extract all text with structure
    all_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        all_text += f"\n\n--- PAGE {page_num + 1} ---\n{text}"
    
    # Search for equations
    target_eqs = list(range(3, 12)) + list(range(16, 21)) + [4, 6] + list(range(28, 34))
    
    for eq_num in target_eqs:
        patterns = [f"Eq. {eq_num}", f"Eq.({eq_num})", f"Equation {eq_num}", f"({eq_num})"]
        for pattern in patterns:
            if pattern.lower() in all_text.lower():
                # Extract context around equation
                idx = all_text.lower().find(pattern.lower())
                if idx != -1:
                    start = max(0, idx - 200)
                    end = min(len(all_text), idx + 800)
                    context = all_text[start:end]
                    extraction_result["equations"][f"Eq. {eq_num}"] = context
                    break
    
    # Search for noise terms
    noise_terms_search = ["xi", "chi_line", "chi_tot", "homodyne", "heterodyne", "detector noise"]
    for term in noise_terms_search:
        if term.lower() in all_text.lower():
            idx = all_text.lower().find(term.lower())
            if idx != -1:
                start = max(0, idx - 150)
                end = min(len(all_text), idx + 500)
                context = all_text[start:end]
                extraction_result["noise_terms"][term] = context
    
    print(f"Extracted {len(extraction_result['equations'])} target equations")
    print(f"Extracted {len(extraction_result['noise_terms'])} noise terms\n")
    
except ImportError:
    extraction_result["errors"].append("PyMuPDF (fitz) not installed")
except Exception as e:
    extraction_result["errors"].append(f"PyMuPDF error: {str(e)}")

# Try pdfplumber second
if not extraction_result["extraction_method"]:
    try:
        import pdfplumber
        print("=" * 60)
        print("Method 2: pdfplumber")
        print("=" * 60)
        
        with pdfplumber.open(pdf_path) as pdf:
            extraction_result["extraction_method"] = "pdfplumber"
            print(f"Total pages: {len(pdf.pages)}\n")
            
            all_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text += f"\n\n--- PAGE {i + 1} ---\n{text}"
            
            # Search for equations (same as above)
            target_eqs = list(range(3, 12)) + list(range(16, 21)) + [4, 6] + list(range(28, 34))
            
            for eq_num in target_eqs:
                patterns = [f"Eq. {eq_num}", f"Eq.({eq_num})", f"Equation {eq_num}", f"({eq_num})"]
                for pattern in patterns:
                    if pattern.lower() in all_text.lower():
                        idx = all_text.lower().find(pattern.lower())
                        if idx != -1:
                            start = max(0, idx - 200)
                            end = min(len(all_text), idx + 800)
                            context = all_text[start:end]
                            extraction_result["equations"][f"Eq. {eq_num}"] = context
                            break
            
            # Search for noise terms
            noise_terms_search = ["xi", "chi_line", "chi_tot", "homodyne", "heterodyne", "detector noise"]
            for term in noise_terms_search:
                if term.lower() in all_text.lower():
                    idx = all_text.lower().find(term.lower())
                    if idx != -1:
                        start = max(0, idx - 150)
                        end = min(len(all_text), idx + 500)
                        context = all_text[start:end]
                        extraction_result["noise_terms"][term] = context
            
            print(f"Extracted {len(extraction_result['equations'])} target equations")
            print(f"Extracted {len(extraction_result['noise_terms'])} noise terms\n")
            
    except ImportError:
        extraction_result["errors"].append("pdfplumber not installed")
    except Exception as e:
        extraction_result["errors"].append(f"pdfplumber error: {str(e)}")

# Try PyPDF2 third
if not extraction_result["extraction_method"]:
    try:
        import PyPDF2
        print("=" * 60)
        print("Method 3: PyPDF2")
        print("=" * 60)
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            extraction_result["extraction_method"] = "PyPDF2"
            print(f"Total pages: {len(reader.pages)}\n")
            
            all_text = ""
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                all_text += f"\n\n--- PAGE {i + 1} ---\n{text}"
            
            # Search for equations (same as above)
            target_eqs = list(range(3, 12)) + list(range(16, 21)) + [4, 6] + list(range(28, 34))
            
            for eq_num in target_eqs:
                patterns = [f"Eq. {eq_num}", f"Eq.({eq_num})", f"Equation {eq_num}", f"({eq_num})"]
                for pattern in patterns:
                    if pattern.lower() in all_text.lower():
                        idx = all_text.lower().find(pattern.lower())
                        if idx != -1:
                            start = max(0, idx - 200)
                            end = min(len(all_text), idx + 800)
                            context = all_text[start:end]
                            extraction_result["equations"][f"Eq. {eq_num}"] = context
                            break
            
            print(f"Extracted {len(extraction_result['equations'])} target equations")
            
    except ImportError:
        extraction_result["errors"].append("PyPDF2 not installed")
    except Exception as e:
        extraction_result["errors"].append(f"PyPDF2 error: {str(e)}")

print("\n" + "=" * 60)
print("EXTRACTION SUMMARY")
print("=" * 60)
print(f"Method used: {extraction_result['extraction_method']}")
print(f"Equations found: {len(extraction_result['equations'])}")
print(f"Noise terms found: {len(extraction_result['noise_terms'])}")
print(f"Errors: {len(extraction_result['errors'])}")

if extraction_result["equations"]:
    print("\nEquations extracted:")
    for eq_num in sorted(extraction_result["equations"].keys()):
        print(f"  ✓ {eq_num}")

if extraction_result["noise_terms"]:
    print("\nNoise terms found:")
    for term in sorted(extraction_result["noise_terms"].keys()):
        print(f"  ✓ {term}")

# Save detailed results
import json
with open(E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\extraction_results.json', 'w') as f:
    json.dump(extraction_result, f, indent=2)

# Print first extraction as sample
if extraction_result["equations"]:
    first_key = list(extraction_result["equations"].keys())[0]
    print(f"\nSample extraction ({first_key}):")
    print(extraction_result["equations"][first_key][:500])
