# Redesigned-baseline global MB/V_A numerical optimization

## A. Baseline audit

- tau_zen: 0.92
- w0: 0.1 m
- D_r: 0.55 m
- r_ap: 0.275 m
- omega_L,eq: 1.41806994941 m
- A0: 0.998118728243
- T_eff: 0.203227370337
- loss: 6.92017802364 dB
- epsilon_total: 0.0186 SNU
- beta: 0.95
- AO = OFF
- PHASE NOISE = OFF
- PEAK CONSTRAINT = OFF
- BUDGET CONSTRAINT = OFF
- HOLEVO = DIRECT Z_MINUS

## B. Uniform optimum

{
  "nu_raw": 0.0,
  "nu_repo": 0.0,
  "VA": 1.075,
  "epsilon_total": 0.0186,
  "peak_photon": 1.4227941176470589,
  "P_peak": 1.4227941176470589,
  "m2": 1.0000000000000004,
  "x_max2": 2.6470588235294126,
  "physical_scale": 0.7331439149307588,
  "feasible": true,
  "H_X": 8.0,
  "N_eff": 255.99999999999994,
  "max_p": 0.00390625,
  "I_AB_GH": 0.14928825824043734,
  "I_AB": 0.14928825824043734,
  "C": 0.9023656334351718,
  "w": 0.019236986168069774,
  "Z_star": 0.8015267775798166,
  "chi_BE": 0.1332722174209635,
  "beta_IAB": 0.14182384532841547,
  "SKR": 0.008551627907451953,
  "ensemble_hash": "58ceb118407aefed1b68f45de5422e33943f4e26dd5b37251c4f99329e7f2589",
  "source_cache_key": "37ee8d498878bf3a4f2f351298ab603116798215645716cdcf2a66069fe8f52b",
  "fresh_or_cache": "FRESH_EXACT_EVALUATION",
  "cache_hit": true,
  "VA_actual": 1.0749999999999997,
  "fourth_moment": 0.4031091911764706,
  "GH_order": 8,
  "holevo_mode": "DIRECT_Z_MINUS",
  "peak_constraint_active": false,
  "budget_constraint_active": false,
  "model_composite_sha256": "a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58"
}

## C. MB global search

- iteration 0: nu_min=CLOSED;nu_max=UNRESOLVED;va_min=UNRESOLVED;va_max=UNRESOLVED
- iteration 1: nu_min=CLOSED;nu_max=UNRESOLVED;va_min=UNRESOLVED;va_max=UNRESOLVED

## D. Best exact candidates

|nu_raw|V_A|I_AB|beta I_AB|chi_BE(Z-)|SKR|
|---:|---:|---:|---:|---:|---:|
|0.0|1.075|0.14928825824043734|0.14182384532841547|0.1332722174209635|0.008551627907451953|
|0.15|3.5548673904962893|0.4441812201448716|0.421972159137628|0.346317801601816|0.07565435753581196|
|0.1|4.0|0.49127547711575836|0.4667117032599704|0.391362549875105|0.07534915338486542|
|0.175|3.0474999561618974|0.38855715411188196|0.36912929640628783|0.29573790032146263|0.0733913960848252|
|0.1|3.025|0.3860396665628114|0.3667376832346708|0.29522921253068324|0.07150847070398758|
|0.2|2.6666460605961313|0.3453470542583945|0.3280797015454748|0.2572240651128146|0.07085563643266019|
|0.225|2.370366810924743|0.3108139605505156|0.2952732625229898|0.2270223696624878|0.06825089286050201|
|0.22|2.15|0.2845819923977331|0.2703528927778464|0.2044858430336003|0.06586704974424612|
|0.0|1.075|0.14928825824043734|0.14182384532841547|0.1332722174209635|0.008551627907451953|

## E. Boundary diagnostics

{
  "nu_min": {
    "status": "CLOSED",
    "exact_points": 9
  },
  "nu_max": {
    "status": "UNRESOLVED",
    "exact_points": 0
  },
  "va_min": {
    "status": "UNRESOLVED",
    "exact_points": 0
  },
  "va_max": {
    "status": "UNRESOLVED",
    "exact_points": 0
  }
}

## F. Final result

{
  "nu_raw": 0.15,
  "nu_repo": 6.375,
  "VA": 3.5548673904962893,
  "epsilon_total": 0.0186,
  "peak_photon": 29.99999999999999,
  "P_peak": 29.99999999999999,
  "m2": 0.15683238487483636,
  "x_max2": 2.6470588235294126,
  "physical_scale": 3.366501646120692,
  "feasible": true,
  "H_X": 5.8308510083515195,
  "N_eff": 56.919497027635835,
  "max_p": 0.044297303045121986,
  "I_AB_GH": 0.4441812201448716,
  "I_AB": 0.4441812201448716,
  "C": 2.221868916147515,
  "w": 1.2741577947753198e-06,
  "Z_star": 2.003172040142379,
  "chi_BE": 0.346317801601816,
  "beta_IAB": 0.421972159137628,
  "SKR": 0.07565435753581196,
  "ensemble_hash": "c3603a3ba5d2867c2db311e6a4a2424f291813088f72a1888c2a4a95e7a77cc7",
  "source_cache_key": "f46625bb2b1d5afb75f92d2c9c8759ccf4cbf6304a09f1bbb572a99ac0393e1f",
  "fresh_or_cache": "FRESH_EXACT_EVALUATION",
  "cache_hit": true,
  "VA_actual": 3.5548673904962897,
  "fourth_moment": 6.31332366535799,
  "GH_order": 8,
  "holevo_mode": "DIRECT_Z_MINUS",
  "peak_constraint_active": false,
  "budget_constraint_active": false,
  "model_composite_sha256": "a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58"
}

GLOBAL_OPTIMUM_UNRESOLVED
