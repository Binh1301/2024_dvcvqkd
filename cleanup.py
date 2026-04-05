import os
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
files_to_remove = [
    'extract_equations_comprehensive.py',
    'direct_pdf_extract.py',
    'run_extraction.py'
]
for f in files_to_remove:
    if os.path.exists(f):
        os.remove(f)
        print(f"✓ Removed {f}")
print("Cleanup complete")
