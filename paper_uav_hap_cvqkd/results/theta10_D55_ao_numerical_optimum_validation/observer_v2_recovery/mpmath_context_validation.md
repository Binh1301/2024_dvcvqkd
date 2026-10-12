# mpmath context protection

Dummy entry imports the real original worker/module, records context object identity, dps, prec,
_prec_rounding and libmp backend before/after. Actual worker main consumes exact float.hex input and
original precision ladder; only numerical leaves are dummy-patched. During dummy rows original
workdps1050/1250/1450 restores context. Observer only READS precision; it never calls workdps,
sets dps or swaps the active context. Dummy fixture is not a full-support convergence oracle.

Initialization, normal completion, original failure, injected observer failure and disabled observer
all verify restored module/context/hooks. Native subprocess results persist before/after metadata
and job containment. Native killed workers cannot report after-context, explicitly NOT_RECORDED;
their process ends and original scientific file/settings hashes remain identical.
