import numpy as np
from math import comb
from scipy.special import gammaln
import matplotlib.pyplot as plt
import seaborn as sns

# --- STEP 1: ĐỊNH NGHĨA CÁC THAM SỐ HỆ THỐNG ---
Ncut = 50               # Fock basis cutoff
alpha0 = 2 * np.sqrt(2) # Biên độ gốc chòm sao QAM

# Khởi tạo ma trận mật độ trống (complex128)
rho = np.zeros((Ncut, Ncut), dtype=complex)

# --- STEP 2: TÍNH TOÁN DENSITY MATRIX CHO 256-QAM ---
print("Đang tính toán ma trận mật độ sử dụng log-gamma để ổn định số học...")
for k in range(16):
    for l in range(16):
        # Biên độ liên kết phức alpha của từng điểm QAM
        alpha = alpha0 / np.sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
        
        # Xác suất tiên nghiệm (Phân phối nhị thức)
        p = comb(15, k) * comb(15, l) / (2**30)
        
        # Tạo Coherent state vector sử dụng cấu trúc Log-space để tránh tràn số (Overflow)
        v = np.zeros(Ncut, dtype=complex)
        
        # Trường hợp đặc biệt khi alpha = 0 (tránh lỗi log(0))
        if abs(alpha) == 0:
            v[0] = 1.0  # Trạng thái chân không |0>
        else:
            angle_alpha = np.angle(alpha)
            log_abs_alpha = np.log(abs(alpha))
            
            for n in range(Ncut):
                # Công thức Log-space: ln(c_n) = -|alpha|^2 / 2 + n*ln(|alpha|) - 0.5*gammaln(n+1)
                log_c_n = -abs(alpha)**2 / 2 + n * log_abs_alpha - 0.5 * gammaln(n + 1)
                # Nhân lại pha exp(i * n * theta)
                v[n] = np.exp(log_c_n) * np.exp(1j * n * angle_alpha)
            
        # Tích ngoài (Outer product) và cộng dồn có trọng số
        rho_kl = np.outer(v, np.conjugate(v))
        rho += p * rho_kl

# --- STEP 3: ÁP DỤNG CÁC CẢI TIẾN LƯỢNG TỬ (NUMERICAL PRECISION) ---
# 1. Ép ma trận về dạng Hermitian chuẩn để xóa sai số floating point
rho = (rho + rho.conj().T) / 2.0

# 2. Kiểm tra tính hợp lệ vật lý (Trace = 1)
trace_val = np.trace(rho).real
print(f"✓ Vết của ma trận (Trace): {trace_val:.6f}")

# 3. Kiểm tra tính nửa xác định dương (Positive semi-definite) qua trị riêng
eigvals = np.linalg.eigvalsh(rho)
min_eig = eigvals.min()
print(f"✓ Trị riêng nhỏ nhất (Min eigenvalue): {min_eig:.4e}")
if min_eig >= -1e-12:
    print("--> Trạng thái lượng tử HỢP LỆ (Positive semi-definite).")
else:
    print("--> Cảnh báo: Ma trận vi phạm tính xác định dương.")

# --- STEP 4: XUẤT DỮ LIỆU VÀ ĐỒ THỊ CHUẨN NGHIÊN CỨU ---
# 1. Xuất ma trận phần thực ra file CSV phục vụ hậu xử lý (Entropy, Holevo Bound...)
csv_filename = "rho_real_50x50.csv"
np.savetxt(csv_filename, np.real(rho), delimiter=",")
print(f"✓ Đã xuất ma trận số liệu thực 50x50 ra file: '{csv_filename}'")

# 2. Vẽ đồ thị Heatmap dạng sạch (annot=False)
print("Đang tạo đồ thị trực quan (Heatmap)...")
fig, ax = plt.subplots(figsize=(12, 10))

sns.heatmap(np.real(rho), 
            annot=False,            # Tắt hiển thị số trực tiếp (giúp ảnh nhẹ, sạch)
            cmap="viridis",         # Bảng màu chuẩn vật lý
            cbar=True,              # Hiển thị thanh đo mật độ xác suất
            square=True, 
            ax=ax)

ax.set_title("Exact Density Matrix $\\rho$ for 256-QAM (Real Part)", fontsize=16, pad=15)
ax.set_xlabel("Fock State |n>", fontsize=12)
ax.set_ylabel("Fock State <m|", fontsize=12)

# Xuất đồ thị ra file PNG
png_filename = "Density_Matrix_50x50_Clean.png"
plt.savefig(png_filename, dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Đã lưu đồ thị ma trận mật độ sạch tại: '{png_filename}'")