"""Compare Gaussian-reference and discrete-input I_AB for UAV-HAP 256-QAM.

The script imports only side-effect-free library modules from ``uav_hap_1`` and
``uav_hap_1_sample``. It does not modify either package. Rayleigh is interpreted
as the channel's radial-displacement fading law, never as an invented symbol
probability mass function.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import inspect
import logging
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import torch


LOGGER = logging.getLogger("compare_iab_methods")
RAYLEIGH_LABEL = "Rayleigh-fading channel (Uniform 256-QAM symbols)"
DETAIL_FIELDS = (
    "distribution",
    "symbol_distribution",
    "scenario",
    "sample_index",
    "T",
    "V_A_input",
    "V_A_measured",
    "epsilon",
    "SNR",
    "H_X",
    "I_AB_gaussian",
    "I_AB_discrete_raw",
    "I_AB_discrete_reported",
    "absolute_difference",
    "signed_difference",
    "relative_difference_percent",
    "visibility_km",
    "beam_waist_m",
    "aperture_radius_m",
    "Cn2",
)
SUMMARY_FIELDS = (
    "distribution",
    "symbol_distribution",
    "scenario",
    "number_of_samples",
    "mean_T",
    "mean_SNR",
    "H_X",
    "mean_I_AB_gaussian",
    "std_I_AB_gaussian",
    "mean_I_AB_discrete",
    "std_I_AB_discrete",
    "mean_absolute_difference",
    "maximum_absolute_difference",
    "RMSE",
    "mean_relative_difference_percent",
    "correlation_coefficient",
    "percent_discrete_le_gaussian",
    "percent_satisfying_mi_bounds",
)


@dataclass(frozen=True)
class SourceDescriptor:
    """Detected package or data source."""

    path: Path
    kind: str
    module_name: str


@dataclass(frozen=True)
class DistributionData:
    """Validated constellation data for one symbol distribution."""

    label: str
    probabilities: np.ndarray
    constellation: np.ndarray
    va_input: float
    va_measured: float
    entropy_bits: float
    detected_names: tuple[str, ...]


@dataclass(frozen=True)
class ProjectData:
    """Inputs imported from the two project packages."""

    uniform: DistributionData
    mb: DistributionData
    t_eff: float
    t_samples: np.ndarray
    excess_noise: float
    metadata: dict[str, float]
    rayleigh_interpretation: str
    source_files: tuple[Path, ...]
    model_compute_iab: Any
    sample_gaussian_iab: Any


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-file", type=Path, help="Path to uav_hap_1 package or source file.")
    parser.add_argument("--sample-file", type=Path, help="Path to uav_hap_1_sample package or source file.")
    parser.add_argument("--noise-samples", type=int, default=128, help="AWGN samples per symbol (default: 128).")
    parser.add_argument("--seed", type=int, default=2026, help="Deterministic evaluation seed (default: 2026).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("iab_comparison_results"),
        help="Output directory (default: iab_comparison_results).",
    )
    parser.add_argument(
        "--fading-samples",
        type=int,
        default=12,
        help="Number of instantaneous Rayleigh-fading samples generated through the project channel API.",
    )
    parser.add_argument(
        "--candidate-chunk-size",
        type=int,
        default=64,
        help="Candidate-symbol chunk size used to bound memory (default: 64).",
    )
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING"), default="INFO")
    args = parser.parse_args(argv)
    if args.noise_samples <= 0:
        parser.error("--noise-samples must be positive.")
    if args.fading_samples <= 0:
        parser.error("--fading-samples must be positive.")
    if args.candidate_chunk_size <= 0:
        parser.error("--candidate-chunk-size must be positive.")
    return args


def detect_source(root: Path, explicit: Path | None, stem: str) -> SourceDescriptor:
    """Detect a package directory or file and record its actual kind/extension."""
    if explicit is not None:
        candidate = explicit if explicit.is_absolute() else root / explicit
        candidates = [candidate]
    else:
        candidates = [root / stem]
        candidates.extend(root / f"{stem}{suffix}" for suffix in (".py", ".npz", ".json", ".csv"))

    for candidate in candidates:
        if not candidate.exists():
            continue
        resolved = candidate.resolve()
        if resolved.is_dir() and (resolved / "__init__.py").exists():
            return SourceDescriptor(resolved, "package-directory", resolved.name)
        if resolved.suffix == ".py":
            return SourceDescriptor(resolved, "python-file", resolved.stem)
        if resolved.suffix.lower() in {".npz", ".json", ".csv"}:
            return SourceDescriptor(resolved, resolved.suffix.lower().lstrip("."), resolved.stem)
        raise ValueError(f"Unsupported source type: {resolved}")
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not detect {stem}. Searched: {searched}")


def ensure_importable_package(source: SourceDescriptor, root: Path) -> str:
    """Return a safely importable package name for the detected project layout."""
    if source.kind != "package-directory":
        raise RuntimeError(
            f"Detected {source.path} as {source.kind}, but this repository's channel and QAM APIs require "
            "a package directory. Supply the package directory containing __init__.py."
        )
    parent = str(source.path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return source.module_name


def import_project_module(package: str, suffix: str) -> Any:
    """Import one library module without importing any run/plot entry point."""
    module_name = f"{package}.{suffix}"
    LOGGER.debug("Importing library module %s", module_name)
    return importlib.import_module(module_name)


def validate_distribution(
    label: str,
    probabilities: np.ndarray,
    constellation: np.ndarray,
    va_input: float,
    detected_names: Iterable[str],
    tolerance: float = 1e-10,
) -> DistributionData:
    """Validate, center, and, only when necessary, restore the project VA convention."""
    probabilities = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    constellation = np.asarray(constellation, dtype=np.complex128).reshape(-1)
    if probabilities.size != 256 or constellation.size != 256:
        raise ValueError(
            f"{label}: expected 256 probabilities and constellation points, got "
            f"{probabilities.size} and {constellation.size}."
        )
    if not np.all(np.isfinite(probabilities)) or np.any(probabilities < 0.0):
        raise ValueError(f"{label}: probabilities must be finite and non-negative.")
    total_probability = float(probabilities.sum())
    if not math.isfinite(total_probability) or total_probability <= 0.0:
        raise ValueError(f"{label}: probability mass must be positive and finite.")
    if abs(total_probability - 1.0) > 1e-8:
        raise ValueError(f"{label}: probability sum {total_probability:.17g} is not a small rounding error.")
    probabilities = probabilities / total_probability
    if abs(float(probabilities.sum()) - 1.0) >= tolerance:
        raise ValueError(f"{label}: probability normalization failed.")
    if not np.all(np.isfinite(constellation.real)) or not np.all(np.isfinite(constellation.imag)):
        raise ValueError(f"{label}: constellation contains NaN or Inf.")

    probabilistic_mean = complex(np.sum(probabilities * constellation))
    if abs(probabilistic_mean) >= tolerance:
        LOGGER.info("%s constellation centered; original probabilistic mean=%s", label, probabilistic_mean)
        constellation = constellation - probabilistic_mean
    va_measured = float(2.0 * np.sum(probabilities * np.abs(constellation) ** 2))
    if va_measured <= 0.0 or not math.isfinite(va_measured):
        raise ValueError(f"{label}: measured modulation variance is invalid: {va_measured}")

    relative_va_error = abs(va_measured - va_input) / max(abs(va_input), 1e-15)
    if relative_va_error > 1e-6:
        LOGGER.warning(
            "%s constellation VA %.12g differs from project VA %.12g; restoring the imported VA convention.",
            label,
            va_measured,
            va_input,
        )
        constellation = constellation * math.sqrt(va_input / va_measured)
        va_measured = float(2.0 * np.sum(probabilities * np.abs(constellation) ** 2))

    positive = probabilities > 0.0
    entropy = float(-np.sum(probabilities[positive] * np.log2(probabilities[positive])))
    if not (0.0 <= entropy <= 8.0 + 1e-12):
        raise ValueError(f"{label}: entropy {entropy} is outside [0, 8].")
    return DistributionData(
        label=label,
        probabilities=probabilities,
        constellation=constellation,
        va_input=float(va_input),
        va_measured=va_measured,
        entropy_bits=entropy,
        detected_names=tuple(detected_names),
    )


def load_project_data(
    root: Path,
    model_source: SourceDescriptor,
    sample_source: SourceDescriptor,
    fading_samples: int,
    seed: int,
) -> ProjectData:
    """Read all comparison inputs through existing project APIs."""
    model_package = ensure_importable_package(model_source, root)
    sample_package = ensure_importable_package(sample_source, root)
    config = import_project_module(model_package, "config")
    sample_config = import_project_module(sample_package, "config")
    model_base = import_project_module(model_package, "zstar.base")
    sample_base = import_project_module(sample_package, "zstar.base")
    uniform_state_module = import_project_module(model_package, "zstar.uniform")
    mb_state_module = import_project_module(model_package, "zstar.mb")
    channel_module = import_project_module(model_package, "channel.channel_model")

    if int(config.QAM_M) != 256 or int(sample_config.QAM_M) != 256:
        raise ValueError("Both packages must identify the modulation as 256-QAM.")

    uniform_probabilities = np.asarray(model_base.build_probs_uniform(), dtype=np.float64)
    uniform_constellation = np.asarray(
        model_base.build_constellation(float(config.QAM_ALPHA0_UNIFORM)), dtype=np.complex128
    )
    mb_probabilities = np.asarray(model_base.build_probs_mb(float(config.QAM_NU_TILDE)), dtype=np.float64)
    mb_constellation = np.asarray(model_base.build_constellation(float(config.QAM_ALPHA0_MB)), dtype=np.complex128)

    # Read V_A from the existing state calculations rather than duplicating it.
    LOGGER.info("Reading state-derived modulation variances from %s", model_source.path)
    uniform_state = uniform_state_module.compute_state(
        float(config.QAM_ALPHA0_UNIFORM), int(config.QAM_NCUT_UNIFORM)
    )
    mb_state = mb_state_module.compute_state(
        float(config.QAM_ALPHA0_MB), int(config.QAM_NCUT_MB), float(config.QAM_NU_TILDE)
    )

    # The sample package must expose the same source constellation/PMFs.
    sample_uniform = np.asarray(sample_base.build_probs_uniform(), dtype=np.float64)
    sample_mb = np.asarray(sample_base.build_probs_mb(float(sample_config.QAM_NU_TILDE)), dtype=np.float64)
    sample_uniform_alpha = np.asarray(
        sample_base.build_constellation(float(sample_config.QAM_ALPHA0_UNIFORM)), dtype=np.complex128
    )
    sample_mb_alpha = np.asarray(
        sample_base.build_constellation(float(sample_config.QAM_ALPHA0_MB)), dtype=np.complex128
    )
    for name, left, right in (
        ("Uniform PMF", uniform_probabilities, sample_uniform),
        ("MB PMF", mb_probabilities, sample_mb),
        ("Uniform constellation", uniform_constellation, sample_uniform_alpha),
        ("MB constellation", mb_constellation, sample_mb_alpha),
    ):
        if not np.allclose(left, right, atol=1e-14, rtol=1e-14):
            raise ValueError(f"{name} differs between uav_hap_1 and uav_hap_1_sample.")

    uniform = validate_distribution(
        "Uniform",
        uniform_probabilities,
        uniform_constellation,
        float(uniform_state["va"]),
        (
            f"{model_package}.zstar.base.build_probs_uniform",
            f"{model_package}.zstar.base.build_constellation",
            f"{model_package}.zstar.uniform.compute_state()['va']",
        ),
    )
    mb = validate_distribution(
        "MB",
        mb_probabilities,
        mb_constellation,
        float(mb_state["va"]),
        (
            f"{model_package}.zstar.base.build_probs_mb",
            f"{model_package}.zstar.base.build_constellation",
            f"{model_package}.zstar.mb.compute_state()['va']",
        ),
    )

    geometry = config.GeometryParams()
    channel_params = config.ChannelParams()
    channel_result = channel_module.channel(
        geometry=geometry,
        channel_params=channel_params,
        N=fading_samples,
        rng=np.random.default_rng(seed),
    )
    t_eff = float(channel_result["T_eff"])
    t_samples = np.asarray(channel_result["T_samples"], dtype=np.float64).reshape(-1)
    if t_samples.size == 0 or not np.all(np.isfinite(t_samples)):
        raise ValueError("The channel returned no finite instantaneous transmittance samples.")

    channel_source = inspect.getsource(channel_module.channel).lower()
    if "rayleigh" not in channel_source or "T_samples" not in channel_result:
        raise RuntimeError(
            "Rayleigh/Reyleigh data was not found. Check whether the intended distribution is Binomial."
        )
    rayleigh_interpretation = (
        "Rayleigh is a fading/channel distribution: channel.channel() samples radial displacement with "
        "numpy.random.Generator.rayleigh and maps it to instantaneous T_samples. No Rayleigh/Reyleigh "
        "256-QAM symbol PMF exists. Because the channel API is modulation-independent and is used for all "
        "project distributions, the dedicated Rayleigh panel uses the existing Uniform 256-QAM PMF and "
        "labels that choice explicitly; Binomial is not substituted."
    )

    sample_gaussian_iab = getattr(sample_base, "gaussian_iab_reference", None)
    if sample_gaussian_iab is None:
        sample_gaussian_iab = lambda t, va, eps: sample_base.compute_IAB(va, t, eps)

    source_files = (
        model_source.path,
        sample_source.path,
        model_source.path / "config.py",
        model_source.path / "zstar" / "base.py",
        model_source.path / "zstar" / "uniform.py",
        model_source.path / "zstar" / "mb.py",
        model_source.path / "channel" / "channel_model.py",
        sample_source.path / "zstar" / "base.py",
        sample_source.path / "iab" / "discrete.py",
    )
    metadata = {
        "visibility_km": float(channel_params.visibility_km),
        "beam_waist_m": float(channel_params.W0_m),
        "aperture_radius_m": float(channel_result["aperture_radius_m"]),
        "Cn2": float(channel_params.Cn2),
    }
    return ProjectData(
        uniform=uniform,
        mb=mb,
        t_eff=t_eff,
        t_samples=t_samples,
        excess_noise=float(config.QAM_EPS),
        metadata=metadata,
        rayleigh_interpretation=rayleigh_interpretation,
        source_files=source_files,
        model_compute_iab=model_base.compute_IAB,
        sample_gaussian_iab=sample_gaussian_iab,
    )


def gaussian_iab_reference(transmittance: np.ndarray | float, va: float, epsilon: float) -> np.ndarray:
    """Evaluate the mandatory legacy Gaussian-input expression."""
    transmittance = np.asarray(transmittance, dtype=np.float64)
    return np.log2(1.0 + transmittance * va / (2.0 + transmittance * epsilon))


def discrete_mi_mismatched_awgn(
    probabilities: np.ndarray,
    constellation: np.ndarray,
    transmittance: np.ndarray | float,
    excess_noise: np.ndarray | float,
    noise_samples_per_symbol: int = 128,
    seed: int = 2026,
    antithetic: bool = True,
    candidate_chunk_size: int | None = None,
) -> np.ndarray:
    """Return one mismatched-decoding discrete MI estimate per T sample.

    All transmitted symbols are enumerated and probability weighted. Only the
    complex AWGN is sampled. One standardized noise tensor is reused across all
    T values; calls with the same seed therefore provide common random numbers
    across Uniform, MB, and Rayleigh-fading comparisons.
    """
    probabilities_np = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    constellation_np = np.asarray(constellation, dtype=np.complex128).reshape(-1)
    t_np = np.asarray(transmittance, dtype=np.float64).reshape(-1)
    epsilon_np = np.asarray(excess_noise, dtype=np.float64)
    if probabilities_np.size != constellation_np.size or probabilities_np.size != 256:
        raise ValueError("probabilities and constellation must both contain 256 entries.")
    if noise_samples_per_symbol <= 0:
        raise ValueError("noise_samples_per_symbol must be positive.")
    if np.any(t_np < 0.0) or not np.all(np.isfinite(t_np)):
        raise ValueError("transmittance must be finite and non-negative.")
    if epsilon_np.ndim == 0:
        epsilon_np = np.full_like(t_np, float(epsilon_np))
    else:
        epsilon_np = epsilon_np.reshape(-1)
        if epsilon_np.size != t_np.size:
            raise ValueError("excess_noise must be scalar or match transmittance.")
    if np.any(epsilon_np < 0.0) or not np.all(np.isfinite(epsilon_np)):
        raise ValueError("excess_noise must be finite and non-negative.")

    probs = torch.as_tensor(probabilities_np, dtype=torch.float64)
    alpha = torch.as_tensor(constellation_np, dtype=torch.complex128)
    log_probs = torch.log(probs.clamp_min(1e-300))
    entropy_bits = -(probs * (log_probs / math.log(2.0))).sum()
    symbol_count = int(probs.numel())
    chunk_size = symbol_count if candidate_chunk_size is None else int(candidate_chunk_size)
    if chunk_size <= 0:
        raise ValueError("candidate_chunk_size must be positive when provided.")

    generator = torch.Generator(device="cpu").manual_seed(int(seed))
    independent_count = (noise_samples_per_symbol + 1) // 2 if antithetic else noise_samples_per_symbol
    noise_shape = (symbol_count, independent_count)
    standard_real = torch.randn(noise_shape, dtype=torch.float64, generator=generator)
    standard_imag = torch.randn(noise_shape, dtype=torch.float64, generator=generator)
    standard_noise = torch.complex(standard_real, standard_imag)
    if antithetic:
        standard_noise = torch.cat((standard_noise, -standard_noise), dim=1)[:, :noise_samples_per_symbol]

    results: list[torch.Tensor] = []
    with torch.no_grad():
        for t_value, epsilon_value in zip(t_np, epsilon_np, strict=True):
            t_tensor = torch.tensor(float(t_value), dtype=torch.float64)
            sigma2 = 1.0 + t_tensor * float(epsilon_value) / 2.0
            means = torch.sqrt(t_tensor) * alpha
            noise = standard_noise * torch.sqrt(sigma2 / 2.0)
            received = means[:, None] + noise

            log_denominator: torch.Tensor | None = None
            for start in range(0, symbol_count, chunk_size):
                stop = min(start + chunk_size, symbol_count)
                distances = (received[:, :, None] - means[None, None, start:stop]).abs().square()
                candidate_logits = log_probs[None, None, start:stop] - distances / sigma2
                chunk_logsumexp = torch.logsumexp(candidate_logits, dim=-1)
                log_denominator = (
                    chunk_logsumexp
                    if log_denominator is None
                    else torch.logaddexp(log_denominator, chunk_logsumexp)
                )

            true_distances = (received - means[:, None]).abs().square()
            true_logits = log_probs[:, None] - true_distances / sigma2
            correct_log_posterior = true_logits - log_denominator
            conditional_term = torch.sum(
                probs * torch.mean(correct_log_posterior, dim=1) / math.log(2.0)
            )
            results.append(entropy_bits + conditional_term)
    return torch.stack(results).cpu().numpy().astype(np.float64, copy=False)


def make_detailed_rows(
    distribution: DistributionData,
    transmittances: np.ndarray,
    scenario: str,
    epsilon: float,
    metadata: dict[str, float],
    noise_samples: int,
    seed: int,
    candidate_chunk_size: int,
) -> list[dict[str, Any]]:
    """Evaluate both MI methods and construct detailed output rows."""
    transmittances = np.asarray(transmittances, dtype=np.float64).reshape(-1)
    gaussian = gaussian_iab_reference(transmittances, distribution.va_input, epsilon)
    discrete = discrete_mi_mismatched_awgn(
        probabilities=distribution.probabilities,
        constellation=distribution.constellation,
        transmittance=transmittances,
        excess_noise=epsilon,
        noise_samples_per_symbol=noise_samples,
        seed=seed,
        antithetic=True,
        candidate_chunk_size=candidate_chunk_size,
    )
    snr = transmittances * distribution.va_input / (2.0 + transmittances * epsilon)
    rows: list[dict[str, Any]] = []
    for index, (t_value, snr_value, old_mi, new_mi) in enumerate(
        zip(transmittances, snr, gaussian, discrete, strict=True)
    ):
        signed_difference = float(new_mi - old_mi)
        absolute_difference = abs(signed_difference)
        rows.append(
            {
                "distribution": distribution.label,
                "symbol_distribution": distribution.label,
                "scenario": scenario,
                "sample_index": index,
                "T": float(t_value),
                "V_A_input": distribution.va_input,
                "V_A_measured": distribution.va_measured,
                "epsilon": float(epsilon),
                "SNR": float(snr_value),
                "H_X": distribution.entropy_bits,
                "I_AB_gaussian": float(old_mi),
                "I_AB_discrete_raw": float(new_mi),
                "I_AB_discrete_reported": max(float(new_mi), 0.0),
                "absolute_difference": absolute_difference,
                "signed_difference": signed_difference,
                "relative_difference_percent": 100.0 * absolute_difference / max(abs(float(old_mi)), 1e-12),
                **metadata,
            }
        )
    return rows


def add_rayleigh_rows(uniform_fading_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Relabel Uniform-symbol fading rows as the requested Rayleigh channel case."""
    rows: list[dict[str, Any]] = []
    for row in uniform_fading_rows:
        rayleigh_row = dict(row)
        rayleigh_row["distribution"] = RAYLEIGH_LABEL
        rayleigh_row["symbol_distribution"] = "Uniform"
        rayleigh_row["scenario"] = "instantaneous Rayleigh fading"
        rows.append(rayleigh_row)
    return rows


