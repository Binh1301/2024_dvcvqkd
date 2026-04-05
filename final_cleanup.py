#!/usr/bin/env python3
"""Final cleanup of temporary extraction task files."""
import os
from pathlib import Path

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Exact list of files to remove
to_remove = [
    'cleanup.py', 'cleanup_task_files.py', 'comprehensive_test.py',
    'cvqkd_simulation (1).py', 'delete_helpers.py', 'diagnose_pdf.py',
    'direct_extract.py', 'DIRECT_EXTRACT_SESSION.py', 'direct_pdf_extract.py',
    'direct_workflow.py', 'equation_extractor.py', 'exec_report.py',
    'execute_cleanup.py', 'execute_workflow.py', 'extract_equations.py',
    'extract_equations_comprehensive.py', 'extract_equations_v2.py',
    'extract_minimal.py', 'extract_now.py', 'extract_pdf_equations.py',
    'final_report.py', 'fresh_extract.py', 'generate_json_output.py',
    'get_sizes.py', 'inline_exec.py', 'main_exec.py',
    'pdf_extraction_runner.py', 'pdf_extractor.py', 'pdf_strict_extract.py',
    'QUICK_REFERENCE.py', 'quick_extract.py', 'run_cleanup_and_verify.py',
    'run_exec.py', 'run_extraction.py', 'runner.py', 'simple_check.py',
    'step_by_step_report.py', 'strict_pdf_extract_simple.py', 'verify_files.py',
    'diagnostic_run.bat', 'exec_sizes.bat', 'run_cleanup.bat',
    'run_extraction.bat', 'run_workflow.bat', 'extract_pdf_data.py'
]

removed = []
not_found = []

for fname in to_remove:
    fpath = Path(fname)
    if fpath.exists():
        try:
            fpath.unlink()
            removed.append(fname)
            print(f"✓ {fname}")
        except Exception as e:
            print(f"✗ {fname}: {e}")
    else:
        not_found.append(fname)

print(f"\n{len(removed)} files removed")
print(f"{len(not_found)} files not found (already deleted or didn't exist)")

# Verify the two required output files still exist
if Path("actual_pdf_extraction_result.json").exists():
    print("✓ actual_pdf_extraction_result.json - PRESENT")
else:
    print("✗ actual_pdf_extraction_result.json - MISSING!")

if Path("actual_pdf_extraction_log.txt").exists():
    print("✓ actual_pdf_extraction_log.txt - PRESENT")
else:
    print("✗ actual_pdf_extraction_log.txt - MISSING!")

# Now delete this cleanup script itself
try:
    Path("final_cleanup.py").unlink()
    print("✓ Removed final_cleanup.py")
except:
    print("  Note: final_cleanup.py should be manually deleted")
