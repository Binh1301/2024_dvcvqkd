"""Write the interpretation and captions from this diagnostic's saved tables."""
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def read(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def table(rows,columns):
    lines = ['| '+' | '.join(label for _,label in columns)+' |',
             '| '+' | '.join('---' for _ in columns)+' |']
    for row in rows:
        def fmt(key):
            value = row[key]
            try:
                return f'{float(value):.12g}'
            except (ValueError,TypeError):
                return str(value)
        lines.append('| '+' | '.join(fmt(k) for k,_ in columns)+' |')
    return '\n'.join(lines)


def main():
    result = json.loads((OUT/'diagnostic_results.json').read_text())
    summary = read('diagnostic_summary.csv')
    moments = {int(r['zenith_deg']):r for r in read('channel_moments.csv')}
    parameters = {int(r['zenith_deg']):r for r in read('channel_parameters.csv')}
    noise = {int(r['zenith_deg']):r for r in read('noise_decomposition.csv')}
    fixed = {int(r['zenith_deg']):r for r in read('skr_decomposition.csv') if r['scheme']=='Fixed MB'}
    controls = read('controlled_diagnostics.csv')
    adjacent = read('adjacent_skr_differences.csv')
    attribution = read('coordinate_attribution.csv')
    peaks = result['peaks']
    nums = []
    for aa,bb in [(0,24),(24,48),(46,48),(48,50),(48,56),(56,60),(48,60)]:
        nums.append(dict(from_deg=aa,to_deg=bb,
            delta_beta_I_AB=float(fixed[bb]['beta_I_AB'])-float(fixed[aa]['beta_I_AB']),
            delta_chi_BE=float(fixed[bb]['chi_BE'])-float(fixed[aa]['chi_BE']),
            delta_K=float(fixed[bb]['K_raw'])-float(fixed[aa]['K_raw'])))
    with (OUT/'interval_summary.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(nums[0]));w.writeheader();w.writerows(nums)
    p48 = next(r for r in summary if int(r['zenith_deg'])==48)
    gain48 = float(p48['optimization_gain'])/float(p48['Fixed_MB_K_raw'])*100
    pct = lambda d,a,b,k:(float(d[b][k])/float(d[a][k])-1)*100
    rep = table(read('representative_angles.csv'),[
        ('zenith_deg','ζ (°)'),('distance_km','L (km)'),('mean_T','⟨T⟩'),('T_eff','Tf'),
        ('xi_fading','ξfading (SNU)'),('xi_f','ξf (SNU)'),('beta_I_AB','βI (bit/use)'),
        ('chi_BE','χ (bit/use)'),('K_raw','Kraw (bit/use)')])
    intervaltable = table(nums,[('from_deg','Từ (°)'),('to_deg','Đến (°)'),
        ('delta_beta_I_AB','Δ(βI)'),('delta_chi_BE','Δχ'),('delta_K','ΔK')])
    attrtable = table(attribution,[('from_deg','Từ (°)'),('to_deg','Đến (°)'),
        ('contribution_Teff_at_fixed_Rf','Đóng góp Tf'),('contribution_Rf_at_fixed_Teff','Đóng góp Rf'),('delta_K','Tổng ΔK')])
    paramtable = table([parameters[a] for a in (0,24,48,56,60)],[('zenith_deg','ζ (°)'),
        ('wL_m','wL (m)'),('w_eq_m','weq (m)'),('sigma_s_squared_m2','σs² (m²)'),
        ('relative_displacement','σs/weq'),('A0','A0'),('sigma_R2','σR²')])
    body = f'''# Điều tra nguyên nhân SKR không đơn điệu theo góc thiên đỉnh

**Phạm vi: nguyên nhân của công thức số đã lưu; không xác thực an toàn lượng tử.**

`UNVALIDATED_SECURITY_MODEL` · `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

## Kết quả chính

Đường cong tăng không phải vì công suất truyền tốt lên: cả ⟨T⟩ và
Tf=⟨√T⟩² giảm tại mọi bước 2°. Trong cấu hình cũ, chùm tia rộng lên làm giảm
độ nhạy tương đối với lệch vị trí; hiệu ứng này thắng sự tăng scintillation
đến 56°, nên Rf và nhiễu quy về đầu vào giảm trong phần lớn miền góc.
Với nguồn MB giữ nguyên, χ giảm nhanh hơn βI trước đỉnh. Sau 48°, mất βI
đã lớn hơn mức giảm χ, mặc dù nhiễu fading vẫn giảm đến 56°.

Đối chứng giữ hình dạng fading ở 30° và chỉ thay đổi B=A0ηatm cho K giảm
liên tục. Đối chứng không fading, cùng ⟨T⟩ và ξch, cũng giảm liên tục.
Do đó nguyên nhân số được xác định là sự cạnh tranh giữa suy giảm Tf và
giảm phạt fading trong **hàm MI–Holevo đang triển khai**. Tối ưu nguồn thay
đổi độ cao đường cong nhưng không tạo ra đỉnh MB ở 48°.

## 1. Dữ liệu gốc, phạm vi và truy vết

Đọc `results/skr_vs_zenith_angle_20261019/run_sweep.py`, `protocol.json`,
`channel_by_angle.json`, `skr_vs_zenith_angle_detailed.csv`, toàn bộ 6758 hàng
ứng viên, 218 nguồn exact (182 MB + 36 Uniform), NPZ ensemble và các receipt.
Đây là catalog của lần quét góc; không thay bằng catalog mobility 233 nguồn.
Toàn bộ 31 góc 0:2:60° và 93 nghiệm chọn được phục hồi bằng dữ liệu đã lưu.
Những giá trị mới suy ra bằng đại số được ghi origin trong CSV; 78 lời gọi
rate mới được ghi riêng trong `validation/new_fixed_source_calls.csv`.

Producer lịch sử tính kênh bằng `channel_at_angle()` (dòng 74), MI bằng
`scripts/optimize_uniform_manuscript_2d.py:uniform_mi_2d` (dòng 59), và Holevo
bằng `scripts/recheck_manuscript_homodyne_noise.py:security` (dòng 84).
`render_figures.py` của kết quả cũ là renderer cuối, đọc CSV mà không chạy số.
Mọi producer, source payload và input hiện đọc đều khớp hash receipt cũ.
`input_manifest.json`, `startup_manifest.json` và receipt mới cung cấp đường
dẫn/hash cụ thể. Không gọi entry point quét góc cũ.

Cấu hình lịch sử thực tế:

| Đại lượng | Giá trị |
| --- | --- |
| Độ cao HAP / UAV | 20000 / 1000 m |
| Bước sóng / phân kỳ **toàn phần** | 1550 nm / 233 µrad |
| Đường kính / bán kính thu | 0.08 / 0.04 m |
| τzen / ξch / β | 0.92 / 0.0186 SNU / 0.95 |
| Angular jitter / horizontal jitter | 15.61 µrad / 1 m |
| Boresight / σAoA / FOV nửa góc | 0 m / 1.5 mrad / 6.25 mrad |
| Hufnagel–Valley | gió 21 m/s; Cn²(0)=10⁻¹⁴ m⁻²ᐟ³ |
| Detector | hiệu suất 1; noise điện tử 0 |
| Nguồn MB cố định | νraw=0.165; VA=5.475 SNU |
| Moment nguồn cố định | C=3.1986564642787387; w=9.973886145561931×10⁻⁷ |

Không dùng cấu hình 55 cm/10 µrad hoặc mặc định 223 µrad của thí nghiệm khác.
Lưu ý `rho=0` trong channel JSON là **boresight displacement** của công thức
pointing, không phải hệ số tương quan mây. Không có mô hình mây trong phép
quét góc đang điều tra.

## 2. Đường SKR gốc và cực đại rời rạc

| Phương án | Đỉnh đã tính (°) | Kraw tại đỉnh (bit/use) | Miền điểm dương |
| --- | --- | --- | --- |
| Uniform tối ưu trong catalog | 52 | 0.000106625951727330 | 44:2:60° |
| MB cố định | 48 | 0.000241357175677000 | 24:2:60° |
| MB tối ưu trong catalog | 48 | 0.000342145110300252 | 24:2:60° |

Đây là cực đại trên lưới được tính, không phải nghiệm liên tục. Có đầy đủ
kết quả âm ở góc nhỏ. Semilog chỉ thay điểm K≤0 bằng khoảng trống khi vẽ;
CSV và hình tuyến tính giữ dấu, không thay bằng ε dương, không clipping
trước tối ưu. Cả ba đường vẫn dương tại 60°, nên không suy ra góc cắt dương
lớn nhất ngoài miền khảo sát. `fig_01_original_semilog` và `fig_02_raw_signed`
phục hồi hai cách trình bày từ cùng dữ liệu.

## 3. Hình học, khí quyển, beam và pointing

Code đổi độ sang radian bằng ζπ/180 và dùng L=19000 secζ m. L tăng 19→38 km;
ηatm=0.92^secζ giảm 0.92→0.8464. Trong hình học phẳng/slant đã giả định,
secζ tăng độ dày quang học; công thức không làm suy hao tốt lên khi góc tăng.
Đây là mô hình khí quyển tổng hợp, không phải đo đạc hoặc mô hình Trái Đất
cong đã hiệu chuẩn. Fig. A xác nhận hai xu hướng này.

Các công thức literal:

- w0=2λ/(πθfull); wL²=w0²+[Lλ/(πw0)]².
- weff=wL√(1+Gd); u=√π Dr/(2√2 weff).
- A0=erf²(u); weq²=weff²√π erf(u)/[2u exp(−u²)].
- σs²=σh²+(Lθjt)²; d=weq²/(4σs²).

{paramtable}

σs² **tăng**, không giảm. Tuy vậy σs/weq giảm 0.471090564638→0.262567375352
({pct(parameters,0,60,'relative_displacement'):.6f}%), và d tăng
1.12650000188→3.62625618703. Với beam gần far field, weq gần tỷ lệ L,
trong khi σs chứa thêm jitter vị trí cố định 1 m: d xấp xỉ tỷ lệ
L²/[1+(Lθjt)²]. Đây là cơ chế giảm **độ nhạy tương đối**, không phải giảm
độ lệch tuyệt đối. Beam rộng hơn đồng thời làm A0 giảm khoảng bốn lần;
không thể suy ra tăng công suất thu từ cải thiện pointing.
Gd tăng 0.000223912786088→0.000447826596744; mọi góc đều tính lại beam.

## 4. Scintillation và outage

Producer dùng hai tích phân HV theo độ cao và các thừa số secζ tương ứng;
σR² tăng 0.0414535270822→0.147723576560. Trong **nhánh literal lịch sử này**,
phương sai lognormal được dùng trực tiếp là v_log=σR², không phải một v_sc
đã aperture-average từ module tổng quát khác. Tỷ số scintillation exp(v_log)−1
cũng tăng. Không thay closure này bằng công thức khác trong điều tra.

AoA dùng P0=exp[−FOV²/(2σAoA²)]=0.000169856676561, P1=0.999830143323439;
cả hai cố định theo cấu hình, không có ánh xạ turbulence→σAoA phụ thuộc góc.
Vì vậy việc P0 không đổi là đúng với code lịch sử, nhưng chưa chứng minh
mô hình AoA thực tế luôn độc lập góc. P0δ(T) được giữ riêng; mọi moment bậc
dương có thừa số P1. Không chuẩn hóa active density lên mass 1, không đưa
atom vào tích phân liên tục, không clip đuôi T>1 về T=1.

Fig. C cho thấy scintillation xấu lên còn AoA không tạo xu hướng góc.
Tích phân PDF độc lập tại 0°,24°,30°,48°,60° kiểm tra cả mass, ⟨√T⟩ và ⟨T⟩
trên [0,1]. Phần moment bị loại ở T>1 tối đa khoảng
{result['max_relative_upper_tail_moment']} theo công thức tail trực tiếp;
đây là chặn thực nghiệm trên 31 trạng thái đã tính, không phải thay support.

## 5. Moment kênh và tách các nguyên nhân fading

Tf=⟨√T⟩², Var(√T)=⟨T⟩−Tf và Rf=Var(√T)/Tf đều tính từ moment gốc,
không lấy mean-power thay cho Tf. Fig. D:

- ⟨T⟩ giảm 0.000318070574320→0.000108250438572.
- Tf giảm 0.000284995109390→0.000102776255693 ({pct(moments,0,60,'T_eff'):.6f}%).
- Rf giảm 0.116056254441→0.0514701339539 tại **56°**, rồi tăng lên
  0.0532631087002 tại 60°; không đổi dấu hoặc đổi chiều ở 48°.
- Tf giảm {abs(pct(moments,24,48,'T_eff')):.6f}% trong 24→48°, còn Rf giảm
  {abs(pct(moments,24,48,'R_f')):.6f}%. Hai hiệu ứng thực sự cạnh tranh.

Với boresight=0, tích phân của đúng luật cũ, trước cắt đuôi cực nhỏ, cho:

M_q=P1 B^q d/(d+q) exp[v_log(q²−q)/2], B=A0ηatm.

Suy ra:

**1+Rf = (1/P1) × [(d+1/2)²/(d(d+1))] × exp(v_log/4).**

Các moment truncated chính xác vẫn được dùng trong mọi rate. Biểu thức factor
trên khớp moment đã lưu với sai số dưới 10⁻⁵⁹ ở precision kiểm tra; ảnh hưởng
đuôi được ghi riêng. Fp−1=1/[4d(d+1)] giảm
0.104362247776→0.0149022500727; Fs−1=exp(v_log/4)−1 tăng
0.0104172675970→0.0376213126472. Outage factor 1/P1 không đổi.
Các thành phần **nhân**, không cộng các R thành phần. Fig. J dùng
log(1+Rf)=−logP1+logFp+v_log/4 để trình bày cộng đúng.
Tổng Rf chạm đáy 56° khi sự suy giảm pointing không còn bù được scintillation.
Atmosphere và A0 tác động trực tiếp qua B, gần như triệt tiêu khỏi Rf trong
miền tail không đáng kể; chúng không phải nguyên nhân làm Rf giảm.

## 6. Phân rã nhiễu với nguồn MB cố định

Theo đúng chuẩn cũ VA=2n̄, ξch=0.0186 SNU, detector lý tưởng:

N=(⟨T⟩−Tf)VA+⟨T⟩ξch;
ξfading=Rf VA; ξphysical=(1+Rf)ξch; ξf=ξfading+ξphysical.

ξfading giảm 0.635407993065→0.281798983397 tại 56°, rồi tăng
0.291615520134 tại 60°. ξf giảm 0.656166639397→0.301356327889 tại 56°,
rồi tăng 0.311206213955. Tại đỉnh SKR 48°, ξfading=0.306765303866,
ξf=0.326407465446 và vẫn đang giảm.
ξphysical thay đổi nhẹ vì nó là noise quy đổi qua fading, còn ξch cố định.
N giảm liên tục từ 0.000187004283173 xuống 0.0000319846094187, kể cả 56→60°,
vì nhân thêm Tf đang giảm. Vì vậy chỉ nhìn N hoặc chỉ nhìn ξf đều không đủ
để xác định đỉnh K. Không thêm vacuum loss hoặc detector noise vào ξch;
vacuum đã ở baseline W=1+Tf VA+N. Fig. E tách rõ noise đầu vào và đầu ra.

## 7. MI–Holevo: định lượng phần tăng và phần giảm

Fig. F là hình chẩn đoán chính, dùng cùng nguồn (0.165,5.475) ở cả 31 góc.
IAB giảm tại mọi bước; βI và χ cũng đều giảm tại mọi bước.
Không có vùng mà MI tăng để làm K tăng. Đặt Δ theo hai góc đã tính:

ΔK=Δ(βI)−Δχ.

{intervaltable}

Mọi giá trị trong bảng là bit/use. Trong **tất cả 24 bước từ 0 đến 48°**,
mức giảm χ lớn hơn mức mất βI; trong **6 bước từ 48 đến 60°**, thứ tự đảo lại.
Riêng 24→48°: Holevo giảm 9.02207260580834×10⁻⁴ trong khi βI mất
6.68449866333237×10⁻⁴, tạo ΔK=+2.33757394247596×10⁻⁴.
46→48° chỉ còn lợi ích ròng 2.86380520387095×10⁻⁷.
48→50° mất MI đã vượt giảm Holevo 4.55696347803885×10⁻⁶.
48→60° tổng K mất 9.51412985994695×10⁻⁵ dù χ vẫn giảm.
Giảm χ trong hàm số này không tự động chứng minh một security bound tốt hơn.

## 8. Kiểm tra đối chứng hữu hạn và phân rã hai tọa độ

Tất cả dùng **một** exact source có hash của MB cố định, không tạo C,w,
không tối ưu nguồn, không đổi MI, Holevo, ξch hoặc detector.

**A — Giữ hình dạng fading tại 30°:** giữ d, v_log, P1; thay B bằng đúng
A0(ζ)ηatm(ζ), tính lại moment truncated [0,1] không renormalize. K lần lượt
ở 0°,30°,48°,60° là 0.000164574321485, 0.0000966579973751,
0.0000295197716169, −0.000000584962572055; giảm ở cả 30 bước.
Đây là can thiệp số tách hình dạng/phần attenuation; không phải một đường
bay vật lý, vì giữ d cố định khi beam thay đổi là một thao tác nhân tạo.

**B — Giữ nguồn:** dữ liệu gốc fixed MB đã loại hoàn toàn source switching.
Đường vẫn có đỉnh 48°. Không cần tính lại 31 rate lịch sử.

**C — Không fading:** chọn T bằng ⟨T⟩ gốc ở mỗi góc, đặt ⟨√T⟩=√T;
ξfading=0 theo đại số, ξf=ξch. K giảm liên tục, từ
0.00125552146271 ở 0° xuống 0.000425923454623 ở 60°.
Đối chứng giữ mean power, nên khác cả Tf và Rf so với fading; không gọi đây
là hiệu quả thực tế có thể đạt được. Fig. I tách hai thang K bằng panel.

**Phân rã (Tf,Rf):** với nguồn cố định, m1=Tf(1+Rf), mh=√Tf; vì vậy
rate số là hàm f(Tf,Rf). Chỉ 6 khoảng đại diện được kiểm tra thêm. Trung bình
hai thứ tự thay tọa độ cho đóng góp Tf và Rf, tổng đúng bằng ΔK. Đây là
quy ước phân bổ số minh bạch, không phải tỷ lệ nhân quả vật lý duy nhất:

{attrtable}

Trong 48→56°, Rf giảm vẫn đóng góp **+2.85582785892×10⁻⁵**, nhưng Tf giảm
đóng góp **−7.51492103430×10⁻⁵**: K đã giảm trước đáy noise. Trong 56→60°,
cả Tf giảm và Rf tăng đều bất lợi. Điều này giải thích vị trí đỉnh chính xác
hơn cách nói chung “pointing giảm rồi scintillation tăng ở 48°”.

## 9. Vai trò hữu hạn của tối ưu nguồn

`source_optimization_effect.csv` lưu ν,VA, raw K và gain của cả 31 góc.
MB tối ưu đổi nguồn tại 12°,14°,18°,20°,22°,24°; từ 24° đến 60° cùng
(ν,VA)=(0.125,8), nên hoàn toàn không có source switching gần đỉnh 48°.
Uniform đổi VA nhiều lần; từ 42° đến 60° chọn VA=12, nên cũng không đổi
nguồn quanh đỉnh riêng 52°. Tất cả là envelope của các ứng viên exact đã lưu,
không phải tối ưu liên tục. Bước nhảy VA ở 42° là đổi lựa chọn catalog,
không phải lỗi tái dùng kênh. Những đoạn tại biên catalog cần giữ giới hạn
`BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY`.

Tại 48°, gain MB tối ưu so với MB cố định là {float(p48['optimization_gain']):.15g}
bit/use ({gain48:.6f}%, mẫu số là K cố định dương). Hai đường MB cùng đỉnh;
dịch góc đỉnh bằng 0° trên lưới 2°. Đây là gain **chọn nguồn gồm cả VA khác**,
không phải shaping gain ở cùng năng lượng. Uniform dùng nguồn khác nên cân
bằng noise/MI/Holevo khác, đạt đỉnh rời rạc 52°; không có quy luật buộc mọi
nguồn chung một góc đỉnh. Fig. G/H thể hiện trực tiếp kết quả này.

## 10. Bảng đại diện đầy đủ — MB cố định

{rep}

CSV giữ toàn bộ chữ số double đã lưu; bảng 12 chữ số có nghĩa để đọc.
Không dùng các giá trị đã làm tròn này làm đầu vào tái tính. Các đại lượng
khác nguồn, beam, pointing, factor và mọi khoảng liền kề nằm trong CSV riêng.

## 11. Kiểm tra số, lỗi triển khai và giới hạn kết luận

- Đổi độ/radian, L, τ^secζ, beam, jitter, hai HV integrals, Gd, A0, d và
  outage đã đối chiếu lại ở cả 31 góc bằng các hằng số lịch sử; không có cache
  kênh “gần bằng” hoặc lấy kênh của góc trước. Tích phân HV theo độ cao là
  cùng hai số ở mọi góc do các mốc cao không đổi; thừa số slant được tính lại.
- 218 payload, C,w/ν/VA, hex identity, hash ensemble, PMF product, 256 phần tử
  dương, chuẩn VA=2Σp|α|² và geometry được kiểm tra. Không trộn moment MB và
  Uniform. Toàn bộ 6758 hàng ứng viên đã kiểm tra lại noise theo VA tương ứng.
- Raw K của cả 93 nghiệm thỏa βI−χ; residual lớn nhất
  {result['K_reconstruction_max_residual']:.15g} bit/use. Kiểm tra argmax từ
  các hàng đã lưu không phải chạy lại optimizer.
- GH16/32/64 của 93 nghiệm: sai khác tối đa
  {result['selected_GH_max_delta']:.15g} bit, nhỏ hơn ngưỡng cũ 2×10⁻¹³.
  Full-mixture controls cũ khác product tensor tối đa
  {result['saved_direct_mixture_max_delta']:.15g}; đây là **mixture 256 symbol
  trong likelihood Gaussian effective**, không phải integral của true fading
  likelihood. Không dùng kết quả này để gọi Gaussian surrogate là đúng vật lý.
- Bốn accuracy probe fixed MB tại 0°,24°,48°,60° tái lập raw K với residual
  double bằng 0. Entropy độc lập dùng closed spectrum ổn định và precision
  80/110 digits: sai khác lớn nhất khoảng 5.87×10⁻⁸⁰; đối chiếu model string
  cũ 65 chữ số tốt hơn 10⁻⁶⁰. Không cần một chiến dịch accuracy mới.
- Condition number của phép trừ βI−χ tối đa khoảng 510.435 (ở miền gần zero).
  Bước 46→48° bằng 2.864×10⁻⁷ lớn hơn sai khác GH đã quan sát hơn 10⁸ lần;
  không có bằng chứng cancellation/quadrature gây đỉnh đang thấy. Các kiểm
  tra này không là error enclosure trên toàn miền hoặc chứng nhận source AP.
- Một assert ban đầu ở đối chứng deterministic 2° bắt sqrt(T)²≤T tuyệt đối;
  rounding 110 digits tạo dư 4.06×10⁻¹¹⁵, covariance vẫn physical. Lưu lỗi và
  phân tích trong `validation/attempt_1_*`. Guard được sửa để chấp nhận tối đa
  4 ulp của phép sqrt-square tại precision hiện tại; không clip noise, không
  sửa covariance/dữ liệu, không đổi tolerance GH/độ khớp SKR hoặc code cũ.

Không phát hiện lỗi lập trình hình học/noise/cache/plot hoặc sai số số học đủ
giải thích đỉnh trong cấu hình được điều tra. Closure raw-Rytov, horizontal
jitter, angle-independent AoA là **giả định mô hình**, cần tác giả đánh giá;
không gọi chúng là bằng chứng thực nghiệm. Audit mu2 float64 trước ở cấu hình
10 µrad/55 cm không được chuyển thành lỗi của lần quét literal MP này.

### Ranh giới an toàn lượng tử

MI cũ dùng hai thành phần thực với mean 2√Tf(Reα,Imα), variance mỗi thành
phần 1+N; Holevo dùng ν3=√[V(V−Z²/W)], tức conditional **homodyne**.
Một phép đo Bob đơn mode chưa được chỉ định nhất quán cho cặp công thức đó.
Nguồn chính [Denys–Brown–Leverrier, 2021](https://arxiv.org/html/2103.13945v3)
phân biệt các biểu thức phụ thuộc measurement; không cho phép ghép hai biến
đo tuỳ ý. Đối chiếu thêm [audit nội bộ](../../docs/security_model_consistency_audit.md).
Tiền lệ covariance fading của [Usenko et al., 2012](https://arxiv.org/abs/1208.4307)
không chứng minh MI Gaussian effective là true discrete fading MI.

Chưa giải quyết worst-case Holevo trên toàn correlation interval, điều kiện
outage/fading, parameter estimation, aggregation, finite-size/composable.
Do đó không kết luận một hệ homodyne hoặc heterodyne nhất quán sẽ có cùng
đỉnh/miền dương. Không đổi bất kỳ phương trình hay bản thảo nào để sửa lỗi
measurement trong nhiệm vụ này. Frozen-spec SHA thực tế df83ea63…db78c15
vẫn khác hash lịch sử 561fecc9…a2a7b1; giữ blocker đã có, Objective C
`USER_STOPPED` và hai trạng thái cảnh báo. Không truy cập final-test/held-out.

## 12. Trả lời trực tiếp mười câu hỏi

1. **Vì sao tăng từ miền dương đến đỉnh?** Trong 24→48°, giảm χ
   9.02207×10⁻⁴ vượt mất βI 6.68450×10⁻⁴, nên K tăng 2.33757×10⁻⁴.
   Rf giảm do pointing-relative cải thiện thắng scintillation; đối chứng A
   bỏ sự thay đổi hình dạng fading thì không còn đoạn tăng.
2. **Vì sao giảm sau 48°?** 48→50° mất βI 7.87780×10⁻⁵ vượt giảm χ
   7.42210×10⁻⁵. Phân rã tọa độ: −1.76862×10⁻⁵ từ Tf lớn hơn
   +1.31292×10⁻⁵ từ giảm Rf. Từ 56° noise còn tăng thêm.
3. **Tf tăng hay giảm?** Giảm ở đủ 30 bước, từ 2.84995×10⁻⁴ xuống
   1.02776×10⁻⁴; optical transmittance không cải thiện.
4. **Fading noise có giảm trong đoạn K tăng?** Có, và tiếp tục giảm đến
   56°; ξfading tại 24/48/56° là 0.516336/0.306765/0.281799 SNU.
5. **MI và Holevo thay đổi thế nào?** Cả hai giảm tại mọi bước của nguồn
   cố định. MI không tăng; raw K là hiệu của hai đại lượng giảm.
6. **Thành phần nào chi phối?** Giảm χ chi phối 0→48°; mất βI chi phối
   48→60°. Tách vật lý/moment cho thấy suy hao Tf thắng lợi ích Rf sau đỉnh.
7. **Giữ nguồn còn hiệu ứng không?** Có. Fixed MB đã giữ (0.165,5.475)
   ở mọi góc và vẫn có đỉnh rời rạc 48°.
8. **Do kênh, optimizer, hay artifact?** Nguyên nhân trong công thức hiện
   tại là tradeoff kênh/moment đi qua MI–Holevo; optimizer tăng mức K,
   không tạo đỉnh MB. Kiểm tra số không chỉ ra artifact đủ lớn. Giá trị
   vật lý an toàn của hàm K vẫn chưa được thiết lập.
9. **Có lỗi triển khai không?** Không tìm thấy bug hình học, parameter reuse,
   normalization, raw clipping, hoặc quadrature giải thích đỉnh. Có vấn đề
   **measurement pairing** đã xác nhận và các closure mô hình cần author
   review; lỗi assert sqrt-square của script diagnostic đã ghi/sửa riêng.
10. **Có thể kết luận gì?** Giải thích và tái lập được đỉnh của công thức
    số đã lưu, cùng cơ chế giảm relative pointing và tăng scintillation.
    Chưa suy ra achievable secure key, quy luật phổ quát theo khoảng cách,
    góc tối ưu liên tục, hoặc kết quả cho một receiver/security model nhất quán.

## 13. Hình, dữ liệu và cách kiểm tra

Ưu tiên Fig. F → D → E → G. Fig. I/J là bằng chứng đối chứng và factorization;
A/B/C/H hỗ trợ phụ lục. Mọi hình có PDF vector và PNG 350 dpi, Times New Roman,
marker riêng, đường mảnh, grid chấm, legend trong trục, không smooth/interpolate.
Semilog giữ mask K≤0, hình raw giữ toàn bộ điểm âm; Fig. J dùng log vì các
thành phần dương trải hơn hai bậc. Không dùng dual Y-axis cho cùng metric.
Captions tiếng Anh nằm trong `figure_captions_en.md`.

`diagnostic_summary.csv` chứa đủ ba raw curves; `channel_parameters.csv` là
beam/pointing/HV/AoA; `channel_moments.csv` là moment/Rf;
`noise_decomposition.csv` là nguồn cố định; `skr_decomposition.csv` chứa đủ
93 kết quả có nguồn; `adjacent_skr_differences.csv` chứa 30 bước;
`source_optimization_effect.csv` tách envelope nguồn;
`coordinate_attribution.csv`, `controlled_diagnostics.csv` và bảng đại diện
ghi phép kiểm tra bổ sung. Bộ kết quả canonical có 78 lời gọi fixed-source:
31 đối chứng A + 31 đối chứng C + 4 accuracy probe + 12 corner attribution.
Lần chạy đầu dừng ở assert sqrt-square đã thực hiện thêm 3 lời gọi trùng và
1 lần security chưa chạy MI. Tổng gồm cả lần dừng là 81 rate calls hoàn tất;
`validation/execution_history.json` ghi rõ, không gộp chúng thành dữ liệu mới.
Không tính C,w, không chạy lại 6758 ứng viên hoặc bất kỳ mobility simulation.

Để kiểm tra **chỉ đọc**, từ thư mục project:

```powershell
.venv/Scripts/python.exe -X utf8 -B results/zenith_angle_root_cause_diagnostic_20261021/verify_results.py
```

Xem `validation_report.md` và `validation/final_receipt.json` để biết coverage,
hash và giới hạn của kiểm chứng cuối. Không commit/push, không sửa production,
source cache, kênh, bản thảo, detector hoặc lifecycle.
'''
    (OUT/'report_vi.md').write_text(body,encoding='utf-8')
    captions = [
        ('fig_01_original_semilog','Stored raw-rate comparison for optimized Uniform, fixed MB, and catalog-optimized MB 256-QAM. The logarithmic ordinate displays only strictly positive values; omitted nonpositive points remain in the numerical tables. Maxima are evaluated on the original 2-degree grid.'),
        ('fig_02_raw_signed','Signed raw rates for all three source choices on the complete original zenith grid. The zero line separates positive and nonpositive model outputs; no negative values are clipped or replaced.'),
        ('fig_A_geometry_atmosphere','Historical geometry and atmospheric attenuation: (a) propagation distance L=19 sec(zeta) km; (b) atmospheric power transmittance 0.92 raised to sec(zeta). Longer slant paths reduce transmittance throughout the evaluated domain.'),
        ('fig_B_beam_pointing','Beam and pointing quantities reconstructed from the recorded historical parameters: (a) free-space, turbulence-broadened, and equivalent beam radii; (b) total, positional, and angular-jitter displacement variances; (c) peak collection fraction; (d) normalized pointing shape d. The three beam-radius curves nearly coincide at this scale; their separate numerical values are retained.'),
        ('fig_C_scintillation_outage','Scintillation and angle-of-arrival quantities in the historical literal channel: (a) Rytov variance, used directly as the lognormal log variance; (b) corresponding scintillation index; (c) prescribed AoA outage probability. In-FOV probability is one minus the constant outage probability. No alternative aperture-averaging closure is substituted.'),
        ('fig_D_channel_moments','Saved fading-channel moments and algebraic penalties: (a) mean power transmittance and effective transmittance; (b) square-root-transmittance variance; (c) normalized fading penalty Rf. Both transmittances decrease monotonically, whereas Rf reaches its discrete minimum at 56 degrees, beyond the MB rate maximum at 48 degrees.'),
        ('fig_E_noise_decomposition','Effective excess-noise decomposition for the fixed exact MB source (nu_raw,VA)=(0.165,5.475): (a) input-referred fading and total excess noise; (b) effective input-referred physical noise; (c) output-referred total, fading, and physical excess noise. Input- and output-referred quantities are kept on separate panels.'),
        ('fig_F_MI_Holevo_SKR','Fixed-source decomposition of the recorded numerical rate: (a) reconciled two-dimensional mutual information; (b) homodyne-conditioned Holevo expression; (c) their signed difference. Both information terms decrease, but the Holevo reduction dominates before 48 degrees and the mutual-information loss dominates afterward. This mixed measurement convention is not a validated secret-key-rate model.'),
        ('fig_G_source_optimization','Effect of finite-catalog MB source selection: (a) fixed-source and catalog-optimized signed rates; (b) their absolute difference. Both curves attain their evaluated maximum at 48 degrees. The gain includes changes of modulation variance and is not an equal-energy shaping comparison.'),
        ('fig_H_selected_source_parameters','Recorded source parameters versus zenith angle: (a) modulation variance; (b) raw MB parameter. Straight segments connect the actual sampled points and do not imply interpolation of the source catalog. No source switches occur near either reported positive-rate maximum.'),
        ('fig_I_controlled_diagnostics','Fixed-source numerical counterfactuals: (a) the original fading result and a control fixing normalized fading statistics at 30 degrees while varying the historical deterministic factor A0 times atmospheric transmittance; (b) a nonfading channel matched to the saved mean power transmittance. Both controls decrease at all 30 adjacent intervals. These artificial controls are diagnostic interventions, not physical flight trajectories or replacement security models.'),
        ('fig_J_relative_fading_factors','Additive logarithmic decomposition of one plus the normalized fading penalty into pointing, scintillation, and AoA factors for zero boresight. The negligible discarded upper-tail moment is explicitly bounded in the diagnostic tables. Pointing improves while scintillation worsens; the ordinate is logarithmic to resolve their different positive magnitudes.')]
    text = '# English figure captions\n\nAll rate figures use the unchanged historical conditional manuscript model. '
    text += '**UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.** '
    text += 'Markers denote evaluated points; connecting lines provide visual guidance only.\n\n'
    for name,caption in captions:
        text += f'## {name}\n\n{caption}\n\n[Vector PDF](figures/{name}.pdf) · [350-dpi PNG](figures/{name}.png)\n\n'
    (OUT/'figure_captions_en.md').write_text(text,encoding='utf-8')
    (OUT/'README_vi.md').write_text('''# Zenith-angle root-cause diagnostic

Đọc [report_vi.md](report_vi.md), [validation_report.md](validation_report.md)
và [captions](figure_captions_en.md). Ưu tiên Fig. F (MI–Holevo–K), D (moment),
E (noise), G (nguồn); I/J là đối chứng cơ chế. PDF vector + PNG 350 dpi.

Dữ liệu gốc được giữ nguyên. Có 78 phép tính fixed-source canonical có giới hạn
(cộng 3 lời gọi trùng trước lỗi assert đã xử lý; xem execution_history.json);
không optimization, không C,w mới, không mobility simulation. Script renderer
chỉ đọc CSV. Dùng verify_results.py để kiểm tra chỉ đọc; không chạy lại producer
đã hoàn tất. UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
''',encoding='utf-8')
    print('Vietnamese report, English captions, interval table and README written')


if __name__=='__main__':
    main()
