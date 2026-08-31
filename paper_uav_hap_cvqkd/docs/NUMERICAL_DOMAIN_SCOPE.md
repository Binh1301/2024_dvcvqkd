# Numerical domain scope

> Current-state note (2026-08-30): the dense-Fock failure below remains
> relevant diagnostic history. Production now uses cutoff-independent C4
> Gram moments, but no numerical-support threshold is certified. See
> `PROJECT_STATE.md` and EVID-0004 through EVID-0008.

## Scope tested now

The current MI artifact certifies `N_MC=2048` for the sixteen hash-bound
reference fixtures in `MI_CERTIFICATION_ROSTER.md` on the
three preregistered representative validation states. This includes synthetic
C4 peak fixtures at both `V_A=0.1` and `V_A=4`, with
`max_i |alpha_i|^2=30` photons, deterministic learned-family fixtures, and a
near-coincident stress fixture. The Fock gate fails on that stress fixture, so
there is currently no complete reference-suite numerical certificate. It does
not certify a learned checkpoint,
training trajectory, full validation realization, test realization, or the
continuous PS/GS policy domain.

The failing near-coincident fixture is an artificial deterministic diagnostic,
not an ensemble realized by the frozen train, validation, or test datasets. It
is physically admissible under the approved continuous PS/GS/VA and 30-photon
constraints and was added prospectively to the finite reference roster. Its
failure blocks that broad reference-domain gate; it does not prove that a
future exact realized roster fails. Such a roster has not been selected or
replayed and remains unsupported.

The prospective stress-only extension through cutoff 256 also has no stable
suffix. Density trace error stays at roundoff, while the active retained
rank-six support has condition number about `1.73e11` and the independently
resolved full physical spectrum has condition number about `1.78e1098`; the
failure is pseudoinverse support selection rather than Fock-tail truncation.
The complete optimized-
MB grid, threshold gate, and baseline ranking were therefore not run.

The later cutoff-independent high-precision Gram oracle resolves the stress
fixture's complete analytic rank 256 and confirms that the active `1e-12`
eigensupport is the defect: it retains six modes, whereas a prospective
`1e-13` complex128 Gram diagnostic retains eight and agrees with the
full-support oracle within all existing convergence allowances. This is not a
retrospective authorization to change the threshold. It narrows the blocker
and supplies a prospective numerical method; a newly frozen protocol and full
nonselective replay would still be required.

After validation-only model and baseline selection is frozen, the exact
selected-roster gate may add a second, still finite claim: numerical
convergence for every hash-bound selected transmitter reconstructed on the
complete preregistered validation realization. That replay uses the already
selected `N_MC`, Fock cutoff, and pseudoinverse threshold. It cannot change
them or use held-out performance.

## Required nonselective realized-ensemble replay

Every train/validation/test ensemble that enters a final reported result must
also pass a fail-closed post-freeze numerical replay using those same settings.
This replay is a validity check, not parameter selection:

1. freeze datasets, seeds, checkpoint and baseline hashes, settings, and the
   analysis plan before held-out evaluation;
2. enumerate and hash every physical ensemble actually evaluated;
3. enforce C4, energy, `V_A`, and 30-photon peak invariants;
4. replay MI/Fock/threshold checks without consulting comparative performance;
5. if any ensemble fails, invalidate the run and report `NOT_READY`.

A failure may not be repaired by increasing a setting after seeing train,
validation, or test performance. A new setting requires a new prospective
protocol and a completely new experiment; the failed run remains excluded.

## Unsupported scope

No uniform conditioning theorem covers the unrestricted continuous PS/GS
parameter space or unevaluated channel states. Finite realized-domain replay
cannot justify "all PS/GS policies," "uniformly conditioned continuous policy
domain," or equivalent extrapolations.

## Exact wording allowed now

> MI convergence was verified for the hash-bound reference fixture suite, but
> Fock convergence was not certified for the near-coincident stress fixture;
> therefore no complete numerical-convergence or publication-performance claim
> is made. Any future publication claim additionally requires a
> nonselective, fail-closed replay over the exact selected validation roster and
> every realized ensemble entering final evaluation. No uniform-conditioning
> claim is made over the unrestricted continuous PS/GS policy domain.

Wording that says Fock/Holevo convergence or the complete publication domain is
already certified is not allowed at the current lifecycle stage.
