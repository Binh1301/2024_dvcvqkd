"""Saved-data Objective A writing/build checks only: forbid scientific reruns."""
import ast
from collections import Counter
from contextlib import ExitStack
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_theta10_D55_ao_scientific_results as saved
from scripts import run_theta10_D55_ao_stopping_sensitivity as sensitivity
from src.cvqkd import gram_moments

OUT = ROOT / 'results/theta10_D55_ao_manuscript_finalization'
SENS = sensitivity.OUT


def sha(path):
    return saved.sweep.sha256(path)


def json_file(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def verify_materials():
    data = saved.analyze()  # Validates existing source/objective provenance; no evaluation.
    configs = saved.rows(SENS / 'sensitivity_grid_16_configs.csv')
    assert {(int(x['Rmax']), float(x['epsilon'])) for x in configs} == {(r, e) for r in (4, 6, 8, 10) for e in (1e-6, 1e-7, 1e-8, 1e-9)}
    for c in configs:
        expected = 279 if float(c['epsilon']) == 1e-6 else 283
        assert int(c['total_outer_iterations']) == expected
        assert int(c['same_solution_distances']) == int(c['catalog_matches']) == 26
        assert float(c['max_abs_delta_K']) == float(c['max_abs_delta_V_A']) == float(c['max_abs_delta_nu']) == 0
        assert int(c['completed_coordinate_calls']) == int(c['runs_cap_terminated']) == 0
        assert int(c['missing_source_blocked_runs']) == 129 and int(c['distinct_missing_sources']) == 55
        assert json.loads(c['stop_reason_counts']) == {'STAGNATED_IN_EXACT_CATALOG': 20, 'UNRESOLVED_BOUNDARY': 109}
    best = {r['L_km']: r for r in data['best']}
    ds = saved.rows(SENS / 'sensitivity_by_distance.csv')
    assert len(ds) == 416
    for row in ds:
        b = best[float(row['L_km'])]
        assert saved.pair(row['nu_raw'], row['V_A']) == saved.pair(b['best_nu_raw'], b['best_V_A'])
        assert float(row['K']) == b['best_SKR']
        assert float(row['delta_K']) == float(row['delta_V_A']) == float(row['delta_nu_raw']) == 0
    coords = saved.rows(SENS / 'coordinate_completion_audit.csv')
    assert len(coords) == 9856 and not any(x['completed'] == 'True' for x in coords)
    missing = set()
    coordinate_counts = Counter()
    for s in coords:
        coordinate_counts[s['configuration']] += 1
        for event in json.loads(s['missing_points']):
            missing.add(saved.pair(s['fixed'], event['value']) if s['variable'] == 'V_A' else saved.pair(event['value'], s['fixed']))
    assert len(missing) == 55
    assert all(coordinate_counts[c['configuration']] == int(c['coordinate_calls']) for c in configs)
    for v in saved.rows(saved.OUT / 'optimized_skr_26_distances.csv'):
        b = best[float(v['L_km'])]
        assert all(float(v[k]) == b[k] for k in ('best_nu_raw', 'best_V_A', 'best_SKR', 'I_AB', 'beta_I_AB', 'chi_BE'))
    # Read literal constants from code, without invoking any optimizer.
    constants = {}
    for node in ast.parse((ROOT / 'scripts/run_theta10_D55_alt_opt.py').read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant):
            constants[node.targets[0].id] = node.value.value
    assert [constants[k] for k in ('MAX_AO_ITERATIONS', 'K_TOLERANCE', 'PARAMETER_TOLERANCE', 'MAX_REFINEMENT_STAGES', 'MAX_BOUNDARY_EXPANSIONS')] == [6, 1e-8, 1e-6, 4, 3]
    uniform = [r for r in data['comparison'] if r['scheme'] == saved.sweep.UNIFORM_SCHEME]
    assert len(uniform) == 26 and max(r['distance_km'] for r in uniform if r['K'] > 0) == 25
    return data, configs, {'MB_sources': 147, 'stored_metrics': 3822, 'distances': 26,
        'sensitivity_configurations': 16, 'baseline_starts': 129, 'baseline_iterations': 283,
        'epsilon_1e6_iterations': 279, 'sensitivity_coordinate_calls': 9856, 'completed_coordinates': 0,
        'distinct_missing_pairs': 55, 'catalog_matches': 26, 'Uniform_compatible_stored_points': 26,
        'Uniform_boundary_fully_optimized': False, 'continuous_global_optimum_certified': False}


def latex_check(directory):
    """Focused structural checker, not a TeX compiler or layout certification."""
    inputs, figures, seen = [], [], set()

    def expand(name):
        path = directory / name
        assert path.exists(), f'Missing input: {name}'
        assert name not in seen, f'Repeated input/cycle: {name}'
        seen.add(name)
        text = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text(encoding='utf-8'))
        inputs.append(name)
        braces = 0
        for token in re.finditer(r'(?<!\\)[{}]', text):
            braces += 1 if token.group() == '{' else -1
            assert braces >= 0, f'Brace underflow: {name}'
        assert braces == 0, f'Unbalanced braces: {name}'
        stack = []
        for kind, env in re.findall(r'\\(begin|end)\{([^}]+)\}', text):
            if kind == 'begin':
                stack.append(env)
            else:
                assert stack and stack.pop() == env, f'Environment mismatch: {name}/{env}'
        assert not stack, f'Unclosed environment: {name}'
        for image in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', text):
            assert (directory / image).exists(), f'Missing figure: {image}'
            figures.append(image)
        return re.sub(r'\\input\{([^}]+)\}', lambda m: expand(m[1]), text)

    flat = expand('overleaf_main.tex')
    labels = re.findall(r'\\label\{([^}]+)\}', flat)
    refs = re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', flat)
    assert len(labels) == len(set(labels)), 'Duplicate labels'
    assert set(refs) <= set(labels), f'Undefined labels: {set(refs) - set(labels)}'
    assert not re.search(r'\\(?:cite\w*|bibliography|bibliographystyle|addbibresource)\b', flat), 'Review bibliography dependency'
    assert len(re.findall(r'\\documentclass', flat)) == 1
    assert len(re.findall(r'\\begin\{algorithm\}', flat)) == 1
    numbers, counter = {}, 2
    for env, content in re.findall(r'\\begin\{(equation|align)\}(.*?)\\end\{\1\}', flat, re.S):
        parts = [content] if env == 'equation' else re.split(r'\\\\', content)
        for part in parts:
            if not part.strip() or re.search(r'\\(?:nonumber|notag)\b', part):
                continue
            counter += 1
            for label in re.findall(r'\\label\{([^}]+)\}', part):
                numbers[label] = counter
    assert [numbers[k] for k in ('eq:p1', 'eq:p2', 'eq:ao-stopping')] == [5, 6, 7], numbers
    return {'status': 'CURRENTLY_VERIFIED_PASS', 'inputs': inputs, 'figures': figures,
        'labels': labels, 'references': refs, 'preview_equation_numbers': numbers,
        'algorithm_count': 1, 'bibliography_dependencies': 0,
        'limitations': 'Static syntax/dependency/label check only; macro expansion, packages, actual numbering and layout require compilation.'}


