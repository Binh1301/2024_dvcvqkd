# Prospective pointwise guard protocol V2

Status: **PROPOSED; IMPLEMENTED AND FROZEN; SMOKE EXECUTION AUTHORIZED**.

The machine-readable contract is
`configs/pointwise_guard_protocol_v2.yaml`, validated by
`schemas/pointwise_guard_protocol_v2.schema.json`. V1 and its completed smoke
artifact remain immutable historical evidence. The implementation and
execution manifest are now frozen. This document authorizes only the scoped
V2 smoke execution; it does not approve the threshold, training, baseline
selection, or test access.

## Three separate claims

1. **Support certification.** Every eigenvalue must be rigorously classified
   relative to the exact dyadic `tau`, either by a complete validated inertia
   certificate or by Arb eigenvalue enclosures wholly separated from `tau`.
2. **Certified distance.** For all enclosures below `tau`, let `U_-` be their
   maximum upper endpoint. For all enclosures above `tau`, let `L_+` be their
   minimum lower endpoint. Equivalently, validated inertia-count changes may
   directly bracket the adjacent eigenvalue on each side. Define

   ```text
   certified_margin = min(tau - U_-, L_+ - tau).
   ```

   Because `U_-` and `L_+` are the inward-facing outward-rounded endpoints,
   this is already a rigorous lower bound on spectral distance from `tau`.
3. **Engineering or gradient safety.** A positive buffer beyond the certified
   distance would be a separate optimization policy. Existing finite-difference
   evidence does not calibrate such a buffer, so V2 fixes it at zero.

## Admission rule

```text
POINTWISE_ADMISSIBLE iff
    support is rigorously certified
    AND certified_margin > 0.
```

`uncertainty_upper`, when reported, is diagnostic only. Subtracting the
outward interval endpoint in `certified_margin` has already accounted for
interval uncertainty. Charging `2 * uncertainty_upper` again is not needed
for support or distance certification and has no independent gradient-safety
justification in the repository evidence.

An implementation must make the strict comparison in Arb or equivalent exact
arithmetic. It must not select an alleged adjacent eigenvalue only by interval
midpoint, and it must not nearest-round an Arb endpoint to binary64 before the
admission decision. For a direct eigenball result, `U_-` and `L_+` are global
extrema over all classified balls. Any overlap, equality, incomplete spectrum,
non-Hermitian result, resource limit, or provenance failure fails closed.

## Gradient scope

The existing diagnostic covers 12 PS/GS/VA coordinates. It reuses common
random numbers, requires every plus/minus evaluation to preserve the center
support mask, and requires at least three consecutive stable finite-difference
step pairs under the frozen `1e-7 + 5e-3 scale` rule. It supports a local
fixed-support derivative claim only. It proves neither a universal
neighborhood radius nor any multiplier of an Arb interval width.

Pre-update rejection, post-update endpoint certification, complete rollback,
and all V1 transaction/provenance requirements remain in force. No
interpolation segment or whole trajectory is certified.

## Frozen prospective smoke settings

Any later V2 smoke must use the same `bad/medium/good` roster, initialization
seed `202613`, common-random seed `202615`, six steps, two repetitions, Arb
precision schedule, Adam settings, learning rates, gradient clipping, energy
dual settings, regularizers, physical model, `tau`, MI, and security
functional as V1. That exact execution is now authorized but has not run.

Candidate `1e-13` remains `PROPOSED_UNAPPROVED`; historical `1e-12` remains
`INVALID_UNAPPROVED`.
