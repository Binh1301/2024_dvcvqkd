"""Exact-tested Uniform VA search for the explicitly requested manuscript comparison.

Reuses the MB recheck's channel and homodyne security formulas. The normalized
2D likelihood and tensor quadrature are unchanged; Cartesian Uniform mixture
factorization avoids evaluating its identical 256-term mixture repeatedly.
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
from scipy.special import logsumexp, roots_hermitenorm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.recheck_manuscript_homodyne_noise import M, channel, converted, mi_gh, security
from scripts.run_exact_mb_test2 import ensemble_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
from scripts.run_theta10_D55_alt_opt_convergence_validation import bounded_process
import torch

OUT = ROOT/'results/uniform_manuscript_2d_optimization_20261019'
MB_DIR = ROOT/'results/manuscript_homodyne_noise_recheck_20261019'
REPORT = ROOT/'docs/UNIFORM_MANUSCRIPT_2D_OPTIMIZATION_VI.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(name,rows):
    if not rows:
        return
    with (OUT/name).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def uniform_mi_2d(p,alpha,t,noise,order):
    """Full normalized 2D Gaussian integral, using its exact product mixture.

    We sum the 2D tensor log ratio over both real and imaginary observations.
    No homodyne MI substitution, factor 1/2, or heterodyne noise is introduced.
    """
    levels_x, ix = np.unique(alpha.real,return_inverse=True)
    levels_y, iy = np.unique(alpha.imag,return_inverse=True)
    px,py = np.bincount(ix,weights=p),np.bincount(iy,weights=p)
    if max(abs(p-px[ix]*py[iy]))>1e-14:
        raise ValueError('Nonproduct PMF cannot use exact mixture factorization')
    nodes,weights=roots_hermitenorm(order)
    weights/=math.sqrt(2*math.pi)
    sigma=math.sqrt(1+noise)
    ratios=[]
    for levels,pmarg in ((levels_x,px),(levels_y,py)):
        means=2*math.sqrt(t)*levels
        y=means[:,None]+sigma*nodes[None,:]
        logmix=logsumexp(np.log(pmarg)[None,None,:]
                        -.5*((y[:,:,None]-means[None,None,:])/sigma)**2,axis=-1)
        ratios.append(-.5*nodes[None,:]**2-logmix)
    ratio_2d=ratios[0][:,None,:,None]+ratios[1][None,:,None,:]
    value=np.einsum('i,j,u,v,ijuv->',px,py,weights,weights,ratio_2d,optimize=True)/math.log(2)
    return float(value)


class UniformSearch:
    def __init__(self):
        torch.set_num_threads(1)
        mp.mp.dps=80
        self.config=unconstrained_config()
        self.settings=source_settings(self.config)
        self.rows=[];self.models={};self.convergence=[];self.inventory={}
        self.calls=[];self.checks=[]
        mb=json.loads((MB_DIR/'result.json').read_text(encoding='utf-8'))
        receipt=json.loads((MB_DIR/'validation_receipt.json').read_text(encoding='utf-8'))
        for name,value in receipt['artifact_sha256'].items():
            if sha(ROOT/name)!=value:
                raise ValueError('MB reference artifact changed: '+name)
        self.mb=mb
        self.channel=channel()
        self.m1,self.mh=self.channel['mean_eta'],self.channel['mean_sqrt_eta']
        reference=mb['high_precision_model']
        self.check('same_channel_mean_eta',abs(self.m1-M(reference['mean_eta']))<M('1e-60'))
        self.check('same_channel_eta_f',abs(self.mh**2-M(reference['eta_f']))<M('1e-60'))
        self.check('rounded_user_moments_match',abs(float(self.m1)-.000264033937028)<5e-16
                   and abs(float(self.mh**2)-.000243545488773)<5e-16)
        save_json(OUT/'channel_once.json',dict(channel=converted(self.channel),
                  high_precision=converted(self.channel,precise=True),
                  moment_evaluation_count=1,MB_result_sha256=sha(MB_DIR/'result.json')))
        self.channel_hash=sha(OUT/'channel_once.json')
        self.rows_dir=OUT/'candidate_records';self.rows_dir.mkdir(exist_ok=True)
        for path in sorted((ROOT/'results').rglob('*.json')):
            if 'exact_source_cache' not in path.parts or OUT in path.parents:
                continue
            raw=path.read_bytes()
            if b'"nu_mb_raw_hex": "0x0.0p+0"' not in raw:
                continue
            payload=json.loads(raw)
            if payload.get('schema')!='exact-mb-source-cache-v1':
                continue
            verification=verify_source_payload(payload,self.settings)
            va=float.fromhex(payload['V_A_hex'])
            ensemble=make_ensemble(self.config,'Uniform',0.,va)
            if ensemble_hash(ensemble)!=payload['ensemble_hash']:
                raise ValueError('Uniform cache ensemble mismatch: '+str(path))
            self.inventory[va.hex()]=dict(path=path,payload=payload,verification=verification)
        write_csv('historical_uniform_inventory.csv',[
            dict(VA=float.fromhex(key),VA_hex=key,C=row['payload']['C'],w=row['payload']['w'],
                 source_path=str(row['path'].relative_to(ROOT)),source_sha256=sha(row['path']),
                 ensemble_hash=row['payload']['ensemble_hash'])
            for key,row in sorted(self.inventory.items(),key=lambda kv:float.fromhex(kv[0]))])
        self.check('no_MB_source_in_Uniform_inventory',all(float.fromhex(r['payload']['nu_mb_raw_hex'])==0 for r in self.inventory.values()))

    def check(self,name,ok,detail=None):
        record=dict(check=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED',detail=detail)
        self.checks.append(record)
        if not ok:
            save_json(OUT/'failed_check.json',record)
            raise AssertionError(record)

    def source(self,va,ensemble):
        existing=self.inventory.get(va.hex())
        if existing:
            return existing['payload'],existing['path'],'HISTORICAL_EXACT_CACHE'
        source_receipt=OUT/'source_receipts'/(ensemble_hash(ensemble)+'.json')
        expected=None
        if source_receipt.exists():
            for path in (OUT/'exact_source_cache').glob('*.json'):
                payload=json.loads(path.read_text(encoding='utf-8'))
                if payload['ensemble_hash']==ensemble_hash(ensemble):
                    expected=(payload,path)
                    break
        if expected is None:
            print('SOURCE_START VA='+repr(va),flush=True)
            began=time.perf_counter()
            logs=OUT/'source_logs';logs.mkdir(exist_ok=True)
            log_path=logs/(ensemble_hash(ensemble)+'.log')
            with log_path.open('w',encoding='utf-8') as log:
                supervision=bounded_process([sys.executable,'-X','utf8','-B',str(OUT/'source_uniform_diagonal.py'),repr(va)],3720,log)
            save_json(log_path.with_suffix('.json'),supervision)
            output=log_path.read_text(encoding='utf-8')
            if supervision['returncode'] or supervision['deadline_exceeded']:
                raise RuntimeError('Exact Uniform source failed: '+output[-3000:])
            info=json.loads(output.strip().splitlines()[-1])
            path=ROOT/info['source_path']
            expected=(json.loads(path.read_text(encoding='utf-8')),path)
            print('SOURCE_READY VA='+repr(va)+' seconds='+str(round(time.perf_counter()-began,2)),flush=True)
        payload,path=expected
        verify_source_payload(payload,self.settings)
        if payload['ensemble_hash']!=ensemble_hash(ensemble) or float.fromhex(payload['V_A_hex'])!=va:
            raise ValueError('Fresh source ensemble mismatch')
        return payload,path,'FRESH_EXACT_SOURCE_SEPARATE_CACHE'

    def evaluate(self,va,stage):
        va=float(va)
        if not math.isfinite(va) or va<=0:
            raise ValueError('VA must be positive')
        self.calls.append(dict(VA=va,VA_hex=va.hex(),stage=stage))
        if va.hex() in self.models:
            return next(row for row in self.rows if row['VA_hex']==va.hex())
        ensemble=make_ensemble(self.config,'Uniform',0.,va)
        identity=ensemble_hash(ensemble)
        p=ensemble.probabilities[0].numpy()
        alpha=ensemble.amplitudes[0].numpy()
        pmass=float(sum(p));energy=float(2*np.dot(p,abs(alpha)**2))
        delta=math.sqrt(3*va/255)
        raw=np.arange(16)-7.5
        expected=(delta*(raw[:,None]+1j*raw[None,:])).ravel()
        self.check(f'Uniform_ensemble_{va.hex()}',max(abs(p-1/256))==0
                   and abs(pmass-1)<1e-14 and abs(energy-va)<1e-12
                   and max(abs(alpha-expected))<1e-12)
        payload,path,origin=self.source(va,ensemble)
        self.check(f'Uniform_exact_source_{va.hex()}',payload['ensemble_hash']==identity
                   and float.fromhex(payload['nu_mb_raw_hex'])==0 and payload['support_size']==256)
        model=security(self.m1,self.mh,M(va),M(payload['C']),M(payload['w']))
        self.check(f'physical_symplectic_{va.hex()}',model['physical'])
        t,noise=float(model['eta_f']),float(model['eta_f_xi_f'])
        values=[uniform_mi_2d(p,alpha,t,noise,order) for order in (16,32,64)]
        residual=max(abs(value-values[-1]) for value in values)
        self.check(f'MI_convergence_{va.hex()}',residual<2e-13,residual)
        I=values[-1];beta_I=M('.95')*M(I);K=beta_I-model['chi_BE']
        self.check(f'noise_and_SKR_identity_{va.hex()}',
                   abs(model['eta_f_xi_f']-((self.m1-self.mh**2)*M(va)+M('.0186')*self.m1))<M('1e-60')
                   and abs(K-(beta_I-model['chi_BE']))<M('1e-60'))
        model.update(I_AB=M(I),beta_I_AB=beta_I,K=K)
        row=dict(VA=va,VA_hex=va.hex(),C=payload['C'],w=payload['w'],I_AB_2D=I,
                 beta_I_AB=float(beta_I),chi_BE=float(model['chi_BE']),K_raw=float(K),
                 eta_f=t,xi_f=float(model['xi_f']),W=float(model['W']),Z=float(model['Z']),
                 nu_1=float(model['nu_1']),nu_2=float(model['nu_2']),nu_3=float(model['nu_3']),
                 first_stage=stage,source_origin=origin,source_route=payload['source_moment_route'],
                 source_path=str(path.relative_to(ROOT)),source_sha256=sha(path),source_cache_key=payload['cache_key'],
                 ensemble_hash=identity,channel_sha256=self.channel_hash,GH_maximum_difference=residual)
        save_json(self.rows_dir/(identity+'.json'),dict(row=row,high_precision_model=converted(model,precise=True),
                    normalization=dict(probability_sum=pmass,twice_mean_photon_number=energy,
                                       amplitude_reconstruction_residual=float(max(abs(alpha-expected)))),
                    producer_sha256=sha(Path(__file__))))
        self.rows.append(row);self.models[va.hex()]=model
        for order,value in zip((16,32,64),values):
            self.convergence.append(dict(VA=va,VA_hex=va.hex(),order=order,I_AB_2D=value,
                                          difference_from_GH64=value-I))
        write_csv('all_candidates.csv',sorted(self.rows,key=lambda r:r['VA']))
        write_csv('MI_convergence.csv',self.convergence)
        save_json(OUT/'checkpoint.json',dict(status='RUNNING',completed=len(self.rows),
                      best=max(self.rows,key=lambda r:r['K_raw']),checks=self.checks,
                      next_stage=stage,producer_sha256=sha(Path(__file__))))
        print('EVALUATED VA='+repr(va)+' K='+repr(float(K))+' stage='+stage,flush=True)
        return row

    def best(self):
        return max(self.rows,key=lambda r:r['K_raw'])


def run_search(search):
    initial=[.1,.5,1.,1.5,2.,3.,4.,5.,8.,12.]
    protocol=dict(scope='Uniform-only exact-tested manuscript-style numerical optimization',
                  authorized_request_sha256=sha(OUT/'request.txt'),coarse_grid=initial,
                  historical_inventory_reused=True,fine_grid=[.025,.05,.075,.1],
                  local_refinement=dict(method='exact_grid_near_catalog_maximum',
                                        candidates=[.0475,.0525],local_spacing=.0025),
                  coarse_adaptation='All 30 historical Uniform points plus 8 and 12; concentrate new exact sources near the observed low-VA maximum',
                  global_optimality_certificate=False,
                  reference='fixed MB point only; no MB source/evaluation/optimization',
                  source_method='full-support C4 Gram; exact diagonal-system solve; ladder 1050/1250/1450',
                  coarse_source_concurrency=2,fixed_refinement_source_concurrency=2,per_source_wall_limit_seconds=3720,
                  MI='same normalized2D Gaussian/tensor GH16/32/64; exact Cartesian mixture factorization',
                  beta=.95,xi_ch=.0186,R=1,xi_det=0,VA_normalization='VA=2*nbar',
                  historical_frozen_hash_conflict='preserved; diagnostic only',
                  lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    save_json(OUT/'search_protocol.json',protocol)
    for key in sorted(search.inventory,key=float.fromhex):
        search.evaluate(float.fromhex(key),'historical_inventory')
    missing=[v for v in initial if v.hex() not in search.inventory]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda v:search.source(v,make_ensemble(search.config,'Uniform',0.,v)),missing))
    for va in initial:
        search.evaluate(va,'adaptive_coarse_through_12')
    # The inherited lower-VA catalog resolves the apparent 0.1 coarse boundary.
    b=search.best()['VA']
    if b>=12 or b<=.02:
        raise RuntimeError('Boundary requires an explicitly recorded domain extension')
    if not .025<=b<=.075:
        raise RuntimeError('Observed best lies outside the prospectively recorded local region')
    refinement=list(dict.fromkeys(protocol['fine_grid']+protocol['local_refinement']['candidates']))
    missing_refinement=[v for v in refinement if v.hex() not in search.models]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda v:search.source(v,make_ensemble(search.config,'Uniform',0.,v)),missing_refinement))
    for va in protocol['fine_grid']:
        search.evaluate(va,'fine_grid_0p025')
    for va in protocol['local_refinement']['candidates']:
        search.evaluate(va,'exact_finer_grid_0p0025')
    save_json(OUT/'local_optimizer.json',dict(status='EXACT_TESTED_GRID_REFINEMENT_COMPLETE',
               finest_sample_spacing=.0025,best=search.best(),continuous_global_optimum_certified=False))
    save_json(OUT/'evaluation_calls.json',search.calls)


def finalize(search):
    best=search.best();model=search.models[best['VA_hex']]
    ensemble=make_ensemble(search.config,'Uniform',0.,best['VA'])
    p,alpha=ensemble.probabilities[0].numpy(),ensemble.amplitudes[0].numpy()
    comparisons=[]
    for order in (16,32,64):
        direct=mi_gh(p,alpha,best['eta_f'],float(model['eta_f_xi_f']),order,dimension=2)
        factored=uniform_mi_2d(p,alpha,best['eta_f'],float(model['eta_f_xi_f']),order)
        search.check(f'original_MB_tensor_2D_kernel_GH{order}',abs(direct-factored)<2e-13,direct-factored)
        comparisons.append(dict(order=order,original_MB_tensor_2D=direct,exact_product_tensor_2D=factored,
                                residual=direct-factored))
        print('DIRECT_2D_KERNEL_CHECK GH'+str(order)+' residual='+str(direct-factored),flush=True)
    write_csv('same_MB_MI_kernel_check.csv',comparisons)
    mp.mp.dps=110
    high=security(search.m1,search.mh,M(best['VA']),M(best['C']),M(best['w']))
    search.check('best_Holevo_precision_80_to_110_dps',abs(high['chi_BE']-model['chi_BE'])<M('1e-65'))
    mb=search.mb['model']
    comparison=[dict(scheme='Uniform_best_exact_tested',nu_raw=0.,VA=best['VA'],
                     I_AB_2D=best['I_AB_2D'],chi_BE=best['chi_BE'],K_raw=best['K_raw']),
                dict(scheme='MB_fixed_reference',nu_raw=.165,VA=5.475,
                     I_AB_2D=mb['I_AB'],chi_BE=mb['chi_BE'],K_raw=mb['K'])]
    write_csv('Uniform_MB_comparison.csv',comparison)
    gap=mb['K']-best['K_raw']
    rows=sorted(search.rows,key=lambda r:r['VA'])
    save_json(OUT/'summary.json',dict(status='CURRENTLY_VERIFIED_PASS',scope='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
                  best=best,best_high_precision=converted(model,precise=True),
                  all_candidates=len(rows),historical_candidates=len(search.inventory),
                  fresh_sources=len(list((OUT/'exact_source_cache').glob('*.json'))),
                  explored_domain=[rows[0]['VA'],rows[-1]['VA']],
                  positive_Uniform_candidates=sum(r['K_raw']>0 for r in rows),
                  MB_minus_Uniform=gap,percentage_improvement=None if best['K_raw']<=0 else 100*gap/best['K_raw'],
                  MI_convergence_max=max(r['GH_maximum_difference'] for r in rows),checks=search.checks,
                  source_interpolation=False,SKR_interpolation=False,MB_optimized=False,
                  channel_changed=False,production_evaluator_changed=False,negative_SKR_clipped=False,
                  global_optimality_certified=False,security_status='UNVALIDATED_SECURITY_MODEL',
                  lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
                  producer_sha256=sha(Path(__file__)),MB_result_sha256=sha(MB_DIR/'result.json')))
    plot_results(rows,comparison)
    write_report(rows,best,model,comparison,gap,search)


def plot_results(rows,comparison):
    plt.rcParams.update({'font.family':'serif','font.size':9,'axes.labelsize':9,
                         'legend.fontsize':8,'savefig.dpi':350,'pdf.fonttype':42})
    x=np.array([r['VA'] for r in rows]);k=np.array([r['K_raw'] for r in rows]);best=max(rows,key=lambda r:r['K_raw'])
    def export(fig,name):
        fig.tight_layout()
        fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
        fig.savefig(OUT/(name+'.png'),dpi=350,bbox_inches='tight')
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(4.1,2.8))
    ax.plot(x,k,'o-',ms=2.4,lw=.8,color='tab:blue',label='Uniform exact-tested')
    ax.scatter([best['VA']],[best['K_raw']],marker='*',s=80,color='tab:red',label='Best tested',zorder=5)
    ax.axhline(0,color='black',lw=.7);ax.set(xlabel=r'$V_A$ (SNU)',ylabel='Raw SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.grid(alpha=.25);ax.legend()
    export(fig,'uniform_SKR_vs_VA')
    fig,ax=plt.subplots(figsize=(4.1,2.8))
    for key,label,color in [('I_AB_2D',r'$I_{AB}^{2D}$','tab:blue'),('beta_I_AB',r'$\beta I_{AB}^{2D}$','tab:green'),('chi_BE',r'$\chi_{BE}$','tab:red')]:
        ax.plot(x,[r[key] for r in rows],'.-',ms=2.5,lw=.8,label=label,color=color)
    ax.axhline(0,color='black',lw=.7);ax.set(xlabel=r'$V_A$ (SNU)',ylabel='Information (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.grid(alpha=.25);ax.legend()
    export(fig,'uniform_MI_Holevo_vs_VA')
    fig,ax=plt.subplots(figsize=(4.1,2.8))
    values=[r['K_raw'] for r in comparison]
    ax.bar(['Uniform\nbest tested','MB\nfixed reference'],values,color=['tab:blue','tab:orange'],width=.5)
    ax.axhline(0,color='black',lw=.8);ax.set_ylabel('Raw SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.grid(axis='y',alpha=.25)
    export(fig,'uniform_vs_fixed_MB')
    fig,ax=plt.subplots(figsize=(4.1,2.8))
    local=[r for r in rows if .02<=r['VA']<=.1]
    ax.plot([r['VA'] for r in local],[r['K_raw'] for r in local],'o-',ms=2.5,lw=.8)
    ax.axhline(0,color='black',lw=.7);ax.set(xlabel=r'$V_A$ (SNU)',ylabel='Raw SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3));ax.grid(alpha=.25)
    export(fig,'uniform_SKR_local_refinement')


def write_report(rows,best,model,comparison,gap,search):
    table='\n'.join('| '+ ' | '.join(f'{r[k]:.15g}' for k in ('VA','C','w','I_AB_2D','beta_I_AB','chi_BE','K_raw'))+' |' for r in rows)
    params='\n'.join(f'| `{k}` | {mp.nstr(model[k],24)} |' for k in ('C','w','eta_f','xi_f','W','Z','nu_1','nu_2','nu_3','I_AB','beta_I_AB','chi_BE','K'))
    cf='\n'.join(f'| {r["scheme"]} | {r["nu_raw"]} | {r["VA"]:.15g} | {r["I_AB_2D"]:.15g} | {r["chi_BE"]:.15g} | {r["K_raw"]:.15g} |' for r in comparison)
    text=f'''# Tối ưu số Uniform 256-QAM theo phép tính manuscript 2D

Ngày 2026-10-19; yêu cầu 6b0f6694. Kết quả: **{'có' if best['K_raw']>0 else 'không có'} SKR Uniform dương trong {len(rows)} điểm exact đã kiểm tra**.
Điểm tốt nhất đã tính trực tiếp: `VA={best['VA']:.17g}`, `K={best['K_raw']:.17g}` bits/use.
Nhãn kết luận: `BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY`; không có chứng chỉ cực đại toàn cục trên mọi VA>0.

## Quy ước cố định và nguồn

Giữ đúng kênh MB recheck: HAP20km/UAV1km, zenith30deg, L21.9393102292km
(làm tròn), lambda1550nm, divergence full-angle233urad, Dr.08m, jitter15.61urad,
sigma_o1.5mrad/FOV6.25mrad, tau_zen.92, wind21m/s, sigma_h1m, rho0, F0infinity,
HV Cn2ground1e-14. Channel được tính đúng một lần, đối chiếu MB ở độ chính xác
cao trước khi tối ưu; số đầy đủ lưu channel_once.json. mean_eta={float(search.m1):.17g},
eta_f={float(search.mh**2):.17g}. Kênh không phụ thuộc VA; cùng channel hash cho mọi ứng viên.

Theo yêu cầu mới, thống nhất `VA=2*nbar`, `p=1/256`, `nu=0`,
`Delta=sqrt(3*VA/255)`; kiểm tra tổng xác suất và năng lượng mỗi ensemble.
Ghi nhận PDF in VA=nbar/2 là mâu thuẫn đã được user chỉ định cách xử lý cho
so sánh này. Không dùng C,w của MB cho Uniform. Kiểm tra identity binary64,
ensemble hash, source implementation/settings và support256 cho từng source.
Tái sử dụng {len(search.inventory)} nguồn Uniform cũ đã xác thực; nguồn mới lưu riêng.

Nguồn mới dùng full-support C4 coherent Gram của repository,
không có finite Fock cutoff và không threshold bỏ support. AP dùng ladder
1050/1250/1450, hai bậc cuối phải có đủ256 mode và đáp ứng tiêu chuẩn hội tụ
đã có. Source receipt lưu toàn bộ rows hội tụ và gate. gmpy2 được cài riêng
trong thư mục tạm và chỉ đưa vào PYTHONPATH của source child để tăng tốc
mpmath; không sửa .venv, code nguồn hay cache cũ. Phép giải hệ chéo trong
worker được thay riêng bằng phép chia từng hàng tương đương đại số; không
đổi eigensolver, công thức, support hoặc precision. Kiểm tra LU/chia hàng
50/1050dps và đối chiếu source đầy đủ được lưu riêng. Version/backend được ghi
trong từng source receipt. PDF không chỉ định Nmax; không tuyên bố đã kiểm
chứng một cutoff hữu hạn không được nêu.

## MI, Holevo và thuật toán tìm kiếm

Giữ Gaussian2D chuẩn hóa `1/(2*pi*sigma_zeta^2)`, mean `2*sqrt(eta_f)*alpha`,
variance **mỗi component** `sigma_zeta^2=1+eta_f*xi_f`. Log-sum-exp dùng cho
mixture. PMF Uniform Cartesian cho phép factor chính xác mixture thành hai
marginal; code vẫn tổng quadrature tensor trên cả hai component của log-ratio2D.
Không thay bằng MI homodyne1D, không đặt1/2 và không dùng correction heterodyne.
Đối chiếu riêng với chính mi_gh tensor256-symbol của MB ở GH16/32/64 tại điểm
tốt nhất, residual lưu same_MB_MI_kernel_check.csv.

Noise `N=(mean_eta-eta_f)*VA+.0186*mean_eta`; R1/xi_det0, beta.95.
Không cộng pure loss hay detector noise vào xi_n. Holevo dùng nguyên
`Z=2*sqrt(eta_f)*C-sqrt(2*N*w)`, `V=1+VA`, `W=1+eta_f*VA+N` và
**nu3=sqrt(V*(V-Z^2/W))**. Entropy chỉ tính khi eigenvalue hợp lệ;
raw K=.95I-chi, không clip.

Khảo sát toàn bộ30 nguồn cũ (0.02 đến5), thêm coarse points8/12 và dùng
fine grid .025,.05,.075,.1 vì vùng tốt nhất nằm dưới .1. Từ bracket cũ
.04/.05/.06, tính thêm exact .0475/.0525 với khoảng cách nhỏ nhất .0025.
Grid .5 đều từ .1 đến12 trong task là gợi ý, không bắt buộc; coarse grid
được thích nghi để tái sử dụng tất cả nguồn cũ và tập trung nguồn mới gần
vùng hứa hẹn. Không nội suy source/MI/Holevo/SKR. Toàn bộ lời gọi và
grid-refinement receipt được lưu; không gọi đây là optimizer hội tụ toàn cục.
Miền đã khảo sát
`[{rows[0]['VA']},{rows[-1]['VA']}]`; ngoài miền này chưa có chứng chỉ.

## Bảng toàn bộ ứng viên

| VA | C | w | I_AB 2D | beta I_AB | chi_BE | K raw |
|---:|---:|---:|---:|---:|---:|---:|
{table}

## Điểm tốt nhất đã kiểm tra

`VA={best['VA']:.17g}`, `nu=0`.

| Đại lượng | Giá trị |
|---|---:|
{params}

## So sánh với MB cố định

| Scheme | nu_raw | VA | I_AB 2D | chi_BE | K raw |
|---|---:|---:|---:|---:|---:|
{cf}

`Delta K=K_MB-K_Uniform={gap:.17g}` bits/use. {'Không tính phần trăm vì Uniform raw SKR không dương.' if best['K_raw']<=0 else 'Phần trăm cải thiện được lưu trong summary.json.'}
MB là điểm tham chiếu cố định, không tối ưu hoặc tạo source MB.

## Kiểm tra và hiện vật

Tất cả ứng viên có GH16/32/64; max difference
`{max(r['GH_maximum_difference'] for r in rows):.6g}` bits/use. Điểm tốt nhất
được kiểm tra thêm entropy80/110dps. Xác thực PMF, normalization, source identity,
channel equality, eigenvalue, noise/SKR identity, không nội suy hoặc nhầm
source MB được lưu trong summary.json. Chỉ số PASS là kiểm tra số học trong
phạm vi này, không phải security proof.

Kết quả lưu results/uniform_manuscript_2d_optimization_20261019/:
all_candidates.csv, MI_convergence.csv, source/convergence receipts,
candidate_records, summary.json, search_protocol.json, local_optimizer.json,
Uniform_MB_comparison.csv, channel_once.json, integrity receipt và bốn hình
PNG350dpi/vectorPDF (ba hình được yêu cầu và một hình phóng vùng refine).
Đường nối hình chỉ để dẫn mắt; tất cả điểm là đánh giá exact, có giữ raw âm
và đường K=0. Không suy ra sign/cực đại giữa các điểm từ đường vẽ.

Production evaluator, công thức khoa học đang dùng, optical config, old source
caches/MB artifacts/frozen spec không đổi. Frozen historical hash discrepancy
được giữ nguyên. Không baseline/threshold certification, training/test-data/
final-test/held-out/publication evaluation, ObjectiveC restart, external edit,
commit hoặc push. Giữ UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

**Trả lời:** Trong các ứng viên đã tính trực tiếp tại L21.9393102292km,
Uniform {'đạt' if best['K_raw']>0 else 'không đạt'} SKR dương theo manuscript-style2D với noise đã sửa;
best-tested VA={best['VA']:.17g}, raw K={best['K_raw']:.17g},
chênh so với MB={gap:.17g} bits/use. Chưa chứng minh kết luận cho mọi VA>0;
tổ hợp MI2D/Holevo homodyne vẫn là phép so sánh số được yêu cầu.
'''
    REPORT.write_text(text,encoding='utf-8',newline='\n')


def main():
    if (OUT/'summary.json').exists():
        raise FileExistsError('Completed results must not be overwritten')
    search=UniformSearch()
    run_search(search)
    finalize(search)
    print('COMPLETE',json.dumps(search.best()),flush=True)


if __name__=='__main__':
    main()
