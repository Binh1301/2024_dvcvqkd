import os
import sys
from pathlib import Path

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Files to remove (temporary/helper scripts created during extraction tasks)
files_to_remove = [
    'fresh_extract.py',
    'extract_pdf_data.py',
    'pdf_extraction_runner.py',
    'extract_equations.py',
    'extract_equations_comprehensive.py',
    'extract_equations_v2.py',
    'extract_minimal.py',
    'extract_now.py',
    'extract_pdf_equations.py',
    'pdf_extractor.py',
    'pdf_strict_extract.py',
    'direct_extract.py',
    'direct_pdf_extract.py',
    'DIRECT_EXTRACT_SESSION.py',
    'direct_workflow.py',
    'quick_extract.py',
    'strict_pdf_extract_simple.py',
    'equation_extractor.py',
    'cleanup.py',
    'comprehensive_test.py',
    'delete_helpers.py',
    'diagnose_pdf.py',
    'execute_workflow.py',
    'exec_report.py',
    'final_report.py',
    'generate_json_output.py',
    'get_sizes.py',
    'inline_exec.py',
    'main_exec.py',
    'runner.py',
    'run_exec.py',
    'run_extraction.py',
    'simple_check.py',
    'step_by_step_report.py',
    'verify_files.py',
    'run_extraction.bat',
    'run_workflow.bat',
    'diagnostic_run.bat',
    'exec_sizes.bat',
    'run_cleanup.bat',  # Also remove the batch file we created
]

removed_count = 0
failed = []

for filename in files_to_remove:
    filepath = Path(filename)
    if filepath.exists():
        try:
            filepath.unlink()
            print(f"✓ Removed: {filename}")
            removed_count += 1
        except Exception as e:
            print(f"✗ Failed to remove {filename}: {e}")
            failed.append(filename)
    else:
        print(f"  (skip) {filename} not found")

print(f"\n{'='*50}")
print(f"Removed: {removed_count} files")
if failed:
    print(f"Failed: {failed}")
    sys.exit(1)
else:
    print("All temporary files removed successfully")
    
    # Check if output files exist
    print(f"\n{'='*50}")
    print("Checking output files...")
    json_exists = Path('actual_pdf_extraction_result.json').exists()
    log_exists = Path('actual_pdf_extraction_log.txt').exists()
    
    print(f"actual_pdf_extraction_result.json: {'✓ EXISTS' if json_exists else '✗ NOT FOUND'}")
    print(f"actual_pdf_extraction_log.txt: {'✓ EXISTS' if log_exists else '✗ NOT FOUND'}")
    
    if json_exists and log_exists:
        print("\n✓ Both output files exist")
        sys.exit(0)
    else:
        print("\n✗ One or more output files missing")
        sys.exit(1)
