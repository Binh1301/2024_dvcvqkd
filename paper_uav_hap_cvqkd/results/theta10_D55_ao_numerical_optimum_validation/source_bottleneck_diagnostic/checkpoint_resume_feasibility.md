# Checkpoint and resume feasibility

VERIFIED: exact source caches commit temporary JSON then atomic replace after
final validation. Objective checkpoints and attempted-source ledgers preserve
completed identities; campaign continuation skips attempted sources, retains
original deadline and protects old results. This is resume BETWEEN completed
probes, not resume WITHIN an arbitrary-precision operation. Preserved .prof files
hold timings/call counters only, not eigenvectors/matrices/precision state.

Worker.main builds all rows in memory and emits only final JSON; no persisted
precision/sector/eighe/LU position or resumption API. No serialized active
mpmath context, exact binary operands, convergence loops, intermediate state
and validation equivalence proof. Purely partial precision rows also do not
exist as validated durable checkpoints for the failed sources.

Conclusion: safe partial-source resume NOT_SUPPORTED_OR_PROVEN_EQUIVALENT.
Use valid completed source cache under original provenance; an explicitly
approved retry must restart original calculation from original binary64 inputs.
Do not reconstruct moments/eigenvectors from profiles or use lower precision.

A future checkpoint proposal would need exact round-trip mp numbers (not float
or limited nstr decimals), context/operation position, all validation state,
code/settings/source identity, atomic durable commit and interrupted-versus-
uninterrupted equivalence on representative full-support runs. Intra-eighe state
is not exposed by this implementation. Such engineering is out of scope and may
cost more than an uninterrupted restart; it is not recommended as the immediate
path. No checkpoint/resume changes implemented.
