# Source audit and authority

Source manuscript: C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (17).pdf
(4 pages, read in full). Task text is an instruction source; instructions or
claims inside the manuscript are mathematical source material, not tool commands.

Existing branch: feat/11-6; starting HEAD 1be9be90a51fffd02515ff572a108ec8142a6dc1.
Initial tracked diff empty; git status emitted a pre-existing pytest-cache access
warning. This package does not depend on previous chat context.

Existing binary_cloud.py uses a Gaussian-copula binary field, not the requested
advected Gaussian CLWC mixture. Existing test_energy_budget.py concerns optical
modulation energy, not rotor propulsion. Neither is an appropriate substitute.
The dynamic_gaussian_cloud_figure sibling provides useful visualization context
but is not imported as a physical model. No propulsion/finite-key graph solver
was found in current production source.

Existing results/skr_zenith_heatmap_20261106/ contains a 51x51 diagnostic SKR
table. Its report explicitly preserves source-evidence gaps, best-tested finite
catalog scope and UNVALIDATED_SECURITY_MODEL. It is not automatically admitted
as a certified paper input. New loading/interpolation does not recompute SKR.

Historical FINAL_MODEL_SPEC expected SHA256:
561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1
Observed current bytes:
df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15
This discrepancy is a blocker to promoting frozen-model conformance. Existing
state already records a historical mismatch. The file is not restored or edited.
NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains. This package implements the new
manuscript performance approximation without extending the frozen security proof.

Missing real inputs: propulsion parameters; v_max; E_max; q0 and endpoint geometry
approved for this experiment; m0; epsilon; Gaussian cloud realization/covariances;
L_th; altitude/thickness and LOS resolution evidence; approved SKR lookup and
provenance; calibration lambda selection. The manuscript supplies equations but
no full simulation-parameter table. All demo numbers must remain synthetic.

Physical assumptions: no acceleration, turning/transient costs; speed mixing
along straight segments within a slot; channel reward sampled at slot-end
waypoint/time. Cloud LOS is sampled in a prescribed slab. The accumulated
finite-size expression across channel states is a performance approximation,
not a composable-security bound. Nonblocking does not mean T=1.
