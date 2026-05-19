"""
SKR công thức M-QAM DM-CVQKD - sạch, ngắn, tính tất cả giá trị từng bước.
Người dùng điền các tham số: VA, T, eps, M, beta, chi_tot, c_value (Z*)
"""

import math


def g(x):
    """g(x) = (x+1)·log₂(x+1) - x·log₂(x); g(x)=0 nếu x≤1"""
    if x <= 1.0 + 1e-10:
        return 0.0
    return ((x + 1) / 2) * math.log2((x + 1) / 2) - (x / 2) * math.log2(x / 2)


def compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c):
    """
    Tính SKR M-QAM từ công thức paper.
    
    INPUT:
        VA      : modulation variance [SNU]
        T       : transmittance (T_eff) [0-1]
        eps     : channel excess noise [SNU]
        M       : constellation size (16, 64, 256, ...)
        beta    : reconciliation efficiency [0-1]
        chi_tot : total noise chi_tot [SNU]
        c       : Z* (correlation coefficient) [SNU]
    
    OUTPUT: dict với các key:
        a, b, c_val          : parameters
        Delta, B, disc       : symplectic invariants
        lambda1, lambda2, lambda3 : eigenvalues
        I_AB, chi_BE         : mutual info và Holevo bound
        SKR_raw, SKR         : secret key rate (raw và clamped)
    """
    
    # === Công thức ===
    # Covariance matrix: Γ*_AB = [[a, c], [c, b]]
    # a = V_A + 1
    # b = 1 + T·V_A + T·ε
    # c = Z*
    
    a = VA + 1.0
    b = 1.0 + T * VA + T * eps
    c_val = c
    
    # Symplectic invariants
    Delta = a**2 + b**2 - 2*c_val**2
    B = (a*b - c_val**2)**2
    disc = Delta**2 - 4*B
    
    # Eigenvalues
    if disc < 0:
        lambda1 = 1.0 + 1e-10
        lambda2 = 1.0 + 1e-10
    else:
        sqrt_disc = math.sqrt(disc)
        lambda1 = math.sqrt(max(0.5*(Delta + sqrt_disc), 0.0))
        lambda2 = math.sqrt(max(0.5*(Delta - sqrt_disc), 0.0))
    
    # λ₃ = (V_A+1) - c²/(2+T·V_A+T·ε)
    lambda3 = max(a - c_val**2 / (2.0 + T*VA + T*eps), 1e-15)
    
    # Holevo bound
    chi_BE = g(lambda1) + g(lambda2) - g(lambda3)
    
    # Mutual information (heterodyne)
    I_AB = math.log2(1.0 + T*VA / (2.0 + T*chi_tot))
    
    # Secret Key Rate
    SKR_raw = beta * I_AB - chi_BE
    SKR = max(SKR_raw, 0.0)
    
    return {
        "a": a,
        "b": b,
        "c": c_val,
        "Delta": Delta,
        "B": B,
        "disc": disc,
        "lambda1": lambda1,
        "lambda2": lambda2,
        "lambda3": lambda3,
        "I_AB": I_AB,
        "chi_BE": chi_BE,
        "SKR_raw": SKR_raw,
        "SKR": SKR,
    }


def print_result(result, VA, T, eps, M, beta, chi_tot, c):
    """In kết quả chi tiết."""
    print(f"\n{'='*70}")
    print(f"M-QAM SKR: M={M}, VA={VA}, T={T}, ε={eps}, β={beta}, χ_tot={chi_tot}, Z*={c}")
    print(f"{'='*70}")
    
    print(f"\n1. Tham số covariance:")
    print(f"   a = VA + 1 = {VA} + 1 = {result['a']}")
    print(f"   b = 1 + T·VA + T·ε = 1 + {T}·{VA} + {T}·{eps} = {result['b']}")
    print(f"   c = Z* = {result['c']}")
    
    print(f"\n2. Symplectic invariants:")
    print(f"   Δ = a² + b² - 2c² = {result['Delta']}")
    print(f"   B = (a·b - c²)² = {result['B']}")
    print(f"   disc = Δ² - 4B = {result['disc']}")
    
    print(f"\n3. Eigenvalues:")
    print(f"   λ₁ = {result['lambda1']}")
    print(f"   λ₂ = {result['lambda2']}")
    print(f"   λ₃ = {result['lambda3']}")
    
    print(f"\n4. Information-theoretic quantities:")
    print(f"   I_AB = log₂(1 + T·VA/(2+T·χ_tot)) = {result['I_AB']}")
    print(f"   χ_BE = g(λ₁) + g(λ₂) - g(λ₃) = {result['chi_BE']}")
    
    print(f"\n5. Secret Key Rate:")
    print(f"   SKR_raw = β·I_AB - χ_BE = {result['SKR_raw']}")
    print(f"   SKR = max(SKR_raw, 0) = {result['SKR']}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # === ĐIỀN CÁC THAM SỐ TẠI ĐÂY ===
    
    # Test case 1: M=16
    VA = 2.0
    T = 0.347
    eps = 0.01
    M = 16
    beta = 0.95
    chi_tot = 2.010683
    c = 0.530160
    
    result = compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c)
    print_result(result, VA, T, eps, M, beta, chi_tot, c)
    
    # Test case 2: M=64
    VA = 2.0
    T = 0.177
    eps = 0.01
    M = 64
    beta = 0.95
    chi_tot = 4.892696
    c = 0.378642
    
    result = compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c)
    print_result(result, VA, T, eps, M, beta, chi_tot, c)
    
    # Test case 3: M=256
    VA = 2.0
    T = 0.1
    eps = 0.01
    M = 256
    beta = 0.95
    chi_tot = 11.7002
    c = 1.547844
    
    result = compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c)
    print_result(result, VA, T, eps, M, beta, chi_tot, c)
    print(f"\n\n")
