# Phase5E ? full clear-sky SKR lookup t?i channel noise0.0136 SNU

**Tr?ng th?i: CURRENTLY_VERIFIED_PASS ? full numerical diagnostic ?? ho?n t?t.**
T?c gi? ?? ph? duy?t r?294 geometries,212 candidates/group v?2processes; kh?ng
c?n th?m x?c nh?n. Snapshot chu?n b? tr??c ph? duy?t v?n gi? ri?ng; tr?ng th?i
hi?n h?nh ???c ch?ng minh b?i approval/preflight v? artifacts b?n d??i.

## 1. D? li?u v? s? l??ng th?c t?

Th? m?c k?t qu? m?i:
[phase5d_full_target_radial_2proc_PHASE5E_20261108](.).
T?n gi? prefix phase5d_ ?? d?ng nguy?n executor ?? ???c chu?n b? v? ki?m th?.

- [CSV2601 positions](./skr_map.csv).
- [NPZ points/rates v? metadata](./skr_map.npz).
- [Core summary/runtime](./summary.json).
- [Validation/pilot/direct checks](./phase5e_validation/validation_summary.json).
- [Geometry mapping2601?294](./phase5e_validation/geometry_mapping.csv).

| Quantity | Actual |
|---|---:|
| Spatial positions | 2601, ??ng51?51 ordered grid |
| Unique geometries | 294 |
| Candidates m?i geometry | 212:179MB +33Uniform |
| Main candidate evaluations | **62,328 fresh calls** |
| Independent original-position checks | 7positions?212 =**1,484 fresh calls** |
| T?ng calls trong task | **63,812**; t?ch main v? validation |
| Worker processes | 2 |

Kh?ng b? candidates ho?c c? ??nh winner. CSV gi? c? MB v?Uniform per-family
signed-K argmax nh? policy c?; `skr_bits_per_use` v? `K_raw_bits_per_use` l?
MB raw rate, potential ???c l?u ri?ng. C?c s? d??i ??y t?nh theo **2601 spatial
positions**, kh?ng l?y mean kh?ng tr?ng s? tr?n294 groups.

## 2. Raw SKR v? selected parameters

| MB raw SKR | bits/use |
|---|---:|
| Minimum | **0.004893349597699492** |
| Mean | **0.004933919138761928** |
| Maximum | **0.00495533778991275** |
| Negative/zero MB map positions | 0 /0 |

So s?nh to?n b?212 candidates theo original catalog order cho th?y MB th?ng
**2601/2601 positions (100%)**, Uniform0/2601. ??y l? k?t qu? t?m ?? catalog,
kh?ng ph?i gi? ??nh t? n?m pilot points.

| Global winning family | VA | nu_raw | Positions |
|---|---:|---:|---:|
| MB | 1.358333319784304 | 0.3 | 2601 |

Convention nu_repo=42.5*nu_raw v?n gi?; nu trong b?ng l? **raw convention**.
VA=Vmod=2*nbar c?a module gi? nguy?n. ??y l? best-tested finite-catalog
selection, kh?ng ch?ng nh?n optimum li?n t?c ho?c t?i ?u to?n c?c modulation.
[Spatial winner analysis](./phase5e_validation/spatial_winner_analysis.csv)
ghi family,VA/nu v? evidence cho t?ng v? tr?.

## 3. Runtime v? memory th?c t?

| Measurement | Actual |
|---|---:|
| Full command wall-clock end-to-end | **680.8145s ?11.35 ph?t** |
| Measured main stage, g?m workers/checkpoint | 663.3379s |
| Parent native initialization resource wall | 11.8443s |
| Main evaluator throughput | 93.9612calls/s |
| Sampled aggregate parent+children RSS peak | **1,735,127,040 bytes ?1.616GiB** |
| Sampled process-tree CPU time | 984.2969CPU-s |
| Direct-check stage, t?ch ri?ng | 25.7323s,1484calls |

RSS l?y m?u v?i50ms wait c?ng collection overhead, c? th? ??m shared pages
nhi?u l?n; kh?ng g?i ??y l? peak li?n t?c ch?nh x?c ho?c RAM v?t l? kh?ng tr?ng.
Main end-to-end time ???c Stopwatch ?o bao g?m startup/initialization/export;
kh?ng c?ng direct checks v?o680.8145s. ETA13.5ph?t t? Phase5D l? projection;
l?n th?c t? n?y nhanh h?n nh?ng kh?ng suy speed guarantee cho run/host kh?c.
[Execution metadata](./phase5e_validation/execution_metadata.json)
ghi nguy?n telemetry v? command ?? ch?y.

## 4. Exact deduplication v? ki?m tra ??c l?p

Preflight ki?m2601 coordinates/order,294 keys t? rational/integer radius? v?
ch?ng minh c?c key b?ng ch?nh float keys c?a executor, kh?ng coarse rounding.
Trong m?i group, native zenith v? L ??u bit-identical; protocol/ordered pool/
active noise c?n l?i gi?ng h?t. Current clear-sky producer nh?n zenith+protocol,
pointing/position jitter ??ng h??ng,zero boresight,scalar RMS wind/FOV; kh?ng c?
azimuth ho?c cloud input b? lo?i. Invariance ch? ?p d?ng **producer n?y**,
kh?ng ?p cho dynamic LOS blockage.

