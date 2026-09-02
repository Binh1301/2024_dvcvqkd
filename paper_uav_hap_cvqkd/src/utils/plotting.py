"""Plotting is intentionally downstream of saved raw numerical data."""

from __future__ import annotations


def require_raw_data_path(raw_data_path) -> None:
    if raw_data_path is None:
        raise ValueError("Every figure must name its saved raw-data source.")

