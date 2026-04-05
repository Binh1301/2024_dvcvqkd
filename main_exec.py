import sys
import os

# Add current directory to path
sys.path.insert(0, r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

# Now execute the get_sizes script
exec(open('get_sizes.py').read(), {'__name__': '__main__'})
