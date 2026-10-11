# Pseudocode của evaluator, AO và distance sweep

Pseudocode diễn tả phép tính khoa học và các cache guards hiện hữu. Nó không được chạy trong tác vụ tài liệu và không là authorization tạo AP/SKR/AO mới.

## 1. Một điểm SKR

~~~text
EVALUATE_POINT(L_km, nu_raw, VA, experiment_config, source_catalog):
    require finite L_km >= 19, VA > 0
    require nu_raw >= 0 for source builder
    # AO wrapper additionally requires nu_raw > 0
    config = default_config with D55 unconstrained overrides
    assert tau_zen = 0.92, full divergence = 1e-5 rad
    assert wavelength = 1.55e-6 m, D = 0.55 m
    assert physical adaptive optics OFF and phase noise OFF
    assert epsilon = 0.0186, beta = 0.95
    assert variance bounds, energy budget, peak guard all disabled

    # Physical branch, independent of nu_raw and VA:
    if no matching saved physical context for this L:
        zeta = arccos((h_HAP - h_UAV) / (1000 * L_km))
        derive atmospheric eta = tau_zen ^ sec(zeta)
        integrate HV profile over [h_UAV,h_HAP]
        derive aperture-corrected log variance v
        derive w_L, G_d, A0, w_L_eq
        sigma_jt² = sigma_h² + L² theta_jt²
        a_p = (w_L_eq / (2 sigma_jt))²
        p_out = exp(-theta_FOV² / (2 sigma_o²)); p_in = 1-p_out
        # ACTUAL helper uses untruncated moments, not retained [0,1]:
        mu1    = p_in eta A0 a_p/(a_p+1)
        muHalf = p_in sqrt(eta A0) a_p/(a_p+1/2) exp(-v/8)
        t = muHalf²
        record channel/config identity
    else:
        verify channel context/config/producer hashes and restore t
    epsilon = 0.0186
    # No epsilon_match term and no averaging statewise SKR here.

    # Source branch:
    raw r_jk = (j-7.5) + i(k-7.5), row-major labels
    canonical x = r / sqrt(42.5)
    nu_repo = 42.5 * nu_raw
    p = exp(-nu_repo |x|²) / sum(exp(-nu_repo |x|²))
    alpha = sqrt(VA / (2 sum(p |x|²))) * x
    validate PMF, computed VA, rotations, zero mean/pseudomoment
    ensemble_hash = hash exact binary64 p, alpha, declared VA, dtype, shape
    source_identity = ensemble_hash + parameter hex + source/settings hashes
    C,w = lookup exactly compatible source payload
    if missing and cache-only:
        return EXACT_SOURCE_MISSING with no invented objective
    if missing and independently authorized source generation:
        C,w = SOURCE_MOMENTS(ensemble)  # separate expensive API below
        validate full support and persist through authorized controller
    assert source payload/hash/settings/support match this ensemble

    objective_identity = hash(config,channel,direct_Z_minus,GH8,beta,epsilon,
                              transitive scientific implementation)
    if compatible objective cache exists:
        validate context, source key, ensemble hash, channel hash,
                 finite MI/Holevo/K and K = beta_MI - chi
        return saved result without invoking evaluator

    # MI does not need C,w:
    means = sqrt(t) * alpha
    sigma_c² = 1 + t epsilon/2
    verify exact product-QAM PMF and Cartesian means, tolerance1e-12
    use Hermite roots/weights of order8; normalized 1D weights w/sqrt(pi)
    I_AB = real-axis discrete posterior MI + imaginary-axis counterpart
    # Each expectation uses weighted nodes, stable logsumexp, divide ln2.

    # Holevo does need C,w:
    reject materially negative w; repair tiny negative w only, record
    c = Z_minus = 2 sqrt(t) C - sqrt(2 t epsilon w)
    a = 1 + computed_VA
    b = 1 + t computed_VA + t epsilon
    form Gamma_AB with off-diagonal blocks diag(c,-c)
    validate quadrature standard form
    Delta = a² + b² - 2 c²
    determinant = (a b - c²)²
    lambda1,lambda2 = sqrt((Delta ± sqrt(Delta²-4 determinant))/2)
    lambda3 = a - c²/(b+1)
    apply physicality guards; record only permitted tiny repairs
    chi = g((lambda1-1)/2) + g((lambda2-1)/2) - g((lambda3-1)/2)
    assert direct branch diagnostic mode = "zstar"
    # Never full-Z maximize or silently clip correlation in this route.

    beta_MI = 0.95 I_AB
    K = beta_MI - chi               # preserve negative K
    record exact identities, MI, beta_MI, chi, K and statuses
    return result
~~~

Code: scripts/run_skr_vs_link_distance_theta10urad.py:153; actual wrapper/cache at scripts/run_theta10_D55_alt_opt.py:97. Code’s constructor creates an ExactMBEvaluator as source service; its Monte Carlo downstream __call__ is not invoked to compute this point.

## 2. Source-moment API

