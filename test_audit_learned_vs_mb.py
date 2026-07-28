import numpy as np
import torch

import audit_learned_vs_mb as audit
import uav_hap_joint_ps_gs as core


def test_mb_grid_contains_project_fixed_parameter():
    config = audit.load_config(
        audit.Path("learned_vs_mb_audit_config.json"), quick=True, output_override=None
    )
    assert np.any(np.isclose(config["nu_grid"], config["mb_fixed_nu"]))


def test_arbitrary_mb_output_is_centered_and_energy_normalized():
    device = torch.device("cpu")
    base_qam = core.build_project_qam(device)
    transmittance = torch.tensor([0.01, 0.1], dtype=core.REAL_DTYPE)
    output = audit.fixed_probability_output(
        audit.mb_probabilities(0.13, device),
        transmittance,
        base_qam,
        target_va=2.0,
    )
    mean = torch.sum(output.probabilities * output.constellation, dim=-1)
    va = 2.0 * torch.sum(
        output.probabilities * output.constellation.abs().square(), dim=-1
    )
    assert torch.allclose(mean, torch.zeros_like(mean), atol=1e-12, rtol=0.0)
    assert torch.allclose(va, torch.full_like(va, 2.0), atol=1e-12, rtol=0.0)


def test_gain_source_categories():
    assert audit.gain_source(1e-3, 0.0) == "MI-driven"
    assert audit.gain_source(0.0, -1e-3) == "Security-driven"
    assert audit.gain_source(1e-3, -1e-3) == "Joint improvement"
    assert audit.gain_source(-1e-3, -2e-3) == "Trade-off"
