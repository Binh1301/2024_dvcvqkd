# AO numerical-optimum completion criteria: unchanged implementation

Finite current facts:147 compatible MB sources/3822 stored objectives,26/26 AO
catalog agreement,0 closed final directions. Reference best(.165,5.5),
K=.07798099387393764;22km(.165,5.475),K=.07661740491526092.

## Labels and evidence

| Label | Necessary evidence | Current status |
|---|---|---|
| FINITE_CATALOG_MAXIMUM | Independent ranking of valid hash-matched stored rows | Verified26/26 |
| COORDINATE_SEARCH_INCOMPLETE | Missing values/open boundary/refinement cap/failure | Current P1 and P2 |
| COORDINATE_WISE_NUMERICAL_OPTIMUM | Both original searches complete at the SAME actual selected pair; two-sided radius<=1e-6, no missing/numerical failures; error sufficient | Not established |
| AO_NUMERICALLY_CONVERGED | Original real updates, absDeltaK<=1e-8, both complete searches, no earlier unresolved or monotonic warning | Not established |
| GLOBAL_OPTIMUM_NOT_CERTIFIED | No proof remote extrema/unbounded boundaries excluded | Remains true even after local closure |

Original settings unchanged:epsilon1e-8,param1e-6,outer6,inner4,boundary3.
Reference P1 [5.4875,5.5125] radius.0125, P2 [.1625,.16562500000000002]
radius.0025. If incumbent remains unchanged and exact paired midpoints halve
both gaps,14 and12 reductions respectively are needed for radius<=1e-6.
After one completed pair13/11 further stages remain; these are conditional,
not lower bounds for every moving-incumbent landscape. Four successful stages
leave radii.00078125 and.00015625. Four-step cap cannot close these current
brackets in one call. Tolerance checked only on entry: crossing tolerance on
fourth pair still returns REFINE_LIMIT/INNER_SEARCH_FAILURE; only after<=3
reductions can current4-stage call observe the tolerance on a later entry.

Unchanged-best conditional P1 after BOTH current missing partners measured:
bracket[5.49375,5.50625], radius.00625; next VA5.496875 and5.503125.
P2 conditional bracket[.16375,.16531250000000003], radius.00125;
nextnu.164375/.16515625000000003. No candidate K inferred. If incumbent moves,
actual nearest measured neighbors and new fixed parameter determine requests.
Measuring A alone can narrow one side or change incumbent; because missing
partner stops the paired stage, it does not complete P1. Existing AO still
returns a finite best and follows genuine next P2 at newly selectedVA.

Six outer calls must not be assumed to provide24 useful refinements: small
DeltaK with incomplete searches stops as catalog stagnation/boundary unresolved;
run's unresolved_inner latch does not clear. Prior cache additions can narrow
initial brackets on a new approved original invocation, without changing algorithm,
but within one trajectory earlier unresolved evidence cannot be relabeled closed.
One authorized strategy is adaptive original-request cache prepopulation before
the final genuine AO replay, until initial slices sufficiently narrow. A prospective
cap increase or revised reset/stopping policy would be a separate algorithm/settings
decision and is NOT implemented/recommended as silently necessary here.

P2 reference's current selected best is interior among measured nu points, so
its immediate local boundary_status is INTERIOR, NOT BOUNDARY_NOT_CLOSED;
missing midpoint refinement is the active local block. Remote nu->0+,nu->infty,
VA->0+,VA->infty directions are NOT globally closed by that local bracket.
Implemented strictnu>0 does not include mathematicalnu=0. Compatible stored
Uniform comparison does not optimize/close the continuousnu=0 boundary.
At22km nu slice singleton remains lowerouter.0825 missing/opposite.33 unchecked.
nu0=.8 run is still boundary-blocked(.4,3.0), lastmissing(.4,1.5)/(.2,3.0);
its lower value is not proof of a distinct continuous basin. Four other starts
agree at each priority distance. Consistent starts are useful, not a requirement
that every nonconvex trajectory reach one point or a global proof.

Required accuracy: candidate-specific full-support AP convergence/provenance,
adequate GH8 MI discretization error evidence without changing the current rule,
entropy/roundoff/covariance checks and propagated totalK error. Four stored
bit-exact metric repeats establish determinism only. Near ties7.834476867e-8
and1.733217454e-7 and epsilon1e-8 need appropriate error control; current
ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED cannot support all displayed optimal
digits. No such new accuracy calculation authorized here. Final manuscript may
present finite best observed results with limitations, not convergence certificate.