Sau full run, g?c ???c d?n xu?t l?i t? original coordinates b?ng
`waypoint_geometry` v?i HAP(1000,1000,20000)m v? UAV altitude1000m; kh?ng d?ng
group ID ho?c lookup angle l?m input cho direct producer. Projection n?y l?
geometry c?a dataset ?? ???c ph? duy?t, kh?ng t? ch?n HAPxy cho mission m?i.

C?c direct positions: (1000,1000),(2000,2000),(1960,2000),(1000,1040),
(520,1000),(280,1720),(1880,400)m. M?i v? tr? ch?y nguy?n212 candidates m?i;
14 comparisons MB/Uniform ??u PASS, **max deviation0 binary64** cho T_f,xi_f,
I_AB,chi_BE,K_raw v? selected-source identity. ??y l? independent geometry-path
recomputation d?ng c?ng quantum implementation, kh?ng ph?i m?t ch?ng minh
??c l?p l?i Z/w ho?c security functional.

N?m target pilot Phase5C ???c ki?m original seals/config/physical/active-noise
v? native producer identity, r?i ??i chi?u:

| Pilot | x,y (m) | Max deviation c?c metrics |
|---|---|---:|
| p0 | 1000,1000 | 0 |
| p1 | 1480,1000 | 0 |
| p2 | 0,0 | 0 |
| p3 | 1000,960 | 0 |
| p4 | 40,0 | 0 |

Tolerance gi? atol2e-10,rtol0 v? exact source/VA/nu identity, kh?ng n?i sau
xem k?t qu?. Native GH64/128 MI guard2e-10 v?80/110-digit guard2e-11 gi? nguy?n;
max GH difference full map **5.551115123125783e-16**. Kh?ng c? native numerical
exception, missing/nonfinite candidate ho?c incomplete geometry.

## 5. Provenance, schema v? readiness t?ch h?p

Config ???c ph? duy?t:
`0671e70ef5a5a78afed6f750859161439153f2030fe6e6b733a216f1f6616111`.
Ordered candidate-pool hash:
`adb057572d5b22be1718bb7535e402129b16af813cc863d2e62b2028c0c36539`.
Executed native executor/source hashes v? execution-config hash n?m trong
`input_manifest.json`, `executed_producer_snapshot.py` v? NPZ metadata. Seed=null:
source vectors, analytic moments,GH v? multiprecision l? deterministic.

Native physical contexts ???c sinh m?i v?i original validated protocol;
target N ???c nguy?n evaluator t?nh t?(m1-mh?)*VA+.0136*m1+.005*M0. Kh?ng
??i nh?n channel.0186 l?ch s? th?nh.0136. Detector.005 v?n l? term ri?ng.
[Target protocol metadata](./phase5e_validation/target_effective_protocol.json)
ghi r? physical-context lineage v? active target noise.

?? verify594 core output hashes,552 inputs,60 producer entries,294 point
seals,212 candidates/geometry, both families/argmax, coordinates/order, raw vs
potential, metadata/units/noise/evidence arrays v? CSV/NPZ equality. C? hai
format load b?ng numeric `SKRLookup` API v? truy v?n l?i to?n b? nodes PASS.
**Technically ready cho matched-context numerical solver integration**, v?i
rate bits/use; ch?a t? c?p positive scientific admission c?a strict reference
loader, ch?a x?c nh?n interpolation error off-grid ho?c mission/paper readiness.
Kh?ng t?ch h?p m?y hay ch?y trajectory trong task n?y.

Evidence c?a62328 candidate evaluations ???c gi? t? source pool:
55860 `INSUFFICIENT_EVIDENCE`,6174 `VERIFIED_EXACT`,294
`VERIFIED_BY_ALTERNATIVE_EVIDENCE`; kh?ng reclassify. Winning MB source v?n
`INSUFFICIENT_EVIDENCE`. `paper_admissible=false`,security_valid=false,
finite-size proxy/composable-security limitations v? NOT_READY lifecycle kh?ng
??i. Frozen-spec discrepancy l?ch s? ???c l?u trong preflight, kh?ng s?a spec.
Catalog v?n1 READY/9 BLOCKED; kh?ng mark h?nh READY do regeneration.

## 6. Tests, review v? package seal

**177 passed in10.65s,0 failed,0 errors,0 skipped**:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5e_validation/tests.xml
```

C?10 tests m?i cho coordinate-derived checks, signed raw/winner identity,
Windows manifest path normalization/collision, NPZ metadata rejection v?
pilot seal/five-point completeness. Review ??c l?p code/preflight t?m ba
validation-contract issues; ?? s?a RED?GREEN trong **module validation m?i**,
kh?ng s?a executor/producer. Final artifact peer review kh?ng ho?n t?t do
h?n m?c subagent; final artifact/hash validation do ch??ng tr?nh v? agent
ch?nh th?c hi?n. Direct numerical recomputation7positions ?? ch?y th?c nh? tr?n.

Core `output_manifest.json` ???c gi? nguy?n sau main job. Preflight,approval,
mapping,tests,report v? direct-check artifacts ???c append m?t l?n v?o
`phase5e_validation/`, v?i seal ri?ng v? `phase5e_package_manifest.json` bao
ph? to?n b? package cu?i; kh?ng rewrite core data ho?c metadata ?? che history.
B?o c?o pending tr??c approval ???c archive ri?ng trong docs validation.

Kh?ng s?a Z/w, MB-QAM/Holevo,rotor profiles,`paper.yaml`,old lookup/pilot ho?c
figures. Kh?ng cloud integration,paper-mode,commit ho?c push. C?c quy?t ??nh
mission/cloud/protocol/security c?n thi?u v?n thu?c task ti?p theo.
