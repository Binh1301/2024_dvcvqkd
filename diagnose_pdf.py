#!/usr/bin/env python3
"""
Fallback: Read PDF binary and attempt text extraction
"""
import os

pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

if os.path.exists(pdf_path):
    print(f"✓ PDF file found: {pdf_path}")
    print(f"✓ File size: {os.path.getsize(pdf_path)} bytes\n")
    
    # Read binary and look for text streams
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read(50000)  # First 50KB
            
            # Look for readable text
            text_parts = []
            current = ""
            for byte in content:
                if 32 <= byte <= 126:  # Printable ASCII
                    current += chr(byte)
                else:
                    if len(current) > 3:
                        text_parts.append(current)
                    current = ""
            
            print("Readable text segments from PDF:")
            print("="*80)
            for i, part in enumerate(text_parts[:30]):
                if any(keyword in part.lower() for keyword in ['eq', 'equation', 'chi', 'xi', 'noise', 'holevo', 'key']):
                    print(f"{i}: {part[:100]}")
        
        # Try to import any available library
        print("\n" + "="*80)
        print("Attempting to use available PDF libraries:")
        print("="*80 + "\n")
        
        libraries_available = []
        
        try:
            import fitz
            libraries_available.append("PyMuPDF (fitz)")
            print("✓ PyMuPDF available - full extraction possible")
        except:
            pass
        
        try:
            import pdfplumber
            libraries_available.append("pdfplumber")
            print("✓ pdfplumber available - full extraction possible")
        except:
            pass
        
        try:
            import pypdf
            libraries_available.append("pypdf")
            print("✓ pypdf available - full extraction possible")
        except:
            pass
        
        try:
            import pdf2image
            libraries_available.append("pdf2image")
            print("✓ pdf2image available - can use OCR")
        except:
            pass
        
        if not libraries_available:
            print("✗ No PDF libraries available")
            print("\nTo enable extraction, install:")
            print("  pip install PyMuPDF pdfplumber pypdf pdf2image pytesseract")
        else:
            print(f"\nAvailable: {', '.join(libraries_available)}")
    
    except Exception as e:
        print(f"Error reading PDF: {e}")
else:
    print(f"✗ PDF file not found: {pdf_path}")
