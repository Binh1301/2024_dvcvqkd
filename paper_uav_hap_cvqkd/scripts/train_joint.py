"""Train joint PS+GS; adaptive-V_A modes require explicit bounds."""

import argparse
import sys

from _train import run_training


if __name__ == "__main__":
    mode_parser = argparse.ArgumentParser(add_help=False)
    mode_parser.add_argument(
        "--mode", choices=("va", "ps_gs", "ps_va", "gs_va", "full"), default="ps_gs"
    )
    known, remaining = mode_parser.parse_known_args()
    sys.argv = [sys.argv[0], *remaining]
    raise SystemExit(run_training(known.mode))
