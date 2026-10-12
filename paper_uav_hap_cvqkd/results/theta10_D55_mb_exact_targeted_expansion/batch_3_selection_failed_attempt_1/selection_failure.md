# Archived selection-only guard failure

The first selection attempt stopped before constructing ExactObjective:
`KeyError: 'BETA'` arose because the fresh-evaluation guard lacked the runtime
constant globals inspected by the original provenance checker.

No AP/source moment or SKR evaluation occurred. Original source/evaluator files
were not changed. The orchestration-only guard was corrected to retain the
original globals while forbidding fresh calls. A later successful selection
run is recorded under `../batch_3/`. This archive retains the failed producer
snapshot and its input manifest; no previous result artifact was overwritten.
