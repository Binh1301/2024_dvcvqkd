# MI certification roster

Status: **SOFTWARE_PREREGISTERED before sequential convergence outcomes**.
This roster uses validation states only. It neither reads the final test set nor
authorizes publication training.

## Frozen sequential rule

- Per-symbol counts: `256, 512, 1024, 2048, 4096, 8192`.
- Five independent base seeds: `202607..202611`; each derived CRN stream is
  reused across configurations and nested across counts.
- Unchanged tolerance: `0.002 bit + 0.001 |I_current|`.
- Stop at the first count for which two consecutive global refinements pass
  for every state, canonical fixture, and replication, and every replication
  is within the same tolerance of its replication mean at both stages.
- Float64/complex128 and the exact 256-state mixture are mandatory.

The canonical JSON roster hash is
`e91c2f9ded0c665e781a450286ffc01633e310a95d77e923efb3b9516791b531`.
The validation realization hash is
`247b428bb5dcbaf5e532ecd15a3b46efdf07bdcc47759348a8625576c2c4c500`.

## Classification of the expanded 90 public / 80 canonical units

Each unit is one fixture and one replication; its three preregistered channel
states are evaluated together.

| Fixture class | Classification | Units |
|---|---:|---:|
| Sixteen byte-distinct canonical fixtures | A/D: distinct or retained because no convergence-error reduction is proven | 80 |
| optimized-MB `nu=0`, low VA | B: exactly Uniform low VA | 5 |
| optimized-MB `nu=0`, high VA | B: exactly Uniform high VA | 5 |

The two category-B identities follow directly from
`exp(-nu |x|^2)` at `nu=0`: every symbol weight is one, so its PMF and
normalized amplitudes are byte-identical to Uniform at the same VA. Runtime
also verifies exact tensor equality after matching SHA-256 hashes. No fixture
was removed based on similar numerical outcomes. No monotonic-convergence
reduction (category C) is asserted. C4 rotations are already represented
inside each exact mixture and are not separate roster units.

The eleventh canonical fixture was added prospectively after the security audit
identified that the earlier `V_A=0.1` peak case did not cover the approved
adaptive `V_A=4` boundary. Its peak orbit has exact mass `1/29`, the remaining
63 orbit masses share `28/29`, peak energy is 30 photons, and all remaining
orbit prototypes have energy 1 photon. Thus its mean photon number is exactly
`(30/29)+(28/29)=2`, or `V_A=4`.

Five additional outcome-independent fixtures exercise nontrivial PS-only,
GS-only, VA-only, jointly deformed Full, and near-coincident/pseudoinverse
stress behavior. They are deterministic parameter vectors, not trained or
validation-selected checkpoints.

## Sixteen canonical fixture hashes

| Fixture | SHA-256 |
|---|---|
| `uniform_low_va_0.1` | `a793b7c6ccc837ac65ae619d721a1120ce99003834fbf6e3d15141e121f7be0f` |
| `uniform_high_va_1.5` | `23da6caeead82b36f8733b9e57b2fb3963c68e8734c760355f42f6395955a804` |
| `binomial_low_va_0.1` | `a21940562f59b1a49fc2d30894dea0aa73896e5567f293dee8b6767833662e33` |
| `binomial_high_va_1.5` | `a656092de81d33d1cb721d66279504b4d193cd1999424c9f519190111cca6902` |
| `fixed_mb_low_va_0.1` | `4f00675bca326ef869cd6ceff238775e1c8bc70ec06f2d28f0a95c04e71c4dbe` |
| `fixed_mb_high_va_1.5` | `5a655a17e61b4db7c845adb77346c1635a65003d19a253577c9b206a5829da6a` |
| `optimized_mb_nu_0.3_low_va_0.1` | `19ac651a574e27543529caee5ea107ee97bcbb6fb722969d2abac8debdfdb49b` |
| `optimized_mb_nu_0.3_high_va_1.5` | `863ef0729d33432ce5018c4b565b07e49a7c622d3ddbec659e2c8c6c09fbaa47` |
| `untrained_full_initialization` | `f7128dc210719de3942c4af8e2a47811d6994b746b06c1001dea542b39fbe8c4` |
| `deterministic_ps_only` | `bd4603f58aecac280dd5adc740d234f7aaf4a7279fc5aa84933b631625e03891` |
| `deterministic_gs_only` | `44f6055092c4bfd80789e942f1d46e57dfa64170c7137c02d178e72893a4973b` |
| `deterministic_va_only` | `35416ab56bbbafbc0afba782de3fe3d1231ad1d5663bdecf1d15c400f29410bd` |
| `deterministic_deformed_full` | `9c7cc47a202f6fbbd6f08db19cd3c09df4dd74cf8653d28388b88ebf8a070362` |
| `near_coincident_pseudoinverse_stress` | `4d36a48e7cb13f5f3bb91c86139d17ddcff6ea213cab4a89d2cb06d69b9501e8` |
| `hard_peak_boundary_at_vmin` | `d0d8bcef1d9b62c8cb1596687c29b195e263013424783032b0cdfd04bbd65502` |
| `hard_peak_boundary_at_vmax` | `d0fc0935a919bd7491743ad8f4e66ae1badda6c7cca42092023c90ca4ff6f761` |

The diagnostic learned initialization uses isolated fixed seed `202613`;
construction saves and restores global RNG state.
