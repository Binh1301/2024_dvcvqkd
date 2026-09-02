"""Production-to-isolated-FLINT point-certifier adapter."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from src.modulation.joint_ps_gs import Ensemble
from .pointwise_guard import PointwiseProvenanceError, PointwiseGuardConfig, validate_provenance_bindings


class RealPointCertifierAdapter:
    """Call the pinned `.venv-cert` worker using canonical JSON only."""

    def __init__(
        self, root: Path, *, worker: Path, certification_python: Path,
        expected_provenance: Mapping[str, str], actual_provenance: Mapping[str, str],
        timeout_seconds: float = 600.0,
    ) -> None:
        self.root = Path(root).resolve()
        self.worker = Path(worker).resolve()
        self.certification_python = Path(certification_python).resolve()
        self.expected_provenance = dict(expected_provenance)
        self.actual_provenance = dict(actual_provenance)
        self.timeout_seconds = float(timeout_seconds)
        if not self.certification_python.is_file() or not self.worker.is_file():
            raise FileNotFoundError("Pinned certification Python or worker is missing.")
        if self.timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be positive.")

    @staticmethod
    def _float_hex(value: float) -> str:
        return float(value).hex()

    @classmethod
    def _request(cls, ensemble: Ensemble, row: int, config: PointwiseGuardConfig) -> dict[str, Any]:
        ensemble.validate()
        probabilities = ensemble.probabilities[row].detach().cpu().tolist()
        amplitudes = ensemble.amplitudes[row].detach().cpu().tolist()
        return {
            "probabilities_float64_hex": [cls._float_hex(value) for value in probabilities],
            "amplitudes_float64_hex": [[cls._float_hex(complex(value).real), cls._float_hex(complex(value).imag)] for value in amplitudes],
            "tau_float64_hex": config.tau_float64_hex,
            "precision_bits": [160, 256, 384, 512],
            "bracket_denominator_power_two": 48,
            "maximum_bracket_expansions": 8,
            "maximum_seconds_per_inertia": 120.0,
            "protocol_version": config.protocol_version,
        }

    def __call__(self, ensemble: Ensemble, row: int, config: PointwiseGuardConfig) -> Mapping[str, Any]:
        valid, mismatches = validate_provenance_bindings(self.expected_provenance, self.actual_provenance)
        if not valid:
            raise PointwiseProvenanceError("; ".join(mismatches))
        request = json.dumps(self._request(ensemble, row, config), sort_keys=True, separators=(",", ":"))
        try:
            completed = subprocess.run(
                [str(self.certification_python), str(self.worker)],
                input=request,
                text=True,
                capture_output=True,
                cwd=self.root,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return {"status": "UNCERTIFIED_POINT", "reason": f"certifier timeout: {error}"}
        if completed.returncode != 0:
            return {"status": "UNCERTIFIED_POINT", "reason": completed.stderr[-2000:] or f"worker exit {completed.returncode}"}
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            return {"status": "UNCERTIFIED_POINT", "reason": f"worker JSON parse failure: {error}"}
        if not isinstance(result, dict):
            return {"status": "UNCERTIFIED_POINT", "reason": "worker result is not an object"}
        return result
