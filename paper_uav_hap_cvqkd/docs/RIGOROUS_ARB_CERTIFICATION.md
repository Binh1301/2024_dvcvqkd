# Experimental Arb Whole-Segment Certification

Status: `EXPERIMENTAL_PROPOSED_NOT_APPROVED`

This backend is certification-only. It neither replaces the production
complex128/PyTorch implementation nor approves a numerical-support threshold.
Configured `1e-12` remains invalid/unapproved and candidate `1e-13` remains
proposed/unapproved.

## Isolated environment

From the project directory on Windows PowerShell:

```powershell
python -m venv .venv-cert
& .\.venv-cert\Scripts\python.exe -m pip install --require-hashes -r requirements-certification-flint.lock
& .\.venv-cert\Scripts\python.exe scripts\capture_flint_certification_environment.py
```

The locked backend is python-flint 0.9.0 with bundled FLINT 3.6.0 and
PyYAML 6.0.3. `.venv-cert` is ignored and deliberately separate from the
publication environment.

## Exact fixture export

The fixture producer runs in the locked production environment solely to
reconstruct the frozen transmitter and serialize each parameter and channel
feature as an exact `float.hex` value:

```powershell
& .\.venv\Scripts\python.exe scripts\freeze_rigorous_segment_fixture_bundle.py
```

The isolated certifier imports neither PyTorch nor NumPy. It reconstructs every
binary64 value as an exact dyadic Arb number.

## Enclosure method

For each straight parameter segment `theta(t)=theta_0+t*(theta_1-theta_0)`,
the backend propagates Arb/acb balls through the actual frozen path:

1. affine/ReLU/affine/softmax probabilistic shaping;
2. affine/ReLU/affine/sigmoid/bounded log-domain modulation variance;
3. GS prototype interpolation and unit-RMS gauge;
4. probability-weighted physical energy normalization;
5. analytic coherent-state overlaps; and
6. the four Hermitian 64-by-64 C4 Gram sectors.

Ambiguous ReLU inputs use the full `[0, upper]` enclosure. For each path
interval, the certifier constructs an exact-midpoint sector enclosure and a
rigorous Frobenius upper bound on the interval-minus-midpoint perturbation.
Validated `acb_mat.eig(multiple=True)` eigenvalue balls are classified by
strict Weyl margins. Unresolved intervals are bisected dyadically; arithmetic,
eigensolver, precision, node, depth, or time failures reject.

The `approx` eigensolver is forbidden. Finite-node ranks and ordinary
float64/`nextafter` values are never accepted as proof.

## Verification and realized result

```powershell
& .\.venv-cert\Scripts\python.exe -m unittest -v tests.test_rigorous_flint_support
& .\.venv-cert\Scripts\python.exe scripts\certify_rigorous_whole_segment_support.py
```

The 11 requested regression classes pass. The frozen realized run attempted
all 12 state/family segments and returned 0 certified, 0 rigorous crossings,
and 12 unresolved in 1061.9827932000626 seconds. Every endpoint spectrum
failed validated full eigenvalue isolation at 160, 256, and 384 bits despite
multiplicity handling, so no realized interval reached subdivision.

Consequently, realized interval perturbation-radius/observed-change ratios and
certified spectral margins are unavailable rather than inferred. The next
prospective method must provide validated threshold-relative Hermitian inertia
or an equivalent eigencluster enclosure without requiring isolation of every
extremely small eigenvalue.

## Artifacts

- `results/certification_flint_environment.json`
- `results/rigorous_segment_fixture_bundle.json`
- `results/rigorous_whole_segment_certification.json`
- `configs/rigorous_whole_segment_support.yaml`

All artifacts keep threshold approval, optimizer integration, publication
training, optimized-MB selection, baseline selection, and final-test access
false.
