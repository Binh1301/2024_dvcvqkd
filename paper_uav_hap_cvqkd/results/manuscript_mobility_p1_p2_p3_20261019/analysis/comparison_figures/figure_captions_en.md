# IEEE-style figure captions

**Figure 1.** Average usable SKR for Stationary (P2), Greedy, and Dynamic Programming (P3), averaged over the same 100 independent synthetic cloud missions at ten stored penalties. Shaded bands are pointwise Student-t 95% confidence intervals for the means, not standard deviations. λ-axis uses base-10 symlog with linear threshold 3.15600889242e-07 bits/use and retains λ=0. These unpenalized rates are distinct from the optimized objective.

**Figure 2.** Mean mobility-penalized objective U=K̄−λD/1000 for the three strategies over 100 common cloud missions. Pointwise Student-t 95% mean intervals are shaded. DP satisfies mission-wise objective dominance within 1e−12 bits/use under common speed constraints and freely selectable initial locations; P2/DP use the complete horizon whereas Greedy uses current-slot states. λ-axis uses base-10 symlog with linear threshold 3.15600889242e-07 bits/use and retains λ=0.

**Figure 3.** Mean total UAV travel distance over 100 common missions, with pointwise Student-t 95% intervals. Stationary distance is exactly zero. DP distance is non-increasing at the tested penalties in each mission; Greedy has no such global guarantee. λ-axis uses base-10 symlog with linear threshold 3.15600889242e-07 bits/use and retains λ=0.

**Figure 4.** Paired objective differences DP−Stationary and DP−Greedy, formed within each of the 100 missions before averaging. Bands are pointwise 95% percentile-bootstrap intervals from the existing 20,000 whole-mission paired resamples (seed 20261019); the horizontal line marks zero. λ-axis uses base-10 symlog with linear threshold 3.15600889242e-07 bits/use and retains λ=0. These are numerical-model uncertainty intervals, not security confidence bounds.

**Figure 5.** Mean usable SKR versus mean travel distance for Greedy and DP at the ten evaluated penalties; points are connected in increasing λ order, not distance order. Stationary is a single reference point at zero distance. Coincident high-penalty points overlap without jitter. λhi=0.00315600889242 bits/use. The curves are sampled policy tradeoffs, not a globally optimal physical Pareto frontier.

**Figure 6.** Per-slot usable SKR for Stationary (P2), Greedy, and DP (P3), read as S[j_n,n] along saved trajectories for mission 84 at the stored λ=9.468026677248516e-06 bits/use. This case is selected post hoc as the largest DP−P2 objective gain among missions with strict DP gains over both baselines. All methods use the same cloud matrix. Zero-rate slots are verified against each selected trajectory’s boolean cloud states; lines are slot steps through saved data.

**Figure 7.** Cumulative usable-SKR sums R(n)=sum(t=1..n)S[j_t,t] for Stationary (P2), Greedy, and DP (P3), using the same mission 84 and λ=9.468026677248516e-06 bits/use as Fig. 6. R(0)=0 is the empty sum. All curves are non-decreasing. The ordinate sums rate values over slots; physical secret-bit counts require a pulse rate and channel uses per slot, which are unspecified.

**Figure 8.** Family-wise optimized raw clear-sky SKR at 100 saved candidate locations, ordered by manuscript index j=1,...,100 (x-first grid ordering). Negative Uniform values are retained with a zero reference line. MB selects (ν,VA)=(0.125,8) throughout the region. Each family chooses from its own finite catalog, including different variance choices; this is not a fixed-energy shaping-isolation claim. No percentage gain is assigned to zero or negative Uniform rates.

All rates are manuscript-style mixed 2D-MI/homodyne-Holevo numerical outputs. UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
