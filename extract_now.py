#!/usr/bin/env python3
import sys
import os

pdf_path = r"e:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

print("Starting equation extraction...")
print(f"PDF path: {pdf_path}")
print(f"File exists: {os.path.exists(pdf_path)}")

# Try PyMuPDF first
try:
    import fitz
    print("\n[SUCCESS] PyMuPDF (fitz) available")
    
    doc = fitz.open(pdf_path)
    print(f"PDF opened: {doc.page_count} pages")
    
    # Extract text from all pages and search for equations
    target_equations = list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
    found_eqs = {}
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            for eq_num in target_equations:
                # Check multiple patterns
                if f"({eq_num})" in line or f"Eq.{eq_num}" in line or f"Eq. {eq_num}" in line:
                    # Get context: current line + next 2 lines + some prev context
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    context_lines = lines[start:end]
                    
                    key = f"Eq_{eq_num}"
                    if key not in found_eqs:
                        found_eqs[key] = {
                            'page': page_num + 1,
                            'text': '\n'.join(context_lines)
                        }
                        print(f"Found Eq. {eq_num} on page {page_num + 1}")
    
    doc.close()
    
    # Print results
    print("\n" + "="*80)
    print("EXTRACTED EQUATIONS:")
    print("="*80)
    
    for eq_key in sorted(found_eqs.keys(), key=lambda x: int(x.split('_')[1])):
        eq_data = found_eqs[eq_key]
        eq_num = eq_key.split('_')[1]
        print(f"\nEquation {eq_num} (Page {eq_data['page']}):")
        print(f"---")
        print(eq_data['text'])
        print(f"---")
    
    print("\n" + "="*80)
    print(f"Total equations found: {len(found_eqs)}")
    
except ImportError as e:
    print(f"PyMuPDF not available: {e}")
    print("\nTrying pdfplumber...")
    
    try:
        import pdfplumber
        print("[SUCCESS] pdfplumber available")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF opened: {len(pdf.pages)} pages")
            
            target_equations = list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
            found_eqs = {}
            
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    for eq_num in target_equations:
                        if f"({eq_num})" in line or f"Eq.{eq_num}" in line or f"Eq. {eq_num}" in line:
                            start = max(0, i - 1)
                            end = min(len(lines), i + 3)
                            context_lines = lines[start:end]
                            
                            key = f"Eq_{eq_num}"
                            if key not in found_eqs:
                                found_eqs[key] = {
                                    'page': page_idx + 1,
                                    'text': '\n'.join(context_lines)
                                }
                                print(f"Found Eq. {eq_num} on page {page_idx + 1}")
            
            print("\n" + "="*80)
            print("EXTRACTED EQUATIONS:")
            print("="*80)
            
            for eq_key in sorted(found_eqs.keys(), key=lambda x: int(x.split('_')[1])):
                eq_data = found_eqs[eq_key]
                eq_num = eq_key.split('_')[1]
                print(f"\nEquation {eq_num} (Page {eq_data['page']}):")
                print(f"---")
                print(eq_data['text'])
                print(f"---")
            
            print("\n" + "="*80)
            print(f"Total equations found: {len(found_eqs)}")
    
    except ImportError as e2:
        print(f"pdfplumber not available: {e2}")
        print("\nTrying pypdf...")
        
        try:
            try:
                from pypdf import PdfReader
            except:
                from PyPDF2 import PdfReader
            
            print("[SUCCESS] PyPDF available")
            
            reader = PdfReader(pdf_path)
            print(f"PDF opened: {len(reader.pages)} pages")
            
            target_equations = list(range(3, 12)) + list(range(16, 21)) + list(range(28, 34))
            found_eqs = {}
            
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    for eq_num in target_equations:
                        if f"({eq_num})" in line or f"Eq.{eq_num}" in line or f"Eq. {eq_num}" in line:
                            start = max(0, i - 1)
                            end = min(len(lines), i + 3)
                            context_lines = lines[start:end]
                            
                            key = f"Eq_{eq_num}"
                            if key not in found_eqs:
                                found_eqs[key] = {
                                    'page': page_idx + 1,
                                    'text': '\n'.join(context_lines)
                                }
                                print(f"Found Eq. {eq_num} on page {page_idx + 1}")
            
            print("\n" + "="*80)
            print("EXTRACTED EQUATIONS:")
            print("="*80)
            
            for eq_key in sorted(found_eqs.keys(), key=lambda x: int(x.split('_')[1])):
                eq_data = found_eqs[eq_key]
                eq_num = eq_key.split('_')[1]
                print(f"\nEquation {eq_num} (Page {eq_data['page']}):")
                print(f"---")
                print(eq_data['text'])
                print(f"---")
            
            print("\n" + "="*80)
            print(f"Total equations found: {len(found_eqs)}")
        
        except Exception as e3:
            print(f"All PDF libraries failed: {e}, {e2}, {e3}")
            sys.exit(1)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
