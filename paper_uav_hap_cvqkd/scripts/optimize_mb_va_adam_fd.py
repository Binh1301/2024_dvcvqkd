"""Version 1: two global MB/VA parameters, exact effective-channel SKR and FD."""
from __future__ import annotations

import argparse
import copy
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
import torch

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import analyze_product, derive_physical_inputs
from scripts.full_support_c4_worker import rows_converged
from scripts.run_baselines_cached_source_moments import evaluate_fixed_ensemble
from scripts.run_effective_channel_va2 import (
    MI_SAMPLES_PER_SYMBOL, MI_SEEDS, _json_value, physical_channel_parameters,
)
from scripts.run_mb_skr_sweep_zeta30_va2 import _load_source
from src.channel.phase_noise import phase_distortion_variance, phase_noise_coefficient
from src.cvqkd.gram_moments import GramMomentResult, c4_gram_source_moments
from src.cvqkd.mutual_information import standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator

OUTPUT = ROOT / "results" / "joint_mb_va_adam_ao095_effective"
REFERENCE = ROOT / "results/mb_skr_sweep_zeta30_va2_ao095_aperture_r004/mb_skr_sweep_ao095_aperture_r004.csv"
FD_STEPS = {"nu": (0.01, 0.003, 0.001), "VA": (0.1, 0.03, 0.01)}
# Optimizer diagnostics only; these do not change any scientific backend gate.
FD_ATOL, FD_RTOL, OBJECTIVE_FLOOR = 1e-7, 0.05, 1e-10


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(_json_value(value), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_csv(path, rows, fields):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def source_fingerprint():
    paths = ("src/cvqkd/gram_moments.py", "scripts/full_support_c4_worker.py",
             "src/modulation/qam256.py", "src/modulation/normalization.py")
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def scenario(config):
    physical = derive_physical_inputs(
        zenith_angle_rad_override=math.radians(30), aperture_radius_m_override=0.04,
    )
    moments = analyze_product(physical["v_sc"], physical)["moments"]
    raw = phase_distortion_variance(
        config["channel"]["phase_noise"]["cn2_phase_m_minus_two_thirds"],
        physical["wavelength_m"], physical["link_length_m"],
    )
    compensated = (1 - 0.95) * raw
    coefficient = phase_noise_coefficient(compensated)
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"], physical["epsilon_base_snu"], coefficient, 1.0,
    )
    return dict(
        eta_AO=0.95, zeta=30.0, aperture_radius=0.04,
        link_distance_m=physical["link_length_m"], effective_T=security["T"],
        epsilon_base=security["epsilon_base"], tau_phi_raw_squared=raw,
        tau_phi_AO_squared=compensated, c_phi_AO=coefficient,
    )


