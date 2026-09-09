# Paper-to-code map

Current-manuscript source for the active amendment:
`C:\Users\HP\Downloads\2026__Binh_s_work (22).pdf`, inspected September 9,
2026.  The prior `(8).pdf` mapping is historical where it conflicts with
`MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md`.

| Paper item | Equations | Implementation | Called by / status |
|---|---:|---|---|
| HAP/UAV geometry | 1 | `src/channel/geometry.py::LinkGeometry` | Channel scripts/tests |
| Pure-loss operator statement | 2--6 | Protocol context only | No Fock channel simulation is needed for the stated rate model |
| Atmospheric loss | 7--9 | `src/channel/atmospheric_loss.py` | `sample_fso_channel` |
| Beam propagation/aperture | 10--15 | `src/channel/pointing_error.py::gaussian_beam_radius`, `pointing_parameters` | Channel sampling |
| UAV position/orientation variance | 16--18 | `src/channel/turbulence.py::UavMotion`, `uav_misalignment_variance_m2` | Channel sampling; Table I values in `configs/channel.yaml` |
| Turbulence variance | 19--20 | `turbulence_beam_wander_variance_m2` | Includes explicit `cos^-4(zeta)` |
| Cartesian/radial displacement | 21--26 | `per_axis_displacement_variance_m2`, NumPy Rayleigh draw | Frozen `sigma_axis` interpretation |
| Pointing loss/shape | 27--34 | `pointing_parameters`, `pointing_power_transmittance` | Direct evaluation |
| Pointing PDT transformation | 35--41 | Direct sampling instead of analytic density | Equivalent accepted computation; explicit PDF not implemented |
| Composite channel/PDT | 42--48 | `src/channel/fso_channel.py::sample_fso_channel` | Returns instantaneous `T_n` |
| Mean channel/rate order | 49--55 | `ChannelSamples.mean_transmittance`; `fading_secret_key_rate` | Mean is descriptor; raw rates averaged after statewise evaluation |
| Baseline-noise state | Current manuscript state equations | `src/channel/state_distribution.py`; `src/cvqkd/protocol.py` | Independent bounded-uniform `epsilon_base` sensitivity domain; no empirical `T`--`epsilon_base` coupling is asserted |
| Turbulence phase distortion | Current manuscript pp. 7--8, Eqs. 90--108 | `src/channel/phase_noise.py` | `Cn_phi2` is external fixed `m^-2/3` scenario input; SI wavelength/link length; never reuse HV/beam-wander `Cn2(h)` |
| Post-action total noise | Current manuscript pp. 7--8, Eqs. 93--103 | `phase_excess_noise`, `total_excess_noise`, `evaluate_transmitter` | `epsilon_total=epsilon_base+c_phi V_A`; same tensor reaches MI and Holevo |
| Square QAM | 65--71 | `src/modulation/qam256.py::square_qam256` | `k*16+l` ordering |
| Uniform/binomial/MB | 72--81 | `uniform_pmf`, `binomial_pmf`, `maxwell_boltzmann_pmf` | Baseline script |
| Instantaneous ensemble/SKR | 82--90 | `src/modulation/joint_ps_gs.py::Ensemble`; `fading_secret_key_rate` | Common object is shared by MI/Holevo |
| Source entropy and channel density | 91--97 | `src/cvqkd/mutual_information.py` | Exact symbol enumeration |
| MI Monte Carlo | 98--102 | `discrete_mutual_information` | Independent explicit RNG stream |
| Density operator | 103--104 | `src/cvqkd/holevo.py::density_operator` | Correct ket--bra orientation |
| Coherent correlation | 105 | `holevo_information` | Differentiable Fock calculation |
| Transformed annihilation/penalty | 106--108 | `holevo_information` | Pseudoinverse threshold reported |
| Correlation interval / physical domain | Current manuscript pp. 13--16, Eqs. 176--222 | `holevo_information`, `physical_correlation_bound` | Records `Z_-`, `Z_+`, `Z_phys`, intersection, endpoint values; empty domain is a structured failure |
| Standard covariance | 111--116 | `src/cvqkd/covariance.py::standard_form_covariance` | Asymmetry guard defaults strict |
| Symplectic eigenvalues | 117--122 | `standard_form_covariance` | Material invalidity raises |
| Bosonic entropy/Holevo maximization | Current manuscript pp. 13--16 and 26--29 | `bosonic_entropy`, `holevo_information` | Ideal heterodyne, asymptotic; numerical full-interval max with recorded `Z_star`, not fixed lower endpoint |
| Fading-average chain | Current manuscript pp. 13--16 | `src/optimization/trainer.py`; `fading_secret_key_rate` | `epsilon_total` and worst-case interval Holevo evaluated statewise before average |
| CSI acquisition/feedback | 138--144 | `ProtocolAssumptions`, `ChannelSamples.metadata` | Exact-CSI oracle only; estimator is missing from paper |
| Frozen C4 PS policy | `FINAL_MODEL_SPEC.md` Sec. 2.1 | `ProbabilisticShapingNetwork` | `2-128-64`, then exact orbit expansion |
| Global GS | 151--153 | `GlobalGeometricShaping` | Shared across states |
| Frozen physical normalization | `FINAL_MODEL_SPEC.md` Sec. 3 | `physical_amplitudes` | One scalar per state; no weighted centering |
| Adaptive variance | 161--166 | `AdaptiveVarianceNetwork` | `V_min/V_max` mandatory |
| Physical amplitudes | 167--169 | `physical_amplitudes`, `Ensemble.validate` | Statewise `V_A` equality asserted |
| Shared MI/security ensemble | 170--176 | `evaluate_transmitter` | One `Ensemble` passed to both branches |
| Variance sensitivity statement | Current manuscript pp. 26--29 | Autograd through `AdaptiveVarianceNetwork` and `c_phi V_A` | Piecewise differentiable away from interval-maximizer switching points; no stationary-solution claim |
| Training objective | 182--185 | `src/optimization/trainer.py::train_step`; optional expression in `src/optimization/losses.py::paper_loss` | Executed path uses Eq. (184), i.e. all optional Eq. (185) regularizer coefficients are zero until their coefficients/gauge are scientifically frozen |
| Gradient paths | 186--190 | Torch graph; `tests/test_gradients.py` | Local, finite-difference, and end-to-end SKR checks cover PS, GS, and `V_A`; C4 symmetry remains valid after smoke updates |
| Training configurations | 191--195 | `JointTransmitter.MODES`; training scripts | Uniform/binomial/fixed and selected MB, PS, GS, VA, PS+GS, PS+VA, GS+VA, full |
| Numerical results | Section V | **MISSING FROM PAPER** | No result or figure copied/invented |
| Conclusion | Section VI | **MISSING FROM PAPER** | No claim implemented |

The draft contains one table (UAV motion parameters) and no research figures or numbered algorithm. Future figure mappings must be added only after the paper defines them and raw numerical data is generated from a resolved configuration.
