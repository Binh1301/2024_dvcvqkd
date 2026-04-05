#!/usr/bin/env python3
"""Get exact file sizes and perform deletion."""
import os
from pathlib import Path

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Get exact file sizes
result_json = Path('actual_pdf_extraction_result.json')
result_log = Path('actual_pdf_extraction_log.txt')
extract_script = Path('extract_pdf_data.py')
run_batch = Path('run_fresh_extraction.bat')

print("EXACT FILE SIZES (bytes):")
print(f"actual_pdf_extraction_result.json: {result_json.stat().st_size}")
print(f"actual_pdf_extraction_log.txt: {result_log.stat().st_size}")
print(f"extract_pdf_data.py: {extract_script.stat().st_size}")
print(f"run_fresh_extraction.bat: {run_batch.stat().st_size}")
print()

# Verify and delete
print("DELETION PROCESS:")
for fname in [extract_script, run_batch]:
    if fname.exists():
        fname.unlink()
        print(f"✓ Deleted: {fname.name}")
    else:
        print(f"- Already deleted: {fname.name}")

print()
print("VERIFICATION OF DELETION:")
for fname in [extract_script, run_batch]:
    if fname.exists():
        print(f"✗ STILL EXISTS: {fname.name}")
    else:
        print(f"✓ CONFIRMED DELETED: {fname.name}")