class ExactEvaluator:
    """One physical source per candidate; identical five MI streams throughout."""

    def __init__(self, config, channel, output, source_provider=None):
        self.config, self.channel, self.output = config, channel, Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.numerical = holevo_numerical_kwargs(config)
        self.cache = {}
        self.moments = {}
        self.source_hash = hashlib.sha256(json.dumps(source_fingerprint(), sort_keys=True).encode()).hexdigest()
        self.source_provider = source_provider or self.source_moments
        self.noises = tuple(standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL), generator=torch_generator(seed),
            device=torch.device("cpu"),
        ) for seed in MI_SEEDS)

    def source_moments(self, ensemble, nu, va):
        if (nu, va) == (0.15, 2.0):
            old = _load_source(ensemble, nu)
            payload = json.loads(Path(old["checkpoint"]).read_text(encoding="utf-8"))
            if not rows_converged(payload["rows"]):
                raise FloatingPointError("Regression source does not pass existing AP convergence checks")
            return GramMomentResult(
                torch.tensor([old["C"]], dtype=torch.float64),
                torch.tensor([old["w"]], dtype=torch.float64),
                ({"route": old["route"], "support_size": 256, "checkpoint": old["checkpoint"],
                  "checkpoint_sha256": hashlib.sha256(Path(old["checkpoint"]).read_bytes()).hexdigest(),
                  "input_hashes": payload["input_hashes"]},),
            )
        key = hashlib.sha256((float(nu).hex() + ":" + float(va).hex()).encode()).hexdigest()
        checkpoint = self.output / "source_checkpoints" / (key + ".json")
        checkpoint.parent.mkdir(exist_ok=True)
        return c4_gram_source_moments(
            ensemble, density_eigenvalue_tolerance=self.numerical["density_eigenvalue_tolerance"],
            physicality_tolerance=self.numerical["physicality_tolerance"],
            fallback_checkpoint_path=checkpoint,
            scheme_config_hash=self.source_hash,
        )

    @staticmethod
    def ensemble(nu, va, regression=False):
        nu, va = float(nu), float(va)
        if not math.isfinite(nu) or not math.isfinite(va) or not 0 <= nu <= 0.30:
            raise ValueError("Invalid MB/VA coordinates")
        if not 0.1 <= va <= 1.5 and not (regression and (nu, va) == (0.15, 2.0)):
            raise ValueError("VA exceeds the fixed-policy budget; VA=2 is regression-only")
        ensemble = reference_ensemble(
            "mb", batch_size=1, modulation_variance=va, nu_mb=nu,
            v_min=0.1, v_max=4.0 if regression else 1.5, n_peak_photons=30.0,
        )
        ensemble.validate(tolerance=1e-12)
        return ensemble

    def prepare_sources(self, candidates, workers=4):
        """Parallelize independent AP subprocesses; keep MI evaluation serial."""
        def prepare(pair):
            if pair not in self.cache and pair not in self.moments:
                print(f"source start nu={pair[0]:.12g} VA={pair[1]:.12g}", flush=True)
                self.moments[pair] = self.source_provider(self.ensemble(*pair), *pair)
                print(f"source ready nu={pair[0]:.12g} VA={pair[1]:.12g}", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(prepare, dict.fromkeys(candidates)))

    def __call__(self, nu, va, *, regression=False):
        nu, va = float(nu), float(va)
        if not math.isfinite(nu) or not math.isfinite(va) or not 0 <= nu <= 0.30:
            raise ValueError("Invalid MB/VA coordinates")
        if not 0.1 <= va <= 1.5 and not (regression and (nu, va) == (0.15, 2.0)):
            raise ValueError("VA exceeds the fixed-policy budget; VA=2 is regression-only")
        if (nu, va) in self.cache:
            return self.cache[nu, va]
        started = time.perf_counter()
        row = {"nu": nu, "VA": va, "status": "FAILED"}
        print(f"evaluate nu={nu:.12g} VA={va:.12g}", flush=True)
        try:
            ensemble = self.ensemble(nu, va, regression)
            moments = self.moments.get((nu, va))
            if moments is None:
                moments = self.source_provider(ensemble, nu, va)
                self.moments[nu, va] = moments
            results = [evaluate_fixed_ensemble(
                ensemble, torch.tensor([self.channel["effective_T"]], dtype=torch.float64),
                torch.tensor([self.channel["epsilon_base"]], dtype=torch.float64),
                phase_coefficient=self.channel["c_phi_AO"],
                beta_reconciliation=self.config["cvqkd"]["beta_reconciliation"],
                awgn_samples=MI_SAMPLES_PER_SYMBOL, standard_noise_samples=noise,
                source_moment_evaluator=lambda *_a, **_k: moments, **self.numerical,
            ) for noise in self.noises]
            raw = [float(r["raw_k"][0]) for r in results]
            row.update(
                status="CURRENTLY_VERIFIED_PASS", I_AB=float(np.mean([float(r["i_ab"][0]) for r in results])),
                chi_BE=float(results[0]["chi_be"][0]), raw_SKR=float(np.mean(raw)),
                raw_SKR_replicates=raw, epsilon_total=float(results[0]["epsilon_total"][0]),
                peak_photons=float(ensemble.amplitudes.abs().square().max()),
                pmf_sum=float(ensemble.probabilities.sum()),
                VA_error=float((ensemble.computed_va() - va).abs().max()),
                holevo_mode=results[0]["holevo_diagnostics"]["mode"],
                source_C=float(moments.coherent_correlation[0]), source_w=float(moments.w[0]),
                source_diagnostics=moments.diagnostics[0], source_producer_hash=self.source_hash,
            )
            if not all(math.isfinite(row[k]) for k in ("I_AB", "chi_BE", "raw_SKR")):
                raise FloatingPointError("Nonfinite objective")
            self.cache[nu, va] = row
            return row
        except Exception as error:
            row.update(status="FAILED", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            row["elapsed_seconds"] = time.perf_counter() - started
            with (self.output / "candidate_evaluations.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(_json_value(row), allow_nan=False) + "\n")


def reproduction(evaluate):
    with REFERENCE.open(newline="", encoding="utf-8") as stream:
        expected = next(r for r in csv.DictReader(stream) if float(r["mb_parameter"]) == 0.15)
    obtained = evaluate(0.15, 2.0, regression=True)
    values = {**evaluate.channel, **obtained}
    aliases = {"effective_T": "effective_transmittance", "tau_phi_AO_squared": "tau_phi_ao_squared"}
    keys = ("effective_T", "epsilon_base", "tau_phi_raw_squared", "tau_phi_AO_squared",
            "c_phi_AO", "epsilon_total", "I_AB", "chi_BE", "raw_SKR")
    aliases["c_phi_AO"] = "c_phi_ao"
    checks = {k: {"expected": float(expected[aliases.get(k, k)]), "obtained": values[k]} for k in keys}
    passed = all(math.isclose(v["obtained"], v["expected"], rel_tol=1e-7, abs_tol=1e-10) for v in checks.values())
    report = {"status": "CURRENTLY_VERIFIED_PASS" if passed else "FAILED", "checks": checks}
    write_json(evaluate.output / "reproduction_check.json", report)
    if not passed:
        raise FloatingPointError("Effective-channel reproduction failed")
    return report


class MBVAParameters(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.u_mb = torch.nn.Parameter(torch.tensor(0.0, dtype=torch.float64))
        self.u_va = torch.nn.Parameter(torch.tensor(math.log(1.8), dtype=torch.float64))

    def forward(self):
        return 0.30 * torch.sigmoid(self.u_mb), 0.1 + 1.4 * torch.sigmoid(self.u_va)

    def assign_loss_gradients(self, g_nu, g_va):
        if not all(math.isfinite(g) for g in (g_nu, g_va)):
            raise FloatingPointError("Nonfinite finite-difference gradient")
        with torch.no_grad():
            s_nu, s_va = torch.sigmoid(self.u_mb), torch.sigmoid(self.u_va)
            self.u_mb.grad = -g_nu * 0.30 * s_nu * (1 - s_nu)
            self.u_va.grad = -g_va * 1.4 * s_va * (1 - s_va)


def stencil(nu, va, coordinate, h):
    if not math.isfinite(h) or h <= 0:
        raise ValueError("Finite-difference step must be positive")
    center = nu if coordinate == "nu" else va
    lower, upper = (0.0, 0.30) if coordinate == "nu" else (0.1, 1.5)
    if center - h < lower or center + h > upper:
        raise ValueError("Validated central stencil crosses a boundary; no silent clipping")
    return ((nu + h, va), (nu - h, va)) if coordinate == "nu" else ((nu, va + h), (nu, va - h))


def difference(evaluate, nu, va, coordinate, h):
    plus_pair, minus_pair = stencil(nu, va, coordinate, h)
    plus, minus = evaluate(*plus_pair), evaluate(*minus_pair)
    values = (np.asarray(plus["raw_SKR_replicates"]) - np.asarray(minus["raw_SKR_replicates"])) / (2 * h)
    gradient = (plus["raw_SKR"] - minus["raw_SKR"]) / (2 * h)
    stderr = float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0
    if not math.isfinite(gradient) or not math.isfinite(stderr):
        raise FloatingPointError("Nonfinite FD result")
    # CRN-paired uncertainty, not the independent marginal MI error bars.
    resolved = abs(gradient) > 2 * stderr + OBJECTIVE_FLOOR / h
    return dict(coordinate=coordinate, h=h, nu=nu, VA=va, gradient=gradient,
                paired_stderr=stderr, resolved=resolved, status="RESOLVED" if resolved else "NEAR_ZERO_OR_UNRESOLVED",
                plus_nu=plus_pair[0], plus_VA=plus_pair[1], minus_nu=minus_pair[0], minus_VA=minus_pair[1],
                plus_SKR=plus["raw_SKR"], minus_SKR=minus["raw_SKR"])


FD_FIELDS = ("coordinate", "h", "nu", "VA", "gradient", "paired_stderr", "resolved", "status",
             "plus_nu", "plus_VA", "minus_nu", "minus_VA", "plus_SKR", "minus_SKR")
HISTORY_FIELDS = ("iteration", "nu", "VA", "epsilon_total", "I_AB", "chi_BE", "raw_SKR",
                  "dK_dnu", "dK_dVA", "grad_u_nu", "grad_u_va", "status", "old_nu", "old_VA",
                  "learning_rate", "peak_photons", "VA_error", "pmf_sum", "error")


def readiness(evaluate, output, workers=4):
    pairs = [(0.15, 1.0)]
    for coordinate, steps in FD_STEPS.items():
        for h in steps:
            pairs.extend(stencil(0.15, 1.0, coordinate, h))
    if hasattr(evaluate, "prepare_sources"):
        evaluate.prepare_sources(pairs, workers)
    initial = evaluate(0.15, 1.0)
    rows, chosen = [], {}
    for coordinate, steps in FD_STEPS.items():
        current = [difference(evaluate, 0.15, 1.0, coordinate, h) for h in steps]
        rows.extend(current)
        stable = all(
            math.copysign(1, a["gradient"]) == math.copysign(1, b["gradient"])
            and abs(a["gradient"] - b["gradient"]) <= FD_ATOL + FD_RTOL * max(abs(a["gradient"]), abs(b["gradient"]))
            for a, b in zip(current, current[1:])
        )
        if stable and all(r["resolved"] for r in current):
            chosen[coordinate] = steps[1]
    write_csv(Path(output) / "finite_difference_readiness.csv", rows, FD_FIELDS)
    report = dict(status="CURRENTLY_VERIFIED_PASS" if len(chosen) == 2 else "FAILED",
                  chosen_steps=chosen, rows=rows, absolute_tolerance=FD_ATOL,
                  relative_tolerance=FD_RTOL, objective_floor=OBJECTIVE_FLOOR,
                  uncertainty="2 paired standard errors across the five fixed CRN seeds; empirical, not certified")
    write_json(Path(output) / "finite_difference_readiness.json", report)
    return initial, report


def joint_adam_step(model, optimizer, evaluate, h_nu, h_va, workers=4):
    with torch.no_grad():
        nu, va = (float(x) for x in model())
    pairs = [*stencil(nu, va, "nu", h_nu), *stencil(nu, va, "VA", h_va)]
    if hasattr(evaluate, "prepare_sources"):
        evaluate.prepare_sources(pairs, workers)
    # Both gradients use exactly the same old pair; no update between stencils.
    g_nu = difference(evaluate, nu, va, "nu", h_nu)["gradient"]
    g_va = difference(evaluate, nu, va, "VA", h_va)["gradient"]
    before = copy.deepcopy(model.state_dict()), copy.deepcopy(optimizer.state_dict())
    optimizer.zero_grad(set_to_none=True)
    model.assign_loss_gradients(g_nu, g_va)
    loss_gradients = float(model.u_mb.grad), float(model.u_va.grad)
    try:
        optimizer.step()
        with torch.no_grad():
            new_nu, new_va = (float(x) for x in model())
        row = dict(evaluate(new_nu, new_va))
    except Exception:
        model.load_state_dict(before[0])
        optimizer.load_state_dict(before[1])
        raise
    row.update(old_nu=nu, old_VA=va, dK_dnu=g_nu, dK_dVA=g_va,
               grad_u_nu=loss_gradients[0], grad_u_va=loss_gradients[1],
               learning_rate=optimizer.param_groups[0]["lr"], status="ACCEPTED")
    return row


def local_landscape(evaluate, best, output, workers=4):
    nus = sorted({min(.30, max(0., best["nu"] + d)) for d in (-.02, -.01, 0., .01, .02)})
    vas = sorted({min(1.5, max(.1, best["VA"] + d)) for d in (-.2, -.1, 0., .1, .2)})
    pairs = [(n, v) for n in nus for v in vas]
    if hasattr(evaluate, "prepare_sources"):
        evaluate.prepare_sources(pairs, workers)
    rows = []
    for nu, va in pairs:
        row = dict(evaluate(nu, va))
        deltas = np.asarray(row["raw_SKR_replicates"]) - np.asarray(best["raw_SKR_replicates"])
        error = float(np.std(deltas, ddof=1) / math.sqrt(len(deltas))) if len(deltas) > 1 else 0.0
        tolerance = max(OBJECTIVE_FLOOR, 2 * error)
        row.update(delta_from_Adam_best=row["raw_SKR"] - best["raw_SKR"], comparison_tolerance=tolerance,
                   materially_better=row["raw_SKR"] > best["raw_SKR"] + tolerance)
        rows.append(row)
        write_csv(Path(output) / "local_landscape.csv", rows,
                  (*HISTORY_FIELDS, "delta_from_Adam_best", "comparison_tolerance", "materially_better"))
    better = [r for r in rows if r["materially_better"]]
    return not better, max(better, key=lambda r: r["raw_SKR"]) if better else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--stage", choices=("regression", "readiness", "optimize"), default="optimize")
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--source-workers", type=int, default=4)
    args = parser.parse_args()
    if args.max_steps < 1 or args.source_workers < 1 or not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
        parser.error("Require positive max-steps, source-workers and learning-rate")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs/default.yaml")
    channel = scenario(config)
    print(json.dumps(channel), flush=True)
    evaluator = ExactEvaluator(config, channel, args.output_dir)
    manifest = dict(scenario=channel, configuration=config, source_files=source_fingerprint(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    mi_seeds=MI_SEEDS, mi_samples=MI_SAMPLES_PER_SYMBOL, backend="full_support_c4",
                    holevo_mode="zstar", objective="fixed_effective_channel_raw_SKR", parameters=vars(args))
    manifest["parameters"]["output_dir"] = str(args.output_dir)
    write_json(evaluator.output / "run_inputs.json", manifest)
    history = []
    summary = dict(channel, status="RUNNING", initial_nu=.15, initial_VA=1., initial_SKR=None,
                   best_nu=None, best_VA=None, best_I_AB=None, best_chi_BE=None, best_SKR=None,
                   K_best_positive=None, local_optimum_verified=None, iterations=0,
                   reproduction="NOT_RUN", fd_readiness="NOT_RUN", local_verification="NOT_RUN")
    for name, fields in (("optimization_history.csv", HISTORY_FIELDS),
                         ("finite_difference_readiness.csv", FD_FIELDS), ("local_landscape.csv", HISTORY_FIELDS)):
        write_csv(evaluator.output / name, [], fields)
    write_json(evaluator.output / "optimization_summary.json", summary)
    try:
        regression = reproduction(evaluator)
        summary["reproduction"] = regression["status"]
        if args.stage == "regression":
            summary["status"] = "REGRESSION_ONLY"
            return
        initial, ready = readiness(evaluator, evaluator.output, args.source_workers)
        summary.update(initial_SKR=initial["raw_SKR"], initial=initial, fd_readiness=ready["status"],
                       chosen_steps=ready["chosen_steps"])
        history.append(dict(initial, iteration=0, status="INITIAL"))
        write_csv(evaluator.output / "optimization_history.csv", history, HISTORY_FIELDS)
        if ready["status"] != "CURRENTLY_VERIFIED_PASS":
            summary["status"] = "STOPPED_FD_READINESS"
            return
        if args.stage == "readiness":
            summary["status"] = "READINESS_ONLY"
            return
        model = MBVAParameters()
        optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=0., maximize=False)
        best, previous, quiet = initial, initial, 0
        for iteration in range(1, args.max_steps + 1):
            row = joint_adam_step(model, optimizer, evaluator, ready["chosen_steps"]["nu"],
                                  ready["chosen_steps"]["VA"], args.source_workers)
            row["iteration"] = iteration
            history.append(row)
            write_csv(evaluator.output / "optimization_history.csv", history, HISTORY_FIELDS)
            if row["raw_SKR"] > best["raw_SKR"]:
                best = row
            summary.update(iterations=iteration, best_nu=best["nu"], best_VA=best["VA"],
                           best_I_AB=best["I_AB"], best_chi_BE=best["chi_BE"], best_SKR=best["raw_SKR"],
                           epsilon_total=best["epsilon_total"], K_best_positive=best["raw_SKR"] > 0)
            write_json(evaluator.output / "optimization_summary.json", summary)
            small = abs(row["raw_SKR"] - previous["raw_SKR"]) <= OBJECTIVE_FLOOR and max(
                abs(row["nu"] - previous["nu"]) / .3, abs(row["VA"] - previous["VA"]) / 1.4) <= 1e-4
            quiet = quiet + 1 if small else 0
            previous = row
            if quiet >= 3:
                break
        verified, neighbor = local_landscape(evaluator, best, evaluator.output, args.source_workers)
        summary.update(status="COMPLETED", local_optimum_verified=verified,
                       local_verification="CURRENTLY_VERIFIED_PASS" if verified else "FAILED", better_neighbor=neighbor,
                       stopping="SMALL_UPDATES" if quiet >= 3 else "MAX_STEPS")
    except Exception as error:
        summary.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        print(summary["error"], flush=True)
    finally:
        write_json(evaluator.output / "optimization_summary.json", summary)
        print(json.dumps(_json_value(summary), allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