def finite_correlation(left: np.ndarray, right: np.ndarray) -> float:
    """Return a finite correlation value, including for one-point summaries."""
    if left.size < 2 or np.std(left) == 0.0 or np.std(right) == 0.0:
        return 1.0 if np.allclose(left, right, atol=1e-12, rtol=1e-12) else 0.0
    return float(np.corrcoef(left, right)[0, 1])


def summarize_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute all requested summary statistics by distribution and scenario."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["distribution"]), str(row["symbol_distribution"]), str(row["scenario"]))
        grouped.setdefault(key, []).append(row)

    summaries: list[dict[str, Any]] = []
    for (distribution, symbol_distribution, scenario), group in grouped.items():
        t_values = np.asarray([row["T"] for row in group], dtype=np.float64)
        snr = np.asarray([row["SNR"] for row in group], dtype=np.float64)
        old = np.asarray([row["I_AB_gaussian"] for row in group], dtype=np.float64)
        new = np.asarray([row["I_AB_discrete_raw"] for row in group], dtype=np.float64)
        entropy = np.asarray([row["H_X"] for row in group], dtype=np.float64)
        difference = new - old
        absolute = np.abs(difference)
        relative = 100.0 * absolute / np.maximum(np.abs(old), 1e-12)
        bound_ok = (new >= -1e-10) & (new <= entropy + 1e-10)
        summaries.append(
            {
                "distribution": distribution,
                "symbol_distribution": symbol_distribution,
                "scenario": scenario,
                "number_of_samples": int(len(group)),
                "mean_T": float(np.mean(t_values)),
                "mean_SNR": float(np.mean(snr)),
                "H_X": float(entropy[0]),
                "mean_I_AB_gaussian": float(np.mean(old)),
                "std_I_AB_gaussian": float(np.std(old, ddof=0)),
                "mean_I_AB_discrete": float(np.mean(new)),
                "std_I_AB_discrete": float(np.std(new, ddof=0)),
                "mean_absolute_difference": float(np.mean(absolute)),
                "maximum_absolute_difference": float(np.max(absolute)),
                "RMSE": float(np.sqrt(np.mean(difference**2))),
                "mean_relative_difference_percent": float(np.mean(relative)),
                "correlation_coefficient": finite_correlation(old, new),
                "percent_discrete_le_gaussian": float(100.0 * np.mean(new <= old + 1e-10)),
                "percent_satisfying_mi_bounds": float(100.0 * np.mean(bound_ok)),
            }
        )
    return summaries


