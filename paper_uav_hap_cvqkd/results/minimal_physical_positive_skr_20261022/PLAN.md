# Minimal-change search, authorized user f1566258

Keep the previous passive random-width/circular-collection optical model,
untrusted(.8,.0135), channel excess.0186, homodyne1D, full-Z diagnostic and
all previous security limitations. Do not reopen theory or modify old code.
Primary rate uses actual pooled fading MI, not the Gaussian surrogate.

1. Authenticate prior receipt, regress CandidateA/B and the new-model baseline.
   Verify Fourier inversion of the SAME fading likelihood against the saved
   direct-mixture integration at identical quadrature nodes. This is a local
   computational acceleration, not a new channel/noise/measurement model.
2. Fixed MB(.165,VA5.475): one-parameter scans of all requested values. Full
   divergence233urad is manuscript baseline; config223urad is separately marked;
   residual angular jitter baseline is15.61urad. Recompute waist/Tx99 aperture.
3. Receiver8cm first: adaptive tiers(jitter_urad,sigma_m)=(15.61,1),(12,.75),
   (10,.5),(7.5,.3),(5,.2),(3,.2),(3,.1),(1.561,.1), all10 divergence values.
   Stop stronger tiers after first robustly positive fixed-source tier.
4. Progress through10/12/15/20cm, then25/30/40/55/75cm only if needed; same
   tiers. Record every evaluated/missing cell, never fill the full Cartesian grid.
5. One promising moment-quality context per tested receiver gets the233-source
   catalog, evaluated with actual MI; use eta_f/[.016875+.0186m1+Var(sqrtT)]
   only to choose contexts, never as an SKR objective. Include a second context
   only near an apparent boundary. Report best tested, not global optimum.
6. At source-shortlisted positive receivers, weaken pointing and broaden the
   beam locally; coordinate searches use existing menu values. Refine bracketed
   K=0 and engineering K=1e-4 crossings with a fixed exact source. Alternating
   source coordinates stop atdeltaK1e-8 or exhausted exact-catalog neighbors.
7. Select minimum-modification, balanced and higher-performance Pareto candidates.
   Engineering dominance minimizes Rx/Tx apertures and maximizes tolerated
   angular/position jitter; include rate separately. No invented hardware costs.
   Perturb each pointing component and both jointly by±10/20percent.
8. MI quadrature128x16 screens; selected256x32/512x48, then1024x64 if necessary,
   require adjacent MI change<2e-6 and a positive margin greater than twice that
   observed change. Boundary values are numerical only. Fourier-grid validation
   uses half spacing and direct-likelihood comparison; log roundoff repairs.
9. Produce tablesA/B/C, seven PDF/350dpiPNG figures (untested heatmap cells masked),
   Vietnamese Q1-Q8 report, all exact sources/calls and read-only receipts.
   Preserve all prior files except the five required task ledgers. No source/AP
   generation, new security claims, training/test/held-out/publication or push.
