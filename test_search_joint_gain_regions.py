from pathlib import Path

import numpy as np

import search_joint_gain_regions as search


def test_matched_mean_fading_is_bounded_and_close_to_target():
    rng = np.random.default_rng(123)
    for kind in (
        "deterministic",
        "beta_low_variance",
        "beta_medium_variance",
        "beta_high_variance",
        "deep_fade_mixture",
        "lognormal_heavy_tail",
    ):
        values = search.matched_mean_fading(kind, 0.01, 10000, rng)
        assert np.all(values > 0.0)
        assert np.all(values <= 1.0)
        assert abs(float(values.mean()) - 0.01) < 0.002


def test_snr_increases_with_transmittance():
    low = search.Point(1e-5, 0.01)
    high = search.Point(1e-2, 0.01)
    assert high.snr_db > low.snr_db


def test_quick_config_reduces_grid():
    config = search.load_config(
        Path("near_threshold_search_config.json"), quick=True, output_override=None
    )
    assert config["coarse"]["T_points"] == 7
    assert config["confirmation"]["repetitions"] == 2
