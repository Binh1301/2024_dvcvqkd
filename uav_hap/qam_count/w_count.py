import numpy as np
from math import comb, sqrt
from scipy.special import gammaln
from scipy.linalg import eigh

# =====================================================
# HÀM PHỤ TRỢ: TẠO TRẠNG THÁI COHERENT |alpha>
# =====================================================
def get_coherent_state(alpha, Ncut):
    """
    Tạo vector trạng thái coherent |alpha> trong cơ sở Fock.
    Sử dụng cấu trúc Log-space để tránh tràn số học (Overflow).
    """
    v = np.zeros(Ncut, dtype=complex)
    if abs(alpha) == 0:
        v[0] = 1.0  # Trạng thái chân không |0>
    else:
        log_abs_alpha = np.log(abs(alpha))
        angle_alpha = np.angle(alpha)
        for n in range(Ncut):
            # ln(c_n) = -|alpha|^2 / 2 + n*ln(|alpha|) - 0.5*ln(n!)
            log_c_n = -0.5 * abs(alpha)**2 + n * log_abs_alpha - 0.5 * gammaln(n + 1)
            # v[n] = c_n * exp(i * n * theta)
            v[n] = np.exp(log_c_n) * np.exp(1j * n * angle_alpha)
    return v

# =====================================================
# CHƯƠNG TRÌNH CHÍNH TÍNH TOÁN CỤ THỂ THAM SỐ W
# =====================================================
def main():
    # Định nghĩa tham số hệ thống
    Ncut = 25               # Cắt cụt không gian Fock theo yêu cầu
    alpha0 = 2 * sqrt(2)    # Biên độ gốc chòm sao QAM
    eps = 1e-12             # Ngưỡng lọc trị riêng cho ma trận nghịch đảo

    print("=" * 60)
    print(f"TÍNH TOÁN THAM SỐ W CHI TIẾT (Ncut = {Ncut})")
    print("=" * 60)

    # -------------------------------------------------
    # BƯỚC 1: TÍNH MA TRẬN MẬT ĐỘ RHO (ρ)
    # -------------------------------------------------
    print("Bước 1: Đang khởi tạo ma trận mật độ rho...")
    rho = np.zeros((Ncut, Ncut), dtype=complex)

    for k in range(16):
        for l in range(16):
            # Biên độ phức của từng điểm trong chòm sao 256-QAM
            alpha = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
            
            # Xác suất tiên nghiệm (Phân phối nhị thức Binomial)
            p = comb(15, k) * comb(15, l) / (2**30)
            
            # Tạo vector trạng thái coherent v = |alpha>
            v = get_coherent_state(alpha, Ncut)
            
            # Tích ngoài và cộng dồn: rho += p * |alpha><alpha|
            rho += p * np.outer(v, v.conj())

    # Ép ma trận về dạng Hermitian chuẩn để xóa sai số floating point
    rho = (rho + rho.conj().T) / 2.0

    # -------------------------------------------------
    # BƯỚC 2: TÍNH ρ^(1/2) VÀ ρ^(-1/2) QUA TRỊ RIÊNG
    # -------------------------------------------------
    print("Bước 2: Phân tích trị riêng để tính rho^(1/2) và rho^(-1/2)...")
    eigvals, V = eigh(rho)
    eigvals = np.maximum(eigvals, 0.0)  # Cắt các giá trị âm siêu nhỏ do sai số máy tính
    
    # Tính căn bậc hai và nghịch đảo căn bậc hai của các trị riêng
    sqrt_eigvals = np.sqrt(eigvals)
    inv_sqrt_eigvals = np.array([1.0 / np.sqrt(ev) if ev > eps else 0.0 for ev in eigvals])
    
    # Tái cấu trúc lại các ma trận: V * D * V†
    rho_sqrt = (V * sqrt_eigvals[None, :]) @ V.conj().T
    rho_inv_sqrt = (V * inv_sqrt_eigvals[None, :]) @ V.conj().T

    # -------------------------------------------------
    # BƯỚC 3: XÂY DỰNG TOÁN TỬ HỦY a VÀ TOÁN TỬ BIẾN ĐỔI a_tau (a_τ)
    # -------------------------------------------------
    print("Bước 3: Xây dựng toán tử hủy a và toán tử biến đổi a_tau...")
    a_op = np.zeros((Ncut, Ncut), dtype=complex)
    for j in range(1, Ncut):
        a_op[j-1, j] = sqrt(j)  # <j-1|a|j> = sqrt(j)

    # Công thức: a_tau = ρ^(1/2) * a * ρ^(-1/2)
    a_tau = rho_sqrt @ a_op @ rho_inv_sqrt
    
    # Toán tử liên hợp sfont (a_tau_dag) và toán tử số hạt biến đổi (n_tau)
    a_tau_dag = a_tau.conj().T
    n_tau = a_tau_dag @ a_tau

    # -------------------------------------------------
    # BƯỚC 4: TÍNH TỔNG CỦA CÔNG THỨC W
    # -------------------------------------------------
    print("Bước 4: Đang chạy vòng lặp tính w theo từng trạng thái...")
    w = 0.0

    for k in range(16):
        for l in range(16):
            alpha = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
            p = comb(15, k) * comb(15, l) / (2**30)
            
            # Lấy vector v = |alpha>
            v = get_coherent_state(alpha, Ncut)
            
            # Thuật toán tính Term 1: v† * a_tau_dag * a_tau * v = <v| n_tau |v>
            term1 = np.vdot(v, n_tau @ v).real
            
            # Thuật toán tính Term 2: |v† * a_tau * v|^2 = |<v| a_tau |v>|^2
            v_a_tau_v = np.vdot(v, a_tau @ v)
            term2 = abs(v_a_tau_v)**2
            
            # Công thức trong ngoặc vuông: [term1 - term2]
            delta_kl = term1 - term2
            
            # Nhân với xác suất p_kl và cộng dồn vào w
            w += p * delta_kl

    # -------------------------------------------------
    # BƯỚC 5: XUẤT KẾT QUẢ
    # -------------------------------------------------
    print("-" * 60)
    print(f"Kết quả Vết Tr(rho)  = {np.trace(rho).real:.10f}")
    print(f"Kết quả cụ thể giá trị w = {w:.8f}")
    print("=" * 60)

if __name__ == "__main__":
    main()