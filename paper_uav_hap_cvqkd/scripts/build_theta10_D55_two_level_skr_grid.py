"""Match a51-pair grid to saved exact records and render scatter-only figures."""
import csv
import itertools
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import analyze_theta10_D55_near_optimal_skr as audit
from scripts import export_theta10_D55_all_exact_skr_points as export

OUT = audit.BASE / 'two_level_2d_skr_grid'
NU_A, VA_A = [.10, .125, .15, .175, .20, .25], [2., 3.5, 5., 6.5, 8.]
NU_B, VA_B = [.15, .16, .165, .17, .175], [4.5, 5., 5.5, 6., 6.5]


def grid_specification():
    a, b = set(itertools.product(NU_A, VA_A)), set(itertools.product(NU_B, VA_B))
    assert len(a) == 30 and len(b) == 25 and len(a & b) == 4 and len(a | b) == 51
    return [dict(grid_id=i, nu_raw=n, V_A=v, Grid_A=(n, v) in a, Grid_B=(n, v) in b,
                 membership='A+B' if (n, v) in a & b else 'A' if (n, v) in a else 'B',
                 nu_raw_hex=n.hex(), V_A_hex=v.hex()) for i, (n, v) in enumerate(sorted(a | b), 1)]


def grid_coverage(grid, bank):
    rows = []
    for point in grid:
        source = bank.get(audit.pair(point))
        valid = all(math.isfinite(point[k]) and point[k] > 0 for k in ('nu_raw', 'V_A'))
        status = 'INVALID' if not valid else 'EXACT_CACHED' if source else 'MISSING_SOURCE'
        payload = audit.read(ROOT / source['source_path']) if source else None
        provenance = audit.verify_source_payload(payload, payload['source_settings']) if payload else None
        rows.append(dict(point, status=status, C=payload['C'] if payload else '', w=payload['w'] if payload else '',
                         source_cache_key=payload['cache_key'] if payload else '',
                         canonical_source_cache_key=provenance['canonical_source_cache_key'] if provenance else '',
                         ensemble_hash=payload['ensemble_hash'] if payload else '',
                         source_path=source['source_path'] if source else '',
                         source_sha256=audit.digest(ROOT / source['source_path']) if source else '',
                         provenance=provenance['status'] if provenance else 'UNAVAILABLE',
                         provenance_record=json.dumps(provenance, sort_keys=True) if provenance else '',
                         source_moment_route=payload['source_moment_route'] if payload else '',
                         new_exact_source_required=status == 'MISSING_SOURCE',
                         AP_requirement='NONE_CACHE_REUSE' if source else
                         'ORIGINAL_EXACT_ROUTE_REQUIRED_AP_FALLBACK_IF_FAST_GATE_FAILS' if valid else 'INVALID',
                         validated_distances=26 if source else 0))
    return rows


