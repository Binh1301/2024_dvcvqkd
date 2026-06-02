from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(repo_root)
    sys.path.insert(0, repo_root)

from uav_hap_1.visualization.skr_vs_visibility_fso import plot_skr_vs_visibility


def main() -> None:
    out_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "output"
    out_path = plot_skr_vs_visibility(out_dir=out_dir)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

