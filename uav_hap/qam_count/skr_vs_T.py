"""
Plot SKR vs T (transmission efficiency) với các thông số cố định.

Thông số cố định:
  VA = 2.0, eps = 0.1, M = 256, beta = 0.95, chi_tot = 0.1, c = 1.5445129885

T sẽ được quét từ 0.01 đến 1.0.
"""

import numpy as np
import matplotlib.pyplot as plt
import math


def g(lam):
    """Hàm entropy độ tin Holevo."""
    if lam <= 1.0:
        return 0.0
    return (lam + 1) / 2 * math.log2((lam + 1) / 2) - (lam - 1) / 2 * math.log2((lam - 1) / 2)


def compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c):
    """
    Tính SKR M-QAM từ công thức paper.
    
    INPUT:
        VA      : modulation variance [SNU]
        T       : transmittance (T_eff) [0-1]
        eps     : channel excess noise [SNU]
        M       : constellation size
        beta    : reconciliation efficiency [0-1]
        chi_tot : total noise chi_tot [SNU]
        c       : Z* (correlation coefficient) [SNU]
    
    OUTPUT: SKR (secret key rate)
    """
    
    a = VA + 1.0
    b = 1.0 + T * VA + T * eps
    c_val = c
    
    # Symplectic invariants
    Delta = a**2 + b**2 - 2 * c_val**2
    B = (a * b - c_val**2) ** 2
    disc = Delta**2 - 4 * B
    
    # Eigenvalues
    if disc < 0:
        lambda1 = 1.0 + 1e-10
        lambda2 = 1.0 + 1e-10
    else:
        sqrt_disc = math.sqrt(disc)
        lambda1 = math.sqrt(max(0.5 * (Delta + sqrt_disc), 0.0))
        lambda2 = math.sqrt(max(0.5 * (Delta - sqrt_disc), 0.0))
    
    lambda3 = max(VA + 1.0 - c_val**2 / (2.0 + T * VA + T * eps), 1e-15)
    
    # Holevo bound
    chi_BE = g(lambda1) + g(lambda2) - g(lambda3)
    
    # Mutual information (heterodyne)
    I_AB = math.log2(1.0 + T * VA / (2.0 + T * chi_tot))
    
    # Secret Key Rate
    SKR_raw = beta * I_AB - chi_BE
    SKR = max(SKR_raw, 0.0)
    
    return SKR, I_AB, chi_BE


def main():
    # === THÔNG SỐ CỐ ĐỊNH ===
    VA = 2.0
    eps = 0.1
    M = 256
    beta = 0.95
    chi_tot = 0.1
    c = 1.5445129885
    
    # === QUÉT T ===
    T_values = np.linspace(0.01, 1.0, 200)
    SKR_values = []
    I_AB_values = []
    chi_BE_values = []
    
    for T in T_values:
        skr, i_ab, chi_be = compute_QAM_SKR(VA, T, eps, M, beta, chi_tot, c)
        SKR_values.append(skr)
        I_AB_values.append(i_ab)
        chi_BE_values.append(chi_be)
    
    SKR_values = np.array(SKR_values)
    I_AB_values = np.array(I_AB_values)
    chi_BE_values = np.array(chi_BE_values)
    
    # === TÌM T_TH (Threshold T nơi SKR = 0) ===
    idx_threshold = np.where(SKR_values > 0)[0]
    if len(idx_threshold) > 0:
        T_threshold = T_values[idx_threshold[0]]
        print(f"\n✓ Threshold T (SKR = 0): T_th ≈ {T_threshold:.4f}")
    else:
        T_threshold = None
        print("\n✗ Không tìm thấy threshold (SKR luôn ≤ 0)")
    
    # === TÌM T_MAX (T nơi SKR đạt cực đại) ===
    idx_max = np.argmax(SKR_values)
    T_max = T_values[idx_max]
    SKR_max = SKR_values[idx_max]
    print(f"✓ T tối ưu (SKR max): T_opt ≈ {T_max:.4f}, SKR_max ≈ {SKR_max:.6f}")
    
    # === VẼ BIỂU ĐỒ ===
    fig, axes = plt.subplots(2, 1, figsize=(10, 10))
    
    # Biểu đồ 1: SKR vs T
    ax1 = axes[0]
    ax1.plot(T_values, SKR_values, 'b-', linewidth=2.5, label='SKR')
    if T_threshold is not None:
        ax1.axvline(x=T_threshold, color='r', linestyle='--', linewidth=1.5, label=f'T_th ≈ {T_threshold:.4f}')
    ax1.axvline(x=T_max, color='g', linestyle='--', linewidth=1.5, label=f'T_opt ≈ {T_max:.4f}')
    ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('Transmittance T', fontsize=12)
    ax1.set_ylabel('Secret Key Rate (bits)', fontsize=12)
    ax1.set_title(f'SKR vs T (M={M}, VA={VA}, ε={eps}, β={beta}, χ_tot={chi_tot}, Z*={c:.4f})', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10, loc='best')
    
    # Biểu đồ 2: Các thành phần (I_AB, χ_BE) vs T
    ax2 = axes[1]
    ax2.plot(T_values, I_AB_values, 'g-', linewidth=2.5, label='I_AB (mutual info)')
    ax2.plot(T_values, chi_BE_values, 'r-', linewidth=2.5, label='χ_BE (Holevo bound)')
    ax2.plot(T_values, beta * I_AB_values, 'orange', linewidth=2, linestyle='--', label=f'β·I_AB (β={beta})')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('Transmittance T', fontsize=12)
    ax2.set_ylabel('Bits', fontsize=12)
    ax2.set_title('Information-theoretic Components vs T', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10, loc='best')
    
    plt.tight_layout()
    plt.savefig('skr_vs_T.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Hình ảnh đã lưu: skr_vs_T.png")
    plt.show()
    
    # === XUẤT BẢNG DỮ LIỆU ===
    print(f"\n{'='*80}")
    print(f"Bảng dữ liệu (chọn lọc):")
    print(f"{'='*80}")
    print(f"{'T':>8} | {'SKR':>12} | {'I_AB':>12} | {'χ_BE':>12}")
    print(f"{'-'*80}")
    
    for i in range(0, len(T_values), max(1, len(T_values) // 15)):
        T = T_values[i]
        skr = SKR_values[i]
        i_ab = I_AB_values[i]
        chi_be = chi_BE_values[i]
        print(f"{T:8.4f} | {skr:12.8f} | {i_ab:12.8f} | {chi_be:12.8f}")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