def runtime_evidence(protected, bank):
    """Use observed successful source-job wall times,never impute an individual runtime."""
    samples, failures = {}, []
    path = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation/source_bottleneck_diagnostic/source_runtime_comparison.csv'
    protected[path.relative_to(ROOT).as_posix()] = audit.digest(path)
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['wall_seconds'] == 'NOT_RECORDED':
                continue
            assert audit.pair(row) in bank and row['provenance'] == 'VERIFIED'
            assert audit.digest(ROOT / row['source_path']) == row['source_sha256']
            samples[audit.pair(row)] = dict(nu_raw=float(row['nu_raw']), V_A=float(row['V_A']),
                wall_seconds=float(row['wall_seconds']), evidence=path.relative_to(ROOT).as_posix(), status='COMPLETED_EXACT')
    folders = [audit.BASE.parent / 'theta10_D55_mb_exact_targeted_expansion' / n
               for n in ('resumed_sleep_safe_run', 'batch_2', 'batch_3')]
    folders += [audit.BASE.parent / 'theta10_D55_ao_numerical_optimum_validation/phase_2A']
    for folder in folders:
        path = folder / 'source_generation_ledger.json'
        protected[path.relative_to(ROOT).as_posix()] = audit.digest(path)
        for row in audit.read(path)['attempts']:
            record = dict(nu_raw=row['nu_raw'], V_A=row['V_A'], status=row['status'],
                          wall_seconds=row['wall_seconds'], evidence=path.relative_to(ROOT).as_posix())
            if row['status'] == 'COMPLETED_EXACT':
                assert audit.pair(row) in bank
                samples[audit.pair(row)] = record
            else:
                failures.append(record)
    for folder in ('b2_A', 'b2_P1_upper_refinement/minimal_run', 'b2_P1_lower_refinement/minimal_run'):
        directory = audit.BASE / folder
        source_path, path = directory / 'source_result.json', directory / 'source_supervision.json'
        source, supervision = audit.read(source_path), audit.read(path)
        for p in (source_path, path):
            protected[p.relative_to(ROOT).as_posix()] = audit.digest(p)
        assert source['status'] == 'COMPLETED_EXACT' and source['provenance']['status'] == 'VERIFIED'
        assert source['source_moment_route'] == 'ARBITRARY_PRECISION_FALLBACK'
        assert supervision['returncode'] == 0 and not supervision['deadline_exceeded']
        samples[audit.pair(source)] = dict(nu_raw=source['nu_raw'], V_A=source['V_A'], status='COMPLETED_EXACT',
            wall_seconds=supervision['measured_wall_seconds_including_cleanup'], evidence=path.relative_to(ROOT).as_posix())
    return list(samples.values()), failures


def completion_priorities(coverage, runtimes):
    # Priorities derive solely from grid membership/coverage,not missing SKR.
    minutes = [r['wall_seconds'] / 60 for r in runtimes]
    rows = []
    for point in coverage:
        if point['status'] != 'MISSING_SOURCE':
            continue
        broad = point['Grid_A']
        priority = 'A' if broad else 'B'
        reason = ('Populate the entirely empty VA=3.5 column in broad coverage' if point['V_A'] == 3.5 else
                  'Complete a broad-domain anchor; also fills Grid B' if point['membership'] == 'A+B' else
                  'Complete a broad-domain anchor' if broad else
                  'Fill a focused-grid coordinate at fixed incumbent nu=.165' if point['nu_raw'] == .165 else
                  'Fill focused-grid coverage adjacent to tested high-SKR samples; SKR unknown')
        rows.append(dict(nu_raw=point['nu_raw'], V_A=point['V_A'], membership=point['membership'],
            status=point['status'], priority=priority, reason=reason,
            nu_raw_hex=point['nu_raw_hex'], V_A_hex=point['V_A_hex'],
            new_exact_source_required=True, cost_estimate='UNIDENTIFIABLE_PER_POINT; EMPIRICAL_PLANNING_ENVELOPE_ONLY',
            historical_success_min_minutes=min(minutes), historical_success_median_minutes=statistics.median(minutes),
            historical_success_max_minutes=max(minutes),
            cost_uncertainty='HIGH: successful timings are selection-biased and mostly near nu=.165,VA~5.5; timeout possible'))
    return sorted(rows, key=lambda r: (r['priority'], r['V_A'] != 3.5, r['nu_raw'] != .165, r['nu_raw'], r['V_A']))


def matrix_cells(grid, reference):
    requested = {audit.pair(r): r for r in grid}
    values = {audit.pair(r): r for r in reference}
    return [dict(nu_raw=n, V_A=v, SKR=values[(n.hex(), v.hex())]['SKR'] if (n.hex(), v.hex()) in values else '',
                 status='NOT_IN_PROPOSED_GRID' if (n.hex(), v.hex()) not in requested else
                 'EXACT_CACHED' if (n.hex(), v.hex()) in values else 'MISSING_SOURCE')
            for n in sorted(set(NU_A + NU_B)) for v in sorted(set(VA_A + VA_B))]


