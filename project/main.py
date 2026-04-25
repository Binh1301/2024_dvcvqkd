import matplotlib

if __package__ in (None, ""):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from project.config import (
        CALC_LOG_XLSX,
        CHI_HET,
        CHI_HOM,
        EPS_CH,
        MATPLOTLIB_BACKEND,
        VA_GM,
        VA_PSK,
        VA_QAM,
    )

    matplotlib.use(MATPLOTLIB_BACKEND)

    from project.channel.channel_model import total_transmittance
    from project.plots.fig4 import plot_fig4
    from project.plots.fig5 import plot_fig5
    from project.plots.fig6 import plot_fig6
    from project.plots.fig7 import plot_fig7
    from project.plots.fig8 import plot_fig8
    from project.protocols.gm import skr_gm
    from project.protocols.psk import skr_psk
    from project.protocols.qam import skr_qam
    from project.reconciliation.finite_size import finite_size_skr
    from project.utils.logger import clear_calc_log, export_calc_log_to_excel
else:
    from .config import (
        CALC_LOG_XLSX,
        CHI_HET,
        CHI_HOM,
        EPS_CH,
        MATPLOTLIB_BACKEND,
        VA_GM,
        VA_PSK,
        VA_QAM,
    )

    matplotlib.use(MATPLOTLIB_BACKEND)

    from .channel.channel_model import total_transmittance
    from .plots.fig4 import plot_fig4
    from .plots.fig5 import plot_fig5
    from .plots.fig6 import plot_fig6
    from .plots.fig7 import plot_fig7
    from .plots.fig8 import plot_fig8
    from .protocols.gm import skr_gm
    from .protocols.psk import skr_psk
    from .protocols.qam import skr_qam
    from .reconciliation.finite_size import finite_size_skr
    from .utils.logger import clear_calc_log, export_calc_log_to_excel


def main():
    clear_calc_log()
    print("=" * 68)
    print("CV-QKD Satellite-to-Ground Simulation")
    print("Sayat et al., IEEE Trans. Commun. 2024  |  Reproducing Figs 4-8")
    print("=" * 68)
    print(f"\nEPS_CH={EPS_CH:.4f} SNU  |  CHI_HOM={CHI_HOM:.4f}  CHI_HET={CHI_HET:.4f}")

    # Quick sanity check
    T, L, ok = total_transmittance(90, 400e3, 1.0, 200, 1e-16)
    print(f"\nSanity | θ=90°, H=400km, Dr=1m, good atm:")
    print(f"  T={T:.5f}, L={L/1e3:.1f} km, far-field={ok}")
    print(f"  SKR_GM(asy) = {skr_gm(VA_GM, T, EPS_CH, 0.9):.4f} bits/pulse")
    print(f"  SKR_8PSK    = {skr_psk(VA_PSK, T, EPS_CH, 8, 0.9):.4f} bits/pulse")
    print(f"  SKR_64QAM   = {skr_qam(VA_QAM, T, EPS_CH, 64, 0.9):.4f} bits/pulse")
    print(f"  SKR_fin(MD) = {finite_size_skr(VA_GM, T, EPS_CH, 'MD')/1e6:.2f} Mbit/s")
    print()

    plot_fig4()
    plot_fig5()
    plot_fig6()
    plot_fig7()
    plot_fig8()

    print("\n" + "=" * 68)
    print("All 5 figures reproduced successfully!")
    try:
        export_calc_log_to_excel(CALC_LOG_XLSX)
    except ModuleNotFoundError as exc:
        print(f"  ! {exc}")
    print("=" * 68)


if __name__ == "__main__":
    main()
