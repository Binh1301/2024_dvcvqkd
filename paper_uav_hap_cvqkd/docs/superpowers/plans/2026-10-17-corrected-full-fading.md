# Corrected full-fading implementation plan

Authority: user attachment f5f45a58-0425-4187-a9cc-4c6a41f34313. No optimization.
Superpowers skill is unavailable; this is a repository plan, not a claim that
an unavailable skill was executed. Ponytail applies. Preserve prior dirty work.

1. Map existing source, fading, covariance, interval Holevo and MI routines.
   Requested Binh (38)(7) not located; available (38) is comparison-only.
   Verify Denys v3 and Hosseinidehaj v1 against their primary online editions.
2. Add tests for two optical modes, aperture integral, support/outage, exact
   source identity, full noise, Denys interval, ideal heterodyne, no-fading and
   pure-loss limits. Never change exact C,w producers or old outputs.
3. Add corrected optical law: independent Rician displacement and unit-mean
   lognormal scintillation, existing HV broadening approximation, explicit
   active conditioning at T<=1 preserving AoA atom. Report raw tail mass.
   PDF_ORIGINAL uses existing analytic PDF only in its validated rho=0 scope;
   APERTURE_CORRECTED uses new integration, never the old analytic PDF.
4. Reuse verified cached source and corrected covariance/interval kernels;
   add deterministic joint-output fading-mixture MI and convergence checks.
5. Route the corrected manuscript CLI to the new full-fading pipeline; retain
   the old CLI only with an explicit legacy model identifier. Do not redirect
   historical optimization, training or publication entry points.
6. Evaluate the two named baselines in both optical modes, fixed MB source.
   Save signed decompositions, independent checks, hashes and Vietnamese audit.
   Mark unresolved reference-version or numerical checks explicitly; no security
   certification, source/pointing search, new source builds, commit or push.
