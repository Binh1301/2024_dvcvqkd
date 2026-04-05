#!/usr/bin/env python3
"""
Comprehensive test script to execute all required steps and capture evidence.
Steps:
1) Run extract_pdf_data.py and capture FULL stdout+stderr
2) Check file sizes
3) Verify files exist
4) Delete files
5) Verify deletion
"""

import subprocess
import os
import sys
from pathlib import Path

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
WORK_DIR = os.getcwd()

print("="*80)
print("COMPREHENSIVE TEST EXECUTION")
print("="*80)
print(f"\nWorking Directory: {WORK_DIR}\n")

# STEP 1: Run extract_pdf_data.py
print("\n" + "="*80)
print("STEP 1: Execute python extract_pdf_data.py")
print("="*80)

try:
    result = subprocess.run(
        [sys.executable, 'extract_pdf_data.py'],
        cwd=WORK_DIR,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    print("\n--- STDOUT ---")
    print(result.stdout)
    print("\n--- STDERR ---")
    print(result.stderr)
    print(f"\n--- RETURN CODE: {result.returncode} ---")
    
    if result.returncode == 0:
        print("\n✓ STEP 1 PASS: Script executed successfully")
    else:
        print(f"\n✗ STEP 1 FAIL: Script returned error code {result.returncode}")
        
except subprocess.TimeoutExpired:
    print("\n✗ STEP 1 FAIL: Script execution timed out after 120 seconds")
except Exception as e:
    print(f"\n✗ STEP 1 FAIL: Exception occurred: {e}")

# STEP 2: Check file sizes
print("\n" + "="*80)
print("STEP 2: Check actual_pdf_extraction_result.json and actual_pdf_extraction_log.txt")
print("="*80)

files_to_check = [
    'actual_pdf_extraction_result.json',
    'actual_pdf_extraction_log.txt'
]

step2_pass = True
for filename in files_to_check:
    filepath = Path(WORK_DIR) / filename
    if filepath.exists():
        size_bytes = filepath.stat().st_size
        if size_bytes > 0:
            print(f"✓ {filename} exists - Size: {size_bytes} bytes")
        else:
            print(f"✗ {filename} exists but is EMPTY - Size: 0 bytes")
            step2_pass = False
    else:
        print(f"✗ {filename} DOES NOT EXIST")
        step2_pass = False

if step2_pass:
    print("\n✓ STEP 2 PASS: Both files exist and are non-empty")
else:
    print("\n✗ STEP 2 FAIL: One or more files missing or empty")

# STEP 3: Check if extract_pdf_data.py and run_fresh_extraction.bat exist
print("\n" + "="*80)
print("STEP 3: Verify extract_pdf_data.py and run_fresh_extraction.bat exist")
print("="*80)

files_to_delete = [
    'extract_pdf_data.py',
    'run_fresh_extraction.bat'
]

step3_pass = True
for filename in files_to_delete:
    filepath = Path(WORK_DIR) / filename
    if filepath.exists():
        size_bytes = filepath.stat().st_size
        print(f"✓ {filename} exists - Size: {size_bytes} bytes")
    else:
        print(f"✗ {filename} DOES NOT EXIST")
        step3_pass = False

if step3_pass:
    print("\n✓ STEP 3 PASS: Both files exist")
else:
    print("\n✗ STEP 3 FAIL: One or more files missing")

# STEP 4: Delete files
print("\n" + "="*80)
print("STEP 4: Delete extract_pdf_data.py and run_fresh_extraction.bat")
print("="*80)

step4_pass = True
for filename in files_to_delete:
    filepath = Path(WORK_DIR) / filename
    try:
        if filepath.exists():
            os.remove(filepath)
            print(f"✓ Deleted: {filename}")
        else:
            print(f"✗ Cannot delete - {filename} does not exist")
            step4_pass = False
    except Exception as e:
        print(f"✗ Failed to delete {filename}: {e}")
        step4_pass = False

if step4_pass:
    print("\n✓ STEP 4 PASS: Both files deleted successfully")
else:
    print("\n✗ STEP 4 FAIL: One or more deletion failed")

# STEP 5: Verify deletion
print("\n" + "="*80)
print("STEP 5: Verify files are deleted")
print("="*80)

step5_pass = True
for filename in files_to_delete:
    filepath = Path(WORK_DIR) / filename
    if not filepath.exists():
        print(f"✓ Confirmed deleted: {filename}")
    else:
        print(f"✗ File still exists: {filename}")
        step5_pass = False

if step5_pass:
    print("\n✓ STEP 5 PASS: Both files confirmed deleted")
else:
    print("\n✗ STEP 5 FAIL: One or more files still exist")

# SUMMARY
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Step 1 (Execute extract_pdf_data.py): {'PASS' if result.returncode == 0 else 'FAIL'}")
print(f"Step 2 (Check file sizes): {'PASS' if step2_pass else 'FAIL'}")
print(f"Step 3 (Verify files exist): {'PASS' if step3_pass else 'FAIL'}")
print(f"Step 4 (Delete files): {'PASS' if step4_pass else 'FAIL'}")
print(f"Step 5 (Verify deletion): {'PASS' if step5_pass else 'FAIL'}")
print("="*80)
