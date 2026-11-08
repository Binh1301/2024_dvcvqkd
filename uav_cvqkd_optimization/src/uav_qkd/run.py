"""CLI: python -m uav_qkd.run --config configs/demo.yaml --output results/demo."""
import argparse
from pathlib import Path
from .config import load_config
from .experiments import run_experiment


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', default='results/demo')
    parser.add_argument('--skip-figures', action='store_true')
    parser.add_argument('--skip-sensitivities', action='store_true')
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error('Output directory is not empty. Choose a new output path to preserve previous results.')
    try:
        report = run_experiment(load_config(args.config), output,
                                figures=not args.skip_figures, sensitivities=not args.skip_sensitivities)
    except (ValueError, KeyError, TypeError, FileNotFoundError) as e:
        parser.exit(2, f'Input/experiment error: {e}\n')
    print(report['data_status'])
    print(f'Results: {output.resolve()}')
    for run in report['runs']:
        print(run['method'], {obj: dict(K=s['K'], value=s['objective_value']) for obj, s in run['solutions'].items()})


if __name__ == '__main__':
    main()
