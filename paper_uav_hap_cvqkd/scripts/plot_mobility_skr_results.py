"""Standalone vector PDF and 300-dpi PNG for saved mobility diagnostics."""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

COLORS = ("#2563eb", "#f28e2b", "#d62728", "#7c3aed")
NAMES = ("S1 Reference fixed", "S2 Stationary", "S3 Moving, lambda=0", "S4 Mobility-aware")


def read_csv(path):
    with Path(path).open(encoding="utf-8",newline="") as stream:
        return list(csv.DictReader(stream))


def plot_results(output, settings):
    output = Path(output)
    rows = read_csv(output/"scheme_time_series.csv")
    schemes = list(dict.fromkeys(r["scheme"] for r in rows))
    series = [[r for r in rows if r["scheme"]==scheme] for scheme in schemes]
    positions = read_csv(output/"positions.csv")
    velocity = read_csv(output/"cloud_velocity_sweep.csv")
    penalty = read_csv(output/"movement_penalty_sweep.csv")
    plt.rcParams.update({"pdf.use14corefonts":True,"font.size":10,"axes.labelsize":11})

    def finish(fig, name):
        fig.text(.5,.012,"Synthetic cloud scenario; effective Gaussian SKR ignores fading-induced variance.",
                 ha="center",fontsize=8)
        fig.tight_layout(rect=(0,.035,1,1))
        fig.savefig(output/(name+".png"),dpi=300,facecolor="white")
        fig.savefig(output/(name+".pdf"),facecolor="white")
        plt.close(fig)

    def decorate(ax):
        ax.grid(alpha=.25)
        ax.ticklabel_format(axis="y",style="sci",scilimits=(-2,2),useMathText=True)

    fig, axes = plt.subplots(1,2,figsize=(11,5.2))
    ax, plane = axes
    ax.scatter([float(r["x_m"]) for r in positions],[float(r["y_m"]) for r in positions],
               s=12,c="0.75",label="100 UAV cell centers")
    for i in (2,3):
        x=[float(r["x_m"]) for r in series[i]];y=[float(r["y_m"]) for r in series[i]]
        ax.plot(x,y,color=COLORS[i],marker="o",markersize=3,
                linestyle="-" if i==2 else "--",linewidth=1.6,label=NAMES[i])
        ax.scatter(x[0],y[0],s=65,marker="^",color=COLORS[i])
    for i,marker in ((0,"s"),(1,"*")):
        row=series[i][0]
        ax.scatter(float(row["x_m"]),float(row["y_m"]),s=120,marker=marker,color=COLORS[i],label=NAMES[i],zorder=5)
    ax.set(xlim=(0,1000),ylim=(0,1000),xlabel="UAV x (m)",ylabel="UAV y (m)",title="UAV plane, altitude 1 km")
    ax.set_aspect("equal");ax.grid(alpha=.25);ax.legend(fontsize=8,loc="upper left")
    plane.scatter([float(r["intersection_x_m"]) for r in positions],
                  [float(r["intersection_y_m"]) for r in positions],s=12,c="0.35",label="Optical-path intersections")
    snapshot_indices = np.linspace(0,len(series[0])-1,4,dtype=int)
    for index,alpha in zip(snapshot_indices,(.18,.28,.38,.5)):
        r=series[0][index];center=(float(r["cloud_x_m"]),float(r["cloud_y_m"]))
        plane.add_patch(Circle(center,settings["cloud"]["radius_m"],facecolor="#93c5fd",edgecolor="#1d4ed8",alpha=alpha))
        plane.scatter(*center,s=24,color="#1d4ed8",marker="x")
        plane.text(center[0],center[1]+settings["cloud"]["radius_m"]+20,f"t={float(r['slot_start_s']):.0f}s",ha="center",fontsize=8)
    plane.autoscale_view();plane.set_aspect("equal");plane.grid(alpha=.25)
    plane.set(xlabel="Cloud-plane x (m)",ylabel="Cloud-plane y (m)",
              title=f"Cloud plane, altitude {settings['cloud']['altitude_m']/1000:g} km")
    plane.legend(fontsize=8,loc="lower right")
    finish(fig,"figure_1_cloud_and_uav_trajectory")

    fig,ax=plt.subplots(figsize=(7.6,4.8))
    for i,group in enumerate(series):
        times=[float(r["slot_start_s"]) for r in group]+[float(group[-1]["slot_end_s"])]
        rates=[float(r["usable_skr"]) for r in group];rates.append(rates[-1])
        ax.step(times,rates,where="post",color=COLORS[i],label=NAMES[i],
                linestyle=("-","--","-.",":")[i],linewidth=1.8)
    ax.set(xlabel="Mission time (s)",ylabel="Usable SKR (bits/use)",title="SKR versus time")
    decorate(ax);ax.legend(fontsize=9);finish(fig,"figure_2_skr_vs_time")

    fig,ax=plt.subplots(figsize=(7.6,4.8))
    report_bits=settings["optimization"]["channel_use_rate_per_s"] is not None
    for i,group in enumerate(series):
        times=[0.]+[float(r["slot_end_s"]) for r in group]
        name="cumulative_secret_bits" if report_bits else "cumulative_skr_contributions"
        values=[0.]+[float(r[name]) for r in group]
        ax.plot(times,values,color=COLORS[i],label=NAMES[i],linestyle=("-","--","-.",":")[i],linewidth=1.8)
    ax.set(xlabel="Mission time (s)",ylabel="Cumulative secret-key estimate (bits)" if report_bits else
           "Cumulative SKR contributions (bits/use-slot)",title="Cumulative SKR contributions")
    decorate(ax);ax.legend(fontsize=9);finish(fig,"figure_3_cumulative_skr")

    fig,ax=plt.subplots(figsize=(7.6,4.8))
    for i,scheme in enumerate(schemes):
        group=sorted((r for r in velocity if r["scheme"]==scheme),key=lambda r:float(r["cloud_speed_m_per_s"]))
        ax.plot([float(r["cloud_speed_m_per_s"]) for r in group],
                [float(r["average_skr_bits_per_use"]) for r in group],color=COLORS[i],marker="o",
                markersize=4,label=NAMES[i],linestyle=("-","--","-.",":")[i])
    ax.set(xlabel="Cloud horizontal speed (m/s)",ylabel="Average usable SKR (bits/use)",title="Cloud-velocity sensitivity")
    decorate(ax);ax.legend(fontsize=9);finish(fig,"figure_4_average_skr_vs_cloud_velocity")

    fig,ax=plt.subplots(figsize=(7.6,4.8));flight=ax.twinx()
    penalties=[float(r["sweep_lambda_bits_per_use"]) for r in penalty]
    rate_line=ax.plot(penalties,[float(r["average_skr_bits_per_use"]) for r in penalty],
                    color=COLORS[3],marker="o",label="Average SKR")
    distance_line=flight.plot(penalties,[float(r["total_flight_distance_m"]) for r in penalty],
                             color=COLORS[1],marker="s",linestyle="--",label="Flight distance")
    ax.set_xscale("symlog",linthresh=.0005)
    ax.set(xlabel=r"Movement penalty $\lambda$ (bits/use)",ylabel="Average usable SKR (bits/use)",
           title="Mobility-penalty sensitivity")
    flight.set_ylabel("Total UAV flight distance (m)",color=COLORS[1]);decorate(ax)
    ax.legend(rate_line+distance_line,[line.get_label() for line in rate_line+distance_line],fontsize=9)
    finish(fig,"figure_5_skr_and_flight_vs_penalty")

    fig,axes=plt.subplots(2,1,figsize=(7.6,5.6),sharex=True)
    group=series[2];times=[float(r["slot_start_s"]) for r in group]+[float(group[-1]["slot_end_s"])]
    for ax,name,label in zip(axes,("nu_raw","V_A"),(r"$\nu_{\rm raw}^{*}$",r"$V_A^{*}$ (SNU)")):
        values=[float(r[name]) for r in group];values.append(values[-1])
        ax.step(times,values,where="post",color=COLORS[2],linewidth=1.8)
        ax.set_ylabel(label);ax.grid(alpha=.25)
    axes[0].set_title("Selected MB source parameters: S3 moving UAV")
    axes[1].set_xlabel("Mission time (s)");finish(fig,"figure_6_optimized_source_parameters")
