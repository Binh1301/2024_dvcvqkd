#!/usr/bin/env python3
import sys
import os

pdf_path = r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf"

print("Testing PDF extraction...\n")
print(f"PDF path: {pdf_path}")
print(f"File exists: {os.path.exists(pdf_path)}\n")

# Try PyMuPDF
try:
    import fitz
    print("✓ PyMuPDF available\n")
    doc = fitz.open(pdf_path)
    print(f"✓ PDF opened: {len(doc)} pages\n")
    
    # Extract all text
    full_text = ""
    for i in range(len(doc)):
        text = doc[i].get_text()
        full_text += f"\n\n=== PAGE {i+1} ===\n{text}"
    
    # Save to file
    with open(r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\pdf_full_text.txt", "w", encoding='utf-8', errors='replace') as f:
        f.write(full_text)
    
    print("✓ Full text saved to pdf_full_text.txt")
    print(f"\nFirst 1500 characters:\n{full_text[:1500]}")
    
except ImportError:
    print("✗ PyMuPDF not available, trying pdfplumber...")
    try:
        import pdfplumber
        print("✓ pdfplumber available\n")
        with pdfplumber.open(pdf_path) as pdf:
            print(f"✓ PDF opened: {len(pdf.pages)} pages\n")
            
            full_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                full_text += f"\n\n=== PAGE {i+1} ===\n{text}"
            
            with open(r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\pdf_full_text.txt", "w", encoding='utf-8', errors='replace') as f:
                f.write(full_text)
            
            print("✓ Full text saved to pdf_full_text.txt")
            print(f"\nFirst 1500 characters:\n{full_text[:1500]}")
    except Exception as e:
        print(f"✗ Error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
