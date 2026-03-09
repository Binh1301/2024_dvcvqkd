import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. Khởi tạo tham số hệ thống (Dựa trên bài báo và chuẩn CV-QKD)
# ---------------------------------------------------------
V_A = 5.0            # Modulation variance (SNU)
beta = 0.90          # Reconciliation efficiency (90%)
eta = 0.90           # Detection efficiency (Bob's detector)
eps_ch = 0.01        # Channel excess noise (SNU)
eps_det = 0.01       # Detection excess noise (SNU)

# Mảng suy hao kênh truyền (từ 0 dB đến 30 dB)
loss_db = np.linspace(0, 30, 100)
# Chuyển đổi suy hao (dB) sang độ truyền qua T (Transmittance)
T_array = 10 ** (-loss_db / 10)

def g_func(x):
    """Hàm phụ trợ tính thông tin lượng tử (Von Neumann entropy)"""
    # Xử lý các giá trị cực nhỏ để tránh lỗi log(0)
    x = np.maximum(x, 1e-12)
    return (x + 1) * np.log2(x + 1) - x * np.log2(x)

# ---------------------------------------------------------
# 2. Vòng lặp tính toán SKR cho từng giá trị suy hao
# ---------------------------------------------------------
skr_list = []

for T in T_array:
    # Tính toán nhiễu hệ thống
    chi_line = (1 / T) - 1 + eps_ch
    chi_hom = ((1 - eta) + eps_det) / eta
    chi_tot = chi_line + (chi_hom / T)
    
    # Mutual Information giữa Alice và Bob (Homodyne)
    I_AB = 0.5 * np.log2((V_A + 1 + chi_tot) / (1 + chi_tot))
    
    # Các ma trận hiệp phương sai và Symplectic Eigenvalues (Holevo bound)
    Z = np.sqrt(V_A**2 + 2*V_A)
    
    A = (V_A + 1)**2 + T**2 * (V_A + 1 + chi_line)**2 - 2*T*Z**2
    B = (T * (V_A + 1)**2 + T * (V_A + 1) * chi_line - T * Z**2)**2
    
    lambda_1 = np.sqrt(0.5 * (A + np.sqrt(max(0, A**2 - 4*B))))
    lambda_2 = np.sqrt(0.5 * (A - np.sqrt(max(0, A**2 - 4*B))))
    
    C_hom = (A * chi_hom + (V_A + 1) * np.sqrt(B) + T * (V_A + 1 + chi_line)) / (T * (V_A + 1 + chi_tot))
    D_hom = np.sqrt(B) * (V_A + 1 + np.sqrt(B) * chi_hom) / (T * (V_A + 1 + chi_tot))
    
    lambda_3 = np.sqrt(0.5 * (C_hom + np.sqrt(max(0, C_hom**2 - 4*D_hom))))
    lambda_4 = np.sqrt(0.5 * (C_hom - np.sqrt(max(0, C_hom**2 - 4*D_hom))))
    
    # Tính thông tin Eve (Holevo bound)
    S_BE = g_func((lambda_1 - 1)/2) + g_func((lambda_2 - 1)/2) - \
           g_func((lambda_3 - 1)/2) - g_func((lambda_4 - 1)/2)
           
    # Secret Key Rate (Asymptotic)
    SKR = beta * I_AB - S_BE
    
    # Nếu SKR âm (tức là không thể tạo khóa bảo mật), ta gán bằng 1e-10 để vẽ đồ thị log
    skr_list.append(max(SKR, 1e-10))

# ---------------------------------------------------------
# 3. Vẽ đồ thị
# ---------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.plot(loss_db, skr_list, label='GM-CVQKD (Homodyne)', color='blue', linewidth=2)
plt.yscale('log')
plt.xlim(0, 30)
plt.ylim(1e-6, 1)
plt.xlabel('Channel Loss (dB)', fontsize=12)
plt.ylabel('Secret Key Rate (bits/pulse)', fontsize=12)
plt.title('Asymptotic Secret Key Rate vs Channel Loss', fontsize=14)
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend(fontsize=12)
plt.show()