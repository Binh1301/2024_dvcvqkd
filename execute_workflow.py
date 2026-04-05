#!/usr/bin/env python3
"""Execute the complete workflow and report results."""
import os
import sys
import subprocess
import json

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
WORK_DIR = os.getcwd()

print("=" * 80)
print("STRUCTURED EXECUTION REPORT")
print("=" * 80)

# STEP 1: Run the extraction script
print("\n[STEP 1] Execute: python extract_pdf_data.py")
print("-" * 80)
try:
    result = subprocess.run(
        [sys.executable, 'extract_pdf_data.py'],
        capture_output=True,
        text=True,
        timeout=120
    )
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    print(f"\nReturn Code: {result.returncode}")
except Exception as e:
    print(f"ERROR: {e}")

# STEP 2: Verify output files exist and report sizes
print("\n" + "=" * 80)
print("[STEP 2] Verify Output Files Exist and Report Exact Sizes")
print("-" * 80)
output_files = ['actual_pdf_extraction_result.json', 'actual_pdf_extraction_log.txt']
for fname in output_files:
    if os.path.exists(fname):
        size = os.path.getsize(fname)
        print(f"✓ {fname}: EXISTS ({size} bytes)")
    else:
        print(f"✗ {fname}: NOT FOUND")

# STEP 3: Verify helper files exist
print("\n" + "=" * 80)
print("[STEP 3] Verify Helper Files Exist")
print("-" * 80)
helper_files = ['extract_pdf_data.py', 'run_fresh_extraction.bat']
for fname in helper_files:
    if os.path.exists(fname):
        size = os.path.getsize(fname)
        print(f"✓ {fname}: EXISTS ({size} bytes)")
    else:
        print(f"✗ {fname}: NOT FOUND")

# STEP 4: Delete helper files
print("\n" + "=" * 80)
print("[STEP 4] Delete Helper Files")
print("-" * 80)
for fname in helper_files:
    if os.path.exists(fname):
        try:
            os.remove(fname)
            print(f"✓ {fname}: DELETED")
        except Exception as e:
            print(f"✗ {fname}: DELETE FAILED - {e}")
    else:
        print(f"- {fname}: NOT FOUND (already deleted or never existed)")

# STEP 5: Verify deletion
print("\n" + "=" * 80)
print("[STEP 5] Verify Deletion")
print("-" * 80)
for fname in helper_files:
    if os.path.exists(fname):
        print(f"✗ {fname}: STILL EXISTS (deletion failed)")
    else:
        print(f"✓ {fname}: DELETED (verified)")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)
