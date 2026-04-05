#!/usr/bin/env python3
import os
from pathlib import Path

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Read files and get exact byte counts
files_to_check = {
    'actual_pdf_extraction_result.json': None,
    'actual_pdf_extraction_log.txt': None,
    'extract_pdf_data.py': None,
    'run_fresh_extraction.bat': None,
}

# Get size by reading file as binary
for fname in files_to_check.keys():
    try:
        with open(fname, 'rb') as f:
            content = f.read()
            size = len(content)
        files_to_check[fname] = size
        print(f"{fname}: {size} bytes")
    except FileNotFoundError:
        files_to_check[fname] = None
        print(f"{fname}: NOT FOUND")

# Now delete the helper files
print("\n--- DELETING HELPER FILES ---")
for fname in ['extract_pdf_data.py', 'run_fresh_extraction.bat']:
    try:
        if os.path.exists(fname):
            os.remove(fname)
            print(f"✓ {fname}: DELETED")
        else:
            print(f"- {fname}: NOT FOUND")
    except Exception as e:
        print(f"✗ {fname}: DELETION FAILED - {e}")

# Verify deletion
print("\n--- VERIFICATION ---")
for fname in ['extract_pdf_data.py', 'run_fresh_extraction.bat']:
    if os.path.exists(fname):
        print(f"✗ {fname}: STILL EXISTS")
    else:
        print(f"✓ {fname}: VERIFIED DELETED")
