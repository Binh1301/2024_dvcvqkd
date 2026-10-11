# SKR pipeline: hai nhánh và vòng tối ưu

Snapshot cố định:151 nguồn MB ×26 khoảng cách; chi tiết hashes trong documentation_snapshot.json. Sơ đồ mô tả phụ thuộc thực, không là lệnh khởi chạy. Physical Adaptive Optics OFF khác Alternating Optimization.

~~~mermaid
flowchart TD
  subgraph CH["Nhánh 1: kênh vật lý"]
    cfg["default config + overrides theta10/D55"]
    geo["Altitudes fixed; L -> zenith angle"]
    atm["Atmosphere eta = tau_zen ^ sec(zenith)"]
    hv["HV integrals + finite-aperture scintillation v"]
    beam["Gaussian spot + turbulence broadening"]
    point["A0, equivalent width, transverse jitter"]
    aoa["Rayleigh FOV gate; p_in / p_out; atom at zero"]
    moments["Implemented untruncated moments mu1, muHalf"]
    eff["t = muHalf squared; epsilon = 0.0186"]
    cfg --> geo
    geo --> atm
    geo --> hv
    geo --> beam
    hv --> beam
    beam --> point
    cfg --> aoa
    atm --> moments
    hv --> moments
    point --> moments
    aoa --> moments
    moments --> eff
    finite["Separate retained [0,1] PDF / moments diagnostic"]
    moments -. "record discrepancy; no substitution" .-> finite
  end
  subgraph SRC["Nhánh 2: điều chế và mômen nguồn"]
    params["nu_raw, V_A"]
    qam["16 by 16 QAM; canonical unit-RMS coordinates"]
    pmf["MB PMF; nu_repo = 42.5 nu_raw"]
    norm["alpha = sqrt(V_A / (2 E_x)) x"]
    common["Same validated 256-state ensemble"]
    hash["Exact binary64 ensemble / source identity"]
    cache{"Compatible exact C,w stored?"}
    cw["Source moments C,w; distance independent"]
    missing["Missing source: unresolved; do not interpolate"]
    ap["Full-support C4 Gram; AP fallback if authorized"]
    params --> pmf
    cfg --> qam
    qam --> pmf
    pmf --> norm
    qam --> norm
    params --> norm
    norm --> common
    common --> hash
    hash --> cache
    cache -->|"yes"| cw
    cache -->|"no; cache-only"| missing
    cache -. "separate authorized scientific execution only" .-> ap
    ap -. "validated source cache" .-> cw
  end
  mi["Discrete-input heterodyne MI: GH8 product quadrature"]
  z["Direct Z_minus from t, epsilon, C,w"]
  cov["Standard-form covariance + physicality guards"]
  chi["Symplectic eigenvalues + bosonic entropy -> chi_BE"]
  skr["Raw K = 0.95 I_AB - chi_BE"]
  common --> mi
  eff --> mi
  eff --> z
  cw --> z
  common --> cov
  eff --> cov
  z --> cov
  cov --> chi
  mi --> skr
  chi --> skr
  one["One exact objective / context-bound saved result"]
  skr --> one
  opt["P1: search V_A; P2: search nu_raw"]
  one --> opt
  opt -->|"exact new parameter requests"| params
  missing --> status["Preserve open boundary / missing-source / stagnation status"]
  opt --> status
  opt --> winner["Best valid terminal across starts"]
  catalog["Expanded finite exact catalog maximum"]
  one --> catalog
  winner --> compare["Compare original AO versus expanded catalog"]
  catalog --> compare
  near["Stored candidate acceptance: relative SKR loss <= 1e-5"]
  compare --> near
  distances["26-distance tables / curves / exact 2D scatter"]
  near --> distances
  distances -. "next L: rebuild physical context; reuse source" .-> geo
  distances -. "previous winner warm start" .-> opt
~~~

Các factors vật lý là các input song song của moments, không chuỗi mà turbulence phụ thuộc attenuation hay AoA phụ thuộc pointing. C,w chỉ cần cho Holevo; MI cần ensemble và kênh, không cần C,w. Cả MI/Holevo dùng cùng ensemble và epsilon.

Nhánh AP nét đứt mô tả API khoa học khi có quyền chạy riêng; **NOT_RUN** trong tác vụ tài liệu. Finite[0,1] diagnostic không tạo số SKR snapshot: runner gọi untruncated closed_form_channel_moments. Không có stage epsilon_match/fading-noise correction trong đường thực này.

Ở22km original strict AO và catalog151 có kết quả khác; xem saved_AO_vs_catalog151.csv. Near selection dùng catalog best từng distance, không chứng nhận continuous/global optimum hoặc sửa stopping rule AO.