def run_internal_checks(
    data: ProjectData,
    detailed_rows: Sequence[dict[str, Any]],
    seed: int,
    candidate_chunk_size: int,
) -> list[str]:
    """Run required numerical and regression diagnostics before output is saved."""
    messages: list[str] = []
    for distribution in (data.uniform, data.mb):
        probability_sum = float(distribution.probabilities.sum())
        if abs(probability_sum - 1.0) >= 1e-10:
            raise AssertionError(f"{distribution.label}: probability normalization check failed.")
        if not (0.0 <= distribution.entropy_bits <= 8.0 + 1e-12):
            raise AssertionError(f"{distribution.label}: entropy check failed.")

        zero_mi = discrete_mi_mismatched_awgn(
            distribution.probabilities,
            distribution.constellation,
            0.0,
            data.excess_noise,
            noise_samples_per_symbol=8,
            seed=seed,
            candidate_chunk_size=candidate_chunk_size,
        )[0]
        if abs(float(zero_mi)) > 1e-11:
            raise AssertionError(f"{distribution.label}: zero-transmittance MI is {zero_mi}.")

        diagnostic_alpha = distribution.constellation * math.sqrt(1e6 / distribution.va_measured)
        high_snr_mi = discrete_mi_mismatched_awgn(
            distribution.probabilities,
            diagnostic_alpha,
            1.0,
            0.0,
            noise_samples_per_symbol=8,
            seed=seed,
            candidate_chunk_size=candidate_chunk_size,
        )[0]
        if abs(float(high_snr_mi) - distribution.entropy_bits) > 1e-8:
            raise AssertionError(
                f"{distribution.label}: high-SNR MI {high_snr_mi} does not approach H(X)={distribution.entropy_bits}."
            )

        reproducibility_t = np.asarray([data.t_eff], dtype=np.float64)
        first = discrete_mi_mismatched_awgn(
            distribution.probabilities,
            distribution.constellation,
            reproducibility_t,
            data.excess_noise,
            noise_samples_per_symbol=8,
            seed=seed,
            candidate_chunk_size=candidate_chunk_size,
        )
        second = discrete_mi_mismatched_awgn(
            distribution.probabilities,
            distribution.constellation,
            reproducibility_t,
            data.excess_noise,
            noise_samples_per_symbol=8,
            seed=seed,
            candidate_chunk_size=candidate_chunk_size,
        )
        if not np.array_equal(first, second):
            raise AssertionError(f"{distribution.label}: fixed-seed reproducibility check failed.")

    legacy_expected = float(gaussian_iab_reference(data.t_eff, data.uniform.va_input, data.excess_noise))
    legacy_model = float(data.model_compute_iab(data.uniform.va_input, data.t_eff, data.excess_noise))
    legacy_sample = float(data.sample_gaussian_iab(data.t_eff, data.uniform.va_input, data.excess_noise))
    if legacy_model != legacy_expected or legacy_sample != legacy_expected:
        raise AssertionError(
            "Legacy formula regression failed: comparison, uav_hap_1, and uav_hap_1_sample do not agree."
        )

    numeric_fields = [field for field in DETAIL_FIELDS if field not in {
        "distribution", "symbol_distribution", "scenario"
    }]
    for row in detailed_rows:
        for field in numeric_fields:
            if not math.isfinite(float(row[field])):
                raise AssertionError(f"Non-finite detailed value: {field}={row[field]}")
        if float(row["I_AB_discrete_raw"]) > float(row["H_X"]) + 1e-10:
            raise AssertionError(f"Discrete MI exceeds entropy in row {row}")

    messages.extend(
        (
            "Probability normalization and entropy checks passed.",
            "Discrete-MI entropy upper bounds passed for every result row.",
            "Near-zero channel and high-SNR diagnostics passed for Uniform and MB.",
            "Legacy Gaussian formula matches both project packages to machine precision.",
            "Fixed-seed reproducibility and finite-value checks passed.",
        )
    )
    return messages


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    """Write dictionaries using a stable column order."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_plot(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    """Create three distribution rows with MI and signed-difference panels."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    distributions = ("Uniform", "MB", RAYLEIGH_LABEL)
    figure, axes = plt.subplots(3, 2, figsize=(14, 13), constrained_layout=True)
    for row_index, distribution in enumerate(distributions):
        distribution_rows = [row for row in rows if row["distribution"] == distribution]
        scenarios = sorted({str(row["scenario"]) for row in distribution_rows})
        mi_axis = axes[row_index, 0]
        difference_axis = axes[row_index, 1]
        for scenario_index, scenario in enumerate(scenarios):
            scenario_rows = sorted(
                (row for row in distribution_rows if row["scenario"] == scenario),
                key=lambda row: float(row["SNR"]),
            )
            x_values = np.asarray([row["SNR"] for row in scenario_rows], dtype=np.float64)
            old = np.asarray([row["I_AB_gaussian"] for row in scenario_rows], dtype=np.float64)
            new = np.asarray([row["I_AB_discrete_raw"] for row in scenario_rows], dtype=np.float64)
            color = f"C{scenario_index}"
            mi_axis.scatter(
                x_values,
                old,
                marker="o",
                facecolors="none",
                edgecolors=color,
                label=f"Gaussian reference - {scenario}",
            )
            mi_axis.scatter(
                x_values,
                new,
                marker="x",
                color=color,
                label=f"Discrete mismatched - {scenario}",
            )
            difference_axis.scatter(x_values, new - old, marker="o", color=color, label=scenario)

        entropy = float(distribution_rows[0]["H_X"])
        mi_axis.text(
            0.02,
            0.96,
            f"H(X)={entropy:.4f} bits/symbol",
            transform=mi_axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            color="0.35",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "0.8",
                "alpha": 0.85,
            },
        )
        difference_axis.axhline(0.0, color="0.3", linewidth=1.0)
        mi_axis.set_title(distribution)
        difference_axis.set_title(f"{distribution}: discrete - Gaussian")
        mi_axis.set_xlabel("SNR (linear)")
        difference_axis.set_xlabel("SNR (linear)")
        mi_axis.set_ylabel("I_AB (bits/symbol)")
        difference_axis.set_ylabel("Signed difference (bits/symbol)")
        mi_axis.grid(alpha=0.3)
        difference_axis.grid(alpha=0.3)
        mi_axis.legend(fontsize=8)
        difference_axis.legend(fontsize=8)

    figure.suptitle("UAV-HAP 256-QAM: Gaussian-reference vs discrete-input I_AB", fontsize=14)
    figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def format_terminal_summary(summaries: Sequence[dict[str, Any]]) -> str:
    """Format concise distribution/scenario summary rows."""
    header = (
        f"{'Distribution / scenario':<58} {'H(X)':>8} "
        f"{'Mean old MI':>13} {'Mean new MI':>13} {'Mean abs diff':>14}"
    )
    lines = [header, "-" * len(header)]
    for row in summaries:
        label = f"{row['distribution']} - {row['scenario']}"
        lines.append(
            f"{label:<58} {row['H_X']:>8.4f} "
            f"{row['mean_I_AB_gaussian']:>13.6f} {row['mean_I_AB_discrete']:>13.6f} "
            f"{row['mean_absolute_difference']:>14.6f}"
        )
    return "\n".join(lines)