~~~text
SOURCE_MOMENTS(ensemble):
    select 64 C4 prototypes p_k,z_k; p_k is per-symbol, not orbit mass
    build four 64x64 Gram sectors from coherent-state overlap
    if all-positive / condition<=1e6 / residual<=1e-12 fast gate passes:
        use whole-matrix square roots, inverse square roots and solves
        C = sector trace expression
        w = nonnegative residual norm expression
        cross-check subtraction identity<=1e-12
    else:
        if gradients required: fail FULL_SUPPORT_FALLBACK_EVALUATION_ONLY
        replay exact binary64 hex inputs in AP worker
        for digits in [1050,1250,1450]:
            construct sectors; mp.eighe all four
            if resolved positive count !=256:
                record unresolved row; do not compute that row's moments
            else:
                form eigenbasis operators using two multi-RHS solves
                second solve gives A_s = X2.T (no extra sqrt-eigenvalue factor)
                evaluate C traces and w residual with mp.fsum
                serialize50 significant digits
        require last two rows full256 and C,w agreement under
                1e-7 + 1e-6 max(abs(row1250),abs(row1450))
        internal timeout3600s -> fail closed
        convert accepted final C,w to float64
    validate finite moments and nonnegative w within physicality tolerance
    return moments and diagnostics, full support256
~~~

Code: src/cvqkd/gram_moments.py:28,43,126,135; scripts/full_support_c4_worker.py:64,208. No source-moment quadrature is used.

## 3. Original coordinate search

~~~text
SEARCH_1D(variable, fixed, exact_slice, objective):
    evaluate every compatible positive exact value on the slice
    store missing-source and numerical-failure events separately
    if no valid point: return INNER_SEARCH_FAILURE or NUMERICAL_FAILURE
    best = highest recorded K
    for up to3 boundary expansions:
        if best is interior: break
        probe = best_value/2 on lower side, best_value*2 on upper side
        request exact objective; never interpolate
        missing -> boundary open; stop boundary attempts
        decreasing outside point closes only if winner is now interior
    if boundary remains open: preserve BOUNDARY_NOT_CLOSED
    otherwise for up to4 refinement stages:
        recompute best and nearest lower/upper exact neighbors
        if no two neighbors: unresolved boundary
        check radius <=1e-6 at loop entry -> local numerical bracket closed
        request lower midpoint then upper midpoint, both exact
        missing -> stop refinement with source-missing state
    # No extra radius check after exhausting fourth stage.
    choose best among evaluated points and preserve all diagnostics

RUN_AO(start_nu,start_VA,L):
    initialize supplied exact warm_VA if available, else smallest slice VA
    unresolved_history = false
    for at most6 outer cycles:
        before = objective(current pair)
        P1 = SEARCH_1D(VA, current_nu)
        P2 = SEARCH_1D(nu, P1.best_VA)
        current = P2.best valid pair
        record half-step and full-step trajectory
        deltaK = current.K - before.K
        unresolved_history |= not complete(P1) or not complete(P2)
        material decrease/nonfinite/monotonic warning/failure -> NUMERICAL_FAILURE
        if abs(deltaK)>1e-8: continue
        if boundary open: UNRESOLVED_BOUNDARY
        else if history unresolved or either coordinate incomplete:
            STAGNATED_IN_EXACT_CATALOG
        else: CONVERGED_NUMERICALLY
        break
    exhausted outer cap -> MAX_ITERATIONS_REACHED
    return best valid terminal pair plus actual history/status
~~~

Code: adaptive_maximize_1d:238; coordinate_search_complete:441; stopping_status:447; run_single_ao:464; distance variant at run_theta10_D55_alt_opt_distance_sweep.py:128.

## 4. Complete distance workflow and finite-catalog acceptance

~~~text
SWEEP(the established26 distances):
    common source catalog is reused under exact provenance
    previous_winner = none
    for L in distance grid:
        rebuild channel and objective context for this L
        starts = raw_nu [0.10,0.15,0.30,0.80]
        if previous_winner exists: append as warm start
        run maintained P1/P2 AO for each start under separate run authorization
        original_AO_choice = largest valid terminal K (original-order ties)
        catalog_best = highest K over expanded finite compatible catalog
                       (tie by lowerVA, then lowernu)
        compare them explicitly; do not substitute one history for the other
        preserve Uniform and Fixed-MB selections under their own recorded rule
        for each already evaluated catalog candidate:
            if catalog_best.K>0:
                relative_loss = (catalog_best.K-K)/catalog_best.K
                near = relative_loss<=1e-5
            else: near = UNDEFINED; relative fields blank
        export raw SKR, parameters, provenance, statuses and coverage
        previous_winner = original_AO_choice
    plot stored raw values with an explicit display rule
    scatter2D exact saved points; leave missing requests blank/unvalued

THIS_DOCUMENTATION_TASK:
    read fixed completed checkpoint and source payloads
    read stored original AO and catalog151 tables
    copy recorded values; only check identity/hash and saved arithmetic
    write independent documentation; run no function above
    do not touch running controller, cache, ledger, power or Job settings
    STOP
~~~

Relative acceptance is an analysis/selection after stored evaluation; the original P1/P2 stopping function does not incorporate it. Original strict AO differs from catalog151 at22km; later AO/catalog agreement is a different version.