def appendices(data, configs):
    lines = [r'\begin{table}[htbp]', r'\centering\small',
        r'\caption{All sixteen settings. $N_{\rm cyc}$ counts outer updates over129 starts; closed includes52 final postchecks. Every row has129 missing-source-blocked starts,20 catalog-stagnation and109 unresolved-boundary states.}',
        r'\label{tab:ao-stopping-detail}', r'\begin{tabular}{rrrrrr}', r'\hline',
        r'$R_{\max}$ & $\epsilon$ & Same & $\max|\Delta K|$ & $N_{\rm cyc}$ & Closed \\', r'\hline']
    for c in sorted(configs, key=lambda x: (int(x['Rmax']), -float(x['epsilon']))):
        exponent = c['epsilon'].split('e-')[-1].lstrip('0')
        lines.append(f"{c['Rmax']} & $10^{{-{exponent}}}$ &26/26 &0 &{c['total_outer_iterations']} &0/{c['coordinate_calls']} " + r'\\')
    lines += [r'\hline', r'\end{tabular}', r'\end{table}']
    (OUT / 'appendix_sensitivity_table.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    lines = [r'\begin{table}[htbp]', r'\centering\small',
        r'\caption{Selected finite-catalog maxima. Parameters use raw MB convention. Values are rounded for presentation only; the supplied CSV preserves exact stored binary64 values.}',
        r'\label{tab:ao-parameters-26}', r'\begin{tabular}{rrrr}', r'\hline',
        r'$L$ (km) & $\nu_{\rm raw}$ & $V_A$ (SNU) & $K$ (bits/use) \\', r'\hline']
    for r in data['best']:
        lines.append(f"{r['L_km']!r} &{r['best_nu_raw']:.12g} &{r['best_V_A']:.12g} &{r['best_SKR']:.10g} " + r'\\')
    lines += [r'\hline', r'\end{tabular}', r'\end{table}']
    (OUT / 'optimized_parameters_table.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def reports(validation):
    audit = """# Manuscript consistency audit

CURRENTLY_VERIFIED_PASS: saved-data/provenance and focused static LaTeX checks.

Repository discovery found only the standalone article master in ao_final_scientific_results; no full-paper master, IEEEtran template, original numbered-equation source or bibliography was available (including hidden-file search outside .git/.venv). We therefore integrate into a NEW standalone article wrapper, not an unseen full paper. No previous manuscript file is edited. Known labels eq:p1, eq:p2, alg:ao and the joint-section/figure labels are preserved. A new eq:ao-stopping label is added. Preview numbering is P1(5), P2(6), stopping(7), using a documented wrapper-only counter offset2; this is not proof of original-paper numbering. Remove the offset when inserting into the actual full master and resolve any colliding labels there.

1. P1 fixes nu^(r-1); P2 fixes new VA^(r). Approximate signs reflect finite numerical search.
2. Algorithm1 preserves original initialization, four raw starts, prior-distance warm start, ordered tie handling, last complete update, unresolved latch and original failure/threshold status logic. Missing moments do NOT independently trigger immediate outer termination when a valid best point exists.
3. Rmax6 is a conservative safeguard: caps4/6/8/10 give identical terminals; no cap termination occurs.
4. Epsilon1e-8 measures objective stagnation, not absolute error;1e-9 gives no gains;1e-6 reduces283 cycles to279 with identical terminals.
5. All16 settings and416 distance records checked against original147-source values. Scope: per-setting129 starts, 20 stagnation/109 unresolved, same55 missing sources. No successful coordinate search among9856 calls (9024 within cycles +832 postchecks).
6. No continuous/global-optimality, universal-start agreement, error-bound or expanded-security claim is made. Manuscript statements about non-certification are intentional, not optimizer failures hidden as convergence.
7. Raw convention explicitly nu_MB=nu_raw; nu_repo=42.5*nu_raw. Ref(.165,5.5),K.07798099387393764;22km(.165,5.475),K.07661740491526092 confirmed. Individual baseline catalog matches59/129, unanimous distances0/26.
8. The intended domain retains nu>=0; original AO searches nu>0. Compatible independently stored Uniform samples exist at26 distances under the same model, but the VA continuum on nu=0 is not fully optimized and Uniform is excluded from positive-MB AO. Existing positive-only plot stops Uniform25km, both MB40km; raw negative tail is not changed.
9. Compact main table groups four caps per epsilon; each cell is per configuration, not a pooled statistic. Detailed16 rows and rounded26-distance parameters are in appendices; copied CSVs are byte-identical. All five figure PDFs are byte-identical to validated originals, with no new rendering.
10. Input graph, braces, environments, labels/references, bibliography dependencies, one algorithm and preview5/6/7 numbering checked. No bibliography commands/dependencies were introduced. Undefined macros/package availability and overfull/layout issues require a real TeX compiler.
11. Compile status is recorded separately; static checks are NOT a build pass. The downloadable package is ready for an external build, not a claim that Overleaf has compiled it.
12. Original scientific source/configs/frozen files/AO defaults/cache/results protected by hashes. No AP, channel, source, MI/Holevo, SKR evaluation, AO rerun, interpolation, observer/profiling or final-test access.

The frozen specification historical-hash discrepancy remains PREEXISTING_UNCHANGED; publication-scale lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS. This task writes existing conditional direct-Z-minus results only and does not certify another protocol or the broader frozen training model.
"""
    (OUT / 'manuscript_consistency_audit.md').write_text(audit, encoding='utf-8')
    instructions = """# Overleaf build instructions

This is a standalone Objective A section package, NOT the unavailable complete original paper.

1. In Overleaf, use **New Project -> Upload Project** and upload objective_A_overleaf.zip.
2. Set **Main document** to `overleaf_main.tex` in the project settings.
3. Select compiler **pdfLaTeX**, retaining a current standard TeX Live version.
4. Recompile. Resolve any errors; recompile again if references request another pass.
5. Check equations P1(5),P2(6),stopping(7), Algorithm1, both sensitivity tables and all five figures. Inspect undefined-reference/package/command messages, overfull boxes and float placement before considering the external build verified.

Required standard packages: geometry, amsmath, amssymb, graphicx, algorithm, algpseudocode. No bibliography or custom font asset is needed. Five existing vector PDFs are under figures/. No optimizer, source cache or Python execution is needed on Overleaf.

For your actual complete paper, retain its own document class/preamble and established algorithm style. Insert joint_optimization_final.tex at the existing optimization section; retain its subsidiary inputs and figures, and place the two appendix inputs in its existing appendix. Do NOT duplicate the standalone document environment or copy its artificial equation-counter offset. Resolve label conflicts against that actual master. Full-paper integration and IEEE-specific float layout cannot be checked until those sources are supplied; no IEEEtran master was discovered here.

Official instructions: [uploading a project](https://docs.overleaf.com/managing-projects-and-files/uploading-a-project), [main document](https://docs.overleaf.com/getting-started/recompiling-your-project/the-main-document), [compiler selection](https://docs.overleaf.com/getting-started/recompiling-your-project/selecting-a-tex-live-version-and-latex-compiler).
"""
    (OUT / 'README_OVERLEAF.md').write_text(instructions, encoding='utf-8')
    compile_report = '# LaTeX compile report\n\n'
    compile_report += f"Compilation: {validation['compile_status']}.\n\n"
    compile_report += ('No suitable pdflatex/xelatex/lualatex/tectonic engine was found on PATH. '
        'No engine was installed and no remote Overleaf compilation was invoked. No compiled manuscript PDF is fabricated; it is absent. '
        'Macro expansion, package availability, actual auxiliary references, overfull boxes, float layout and mathematical rendering are NOT_VERIFIED. '
        'Static structure/dependencies/preview labels pass; this does not substitute for compilation.\n\n'
        if validation['compile_status'] == 'NOT_VERIFIED' else 'Compiler log and actual compiled manuscript.pdf are included; inspect any recorded layout warnings.\n\n')
    compile_report += instructions
    (OUT / 'latex_compile_report.md').write_text(compile_report, encoding='utf-8')
    report = """# Objective A manuscript finalization

Scientific writing/integration: CURRENTLY_VERIFIED_PASS. Local compilation status: COMPILE_STATUS.

All eight requested deliverables and an Overleaf-ready ZIP are present. Newly added manuscript files: joint_optimization_final.tex, algorithm1_ao_final.tex, stopping_parameter_sensitivity_final.tex, sensitivity_table_final.tex, overleaf_main.tex; supplementary generated files appendix_sensitivity_table.tex and optimized_parameters_table.tex. Reports: manuscript_consistency_audit.md, latex_compile_report.md and this report. No previous manuscript or numerical artifact was overwritten.

The available standalone article master has been extended with the finalized joint section, Algorithm1, actual stopping sensitivity and two appendices. The complete original paper was not supplied/discovered, so integration into that absent master is NOT_VERIFIED. Preview numbering5/6/7 is deliberately documented, not invented original-paper evidence. No unrelated physics/security section is rewritten. Required figures and two small exact-source-result CSVs are copied unchanged, without duplicating the research cache.

Best selected AO terminals match finite-catalog maxima26/26, and all16 sensitivity settings preserve selected pairs/K. Rmax6 and epsilon1e-8 are computational safeguards only; tighter thresholds/larger caps do not remove source missingness or certify accuracy. No new optimizer/physics/AP execution. Uniform boundary is sampled independently, not fully optimized; continuous/global convergence is not certified. Stop after Objective A; Objective B is NOT_RUN and no source-run authority is implied.

Machine evidence: manuscript_validation.json, package_manifest.json and protected_input_manifest.json. Applicable current regression results are recorded in verification_results.json after tests; do not substitute historical test counts. Git state remains dirty from preserved preexisting changes on branch10-5-2026/HEAD eec4dd114d9f3ab128f82c37be520dafd197caaa. Only new deliverables/writing checker/tests and relevant lifecycle records are changed by this task. Frozen historical-hash discrepancy and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain unchanged.
""".replace('COMPILE_STATUS', validation['compile_status'])
    (OUT / 'manuscript_finalization_report.md').write_text(report, encoding='utf-8')


def main():
    if (OUT / 'manuscript_validation.json').exists():
        raise SystemExit('Refusing to overwrite finalized artifacts')
    protected = saved.read(SENS / 'protected_input_manifest.json')
    for directory in (SENS, saved.OUT, ROOT / 'src', ROOT / 'configs'):
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                protected[str(p.relative_to(ROOT))] = sha(p)
    for name in ('FINAL_MODEL_SPEC.md', 'SECURITY_SCOPE_FREEZE.md', 'NUMERICAL_CONVERGENCE_PREREGISTRATION.md'):
        protected['docs/' + name] = sha(ROOT / 'docs' / name)
    assert all(sha(ROOT / name) == digest for name, digest in protected.items())
    old_validation = saved.read(SENS / 'sensitivity_validation.json')
    assert all(sha(SENS / name) == digest for name, digest in old_validation['output_hashes'].items())
    with ExitStack() as guard:
        for obj, name in ((saved.ao, 'evaluate_candidate'), (saved.ao, 'run_single_ao'),
                          (saved.ao, 'adaptive_maximize_1d'), (saved.sweep, 'run_single_distance_ao'),
                          (saved.sweep, 'make_channel'), (saved.ao.ExactMBEvaluator, 'source_moments'),
                          (gram_moments, '_fallback')):
            guard.enter_context(patch.object(obj, name, saved.audit.forbidden))
        data, configs, numbers = verify_materials()
    appendices(data, configs)
    (OUT / 'figures').mkdir(exist_ok=True)
    for directory, names in ((saved.OUT, ('ao_convergence.pdf', 'ao_parameter_evolution.pdf', 'skr_vs_distance.pdf')),
                             (SENS, ('rmax_sensitivity.pdf', 'epsilon_sensitivity.pdf'))):
        for name in names:
            shutil.copy2(directory / name, OUT / 'figures' / name)
            assert sha(directory / name) == sha(OUT / 'figures' / name)
    for directory, name in ((saved.OUT, 'optimized_skr_26_distances.csv'), (SENS, 'sensitivity_grid_16_configs.csv')):
        shutil.copy2(directory / name, OUT / name)
        assert sha(directory / name) == sha(OUT / name)
    structural = latex_check(OUT)
    engine = next((p for n in ('pdflatex', 'xelatex', 'lualatex') if (p := shutil.which(n))), None)
    validation = {'status': 'CURRENTLY_VERIFIED_PASS_WRITING_STATIC_ONLY', 'scientific_checks': numbers,
        'latex_static': structural, 'compile_status': 'NOT_VERIFIED', 'compile_engine': engine,
        'full_paper_master_available': False, 'original_template': 'article',
        'original_sources_modified': False, 'new_AP_or_AO_or_objective_evaluations': 0,
        'protected_count': len(protected), 'frozen_historical_hash_discrepancy': 'PREEXISTING_UNCHANGED',
        'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS', 'producer_sha256': sha(Path(__file__)),
        'authorization_attachment_sha256': sha(Path('C:/Users/HP/.codex/attachments/525d3c8c-53da-4068-83a5-63907452c8b0/Pasted text.txt')),
        'compile_discovery_scope': 'PATH engines; no installation or remote build', 'Objective_B': 'NOT_RUN'}
    if engine:
        build_log = []
        for _ in range(2):
            process = subprocess.run([engine, '-interaction=nonstopmode', '-halt-on-error', 'overleaf_main.tex'],
                cwd=OUT, capture_output=True, text=True, errors='replace', timeout=60)
            build_log.append(process.stdout + process.stderr)
            assert process.returncode == 0, 'LaTeX compilation failed; preserve build log'
        log = '\n'.join(build_log)
        (OUT / 'compiler_stdout.log').write_text(log, encoding='utf-8')
        assert not re.search(r'undefined references|Reference .+ undefined|LaTeX Error', build_log[-1], re.I)
        shutil.copy2(OUT / 'overleaf_main.pdf', OUT / 'manuscript.pdf')
        validation['compile_status'] = 'CURRENTLY_VERIFIED_PASS'
    reports(validation)
    json_file('protected_input_manifest.json', protected)
    package_files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.suffix in ('.tex', '.md', '.pdf', '.csv')
                           and p.name not in ('overleaf_main.pdf', 'manuscript.pdf'))
    manifest = {p.relative_to(OUT).as_posix(): sha(p) for p in package_files}
    json_file('package_manifest.json', manifest)
    archive = OUT / 'objective_A_overleaf.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in package_files + [OUT / 'package_manifest.json']:
            z.write(p, p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        import hashlib
        assert all(hashlib.sha256(z.read(n)).hexdigest() == h for n, h in manifest.items())
    assert all(sha(ROOT / name) == digest for name, digest in protected.items())
    validation.update(protected_hashes_unchanged=True, package_file_count=len(package_files) + 1,
        archive_sha256=sha(archive), output_hashes={p.relative_to(OUT).as_posix(): sha(p) for p in OUT.rglob('*') if p.is_file()})
    json_file('manuscript_validation.json', validation)
    print(json.dumps({k: validation[k] for k in ('status', 'compile_status', 'protected_count', 'package_file_count', 'Objective_B')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
