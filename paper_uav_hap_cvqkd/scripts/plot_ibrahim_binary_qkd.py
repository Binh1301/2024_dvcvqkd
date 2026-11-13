"""Saved-data scientific figures and binary animation; no field or QKD runs."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'pdf.fonttype':42,
 'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':400})
STATE_COLORS=['#d6f0de','#cc5a28','#b8c0c8']
STATE_CMAP=ListedColormap(STATE_COLORS)
STATE_NORM=BoundaryNorm([-.5,.5,1.5,2.5],3)


def plot(out):
    cfg=json.loads((out/'configuration.json').read_text());meta=json.loads((out/'metadata.json').read_text())
    for name,digest in meta['inputs'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    with np.load(ROOT/cfg['gaussian_input'],allow_pickle=False) as d:g=d['X']
    with np.load(ROOT/cfg['continuous_directory']/'cloud_attenuation_db.npz',allow_pickle=False) as d:a=d['attenuation_db']
    with np.load(out/'diagnostic_binary_blockage.npz',allow_pickle=False) as d:b=d['binary_blockage']
    with np.load(out/'official_pending_status.npz',allow_pickle=False) as d:pending=d['binary_blockage']
    edges=np.linspace(0,2,51);time=np.arange(1000);figures=[]
    def mesh(ax,z,cmap='viridis',vmin=None,vmax=None,state=False):
        if state:
            z=np.where(z==255,2,z)
            m=ax.pcolormesh(edges,edges,z,cmap=STATE_CMAP,norm=STATE_NORM,shading='flat',rasterized=False)
        else:m=ax.pcolormesh(edges,edges,z,cmap=cmap,vmin=vmin,vmax=vmax,shading='flat',rasterized=False)
        ax.set(xlabel='x (km)',ylabel='y (km)',xlim=(0,2),ylim=(0,2));ax.set_aspect('equal')
        return m
    def colorbar(fig,m,axes,label,state=False):
        cb=fig.colorbar(m,ax=axes,label=label,shrink=.85,pad=.015)
        if cb.solids:cb.solids.set_rasterized(False)
        if state:cb.set_ticks([0,1,2],labels=['0: available','1: unavailable','?: unresolved'])
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=400,facecolor='white');fig.savefig(out/(name+'.pdf'),facecolor='white')
        plt.close(fig);figures.append(name)

    fig,axs=plt.subplots(3,3,figsize=(12.6,11.2),layout='constrained')
    extent=float(np.max(abs(g)))
    for j,k in enumerate(cfg['snapshot_slots']):
        gm=mesh(axs[0,j],g[k],cmap='RdBu_r',vmin=-extent,vmax=extent);axs[0,j].set_title(f'Saved Gaussian G, k={k} s')
        bm=mesh(axs[1,j],b[k],state=True);axs[1,j].set_title(f'Diagnostic 0.1 dB, k={k} s')
        mesh(axs[2,j],pending[k],state=True);axs[2,j].set_title(f'0.55 m: unresolved, k={k} s')
    colorbar(fig,gm,list(axs[0]),'Dimensionless G')
    colorbar(fig,bm,list(axs[1:].flat),'QKD proxy state b',state=True)
    fig.suptitle('A. Original Gaussian and QKD availability state at identical saved coordinates\nDiagnostic reference columns only; official 0.55 m threshold pending',fontsize=13)
    save(fig,'figure_A_gaussian_and_binary_qkd')

    fig,axs=plt.subplots(1,3,figsize=(13.6,4.8),layout='constrained');k=400
    m=mesh(axs[0],a[k],cmap='magma',vmin=0,vmax=float(a.max()));colorbar(fig,m,axs[0],'A (dB)')
    axs[0].set_title('Saved continuous attenuation')
    th=mesh(axs[1],np.full((50,50),.1),cmap='Purples',vmin=0,vmax=.2);colorbar(fig,th,axs[1],'Illustrative threshold (dB)')
    axs[1].set_title('Diagnostic scalar threshold: 0.1 dB')
    bm=mesh(axs[2],b[k],state=True);colorbar(fig,bm,axs[2],'b',state=True);axs[2].set_title('Diagnostic QKD unavailability')
    fig.suptitle('B. Continuous attenuation and binary classification at k=400 s\nNo validated 0.55 m threshold is supplied; physical transmittance is preserved',fontsize=12)
    save(fig,'figure_B_attenuation_threshold_blockage')

    fig,axs=plt.subplots(1,3,figsize=(12.3,4.6),layout='constrained')
    for ax,k in zip(axs,cfg['dynamic_snapshot_slots']):
        bm=mesh(ax,b[k],state=True);ax.set_title(f'k={k} s')
    colorbar(fig,bm,list(axs),'b',state=True)
    fig.suptitle('C. Dynamic diagnostic QKD proxy state - fixed 0.1 dB threshold\n0=available; 1=unavailable; unresolved is separate. Not optical extinction.',fontsize=12)
    save(fig,'figure_C_dynamic_binary_maps')

    fig,axs=plt.subplots(1,2,figsize=(12.4,4.5),layout='constrained')
    fraction=(b==1).mean((1,2));affected=(a>0).mean((1,2))
    axs[0].plot(time,100*affected,color='#557e94',label='Cloud-affected: A > 0')
    axs[0].plot(time,100*fraction,color='#b04f24',label='Diagnostic blockage: all cells')
    axs[0].plot(time,100*fraction,color='black',ls='--',lw=.8,label='Given assumed clear feasibility (same population)')
    axs[0].set(xlabel='Time (s)',ylabel='Cell fraction (%)',title='Diagnostic ratios: denominators = 2500 cells/slot');axs[0].legend(fontsize=8)
    axs[1].plot(time,np.full(1000,100),color='#6e7882',label='Unresolved fraction')
    axs[1].set(xlabel='Time (s)',ylabel='Unresolved cells (%)',ylim=(0,105),title='Official 0.55 m: pending, blockage ratio undefined')
    axs[1].text(.5,.4,'No official blockage or availability ratio\nUnknown cells are never marked available',transform=axs[1].transAxes,ha='center')
    for ax in axs:ax.grid(alpha=.2)
    fig.suptitle('D. Frame-level statistics - diagnostic assumptions and official unknowns kept separate',fontsize=12)
    save(fig,'figure_D_blockage_statistics')

    fig,axs=plt.subplots(1,3,figsize=(13.4,4.5),layout='constrained')
    axs[0].hist(a.ravel(),bins=100,weights=np.full(a.size,1/a.size),color='#4b768e')
    axs[0].set(yscale='log',xlabel='Attenuation (dB)',ylabel='Probability per bin',title='All cells/slots, including A=0 atom')
    ordered=np.sort(a.ravel());nodes=np.unique(np.r_[0.,np.linspace(0,a.max(),500),.1])
    cdf=np.searchsorted(ordered,nodes,side='right')/a.size
    axs[1].plot(nodes,cdf,color='#4b768e');axs[1].vlines(0,0,np.mean(a==0),color='#4b768e')
    axs[1].set(xlabel='Attenuation (dB)',ylabel='Empirical CDF',ylim=(0,1.02),title='Empirical distribution at saved value nodes')
    positive=a[a>0]
    axs[2].hist(positive,bins=np.linspace(0,.3,61),weights=np.full(positive.size,1/positive.size),color='#4b768e')
    axs[2].set(xlim=(0,.3),xlabel='Attenuation (dB)',ylabel='Probability per bin given A > 0',title='Low-loss tail: conditional population A > 0')
    for ax in axs:
        ax.axvline(.1,color='#ba4e2e',ls='--',label='Illustrative 0.1 dB only');ax.grid(alpha=.15);ax.legend(fontsize=8)
    fig.suptitle('E. Saved attenuation statistics and diagnostic threshold - no official scalar threshold',fontsize=12)
    save(fig,'figure_E_distribution_and_threshold')

    fig,axs=plt.subplots(2,3,figsize=(13,6.5),sharex=True,layout='constrained')
    for j,(iy,ix) in enumerate(cfg['probe_indices_yx']):
        axs[0,j].step(time,b[:,iy,ix],where='post',color='#b04f24',lw=.7)
        axs[0,j].set(ylim=(-.1,1.1),yticks=[0,1],yticklabels=['0: available','1: unavailable'],
            title=f'Reference x={(ix+.5)*40:g} m, y={(iy+.5)*40:g} m')
        axs[0,j].grid(alpha=.2)
        axs[1,j].axhspan(0,1,color=STATE_COLORS[2]);axs[1,j].set(ylim=(0,1),yticks=[.5],yticklabels=['Unresolved'],xlabel='Time (s)')
        axs[1,j].text(.5,.5,'0.55 m threshold pending',transform=axs[1,j].transAxes,ha='center',fontsize=9)
    fig.suptitle('F. QKD availability proxy time series (shown as b)\nTop: diagnostic 0.1 dB; bottom: official unresolved, not an unavailable measurement',fontsize=12)
    save(fig,'figure_F_qkd_availability_time_series')

    colors=np.array([[214,240,222],[204,90,40],[184,192,200]],dtype=np.uint8)
    palette=colors.ravel().tolist()+[255,255,255,0,0,0]+[0,0,0]*251
    font=ImageFont.load_default(size=12);frames=[]
    for k in range(1000):
        frame=Image.new('P',(440,282),3);frame.putpalette(palette)
        for z,x0 in [(b[k],10),(pending[k],230)]:
            indices=np.where(z==255,2,z).astype(np.uint8)
            pixels=np.repeat(np.repeat(np.flipud(indices),4,axis=0),4,axis=1)
            tile=Image.frombytes('P',(200,200),pixels.tobytes());tile.putpalette(palette);frame.paste(tile,(x0,45))
        draw=ImageDraw.Draw(frame)
        draw.text((10,2),f'QKD proxy state; k={k:03d} s; y upward',fill=4,font=font)
        draw.text((10,24),'Diagnostic 0.1 dB',fill=4,font=font);draw.text((230,24),'0.55 m: unresolved',fill=4,font=font)
        draw.text((10,248),'Reference x,y: 0 - 2 km',fill=4,font=font)
        draw.text((10,266),'0 available   1 unavailable   ? unresolved',fill=4,font=font)
        frames.append(frame)
    frames[0].save(out/'figure_G_binary_qkd_1000_frames.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,disposal=2,optimize=False)
    receipt=dict(plotter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),figures=figures,PNG_dpi=400,
        PDF_maps='Native vector quadrilateral cells, no rasterization; vector text and axes',GIF_frames=1000,GIF_duration_ms=50,
        GIF_diagnostic_bbox=[10,45,210,245],GIF_official_bbox=[230,45,430,245],state_RGB_colors=colors.tolist(),
        source_array_regeneration=False,official_threshold_validated=False)
    (out/'render_receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
    print('Six PNG/PDF figures and 1000-frame GIF rendered from saved data')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);plot(parser.parse_args().output.resolve())
