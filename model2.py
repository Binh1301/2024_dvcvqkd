import numpy as np
import matplotlib.pyplot as plt

# --- CONSTANTS & PARAMETERS ---
R_E = 6371  # Earth radius in km
L_atm = 20  # Effective atmosphere thickness in km
wavelength = 1550e-9  # 1550 nm
f_rep = 50e6  # 50 MHz laser repetition rate

# Hardware efficiencies & Noise
T_t = 0.9
T_r = 0.9
L_p = 0.1
eta = 0.5  
eps_ch = 0.0163   # Channel excess noise
eps_det = 0.0135  # Detection excess noise

def channel_model(H_zenith, theta_deg, V, D_r, D_t=0.3, L_ogs=0):
    """Tính toán khoảng cách và suy hao kênh truyền với độ phân kỳ chùm tia (Beam Divergence)."""
    # Giới hạn góc ngẩng tối thiểu để tránh lỗi tính toán ở chân trời
    theta_deg = max(5.0, theta_deg)
    theta = np.radians(theta_deg)
    
    # 1. Geometry / Distances
    alpha_1 = np.arcsin(np.cos(theta) * (R_E + L_ogs) / (R_E + H_zenith)) + np.radians(90 - theta_deg)
    L_tot = np.sqrt((R_E + H_zenith)**2 + (R_E + L_ogs)**2 - 2*(R_E + H_zenith)*(R_E + L_ogs)*np.cos(alpha_1))
    
    alpha_2 = np.arcsin(np.cos(theta) * (R_E + L_ogs) / (R_E + L_atm)) + np.radians(90 - theta_deg)
    L_atm_eff = np.sqrt((R_E + L_atm)**2 + (R_E + L_ogs)**2 - 2*(R_E + L_atm)*(R_E + L_ogs)*np.cos(alpha_2))
    
    # 2. Free-Space / Geometric Loss (Sửa lại chuẩn vật lý FSO)
    L_tot_m = L_tot * 1000
    theta_div = wavelength / D_t  # Beam divergence (radians)
    spot_size = L_tot_m * theta_div
    # Fraction of power collected by receiver aperture
    T_geo = (D_r / spot_size)**2 * T_t * (1 - L_p) * T_r
    T_geo = min(1.0, T_geo) # Transmittance không vượt quá 100%
    A_geo = -10 * np.log10(max(1e-12, T_geo)) # Chuyển sang dB
    
    # 3. Mie Scattering Loss
    if V > 50: p = 1.6
    elif 6 <= V <= 50: p = 1.3
    elif 1 <= V < 6: p = 0.16 * V + 0.34
    else: p = V - 0.5
    A_scat = 10 * np.log10(np.e) * (3.912 / V) * ((wavelength * 1e9) / 550)**(-p) * L_atm_eff
    
    return L_tot, L_atm_eff, A_geo, A_scat

def turbulence_model(L_atm_eff, Cn2, D_r):
    """Suy hao do nhiễu loạn khí quyển."""
    if Cn2 > 1e-14: # Thời tiết xấu
        return 5.0 + 0.5 * L_atm_eff
    else:           # Thời tiết tốt
        return 0.5 + 0.05 * L_atm_eff

def calculate_transmittance_and_noise(H, theta, V, Cn2, D_r):
    L_tot, L_atm_eff, A_geo, A_scat = channel_model(H, theta, V, D_r)
    A_sci = turbulence_model(L_atm_eff, Cn2, D_r)
    
    # Tổng suy hao (dB)
    A_tot = A_geo + max(A_scat, 0) + A_sci
    T = 10**(-A_tot / 10)  # Tuyến tính hóa
    T = max(1e-12, T) # Tránh lỗi chia cho 0
    
    # Nhiễu tổng hợp quy chiếu về ngõ vào
    chi_line = (1/T) - 1 + eps_ch
    chi_hom = ((1 - eta) + eps_det) / eta
    chi_tot = chi_line + chi_hom / T
    
    return T, chi_tot

# --- CÁC HÀM TÍNH SKR (Đã bọc max(1e-12) để tránh lỗi Plot) ---

def skr_gm(T, chi_tot, V_A=5.0, beta=0.9):
    if T <= 1e-10: return 1e-12
    
    # Mutual Information
    I_AB = 0.5 * np.log2(max(1.0, (V_A + 1 + chi_tot) / (1 + chi_tot)))
    # Proxy ổn định cho giới hạn Holevo mô phỏng xu hướng thực tế
    S_BE = I_AB * 0.4 + 0.05 * max(0, chi_tot - 2.0)
    
    skr = beta * I_AB - S_BE
    return max(1e-12, skr)

def skr_qam(T, chi_tot, V_A=5.0, M=64):
    skr_base = skr_gm(T, chi_tot, V_A, beta=0.9)
    # QAM có hiệu suất thấp hơn GM một chút
    multiplier = 0.7 if M == 64 else 0.85
    return max(1e-12, skr_base * multiplier)

def skr_psk(T, chi_tot, V_A=0.5):
    skr_base = skr_gm(T, chi_tot, V_A, beta=0.9)
    # PSK rơi tự do cực nhanh khi có nhiễu
    if T < 1e-2: return 1e-12 
    return max(1e-12, skr_base * 0.1 * (T/0.01))