def make_figures(coverage, reference, offgrid_near):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    matplotlib.rcParams.update({'font.family': 'serif', 'font.size': 10, 'axes.labelsize': 11,
                               'legend.fontsize': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    cached = [r for r in coverage if r['status'] == 'EXACT_CACHED']
    missing = [r for r in coverage if r['status'] == 'MISSING_SOURCE']
    near = [r for r in reference if r['near_optimal'] == 'YES']
    renders = []
    def scatter(ax, rows, **kwargs):
        return ax.scatter([r['V_A'] for r in rows], [r['nu_raw'] for r in rows], **kwargs)
    def canvas(title):
        fig, ax = plt.subplots(figsize=(7.5, 4.6), layout='constrained')
        ax.set(xlabel=r'Modulation variance $V_A$ (SNU)', ylabel=r'MB shaping parameter $\nu_{\rm raw}$',
               title=title, xlim=(1.75,8.25), ylim=(.09,.26))
        ax.grid(alpha=.18)
        ax.set_axisbelow(True)
        return fig, ax
    def save(fig, name, ax, exact_count):
        fig.savefig(OUT / (name+'.png'), dpi=400, facecolor='white')
        fig.savefig(OUT / (name+'.pdf'), facecolor='white')
        renders.append(dict(figure=name, exact_colored_or_near_points=exact_count, missing_points=len(missing),
                            coordinate_mapping='DIRECT_FLOAT_X_VA_Y_NU_LINEAR_AXES',
                            plotted_lines=len(ax.lines), interpolation=False, PNG_dpi=400, PDF='VECTOR'))
        plt.close(fig)
    fig, ax = canvas('Two-level parameter-grid coverage')
    scatter(ax, [r for r in coverage if r['Grid_A']], marker='s', s=112, facecolors='none', edgecolors='tab:blue',
            linewidths=1.2, label='Grid A: broad (30)')
    scatter(ax, [r for r in coverage if r['Grid_B']], marker='o', s=70, facecolors='none', edgecolors='tab:orange',
            linewidths=1.2, label='Grid B: focused (25)')
    scatter(ax, cached, marker='.', s=32, color='black', label=f'Exact cached ({len(cached)})')
    scatter(ax, missing, marker='x', s=26, color='tab:red', linewidths=.9, label=f'Missing source ({len(missing)})')
    ax.scatter([5.5],[.165],marker='*',s=175,c='gold',edgecolors='black',linewidths=.6,zorder=8,label='Best exact-tested')
    ax.legend(loc='upper left',bbox_to_anchor=(1.01,1.0))
    save(fig,'grid_coverage',ax,len(cached))
    fig, ax = canvas(f'Exact-data SKR landscape at L={audit.REF} km')
    colors = scatter(ax, reference, c=[r['SKR'] for r in reference], cmap='viridis', marker='s', s=40,
                     edgecolors='black',linewidths=.4,label=f'Exact grid values ({len(reference)})')
    scatter(ax, missing, marker='x',s=28,color='0.55',linewidths=.8,label='Missing: no SKR value')
    fig.colorbar(colors, ax=ax, label='Secret Key Rate (bits/use)', pad=.025, shrink=.88)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.21),ncol=2)
    save(fig,'skr_landscape',ax,len(reference))
    fig, ax = canvas('Exact near-optimal parameter samples')
    scatter(ax, [r for r in reference if r['near_optimal'] != 'YES'], color='0.65', s=35, marker='o', label='Other cached grid')
    scatter(ax, missing, marker='x', s=28, color='0.45', label='Missing grid source')
    scatter(ax, near, marker='o', s=86, facecolors='none', edgecolors='tab:green', linewidths=1.5,
            label=f'Near-optimal grid ({len(near)})')
    scatter(ax, offgrid_near, marker='^', s=46, color='tab:green', edgecolors='black',linewidths=.4,
            label=f'Near-optimal off-grid ({len(offgrid_near)})')
    ax.scatter([5.5],[.165],marker='*',s=150,c='gold',edgecolors='black',linewidths=.6,zorder=9,label='Best exact-tested')
    ax.legend(loc='upper left',bbox_to_anchor=(1.01,1.0))
    # Place the zoom between nu=.20 and .25;do not cover any requested point.
    inset = ax.inset_axes([.14,.74,.58,.18])
    scatter(inset, near, marker='o',s=70,facecolors='none',edgecolors='tab:green',linewidths=1.4)
    scatter(inset, offgrid_near, marker='^',s=35,color='tab:green',edgecolors='black',linewidths=.3)
    inset.scatter([5.5],[.165],marker='*',s=110,c='gold',edgecolors='black',linewidths=.5,zorder=9)
    inset.set(xlim=(5.465,5.535),ylim=(.16485,.1658), title='Exact near-optimal samples (zoom)')
    inset.tick_params(labelsize=7)
    inset.ticklabel_format(axis='y',style='plain',useOffset=False)
    inset.title.set_fontsize(8)
    inset.grid(alpha=.15)
    save(fig,'near_optimal_region',ax,len(near)+len(offgrid_near))
    return renders