def write_report(
    path: Path,
    model_source: SourceDescriptor,
    sample_source: SourceDescriptor,
    data: ProjectData,
    summaries: Sequence[dict[str, Any]],
    validation_messages: Sequence[str],
    noise_samples: int,
    seed: int,
) -> None:
    """Write source mappings, interpretation, validation, results, and limitations."""
    source_lines = "\n".join(f"  - {source.resolve()}" for source in data.source_files)
    mapping_lines = "\n".join(
        f"  - {distribution.label}: " + ", ".join(distribution.detected_names)
        for distribution in (data.uniform, data.mb)
    )
    checks = "\n".join(f"  - {message}" for message in validation_messages)
    report = f"""UAV-HAP 256-QAM I_AB comparison report
=========================================

Detected inputs
---------------
Model source:  {model_source.path.resolve()} ({model_source.kind})
Sample source: {sample_source.path.resolve()} ({sample_source.kind})

Files and package resources read:
{source_lines}

Detected variable/function mappings:
{mapping_lines}
  - T_eff and T_samples: {model_source.module_name}.channel.channel_model.channel
  - epsilon: {model_source.module_name}.config.QAM_EPS

Evaluation settings
-------------------
Noise samples per symbol: {noise_samples}
Seed: {seed}
Complex noise variance: sigma_c^2 = 1 + T * epsilon / 2
Fading convention: mean_b I(T_b), not I(mean_b T_b)

Rayleigh/Reyleigh interpretation
--------------------------------
{data.rayleigh_interpretation}

Validation
----------
{checks}

Summary
-------
{format_terminal_summary(summaries)}

Why the methods differ
----------------------
The Gaussian expression is a Gaussian-input reference with no finite-alphabet
entropy ceiling. The mismatched-decoding estimator evaluates the actual 256-QAM
constellation and PMF, so it depends on the symbol distribution and saturates at
H(X) <= 8 bits/symbol. Monte Carlo AWGN integration adds small finite-sample
variation; no correction factor, offset, fitted scaling, or equality-forcing
clipping is applied. Only very small negative estimates are clipped to zero in
the reported column, while the raw estimate is preserved.
"""
    path.write_text(report, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Load project data, compare methods, validate results, and save outputs."""
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )
    root = Path(__file__).resolve().parent
    model_source = detect_source(root, args.model_file, "uav_hap_1")
    sample_source = detect_source(root, args.sample_file, "uav_hap_1_sample")
    LOGGER.info("Detected model source: %s (%s)", model_source.path, model_source.kind)
    LOGGER.info("Detected sample source: %s (%s)", sample_source.path, sample_source.kind)

    data = load_project_data(
        root=root,
        model_source=model_source,
        sample_source=sample_source,
        fading_samples=args.fading_samples,
        seed=args.seed,
    )
    LOGGER.info("Rayleigh interpretation: %s", data.rayleigh_interpretation)

    detailed_rows: list[dict[str, Any]] = []
    LOGGER.info("Evaluating Uniform T_eff and instantaneous fading samples")
    uniform_effective = make_detailed_rows(
        data.uniform,
        np.asarray([data.t_eff]),
        "T_eff",
        data.excess_noise,
        data.metadata,
        args.noise_samples,
        args.seed,
        args.candidate_chunk_size,
    )
    uniform_fading = make_detailed_rows(
        data.uniform,
        data.t_samples,
        "instantaneous fading",
        data.excess_noise,
        data.metadata,
        args.noise_samples,
        args.seed,
        args.candidate_chunk_size,
    )
    detailed_rows.extend(uniform_effective)
    detailed_rows.extend(uniform_fading)

    LOGGER.info("Evaluating MB T_eff and instantaneous fading samples")
    detailed_rows.extend(
        make_detailed_rows(
            data.mb,
            np.asarray([data.t_eff]),
            "T_eff",
            data.excess_noise,
            data.metadata,
            args.noise_samples,
            args.seed,
            args.candidate_chunk_size,
        )
    )
    detailed_rows.extend(
        make_detailed_rows(
            data.mb,
            data.t_samples,
            "instantaneous fading",
            data.excess_noise,
            data.metadata,
            args.noise_samples,
            args.seed,
            args.candidate_chunk_size,
        )
    )
    detailed_rows.extend(add_rayleigh_rows(uniform_fading))

    validation_messages = run_internal_checks(
        data=data,
        detailed_rows=detailed_rows,
        seed=args.seed,
        candidate_chunk_size=args.candidate_chunk_size,
    )
    summaries = summarize_rows(detailed_rows)
    for summary in summaries:
        for field in SUMMARY_FIELDS:
            if field in {"distribution", "symbol_distribution", "scenario"}:
                continue
            if not math.isfinite(float(summary[field])):
                raise AssertionError(f"Non-finite summary value: {field}={summary[field]}")

    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    detailed_path = (output_dir / "iab_comparison_detailed.csv").resolve()
    summary_path = (output_dir / "iab_comparison_summary.csv").resolve()
    plot_path = (output_dir / "iab_comparison.png").resolve()
    report_path = (output_dir / "iab_comparison_report.txt").resolve()

    write_csv(detailed_path, detailed_rows, DETAIL_FIELDS)
    write_csv(summary_path, summaries, SUMMARY_FIELDS)
    create_plot(plot_path, detailed_rows)
    write_report(
        report_path,
        model_source,
        sample_source,
        data,
        summaries,
        validation_messages,
        args.noise_samples,
        args.seed,
    )

    print(format_terminal_summary(summaries))
    print("\nGenerated files:")
    for path in (detailed_path, summary_path, plot_path, report_path):
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
