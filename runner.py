import subprocess
import sys

# Run the extraction script
result = subprocess.run([sys.executable, r"E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\quick_extract.py"], 
                       capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
