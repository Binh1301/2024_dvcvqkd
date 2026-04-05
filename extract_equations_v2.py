#!/usr/bin/env python3
"""
Enhanced PDF Equation Extractor with OCR Fallback
Extracts equations and variable definitions from CV-QKD satellite paper
"""

import sys
import os

# First, check if file exists
pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"
print(f"Checking PDF file: {pdf_path}")
print(f"File exists: {os.path.exists(pdf_path)}")
print(f"File size: {os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A'} bytes")
print()

extraction_data = {}

# === TRY PYMUPDF ===
print("=" * 80)
print("ATTEMPTING PYMUPDF EXTRACTION")
print("=" * 80)
try:
    import fitz
    doc = fitz.open(pdf_path)
    print(f"✓ PyMuPDF loaded successfully")
    print(f"✓ PDF opened: {len(doc)} pages")
    
    # Extract text from all pages
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text()
        extraction_data[page_idx] = {
            'text': text,
            'library': 'PyMuPDF'
        }
    
    print(f"✓ Extracted text from all {len(doc)} pages")
    extraction_success = True
    
except ImportError as e:
    print(f"✗ PyMuPDF not installed: {e}")
    extraction_success = False
except Exception as e:
    print(f"✗ PyMuPDF error: {e}")
    extraction_success = False

# === FALLBACK: TRY PDFPLUMBER ===
if not extraction_success:
    print("\n" + "=" * 80)
    print("ATTEMPTING PDFPLUMBER EXTRACTION")
    print("=" * 80)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            print(f"✓ pdfplumber loaded successfully")
            print(f"✓ PDF opened: {len(pdf.pages)} pages")
            
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                extraction_data[page_idx] = {
                    'text': text,
                    'library': 'pdfplumber'
                }
            
            print(f"✓ Extracted text from all {len(pdf.pages)} pages")
            extraction_success = True
            
    except ImportError as e:
        print(f"✗ pdfplumber not installed: {e}")
    except Exception as e:
        print(f"✗ pdfplumber error: {e}")

# === FINAL FALLBACK: PYPDF ===
if not extraction_success:
    print("\n" + "=" * 80)
    print("ATTEMPTING PYPDF EXTRACTION")
    print("=" * 80)
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        print(f"✓ PyPDF loaded successfully")
        print(f"✓ PDF opened: {len(reader.pages)} pages")
        
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            extraction_data[page_idx] = {
                'text': text,
                'library': 'PyPDF'
            }
        
        print(f"✓ Extracted text from all {len(reader.pages)} pages")
        extraction_success = True
        
    except ImportError as e:
        print(f"✗ PyPDF not installed: {e}")
    except Exception as e:
        print(f"✗ PyPDF error: {e}")

# === ANALYZE EXTRACTED TEXT ===
if extraction_success and extraction_data:
    print("\n" + "=" * 80)
    print("EQUATION SEARCH AND EXTRACTION")
    print("=" * 80)
    
    # Target equations
    target_eqs = {
        'channel_model': list(range(28, 34)),      # 28-33
        'covariance': list(range(3, 12)),           # 3-11
        'key_rate': [4, 6, 16, 17, 18, 19, 20],   # Key rate equations
    }
    
    found_equations = {}
    
    # Search across all pages
    for page_idx, page_data in extraction_data.items():
        text = page_data['text']
        lines = text.split('\n')
        
        # Look for equation references
        for line_idx, line in enumerate(lines):
            # Check for equation numbers
            for eq_num in [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 28, 29, 30, 31, 32, 33]:
                # Various patterns: "Eq. 28", "Equation 28", "(28)", "eqn. 28"
                patterns = [
                    f"Eq. {eq_num}",
                    f"Eq.{eq_num}",
                    f"Equation {eq_num}",
                    f"({eq_num})",
                    f"eqn {eq_num}",
                    f"eqn. {eq_num}"
                ]
                
                if any(pattern in line for pattern in patterns):
                    # Get context
                    start = max(0, line_idx - 1)
                    end = min(len(lines), line_idx + 8)
                    context = '\n'.join(lines[start:end])
                    
                    found_equations[eq_num] = {
                        'page': page_idx + 1,
                        'line': line_idx,
                        'context': context,
                        'source_line': line
                    }
    
    # === OUTPUT RESULTS ===
    print(f"\nTotal pages extracted: {len(extraction_data)}")
    print(f"Equations found: {len(found_equations)}")
    
    if found_equations:
        print("\n" + "=" * 80)
        print("FOUND EQUATIONS - DETAILED OUTPUT")
        print("=" * 80)
        
        for eq_num in sorted(found_equations.keys()):
            data = found_equations[eq_num]
            print(f"\n{'='*80}")
            print(f"EQUATION {eq_num} (Page {data['page']}, Line ~{data['line']})")
            print(f"{'='*80}")
            print(data['context'])
            print()
    else:
        print("\n⚠ No equations found with standard pattern matching.")
        print("\nShowing first 2000 characters from page 1:")
        if 0 in extraction_data:
            print("-" * 80)
            print(extraction_data[0]['text'][:2000])
            print("-" * 80)
        
        print("\nPossible reasons:")
        print("1. Equations may use different notation/formatting")
        print("2. Text extraction may be garbled (OCR needed)")
        print("3. Equations may be in images (requires OCR)")
    
    # Save raw text for manual inspection
    print("\n" + "=" * 80)
    print("SAVING EXTRACTED TEXT FOR INSPECTION")
    print("=" * 80)
    
    output_file = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\pdf_extracted_text.txt"
    try:
        with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
            f.write(f"PDF EXTRACTION REPORT\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"Extraction Library: {extraction_data[0]['library']}\n")
            f.write(f"Total Pages: {len(extraction_data)}\n")
            f.write(f"{'='*80}\n\n")
            
            for page_idx in sorted(extraction_data.keys()):
                f.write(f"\n{'='*80}\n")
                f.write(f"PAGE {page_idx + 1}\n")
                f.write(f"{'='*80}\n")
                f.write(extraction_data[page_idx]['text'])
                f.write("\n")
        
        print(f"✓ Full extracted text saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Could not save text file: {e}")

else:
    print("\n✗ EXTRACTION FAILED")
    print("No PDF libraries available or extraction error occurred")
    print("\nTo install required libraries, run:")
    print("  pip install PyMuPDF pdfplumber pypdf")
    sys.exit(1)
