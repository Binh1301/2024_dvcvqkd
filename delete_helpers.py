#!/usr/bin/env python3
"""Delete helper files as requested."""
import os
import sys

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

files_to_delete = [
    'extract_pdf_data.py',
    'run_fresh_extraction.bat'
]

print("=" * 80)
print("DELETING HELPER FILES")
print("=" * 80)

deleted_files = []
for filename in files_to_delete:
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"✓ DELETED: {filename}")
            deleted_files.append(filename)
        except Exception as e:
            print(f"✗ FAILED TO DELETE {filename}: {e}")
    else:
        print(f"✗ NOT FOUND: {filename}")

print("\n" + "=" * 80)
print(f"SUMMARY: Deleted {len(deleted_files)}/{len(files_to_delete)} files")
print("=" * 80)

for f in deleted_files:
    print(f"  - {f}")

# Verify deletion
print("\n" + "=" * 80)
print("VERIFICATION - Files after deletion:")
print("=" * 80)

for filename in files_to_delete:
    if os.path.exists(filename):
        print(f"✗ {filename}: EXISTS (deletion failed)")
    else:
        print(f"✓ {filename}: NOT FOUND (successfully deleted)")
