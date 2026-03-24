import numpy as np
from scipy.special import erfinv

# =====================================================================
# BƯỚC 1: QUẢN LÝ THAM SỐ (TABLE III)
# =====================================================================
class QKDParams:
    def __init__(self):
        # Detection / modulation
        self.eta = 0.5              # Homodyne efficiency
        self.eps_ch = 1e-3          # Noise kênh vệ tinh
        self.eps_det = 1e-9         # Detection noise
        # Laser & optical system
        self.f_rep = 50e6
        self.wavelength = 1550e-9   # m
        self.D_t = 0.3               # m
        self.T_t = 0.9
        self.T_r = 0.9
        self.L_p = 0.1               # Pointing loss
        self.L_OGS = 1.029           # km
        self.L_atm = 20.0            # km
        # Other
        self.p_thr = 1e-6            # Probability threshold for scintillation

# =====================================================================
# BƯỚC 2 & 3: MÔ HÌNH KÊNH SAYAT 2024
# =====================================================================
class Sayat2024Channel:
    def __init__(self, params):
        self.p = params

    # Khoảng cách tổng và khí quyển hiệu dụng
    def get_geometry(self, H_sat, theta_deg):
        theta = np.radians(theta_deg)
        RE_LOGS = 6371 + self.p.L_OGS  # km

        # Khoảng cách tổng
        sin_val1 = (np.cos(theta) * RE_LOGS) / (6371 + H_sat)
        alpha1 = np.arcsin(sin_val1) + (np.pi/2 - theta)
        L_tot = np.sqrt((6371 + H_sat)**2 + RE_LOGS**2 - 
                        2*(6371 + H_sat)*RE_LOGS*np.cos(alpha1))

        # Khoảng cách khí quyển hiệu dụng
        sin_val2 = (np.cos(theta) * RE_LOGS) / (6371 + self.p.L_atm)
        alpha2 = np.arcsin(sin_val2) + (np.pi/2 - theta)
        L_atm_eff = np.sqrt((6371 + self.p.L_atm)**2 + RE_LOGS**2 - 
                            2*(6371 + self.p.L_atm)*RE_LOGS*np.cos(alpha2))

        return L_tot, L_atm_eff

    # Ageo (geometric loss, dB) – sửa đúng đơn vị
    def get_ageo(self, L_tot, D_r):
        # L_tot: km, D_t/D_r: m, λ: m → công thức đúng
        Ageo = 10 * np.log10((L_tot*1000)**2 * self.p.wavelength**2 / 
                             (self.p.D_t**2 * D_r**2 * self.p.T_t * (1 - self.p.L_p) * self.p.T_r))
        return Ageo

    # Ascat (Mie scattering, dB)
    def get_ascat(self, L_atm_eff, V_vis):
        if V_vis >= 50: p = 1.6
        elif 6 <= V_vis < 50: p = 1.3
        elif 1 <= V_vis < 6: p = 0.16*V_vis + 0.34
        elif 0.5 <= V_vis < 1: p = V_vis - 0.5
        else: p = 0
        coeff = 10*np.log10(np.e)*(3.912/V_vis)
        Ascat_per_km = coeff*((self.p.wavelength*1e9)/550)**(-p)
        return Ascat_per_km * L_atm_eff  # L_atm_eff in km

    # Asci (scintillation, dB)
    def get_asci(self, L_atm_eff, Cn2, D_r):
        k = 2*np.pi/self.p.wavelength
        L_m = L_atm_eff * 1000
        sigma_R2 = 2.25 * k**(7/6) * Cn2 * (3/11) * (L_m**(11/6))
        d = D_r * np.sqrt(np.pi / (2 * self.p.wavelength * L_m))
        t1 = (0.20 * sigma_R2) / ((1 + 0.18*d**2 + 0.20*sigma_R2**(6/5))**(7/6))
        t2 = (0.21*sigma_R2*(1 + 0.24*sigma_R2**(6/5))**(-5/6)) / (1 + 0.90*d**2 + 0.21*d**2*sigma_R2**(6/5))
        sigma_I2 = np.exp(t1 + t2) - 1
        term_erf = erfinv(2*self.p.p_thr - 1)
        term_ln = np.log(sigma_I2 + 1)
        Asci = 4.343 * (term_erf * np.sqrt(2*term_ln) - 0.5*term_ln)
        return abs(Asci)

    # Tính tất cả các giá trị
    def compute_all(self, H_sat, theta_deg, V_vis, Cn2, D_r):
        L_tot, L_atm_eff = self.get_geometry(H_sat, theta_deg)
        Ageo = self.get_ageo(L_tot, D_r)
        Ascat = self.get_ascat(L_atm_eff, V_vis)
        Asci = self.get_asci(L_atm_eff, Cn2, D_r)

        Atot = Ageo + Ascat + Asci
        T = 10**(-Atot/10)
        T = max(T, 1e-15)   # chặn cực nhỏ

        # Nhiễu tổng cộng hợp lý
        chi_line = self.p.eps_ch
        chi_hom = ((1 - self.p.eta) + self.p.eps_det) / self.p.eta
        chi_tot = chi_line + chi_hom

        return T, chi_tot, Atot

# =====================================================================
# CHẠY THỬ VỚI THÔNG SỐ TABLE III
# =====================================================================
params = QKDParams()
channel = Sayat2024Channel(params)

# Zenith
L_zen, L_atm_zen = channel.get_geometry(500, 90)
Ageo_zen = channel.get_ageo(L_zen, 1.0)

# Mô phỏng tại 60°
T, chi, loss = channel.compute_all(H_sat=500, theta_deg=60, V_vis=200, Cn2=1e-16, D_r=1.0)

print(f"--- KIỂM TRA ĐƠN VỊ ---")
print(f"L_tot tại Zenith (km): {L_zen:.2f} (Kỳ vọng: ~499 km)")
print(f"Ageo tại Zenith (dB): {Ageo_zen:.2f} (Kỳ vọng: ~34–35 dB)")
print(f"\n--- KẾT QUẢ MÔ PHỎNG (60°) ---")
print(f"Độ truyền dẫn (T): {T:.4e}")
print(f"Tổng tổn hao (dB): {loss:.2f} dB")
print(f"Nhiễu tổng cộng (chi_tot): {chi:.4f} SNU")
