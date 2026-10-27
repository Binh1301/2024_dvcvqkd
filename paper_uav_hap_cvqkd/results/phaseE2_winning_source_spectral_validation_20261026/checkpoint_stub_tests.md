# Checkpoint and resume validation

Latest result: **CURRENTLY_VERIFIED_PASS**, 14 focused tests in 1.5681s.
Machine record: checkpoint_test_results.json. Test producer: test_checkpoint.py.

Checks cover roundtrip, skipping an already completed eigensolve, interruption
before atomic replacement, preservation of an existing final file, source/precision/
producer mismatch, checksum corruption, a recomputed checksum with inconsistent
eigenpairs, incomplete receipts, failed consistency checks, a real stub process
being killed, resume after that kill, and refusal without a bound authorization.

The scientific check uses only saved Uniform4 and MB16 input arrays. At 50/70
digits the wrapper is compared to the unchanged Phase E Gram method; the
unchanged Fock method at NF48/dps70 supplies a second construction. All small
source modes are retained. C and w differ by less than 1e-39 between Gram
implementations, and by less than 1e-30 between Fock and the wrapper. Direct
variance and stable residual agree within 1e-39. Moment resume returns the saved
identical object; no repeated source calculation occurs on that path.

Each sector receipt binds source array/NPZ hashes, canonical ensemble hash when
available, implementation/helper hashes, Python/mpmath versions, precision,
sector, dimension, floor and numerical-check policy. It stores the matrix,
full spectrum, eigenvectors, per-pair residuals, reconstruction, orthogonality,
conditioning diagnostics, CPU/wall times and a payload digest. C,w contributions
are explicitly NOT_RUN until all four sectors exist; the dependent moments.json
then records C and residual-norm contributions by sector plus the coherent-norm
correction. Old Phase E spectra cannot masquerade as these richer checkpoints.

Same-directory temporary files are flushed/fsynced and replaced using os.replace.
A sector becomes complete only after numerical checks pass. Loading recomputes
the digest and consistency checks at the declared precision. .pending files
are never accepted as complete. Atomic replacement is tested against process
interruption, not power loss or storage-controller failure. Complete means a
valid numerical sector record, not a full-support or C,w certificate.

The first development run also passed 14 tests before additional controller
stop/conditioning/provenance checks were added. Its code/results remain under
development_evidence/ and its original stub directories are preserved. The
current run is under stub_checkpoints/round2/. These are two executions of
14 unique tests, not 28 distinct tests. Across both batches there were 20
small-source moment checks, all M<=16; **zero** target-source C,w calculations.

The target-size high-precision resource controller has not been exercised on
the winner. Its memory monitor reuses the corrected Phase E actual-worker-PID
helper. End-to-end 400/500-digit execution, resource sufficiency and convergence
remain NOT_RUN, as requested.
