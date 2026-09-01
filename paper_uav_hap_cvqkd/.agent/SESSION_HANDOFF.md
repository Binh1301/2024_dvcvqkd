# Session Handoff

Updated from repository evidence during the prospective V3 preparation cycle.

## Authoritative lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

No threshold is approved. The configured `1e-12` threshold is invalid and
unapproved. Candidate `1e-13`, represented exactly by binary64 hex
`0x1.c25c268497682p-44` and dyadic `3961408125713217/2^95`, remains proposed
and unapproved.

No publication training, optimized-MB grid, baseline selection, final-test
access, held-out evaluation, production `src/cvqkd` change, security-functional
change, or frozen-model change is authorized or has occurred in this cycle.

## Immutable V2.3 failure evidence

V2.3 already ran and failed its prospectively frozen feasibility gate:

- result SHA-256:
  `b7430af4831d96a7b94d88383aab3a64190aecf4ad50099bc3e6a8901921fd1d`;
- config SHA-256:
  `a3ee9c1afcfb35b4422265057ef2635fd61479317af9b47bae725c7df9b68406`;
- manifest SHA-256:
  `57e3f7692fcd86c8f31ce70daf7b82a2a8dfa757064a3c44a3be6e6eb426fb1b`;
- `0/4` complete certificates, `0/4` crossings, and `4/4` resource limits;
- runtime `1800.0382972999942 s`;
- 11 checkpointed completed nodes despite the final aggregate reporting zero;
- cluster cap 24, only 2/40 far modes sign-certified at last checkpoints,
  38 unresolved far modes, and no executed Schur reduction;
- no standalone durable path-domain certificate.

Do not rerun V2.3. Do not overwrite or reinterpret its result, checkpoints,
watchdog records, config, or manifest. The full 12-segment V2.3 run is
forbidden.

## Frozen identities

- `docs/FINAL_MODEL_SPEC.md`:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- Independent roster:
  `a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de`.
- Exact-tau V2.2 artifact:
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`.
- Environment artifact:
  `053e6bf516729f44a960ae8e5c433d9531690257ebd878945d51c21ac49d6b61`.
- MI remains certified at `N_MC=2048`.

## Current permitted work

The only current implementation direction is a new prospectively frozen V3
whole-segment producer with:

- Windows Job-Object process-tree deadlines;
- fsync-backed hash-chained node and Schur journaling;
- path-domain evidence committed before spectral work;
- exact four-sector C4 decomposition;
- coefficient-level Taylor congruence with the correct `-tau Q*Q` shift;
- deterministic sign-separated sequential validated Schur elimination;
- a new namespace-separated hash-selected four-row feasibility subset.

The selection rule must be committed before selected IDs are resolved. All 20
synthetic preflight classes must pass before the new small feasibility subset
runs. If that gate fails, stop without rerun or retuning and do not run all 12.

This handoff is lower authority than active specifications, source, frozen
configs, machine-readable artifacts, and `docs/PROJECT_STATE.md`.
