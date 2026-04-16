import subprocess
import sys
import os

os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

print("STEP 1: Running python -m py_compile cvqkd_simulation.py")
print("=" * 70)
result1 = subprocess.run([sys.executable, '-m', 'py_compile', 'cvqkd_simulation.py'], capture_output=True, text=True)
print(result1.stdout if result1.stdout else "(no output)")
if result1.stderr:
    print("STDERR:", result1.stderr)
print("Return code:", result1.returncode)

print("\nSTEP 2: Running python check_skr.py")
print("=" * 70)
result2 = subprocess.run([sys.executable, 'check_skr.py'], capture_output=True, text=True)
print(result2.stdout if result2.stdout else "(no output)")
if result2.stderr:
    print("STDERR:", result2.stderr)
print("Return code:", result2.returncode)
