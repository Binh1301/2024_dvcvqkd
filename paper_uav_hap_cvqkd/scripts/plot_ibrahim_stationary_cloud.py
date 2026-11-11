"""Render A-F and all-slot GIF from saved cloud arrays; no simulation calls."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image, ImageDraw
from scipy.stats import t

ROOT=Path(__file__).resolve().parents[1]


def export(fig,out,name):
    for ext in ("png","pdf"):
        fig.savefig(out/f"{name}.{ext}",dpi=400,bbox_inches="tight")
    plt.close(fig)


def map_axis(ax,array,title,extent,limits,binary=False):
    im=ax.imshow(array,origin="lower",extent=extent,aspect="equal",interpolation="nearest",
                 cmap=ListedColormap(["black","white"]) if binary else "viridis",
                 vmin=limits[0],vmax=limits[1])
    ax.set(title=title,xlabel="x (km)",ylabel="y (km)")
    return im


def render(out):
    data=np.load(out/"cloud_fields.npz",allow_pickle=False)
    ens=np.load(out/"ensemble_validation.npz",allow_pickle=False)
    report=json.loads((out/"validation.json").read_text())
    settings=json.loads((out/"design_receipt.json").read_text())["settings"]
    meta=json.loads(str(data["metadata_json"]))
    c=meta["parameters"]
    slots=settings["snapshot_slots"]
    plt.rcParams.update({"font.family":"serif","font.size":9,"pdf.fonttype":42,"ps.fonttype":42,
                         "axes.linewidth":.7,"lines.linewidth":1.2})
    extent=(0,c["nx"]*c["dx_m"]/1000,0,c["ny"]*c["dy_m"]/1000)
    fields=[data["initial_fine"],data["initial_coarse"],data["X"][0]]
    limit=max(np.max(abs(a)) for a in fields)
    fig,axs=plt.subplots(1,3,figsize=(10.3,3.1),layout="constrained")
    for ax,x,title in zip(axs,fields,["Fine Gaussian field","Fourier-interpolated coarse field","Normalized combined latent X0"]):
        im=map_axis(ax,x,title,extent,(-limit,limit))
    fig.colorbar(im,ax=list(axs),shrink=.8,label="Dimensionless Gaussian field")
    export(fig,out,"figure_A_multiscale")
    maximum=float(data["intensity"].max())
    fig,axs=plt.subplots(1,2,figsize=(7.5,3.3),layout="constrained")
    im=map_axis(axs[0],data["intensity"][0],"Initial relative intensity",extent,(0,maximum))
    fig.colorbar(im,ax=axs[0],shrink=.8,label="Relative Cloud Intensity (a.u.)")
    im=map_axis(axs[1],data["diagnostic_mask"][0],"Initial presence diagnostic (30%)",extent,(0,1),True)
    cb=fig.colorbar(im,ax=axs[1],shrink=.8,label="Presence diagnostic")
    cb.set_ticks([0,1],labels=["Clear","Cloud"])
    export(fig,out,"figure_B_intensity_presence")
    xlimit=float(np.max(abs(data["X"])))
    for name,key,binary,limits,label in (
        ("figure_C_latent_snapshots","X",False,(-xlimit,xlimit),"Latent Gaussian field X (a.u.)"),
        ("figure_D_presence_snapshots","diagnostic_mask",True,(0,1),"Cloud presence diagnostic")):
        fig,axs=plt.subplots(2,4,figsize=(11.8,6.2),layout="constrained")
        for ax,k in zip(axs.flat,slots):
            im=map_axis(ax,data[key][k],f"k = {k}, t = {k*c['dt_s']:g} s",extent,limits,binary)
        axs.flat[-1].set_axis_off()
        used=list(axs.flat)[:len(slots)]
        cb=fig.colorbar(im,ax=used,shrink=.7,label=label)
        if binary:
            cb.set_ticks([0,1],labels=["Clear","Cloud"])
        fig.suptitle(f"Fixed observation window; wind vx = {c['vx_m_s']:g} m/s",fontsize=11)
        export(fig,out,name)
    metrics=ens["metrics"]; names=list(ens["metric_names"])
    means=metrics.mean(axis=0)
    ci=t.ppf(.975,len(metrics)-1)*metrics.std(axis=0,ddof=1)/np.sqrt(len(metrics))
    time=data["time_s"]
    fig,axs=plt.subplots(3,1,figsize=(7.4,7.1),sharex=True,layout="constrained")
    for ax,name,title,target in zip(axs,["cloud_fraction","mean","variance"],
                                    ["Diagnostic cloud fraction","Latent spatial mean","Latent ROI population variance"],
                                    [c["initial_fraction"],0.,report["expected_crop_population_variance"]]):
        mi=names.index(name)
        ax.plot(time,metrics[0,:,mi],color="#a1a1a1",lw=.7,label="Main seed")
        ax.plot(time,means[:,mi],color="#2166ac",label=f"Mean of {len(metrics)} seeds")
        ax.fill_between(time,means[:,mi]-ci[:,mi],means[:,mi]+ci[:,mi],color="#2166ac",alpha=.18,label="Approx. 95% seed-level CI")
        ax.axhline(target,color="#b2182b",ls="--",lw=.9,label="Initial calibration target" if name=="cloud_fraction" else "Theoretical expectation")
        ax.set_ylabel(title); ax.grid(alpha=.18)
    axs[0].legend(ncol=2,fontsize=8)
    axs[-1].set_xlabel("Time (s)")
    export(fig,out,"figure_E_time_statistics")
    fig,axs=plt.subplots(1,2,figsize=(10.3,3.6),layout="constrained")
    lag=np.arange(21)
    target=ens["covariance_target"][0,:21]
    axs[0].plot(lag*c["dx_m"]/1000,target,color="black",label="Combined target")
    axs[0].plot(lag*c["dx_m"]/1000,ens["fine_covariance_target"][0,:21],":",color="#888888",label="Fine target")
    axs[0].plot(lag*c["dx_m"]/1000,ens["coarse_covariance_target"][0,:21],"--",color="#d95f02",label="Coarse target")
    for key,col,marker,tag in (("covariance_initial","#2166ac","o","Initial ensemble"),("covariance_final","#1b9e77","s","Final ensemble")):
        v=ens[key][:,0,:21]
        err=t.ppf(.975,len(v)-1)*v.std(axis=0,ddof=1)/np.sqrt(len(v))
        axs[0].errorbar(lag*c["dx_m"]/1000,v.mean(axis=0),yerr=err,fmt=marker,ms=3,capsize=2,color=col,label=tag)
    axs[0].set(xlabel="x separation (km)",ylabel="Covariance / target marginal variance",title="Spatial covariance")
    lags=ens["temporal_lags"]
    vals=ens["temporal"]
    err=t.ppf(.975,len(vals)-1)*vals.std(axis=0,ddof=1)/np.sqrt(len(vals))
    dense=np.linspace(0,max(lags)*c["dt_s"],400)
    axs[1].plot(dense,np.exp(-dense/c["tau_c_s"]),color="black",label="Theory: exp(-lag / tau_c)")
    axs[1].errorbar(lags*c["dt_s"],vals.mean(axis=0),yerr=err,fmt="o",color="#2166ac",capsize=3,ms=4,label="Motion-compensated ensemble")
    axs[1].set(xlabel="Lag (s)",ylabel="Motion-compensated autocorrelation",title="Independent-seed mean and approx. 95% CI")
    for ax in axs:
        ax.legend(fontsize=7); ax.grid(alpha=.18)
    export(fig,out,"figure_F_correlations")
    palette=np.vstack([(plt.colormaps["viridis"](np.linspace(0,1,254))[:,:3]*255).astype(np.uint8),[[0,0,0],[255,255,255]]]).astype(np.uint8).ravel().tolist()
    frames=[]
    for k in range(c["slots"]):
        canvas=Image.new("P",(400,234),254); canvas.putpalette(palette)
        colors=np.minimum(253,np.floor(data["intensity"][k]/maximum*253)).astype(np.uint8)
        presence=np.where(data["diagnostic_mask"][k],255,254).astype(np.uint8)
        for x,array in ((0,colors),(200,presence)):
            img=Image.fromarray(np.flipud(array)); img.putpalette(palette)
            canvas.paste(img.resize((200,200),Image.Resampling.NEAREST),(x,34))
        draw=ImageDraw.Draw(canvas)
        draw.text((4,2),f"k={k:03d}; t={k*c['dt_s']:g} s; vx={c['vx_m_s']:g} m/s",fill=255)
        draw.text((4,18),"Relative intensity",fill=255)
        draw.text((204,18),"Presence diagnostic",fill=255)
        frames.append(canvas)
    frames[0].save(out/"cloud_1000_slots.gif",save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False,disposal=2)
    print(f"Exported six PNG/PDF figures and {len(frames)} GIF frames",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path,nargs="?",default=ROOT/"results/ibrahim_stationary_cloud_20261111")
    render(parser.parse_args().output)
