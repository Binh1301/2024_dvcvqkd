# P1 baseline and conditional refinement estimate — AP NOT_RUN

The live original P1 call reproduces the saved upper-run history exactly.
Best VA=5.5; bracket `[5.49375,5.50625]`. No new source or SKR has been computed,
so the bracket has NOT been advanced in this lower-probe task.

Binary64 width is `0.01249999999999929`, radius
`max(best-lower,upper-best)=0.006249999999999645`; the nominal decimal width
is 0.0125. With parameter tolerance1e-6, width is approximately12,500 tolerances
and the actual original stopping radius is approximately6,250 tolerances.
Width decrease in this task: zero.

The original criterion checks the maximum distance from the best point to
each neighbor, not the full bracket width. Under IDEALIZED balanced midpoint
halving with a fixed best and both exact moments available at every stage,
13 additional paired midpoint levels would reduce this radius below1e-6.
Because the original loop checks the criterion before evaluating the next
pair, a 14th loop visit would be needed to recognize that closure. Requiring
the entire width to be <=1e-6 instead would take14 width halvings.
These are conditional estimates, not execution guarantees or a proposal to
change the algorithm.

After four idealized balanced levels the radius would still be approximately
`0.000390625`, roughly390.625 tolerances. The unchanged inner cap4 therefore
cannot close this fixed-best bracket within one such call, even with complete
source coverage. Current actual execution is blocked sooner: the first paired
level requests `(0.165,5.496875)` and `(0.165,5.503125)`, both missing; it ends
`SOURCE_MISSING_REFINEMENT` after one attempted stage. A stage count is not a
completed level. Zero coordinate searches are verified complete.

P2 remains unresolved with missing `(0.16375,5.5)` and
`(0.16531250000000003,5.5)`. Total-SKR numerical discrimination and outer-domain
closure are also unresolved. No convergence or continuous/global optimum claim.
After a valid approved lower probe, the original P1 code must determine the
new winner/bracket/next pair; do not assume VA=5.5 will stay best or force shrinkage.
