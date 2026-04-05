import sys
import os

# Set up paths
sys.path.insert(0, r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Execute the step-by-step report
try:
    with open('step_by_step_report.py', 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code, {'__name__': '__main__', '__file__': 'step_by_step_report.py'})
except Exception as e:
    print(f"Error executing step_by_step_report.py: {e}")
    import traceback
    traceback.print_exc()
