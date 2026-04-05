#!/usr/bin/env python3
"""Quick verification script to check file sizes and execution."""
import os
import sys
import json

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

print("=" * 80)
print("FILE SIZE VERIFICATION")
print("=" * 80)

files_to_check = [
    'actual_pdf_extraction_result.json',
    'actual_pdf_extraction_log.txt',
    'extract_pdf_data.py',
    'run_fresh_extraction.bat'
]

for filename in files_to_check:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"✓ {filename}: {size} bytes")
    else:
        print(f"✗ {filename}: NOT FOUND")

print("\n" + "=" * 80)
print("RUNNING EXTRACTION SCRIPT")
print("=" * 80 + "\n")

# Run the extraction script
import subprocess
result = subprocess.run([sys.executable, 'extract_pdf_data.py'], 
                       capture_output=False, 
                       text=True)

sys.exit(result.returncode)
