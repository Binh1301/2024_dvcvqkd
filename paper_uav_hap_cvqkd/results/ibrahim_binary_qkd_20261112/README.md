# Independent QKD-aware binary cloud diagnostic

Read report_vi.md first. Official 0.55 m QKD threshold is PENDING.
0.1 dB is an explicitly illustrative diagnostic only; no automatic official fallback.
Input arrays are immutable, axis order [t,y,x]. Diagnostic baseline feasibility
is assumed. These are vertical-reference cloud columns, not ray-traced UAV links.

Reproduce from paper_uav_hap_cvqkd/ in a fresh directory:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/run_ibrahim_binary_qkd.py --output results/ibrahim_binary_qkd_new
.\.venv\Scripts\python.exe -X utf8 -B scripts/plot_ibrahim_binary_qkd.py results/ibrahim_binary_qkd_new
.\.venv\Scripts\python.exe -X utf8 -B scripts/report_ibrahim_binary_qkd.py results/ibrahim_binary_qkd_new
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_ibrahim_binary_qkd -v
```

Pure classifier: src/ibrahim_binary_qkd.py::classify_attenuation.
No SKR formula or Gaussian generator is called by the conversion.
binary_blockage: uint8 0/1/255(unknown); qkd_available: bool, False at unknown;
always carry resolved_mask and scope. clear_sky_available is 0/1/255, compare ==1.
classification_status: 0 validated-input assumption,1 clear-unavailable,
2 unresolved,3 diagnostic-assumed. Never cast unknown states to availability.
NaN/Inf A or thresholds do not produce available links.

Optional binary_effective_approximations is a separate surrogate interface;
it refuses unresolved cells and requires actual clear T/R inputs. No such
physical approximation arrays are fabricated in this delivery. Physical cloud
transmittance remains in its original NPZ, referenced with its checksum.

Diagnostic datasets have diagnostic_ prefixes. official_pending_status.npz
has only unresolved official classification, no official critical threshold.
statistics.json and frame_blockage_statistics.csv define exact populations.
Figures A-F are PNG400dpi/native-vector PDF; G is a1000-frame GIF.
Complete file/hash index: artifact_hashes.json. Read-only verification:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/ibrahim_binary_qkd_20261112/verify.py
```

The delivered verifier requires sealed export/provenance/test evidence; a fresh
numerical-only run needs export QA and sealing before it becomes a sealed package.
Do not use the illustrative result as official QKD outage or trajectory reward.
