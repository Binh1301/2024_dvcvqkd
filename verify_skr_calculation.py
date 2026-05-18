#!/usr/bin/env python3
"""
Reference verification at L=20 km, Cn2=1e-15, VA=2.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from uav_hap.plots.skr_gaussian_uav_hap import debug_reference_case


if __name__ == "__main__":
    print("=" * 72)
    print("DEBUG CHECKLIST (REFERENCE POINT)")
    print("=" * 72)
    vals = debug_reference_case(seed=42, n_samples=30_000)
    print("=" * 72)
    print(f"SKR_raw = {vals['SKR_raw']:.6f} bits/pulse")
    print(f"SKR     = {vals['SKR']:.6f} bits/pulse")
    print("=" * 72)
