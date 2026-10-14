"""IEEE-sized figures from explicit CSV plotting data, without SKR evaluation."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from src.mobility_results_package import read_csv, projected_cloud_footprint
from scripts.run_mobility_skr_experiment import SCHEMES

COLORS=("#0072B2","#E69F00","#009E73","#CC79A7")
STYLES=("-","--","-.",":")
MARKERS=("o","s","^","D")
LABELS=("S1 Reference fixed","S2 Stationary",r"S3 Moving, $\lambda=0$","S4 Mobility-aware")


def render_package(output,settings,include_uniform=False):
    output=Path(output);data=output/"plot_data";figures=output/"figures";figures.mkdir(exist_ok=True)
    series=read_csv(data/"figure_2_skr_time.csv")
    cumulative=read_csv(data/"figure_3_cumulative_normalized.csv")
    penalty=read_csv(data/"figure_4_skr_flight.csv")
    velocity=read_csv(data/"figure_5_cloud_velocity.csv")
    positions=read_csv(data/"figure_1_positions.csv")
    def grouped(rows):return [[r for r in rows if r["scheme"]==scheme] for scheme in SCHEMES]
    groups=grouped(series)
    for layout,width in (("single",3.5),("double",7.16)):
        with plt.rc_context({"font.family":"serif","font.size":8,"axes.labelsize":8,
            "axes.titlesize":9,"legend.fontsize":6.5,"xtick.labelsize":7,"ytick.labelsize":7,
            "pdf.use14corefonts":True,"lines.linewidth":1.3}):
            def finish(fig,name):
                fig.text(.5,.007,"Preliminary effective-Gaussian results",ha="center",fontsize=6)
                fig.tight_layout(rect=(0,.035,1,.97))
                fig.savefig(figures/f"{name}_{layout}.png",dpi=300,facecolor="white")
                fig.savefig(figures/f"{name}_{layout}.pdf",facecolor="white")
                plt.close(fig)
            def axes_style(ax,zero=True):
                ax.grid(alpha=.22,linewidth=.5);ax.ticklabel_format(axis="y",style="sci",scilimits=(-2,2),useMathText=True)
                if zero:ax.set_ylim(bottom=0.)
            def time_plot(ax,rows,field,steps=True):
                for i,group in enumerate(grouped(rows)):
                    if steps:
                        x=[float(r["slot_start_s"]) for r in group]+[float(group[-1]["slot_end_s"])]
                        y=[float(r[field]) for r in group];y.append(y[-1])
                        ax.step(x,y,where="post",color=COLORS[i],linestyle=STYLES[i],label=LABELS[i])
                        ax.plot(x[:-1:4],y[:-1:4],linestyle="none",marker=MARKERS[i],markersize=2.8,color=COLORS[i])
                    else:
                        ax.plot([float(r["time_s"]) for r in group],[float(r[field]) for r in group],
                            color=COLORS[i],linestyle=STYLES[i],marker=MARKERS[i],markersize=2.5,markevery=5,label=LABELS[i])
                ax.set_xlim(0,settings["mission"]["slots"]*settings["mission"]["slot_duration_s"])
                axes_style(ax);ax.set_xlabel("Time (s)")

            fig,axes=plt.subplots(2 if layout=="single" else 1,1 if layout=="single" else 2,
                figsize=(width,6.3 if layout=="single" else 3.9))
            axes=np.asarray(axes).reshape(-1)
            for ax,i,panel in zip(axes,(2,3),("(a) S3","(b) S4")):
                for n in (0,9,16,20,29):
                    row=groups[i][n]
                    center,radius=projected_cloud_footprint(settings,[float(row["cloud_x_m"]),float(row["cloud_y_m"])])
                    ax.add_patch(Circle(center,radius,facecolor="0.55",edgecolor="0.4",alpha=.07,linewidth=.6,zorder=0))
                    if 0<center[0]<1000:
                        ax.text(center[0],650 if n==9 else 220,f"t={float(row['slot_start_s']):g}s",
                            fontsize=6,ha="center",color="0.3",bbox=dict(facecolor="white",edgecolor="none",alpha=.7,pad=1))
                ax.scatter([float(r["x_m"]) for r in positions],[float(r["y_m"]) for r in positions],s=7,c="0.7",zorder=1)
                x=np.array([float(r["x_m"]) for r in groups[i]]);y=np.array([float(r["y_m"]) for r in groups[i]])
                ax.plot(x,y,color=COLORS[i],linestyle=STYLES[i],marker=MARKERS[i],markersize=2.5,zorder=3)
                for n in range(1,len(x)):
                    if x[n]!=x[n-1] or y[n]!=y[n-1]:
                        ax.annotate("",xy=(x[n],y[n]),xytext=(x[n-1],y[n-1]),
                            arrowprops=dict(arrowstyle="->",color=COLORS[i],lw=.8),zorder=4)
                for k,mark,label in ((0,"s","S1"),(1,"*","S2")):
                    row=groups[k][0];ax.scatter(float(row["x_m"]),float(row["y_m"]),s=35 if k==0 else 65,
                        marker=mark,color=COLORS[k],edgecolor="black",linewidth=.3,label=label,zorder=5)
                ax.scatter(x[0],y[0],s=75,facecolor="none",edgecolor=COLORS[i],linewidth=1.3,label="Start",zorder=6)
                ax.scatter(x[-1],y[-1],s=45,marker="x",color=COLORS[i],linewidth=1.2,label="End",zorder=7)
                ax.annotate("Cloud footprint moves +x",xy=(720,330),xytext=(160,330),fontsize=6,
                    arrowprops=dict(arrowstyle="->",color="0.25",lw=.6),color="0.25",
                    bbox=dict(facecolor="white",edgecolor="none",alpha=.7,pad=1))
                ax.set(xlim=(0,1000),ylim=(0,1000),xlabel="UAV horizontal x (m)",ylabel="UAV horizontal y (m)",title=panel)
                ax.set_aspect("equal");ax.grid(alpha=.15);ax.legend(loc="lower left",ncol=2,framealpha=.9)
            finish(fig,"figure_1_cloud_trajectories")

            fig,ax=plt.subplots(figsize=(width,3.2 if layout=="single" else 3.7))
            reference=groups[0]
            for row in reference:
                if row["blocked"]=="True":
                    ax.axvspan(float(row["slot_start_s"]),float(row["slot_end_s"]),color="0.6",alpha=.10,lw=0)
            time_plot(ax,series,"usable_skr");ax.set_ylabel("SKR (bits/use)")
            ax.legend(loc="lower center",bbox_to_anchor=(.5,1.055),ncol=2,
                frameon=False,borderaxespad=0);finish(fig,"figure_2_skr_time")

            fig,ax=plt.subplots(figsize=(width,2.8 if layout=="single" else 3.5))
            time_plot(ax,cumulative,"cumulative_normalized_skr",steps=False)
            ax.set_ylabel("Cumulative normalized SKR (bits/use)")
            ax.legend(loc="upper left",framealpha=.9);finish(fig,"figure_3_cumulative_normalized")

            fig,ax=plt.subplots(figsize=(width,2.9 if layout=="single" else 3.6))
            x=[float(r["total_flight_distance_m"]) for r in penalty]
            y=[float(r["average_skr_bits_per_use"]) for r in penalty]
            ax.scatter(x,y,s=24,color=COLORS[3],edgecolor="black",linewidth=.3,label=r"Evaluated $\lambda$ values")
            annotations=[(0,r"S3: $\lambda=0$",(1700,.043)),(2,r"S4: $\lambda=0.001$",(700,.035)),
                (7,r"S2 / $\lambda=0.05$",(120,.021))]
            for index,label,location in annotations:
                ax.annotate(label,(x[index],y[index]),xytext=location,fontsize=6.5,
                            arrowprops=dict(arrowstyle="-",lw=.5,color="0.4"))
            ax.scatter(x[0],y[0],marker="^",s=42,color=COLORS[2],zorder=4)
            ax.scatter(x[2],y[2],marker="D",s=38,color=COLORS[3],edgecolor="black",linewidth=.4,zorder=4)
            ax.scatter(0,y[-1],marker="*",s=60,color=COLORS[1],zorder=4)
            ax.set(xlabel="Total UAV flight distance (m)",ylabel="Average SKR (bits/use)",xlim=(-100,max(x)*1.12),ylim=(0,max(y)*1.12))
            axes_style(ax);ax.legend(loc="lower right");finish(fig,"figure_4_skr_flight_tradeoff")

            fig,ax=plt.subplots(figsize=(width,2.8 if layout=="single" else 3.5))
            for i,group in enumerate(grouped(velocity)):
                group=sorted(group,key=lambda r:float(r["cloud_speed_m_per_s"]))
                ax.plot([float(r["cloud_speed_m_per_s"]) for r in group],
                    [float(r["average_skr_bits_per_use"]) for r in group],color=COLORS[i],linestyle=STYLES[i],
                    marker=MARKERS[i],markersize=3,label=LABELS[i])
            ax.set(xlabel="Cloud velocity (m/s)",ylabel="Average SKR (bits/use)")
            axes_style(ax);ax.legend(loc="lower right");finish(fig,"figure_5_cloud_velocity")

            fig,axes=plt.subplots(2,1,sharex=True,figsize=(width,3.8 if layout=="single" else 4.3))
            for ax,field,label,panel in zip(axes,("nu_raw","V_A"),(r"$\nu_{\rm MB,raw}^{\star}$",r"$V_A^{\star}$ (SNU)"),("(a)","(b)")):
                for i in (1,3):
                    group=groups[i];x=[float(r["slot_start_s"]) for r in group]+[float(group[-1]["slot_end_s"])]
                    y=[float(r[field]) for r in group];y.append(y[-1])
                    ax.step(x,y,where="post",color=COLORS[i],linestyle=STYLES[i],label=LABELS[i])
                    ax.plot(x[:-1:4],y[:-1:4],linestyle="none",marker=MARKERS[i],markersize=2.8,color=COLORS[i])
                ax.set_ylabel(label);ax.set_title(panel,loc="left",pad=3);ax.grid(alpha=.22,linewidth=.5)
            axes[0].legend(loc="upper left");axes[1].set_xlabel("Time (s)")
            finish(fig,"figure_6_source_parameters")

            if include_uniform:
                bars=read_csv(data/"figure_7_uniform_mb.csv")
                fig,ax=plt.subplots(figsize=(width,2.8 if layout=="single" else 3.5))
                categories=("Stationary",r"Moving ($\lambda=0$)")
                for i,family in enumerate(("Uniform","MB")):
                    values=[float(next(r["average_skr"] for r in bars if r["family"]==family and r["configuration"]==name))
                        for name in ("stationary","moving_lambda0")]
                    centers=np.arange(2)+(i-.5)*.3
                    rectangles=ax.bar(centers,values,width=.3,label=family,color="0.55" if i==0 else COLORS[2],
                        hatch="//" if i==0 else "",edgecolor="black",linewidth=.4)
                    for rect,value in zip(rectangles,values):
                        ax.text(rect.get_x()+rect.get_width()/2,value+.001,f"{value:.4f}",ha="center",fontsize=6.5)
                ax.set_xticks(np.arange(2),categories);ax.set_ylabel("Average SKR (bits/use)")
                axes_style(ax);ax.set_ylim(top=max(float(r["average_skr"]) for r in bars)*1.2)
                ax.legend(loc="upper left");finish(fig,"figure_7_uniform_mb")
