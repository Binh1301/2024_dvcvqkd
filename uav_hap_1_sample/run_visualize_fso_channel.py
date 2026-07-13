from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(repo_root)
    sys.path.insert(0, repo_root)

from uav_hap_1_sample.visualization.fso_channel_illustration import generate_fso_channel_figure


def main() -> None:
    out_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "output"
    out_path = generate_fso_channel_figure(out_dir=out_dir)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

