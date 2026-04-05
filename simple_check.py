import os
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Get file sizes
import os.path
files = {
    'actual_pdf_extraction_result.json': os.path.getsize('actual_pdf_extraction_result.json'),
    'actual_pdf_extraction_log.txt': os.path.getsize('actual_pdf_extraction_log.txt'),
}

print("FILE SIZES IN BYTES:")
for fname, size in files.items():
    print(f"{fname}: {size}")

# Delete helper files
print("\nDELETING HELPER FILES:")
for fname in ['extract_pdf_data.py', 'run_fresh_extraction.bat']:
    try:
        if os.path.exists(fname):
            os.remove(fname)
            print(f"✓ Deleted: {fname}")
    except Exception as e:
        print(f"✗ Failed: {fname} - {e}")

# Verify deletion
print("\nVERIFYING DELETION:")
for fname in ['extract_pdf_data.py', 'run_fresh_extraction.bat']:
    if os.path.exists(fname):
        print(f"✗ Still exists: {fname}")
    else:
        print(f"✓ Confirmed deleted: {fname}")