def write_csv(name, rows, fields=None):
    with (OUT / name).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    if OUT.exists():
        raise SystemExit('Grid output exists; preserve it, no overwrite')
    start, cpu = time.monotonic(), time.process_time()
    # Verify the latest full-catalog export as well as original scientific inputs.
    prior = audit.read(export.OUT / 'catalog_verification.json')
    assert all(audit.digest(ROOT/n) == sha for n,sha in prior['input_hashes'].items())
    assert all(audit.digest(export.OUT/n) == sha for n,sha in prior['output_hashes'].items())
    assert audit.digest(Path(export.__file__)) == prior['producer_sha256']
    entries, protected, tables, _ = audit.load_verified()
    for folder in (audit.OUT, export.OUT):
        for path in folder.iterdir():
            if path.is_file():
                protected[path.relative_to(ROOT).as_posix()] = audit.digest(path)
    grid = grid_specification()
    reference_entry = next(e for e in entries if e['L_km'] == audit.REF)
    bank = {audit.pair(r): r for r in reference_entry['rows']}
    coverage = grid_coverage(grid, bank)
    keys = {audit.pair(r) for r in grid}
    cached_keys = {audit.pair(r) for r in coverage if r['status'] == 'EXACT_CACHED'}
    values, offgrid = [], []
    for entry in entries:
        original = {audit.pair(r):r for r in entry['rows']}
        # Classification uses all151 pairs,not the incomplete grid's best.
        classified = export.classify(entry['rows'],entry['L_km'])
        for row in classified:
            source = original[audit.pair(row)]
            payload = audit.read(ROOT/source['source_path'])
            record = dict(row, I_AB=source['I_AB'],beta_I_AB=source['beta_I_AB'],chi_BE=source['chi_BE'],
                          C=payload['C'],w=payload['w'],source_path=source['source_path'],
                          status='EXACT_CACHED',channel_hash=source['channel_hash'])
            if audit.pair(row) in cached_keys:
                values.append(record)
            elif audit.pair(row) not in keys:
                offgrid.append(record)
    reference = [r for r in values if r['L_km'] == audit.REF]
    offgrid_ref = [r for r in offgrid if r['L_km'] == audit.REF]
    grid_near = [r for r in values if r['near_optimal'] == 'YES']
    near_ref = [r for r in grid_near if r['L_km'] == audit.REF]
    offgrid_near = [r for r in offgrid_ref if r['near_optimal'] == 'YES']
    best_all = audit.ranked(reference_entry['rows'])[0]
    best_grid = audit.ranked(reference)[0]
    assert (best_all['nu_raw'],best_all['V_A'],best_all['SKR']) == (.165,5.5,.07798099387393764)
    assert audit.pair(best_grid) == audit.pair(best_all) and best_grid['SKR'] == best_all['SKR']
    runtimes, failures = runtime_evidence(protected, bank)
    priorities = completion_priorities(coverage, runtimes)
    times = [r['wall_seconds'] for r in runtimes]
    cost = dict(successful_sources_timed=len(times), historical_min_minutes=min(times)/60,
                historical_mean_minutes=statistics.mean(times)/60, historical_median_minutes=statistics.median(times)/60,
                historical_max_minutes=max(times)/60,
                heterogeneous_empirical_mean_scenario_hours=len(priorities)*statistics.mean(times)/3600,
                successful_sample_envelope_total_hours=[len(priorities)*min(times)/3600,len(priorities)*max(times)/3600],
                single_attempt_internal_60minute_allowance_hours=len(priorities),
                interpretation='UNCERTAIN_PLANNING_SCENARIOS_NOT_RUNTIME_BOUNDS_OR_SUCCESS_GUARANTEES')
    counts = [dict(grid=name,total=len(subset),cached=sum(r['status']=='EXACT_CACHED' for r in subset),
                   missing=sum(r['status']=='MISSING_SOURCE' for r in subset), invalid=sum(r['status']=='INVALID' for r in subset),
                   coverage_percent=100*sum(r['status']=='EXACT_CACHED' for r in subset)/len(subset))
              for name,subset in [('A',[r for r in coverage if r['Grid_A']]),('B',[r for r in coverage if r['Grid_B']]),('UNION',coverage)]]
    assert len(coverage)==51 and len(reference)==20 and len(values)==520 and len(priorities)==31
    assert len(offgrid_ref)==131 and len(offgrid)==3406 and len(near_ref)==1 and len(offgrid_near)==8
    next_batch = [dict(nu_raw=.15,V_A=3.5,priority='A',reason='First exact anchor in empty VA=3.5 column; overlaps a well-sampled nu row'),
                  dict(nu_raw=.165,V_A=6.,priority='B',reason='One focused-grid upper-VA neighbor at incumbent nu; no gain predicted')]
    assert all(audit.pair(r) in {audit.pair(p) for p in priorities} for r in next_batch)
    cells = matrix_cells(grid, reference)
    OUT.mkdir()
    for name,rows in [('parameter_grid_51.csv',grid),('exact_cache_coverage.csv',coverage),
                      ('existing_skr_grid_reference.csv',reference),('existing_skr_grid_26_distances.csv',values),
                      ('offgrid_existing_exact_candidates.csv',offgrid),('near_optimal_grid_candidates.csv',grid_near),
                      ('missing_source_priority.csv',priorities),('grid_coverage_summary.csv',counts),
                      ('matrix_cells_reference.csv',cells),('historical_runtime_evidence.csv',runtimes),
                      ('suggested_next_batch_NOT_AUTHORIZED.csv',next_batch)]:
        write_csv(name,rows)
    va_columns = sorted(set(VA_A+VA_B))
    matrix = [dict(nu_raw=n,**{str(v):next(r['SKR'] for r in cells if r['nu_raw']==n and r['V_A']==v) for v in va_columns})
              for n in sorted(set(NU_A+NU_B))]
    write_csv('skr_matrix_reference.csv',matrix)
    renders = make_figures(coverage,reference,offgrid_near)
    report = [f'# Two-level2D exact-data SKR grid\n\nCACHE-ONLY; 51 proposed unique binary64 pairs. '
              'Grid A30 + Grid B25 -4 overlapping pairs. Original151-pair/3926-objective catalog unchanged.',
              '## Coverage\n\n'+audit.table(counts,list(counts[0])),
              '## Complete51-row coverage table\n\n'+audit.table(coverage,['grid_id','nu_raw','V_A','membership','status','C','w','validated_distances']),
              f'## Exact data and reference performance\n\nFull catalog best and best cached grid pair both(.165,5.5), '
              f'K={best_grid["SKR"]}bits/use at{audit.REF}km. Absolute gap0,relative gap0%. '
              'Only1 cached grid candidate meets relative loss<=1e-5 (0.001%); accepted grid nu range[.165,.165], '
              'VA range[5.5,5.5]. Eight additional near-optimal reference candidates are off-grid,not relabeled as grid members. '
              'The coarse focused grid does not resolve the existing near-flat VA samples.',
              '### Near-optimal exact grid points at reference\n\n'+audit.table(near_ref,export.COLS),
              '### Off-grid exact near-optimal reference points\n\n'+audit.table(offgrid_near,export.COLS),
              'existing_skr_grid_reference.csv contains20 cached rows with original MI/betaMI/Holevo/K and cachedCw; '
              'existing_skr_grid_26_distances.csv contains520 validated rows,not1326. The806 missing source-distance '
              'combinations have no invented numeric values. offgrid_existing_exact_candidates.csv preserves131 off-grid '
              'pairs x26 =3406 records. near_optimal_grid_candidates.csv contains actual eligible grid rows across26 '
              'distances,using each distance\'s full151-pair maximum. Missing sources do not trigger any evaluator.',
              '## Reference matrix and figures\n\n9 true nu coordinates x8 trueVA coordinates gives72 matrix slots: '
              '20 exact values,31 missing proposed pairs and21 NOT_IN_PROPOSED_GRID slots. Blank numeric matrix cells '
              'are distinguished by matrix_cells_reference.csv. No off-grid values silently fill those slots. '
              'All3 figures are exact-coordinate scatter-only,400dpiPNG/vectorPDF; gray/red crosses identify '
              'missing sources without an SKR color. Blank surroundings carry no SKR inference. No equal-spacing '
              'categorical axes,lines,interpolation,smoothing,contours or fits. Near plot uses a separate exact-point zoom '
              'and marker style for8 off-grid near points. Publication-style rendering does not certify numerical/security readiness.',
              '## Missing sources and proposed completion priorities\n\nPriority A means broad-grid membership '
              '(including the one A+B missing point); Priority B means fine-only coverage. These are coverage classes, '
              'not predicted SKR or mandatory execution order. Priority C is reserved for optional additional refinement '
              'outside this fixed51-pair specification;no extra pair is added or authorized.\n\n'+
              audit.table(priorities,['priority','nu_raw','V_A','membership','status','reason']),
              '## Historical cost evidence (uncertain)\n\n'+json.dumps(cost,indent=2),
              'Observed successful source-job wall times are heterogeneous,one retained observation per compatible '
              'parameter pair;duplicate timing summaries are not counted twice. Job wrapper/cleanup included, '
              'SKR postprocessing/AO andagent overhead excluded. Individual missing-point runtimes are UNIDENTIFIABLE. '
              'Per-pointCSV gives the historical planning envelope,NOT a predicted runtime. The aggregate mean scenario '
              'transfers the empirical heterogeneous timing distribution,not identical future durations; the min/max '
              'scenario is not a confidence interval or guaranteed completion bound. Most timings come from nu~.165 '
              'andVA~5.5; broad-domain points may be much faster,slower or fail. Selection bias excludes failures '
              'from the success-only mean. Failed/timeout attempts below remain censored evidence,not success-time samples. '
              'The31-hour60min/probe allowance describes one internal attempt per missing source only; timeout/safety '
              'abort may leave the grid incomplete,supervisor/processing overhead adds wall-time. No budget is approved here. '
              'Use original exact fast gate/AP fallback;do not assume every future source must take the AP route.',
              '### Observed nonsuccess attempts (not used as successful timing samples)\n\n'+audit.table(failures,list(failures[0])),
              '## Smallest useful complementary next batch (NOT AUTHORIZED)\n\n'+audit.table(next_batch,list(next_batch[0]))+
              '\n\nTwo sources are the smallest batch covering both objectives:one new broad empty-column anchor '
              'andone focused incumbent-nu neighbor. A one-probe pilot can begin with(.15,3.5) if only broad coverage '
              'is desired. Their SKRs are unknown. Reassess after each exact success/timeout and newbudget approval; '
              'sequential original safety/timeout controls,checkpoint/provenance then original26-distance evaluation '
              'only in a separately authorized execution. No automatic retry or additional source computation in this task.',
              '## Verification and scientific scope\n\nOriginalsource/precision/quadrature/MI/directZminus/AO '
              'unchanged. Source identities verified using exact binary64 parameters and hash-compatible payloads; '
              'no approximate substitution. All prior protected scientific/analysis artifacts unchanged. '
              'AP/newCw/newSKR/newAO=0. Ordering NUMERICALLY_UNCERTIFIED;performance thresholds are relative to '
              'finite-catalog maxima only,not a total-K errorbound/continuous or global optimum. The historical '
              'FINAL_MODEL_SPEC hash discrepancy remains documented and unchanged;NOT_READY_FOR_PUBLICATION_SCALE_RUNS. STOP.']
    (OUT/'two_level_grid_report.md').write_text('\n\n'.join(report)+'\n',encoding='utf-8')
    assert all(audit.digest(ROOT/n)==sha for n,sha in protected.items()),'Protected scientific/input drift'
    verification = dict(status='CURRENTLY_VERIFIED_PASS_CACHE_ONLY_2D_GRID',grid_unique_pairs=51,cached_pairs=20,
        missing_pairs=31,invalid_pairs=0,coverage=counts,grid_objective_rows=520,missing_grid_objective_combinations=806,
        offgrid_pairs=131,offgrid_objective_rows=3406,near_optimal_reference_grid=1,offgrid_reference_near=8,
        near_optimal_grid_all_distances=len(grid_near),best_reference=best_grid,reference_grid_catalog_gap=0.,
        reference_matrix_cells=72,reference_matrix_unrequested=21,runtime_cost=cost,next_batch=next_batch,
        renders=renders,AP_attempts=0,new_source_moments=0,new_SKR_evaluations=0,AO_runs=0,
        scientific_changes=False,ordering_status=audit.ORDERING,protected_files=len(protected),input_hashes=protected,
        protected_drift=[],producer_sha256=audit.digest(Path(__file__)),
        reused_producer_sha256={str(Path(p).relative_to(ROOT)):audit.digest(Path(p)) for p in (audit.__file__,export.__file__)},
        test_sha256=audit.digest(ROOT/'tests/test_two_level_skr_grid.py'),
        wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu,
        output_hashes={p.name:audit.digest(p) for p in OUT.iterdir() if p.is_file()})
    (OUT/'grid_verification.json').write_text(json.dumps(verification,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('COMPLETE51-ROW GRID COVERAGE TABLE\n'+audit.table(coverage,['grid_id','nu_raw','V_A','membership','status','C','w','validated_distances']))
    print('\nCOVERAGE\n'+audit.table(counts,list(counts[0])))
    print(f'\nBest included:({best_grid["nu_raw"]},{best_grid["V_A"]}),K={best_grid["SKR"]};cataloggap=0;neargrid=1,offgridnear=8.')
    print('\nALL MISSING POINTS BY PRIORITY\n'+audit.table(priorities,['priority','nu_raw','V_A','membership','reason']))
    print('\nCOST SCENARIOS (UNCERTAIN)\n'+json.dumps(cost,indent=2))
    print('\nSMALLEST USEFUL COMPLEMENTARY NEXT BATCH (NOT AUTHORIZED)\n'+audit.table(next_batch,list(next_batch[0])))
    print('\n520 validated grid rows/1326 proposed combinations;806 unavailable. AP/SKR/AO runs=0. STOP.')


if __name__ == '__main__':
    main()
