#!/usr/bin/env python3
import os
import subprocess
import sys

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# First run the cleanup_task_files.py
print("Running cleanup_task_files.py...")
result = subprocess.run([sys.executable, 'cleanup_task_files.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Exit code: {result.returncode}")
