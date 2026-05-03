#!/usr/bin/env python3
"""
Debug Holevo bound calculation to find source of discrepancy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

# Test parameters
lambda1 = 4.40806
lambda2 = 1.00164
lambda3 = 3.63250

def g_from_code(x):
    """Symplectic entropy function as implemented in code."""
    x_arr = np.maximum(x, 1.0 + 1e-12)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((x_arr + 1.0) / 2.0) * np.log2((x_arr + 1.0) / 2.0) - ((x_arr - 1.0) / 2.0) * np.log2((x_arr - 1.0) / 2.0)

def g_from_hand(x):
    """Symplectic entropy function as computed by hand."""
    return ((x + 1.0) / 2.0) * np.log2((x + 1.0) / 2.0) - ((x - 1.0) / 2.0) * np.log2((x - 1.0) / 2.0)

print("=" * 70)
print("HOLEVO BOUND DEBUGGING")
print("=" * 70)

print(f"\nλ₁ = {lambda1}")
g_lambda1_code = g_from_code(lambda1)
g_lambda1_hand = g_from_hand(lambda1)
print(f"  g(λ₁) from code = {g_lambda1_code:.5f}")
print(f"  g(λ₁) from hand = {g_lambda1_hand:.5f}")
print(f"  Hand calc detail:")
print(f"    = 2.7037 × log₂(2.7037) - 1.7037 × log₂(1.7037)")
x = (lambda1 + 1.0) / 2.0
y = (lambda1 - 1.0) / 2.0
print(f"    = {x:.5f} × log₂({x:.5f}) - {y:.5f} × log₂({y:.5f})")
print(f"    = {x:.5f} × {np.log2(x):.5f} - {y:.5f} × {np.log2(y):.5f}")
print(f"    = {x * np.log2(x):.5f} - {y * np.log2(y):.5f}")
print(f"    = {x * np.log2(x) - y * np.log2(y):.5f}")

print(f"\nλ₂ = {lambda2}")
g_lambda2_code = g_from_code(lambda2)
g_lambda2_hand = g_from_hand(lambda2)
print(f"  g(λ₂) from code = {g_lambda2_code:.5f}")
print(f"  g(λ₂) from hand = {g_lambda2_hand:.5f}")
x = (lambda2 + 1.0) / 2.0
y = (lambda2 - 1.0) / 2.0
print(f"  Hand calc detail:")
print(f"    = {x:.5f} × log₂({x:.5f}) - {y:.5f} × log₂({y:.5f})")
print(f"    = {x:.5f} × {np.log2(x):.5f} - {y:.5f} × {np.log2(y):.5f}")
print(f"    = {x * np.log2(x):.5f} - {y * np.log2(y):.5f}")

print(f"\nλ₃ = {lambda3}")
g_lambda3_code = g_from_code(lambda3)
g_lambda3_hand = g_from_hand(lambda3)
print(f"  g(λ₃) from code = {g_lambda3_code:.5f}")
print(f"  g(λ₃) from hand = {g_lambda3_hand:.5f}")
x = (lambda3 + 1.0) / 2.0
y = (lambda3 - 1.0) / 2.0
print(f"  Hand calc detail:")
print(f"    = {x:.5f} × log₂({x:.5f}) - {y:.5f} × log₂({y:.5f})")
print(f"    = {x:.5f} × {np.log2(x):.5f} - {y:.5f} × {np.log2(y):.5f}")
print(f"    = {x * np.log2(x):.5f} - {y * np.log2(y):.5f}")

print("\n" + "=" * 70)
print("HOLEVO BOUND χ(B:E)")
print("=" * 70)

chi_be_code = g_lambda1_code + g_lambda2_code - g_lambda3_code
chi_be_hand = g_lambda1_hand + g_lambda2_hand - g_lambda3_hand

print(f"\nχ(B:E) from code = {g_lambda1_code:.5f} + {g_lambda2_code:.5f} - {g_lambda3_code:.5f}")
print(f"                 = {chi_be_code:.5f}")

print(f"\nχ(B:E) from hand = {g_lambda1_hand:.5f} + {g_lambda2_hand:.5f} - {g_lambda3_hand:.5f}")
print(f"                 = {chi_be_hand:.5f}")

print(f"\nExpected (from hand): 0.29046")
print(f"Difference: {chi_be_code - 0.29046:.5f}")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print("Both code and hand calculations use the SAME g(x) formula.")
print("The difference lies in the λ values used:")
print(f"  Code λ₁ = {lambda1:.5f} vs Hand λ₁ = 4.4074")
print(f"  Code λ₂ = {lambda2:.5f} vs Hand λ₂ = 1.0012")
print(f"  Code λ₃ = {lambda3:.5f} vs Hand λ₃ = 3.6317")
print("\nThis suggests the discrepancy is in the eigenvalue calculation,")
print("not in the g(x) function itself.")