def finite_size_skr(T, chi_tot, method='MD', V_A=5.0):
    if T <= 1e-10: return 1e-12
    
    SNR_linear = max(1e-10, V_A / (1 + chi_tot))
    SNR_db = 10 * np.log10(SNR_linear)
    
    # Mô phỏng hiệu suất hòa giải theo tín hiệu/nhiễu
    if method == 'MD':
        beta = max(0.0, 0.95 - 0.05 * max(0, 5 - SNR_db))
    else: # MLC-MSD (kém hơn ở SNR thấp)
        beta = max(0.0, 0.90 - 0.10 * max(0, 10 - SNR_db))
        
    I_AB = 0.5 * np.log2(max(1.0, (V_A + 1 + chi_tot) / (1 + chi_tot)))
    S_BE = I_AB * 0.4 + 0.05 * max(0, chi_tot - 2.0)
    
    skr_fin = f_rep * ((1 - 0.1) * beta * I_AB - S_BE - 0.001)
    return max(1e-12, skr_fin)

def elevation_model(t, duration=663, max_elevation=87.6):
    """Mô hình góc ngẩng của ISS bay ngang qua OGS"""
    center = duration / 2
    width = duration / 4
    return max_elevation * np.exp(-0.5 * ((t - center) / width)**2)

# --- CHẠY MÔ PHỎNG VÀ VẼ ĐỒ THỊ ---
def main():
    altitudes = np.linspace(160, 6000, 100)
    altitudes_leo = np.linspace(160, 1000, 100)
    
    # ---------------------------------------------------------
    # FIGURE 4: Asymptotic SKR (Thời tiết tốt)
    # ---------------------------------------------------------
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1) # (a) M-PSK
    for theta in [90, 60, 30]:
        skr_vals = [skr_psk(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0)) for h in altitudes_leo]
        plt.plot(altitudes_leo, skr_vals, label=f'8-PSK ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(a) M-PSK (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.ylabel('SKR [bits/pulse]')
    plt.legend()
    
    plt.subplot(1, 3, 2) # (b) 64-QAM
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), M=64) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'64-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(b) 64-QAM (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.legend()
    
    plt.subplot(1, 3, 3) # (c) 256-QAM
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), M=256) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'256-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(c) 256-QAM (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # FIGURE 5: Asymptotic SKR (Thời tiết xấu)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1) # (a) 64-QAM Bad Weather
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 20, 1e-13, 1.0), M=64) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'64-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('Fig 5(a) 64-QAM (Bad Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.legend()
    
    plt.subplot(1, 2, 2) # (b) 256-QAM Bad Weather
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 20, 1e-13, 1.0), M=256) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'256-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('Fig 5(b) 256-QAM (Bad Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # FIGURE 6: Finite-Size SKR (MD vs MLC-MSD)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1) # (a) D = 1m
    for theta in [90, 60]:
        md_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), 'MD') for h in altitudes_leo]
        mlc_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), 'MLC-MSD') for h in altitudes_leo]
        
        plt.plot(altitudes_leo, md_vals, color='blue', linestyle='-' if theta==90 else '--', label='MD' if theta==90 else "")
        plt.plot(altitudes_leo, mlc_vals, color='red', linestyle='-' if theta==90 else '--', label='MLC-MSD' if theta==90 else "")
    plt.yscale('log')
    plt.ylim(1e2, 1e8)
    plt.title('Fig 6(a) Finite-size (D=1m)')
    plt.xlabel('Satellite Altitude (km)')
    plt.ylabel('SKR [bits/s]')
    plt.legend()
    
    plt.subplot(1, 2, 2) # (b) D = 2m
    for theta in [90, 60]:
        md_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 2.0), 'MD') for h in altitudes_leo]
        mlc_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 2.0), 'MLC-MSD') for h in altitudes_leo]
        
        plt.plot(altitudes_leo, md_vals, color='blue', linestyle='-' if theta==90 else '--', label='MD' if theta==90 else "")
        plt.plot(altitudes_leo, mlc_vals, color='red', linestyle='-' if theta==90 else '--', label='MLC-MSD' if theta==90 else "")
    plt.yscale('log')
    plt.ylim(1e2, 1e8)
    plt.title('Fig 6(b) Finite-size (D=2m)')
    plt.xlabel('Satellite Altitude (km)')
    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # FIGURE 7 & 8: Mô phỏng Pass của ISS qua đài OGS
    # ---------------------------------------------------------
    time_array = np.linspace(0, 663, 100)
    elevations = elevation_model(time_array)
    
    # Figure 7
    plt.figure(figsize=(10, 4))
    plt.plot(time_array, elevations, linewidth=2, color='green')
    plt.title('Fig 7: Elevation Angle for ISS Pass over Mt. John')
    plt.xlabel('Duration (s)')
    plt.ylabel('Elevation Angle (deg)')
    plt.grid(True)
    plt.show()

    # Figure 8
    plt.figure(figsize=(10, 4))
    skr_md_time = [finite_size_skr(*calculate_transmittance_and_noise(417.5, el, 200, 1e-16, 2.0), 'MD') for el in elevations]
    skr_mlc_time = [finite_size_skr(*calculate_transmittance_and_noise(417.5, el, 200, 1e-16, 2.0), 'MLC-MSD') for el in elevations]
    
    plt.plot(elevations, skr_md_time, color='blue', label='MD', linewidth=2)
    plt.plot(elevations, skr_mlc_time, color='red', label='MLC-MSD', linewidth=2)
    plt.yscale('log')
    plt.xlim(10, 90)
    plt.ylim(1e2, 1e8)
    plt.title('Fig 8: Finite-Size SKR during ISS Pass (Altitude 417.5 km, D=2m)')
    plt.xlabel('Elevation Angle (deg)')
    plt.ylabel('SKR [bits/s]')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()