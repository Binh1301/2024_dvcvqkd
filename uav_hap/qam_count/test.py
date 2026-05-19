import numpy as np
from math import factorial, comb, sqrt
import matplotlib.pyplot as plt
import seaborn as sns

# --- STEP 1: ĐỊNH NGHĨA CÁC THAM SỐ HỆ THỐNG ---
Ncut = 25          # Kích thước ma trận mật độ (Fock basis cutoff)
alpha0 = 2 * np.sqrt(2) # Biên độ gốc của chòm sao QAM

# Khởi tạo ma trận mật độ trống (kiểu số phức) kích thước 50x50
rho = np.zeros((Ncut, Ncut), dtype=complex)

# --- STEP 2: TÍNH TOÁN MA TRẬN MẬT ĐỘ CHO 256-QAM ---
print("Đang tính toán ma trận mật độ 50x50...")
for k in range(16):
    for l in range(16):
        # Biên độ liên kết phức alpha của từng symbol QAM
        # (k - 7.5) và (l - 7.5) đảm bảo tính đối xứng hoàn hảo qua gốc tọa độ
        alpha = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))
        
        # Xác suất tiên nghiệm của từng symbol (Phân phối nhị thức / Gauss)
        p = comb(15, k) * comb(15, l) / (2**30)
        
        # Tạo vector trạng thái liên kết (Coherent State Vector) trong Fock basis
        v = np.zeros(Ncut, dtype=complex)
        for n in range(Ncut):
            # Biểu diễn trạng thái liên kết trên cơ sở Fock
            v[n] = np.exp(-abs(alpha)**2 / 2) * (alpha**n) / sqrt(factorial(n))
            
        # Tính tích ngoài (Outer product) để thu được ma trận mật độ riêng phần
        rho_kl = np.outer(v, np.conjugate(v))
        
        # Cộng dồn có trọng số xác suất vào ma trận mật độ tổng
        rho += p * rho_kl

# Lấy phần thực (Real part) của ma trận vì phần ảo triệt tiêu bằng 0
rho_real = np.real(rho)

print(f"Tính toán xong! Vết của ma trận (Trace): {np.trace(rho).real:.4f}")

# --- STEP 3: VẼ VÀ XUẤT ẢNH PNG SIÊU ĐỘ PHÂN GIẢI CHỨA SỐ ---
print("Đang vẽ và xuất ảnh PNG kích thước lớn...")

# Tạo một Canvas khổng lồ (40x40 inches) để chứa đủ 2500 con số không bị đè chữ
fig, ax = plt.subplots(figsize=(40, 40))

# Sử dụng Seaborn Heatmap để vẽ ma trận và điền text số liệu
sns.heatmap(rho_real, 
            annot=True,               # Bật hiển thị số liệu trong từng ô
            fmt=".4f",                # Định dạng hiển thị 4 chữ số thập phân
            cmap="Blues",             # Bảng màu xanh hiển thị độ đậm nhạt
            cbar=False,               # Tắt thanh màu bên cạnh
            square=True,              # Cấu hình các ô luôn là hình vuông
            linewidths=0.5,           # Độ dày đường lưới phân tách giữa các ô
            linecolor='lightgray',    # Màu của đường lưới
            annot_kws={"size": 10},   # Kích thước phông chữ của các con số
            ax=ax)

# Cài đặt tiêu đề và nhãn cho đồ thị
ax.set_title("Density Matrix 50x50 - Real Part (Exact Numbers)", fontsize=40, pad=20)
ax.set_xlabel("Fock State |n>", fontsize=30, labelpad=15)
ax.set_ylabel("Fock State <m|", fontsize=30, labelpad=15)

# Cài đặt kích thước số của các trục tọa độ từ 0 đến 49
ax.tick_params(axis='both', which='major', labelsize=16)

# Xuất ảnh ra file PNG chất lượng cao (dpi=150 kết hợp kích thước lớn giúp ảnh siêu nét khi zoom)
png_filename = "Density_Matrix_50x50_Full_Numbers.png"
plt.savefig(png_filename, dpi=150, bbox_inches='tight')
plt.close()

print(f"Thành công! Ảnh chứa số cụ thể đã được lưu tại: '{png_filename}'")