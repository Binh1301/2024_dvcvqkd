"""Independent physical audit. No imports from src or production numerical helpers."""
import argparse,csv,hashlib,json,math,time
from pathlib import Path
import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import erfc,logsumexp
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/negative_skr_independent_audit_20261017'
mp.mp.dps=70
M=lambda x:mp.mpf(str(x))
TOL=1e-10


def g(x):
    x=mp.mpf(x)
    if x==0:return mp.mpf(0)
    if x<0:raise ValueError('Negative bosonic occupation; no entropy clipping')
    return ((x+1)*mp.log(x+1)-x*mp.log(x))/mp.log(2)


def omega(n):
    result=mp.zeros(2*n)
    for k in range(n):result[2*k,2*k+1]=1;result[2*k+1,2*k]=-1
    return result


def spectrum(matrix):
    raw=mp.eig(mp.j*omega(matrix.rows//2)*matrix,left=False,right=False)
    if max(abs(mp.im(x)) for x in raw)>mp.mpf('1e-55'):raise ValueError('Nonreal high-precision symplectic eigenvalue')
    values=sorted(abs(mp.re(x)) for x in raw)
    if max(abs(values[2*k]-values[2*k+1]) for k in range(len(values)//2))>mp.mpf('1e-55'):raise ValueError('Symplectic eigenvalue pairs disagree')
    return [(values[2*k]+values[2*k+1])/2 for k in range(len(values)//2)]


def entropy_spectrum(values):
    terms=[];vacuum_residuals=[]
    for value in values:
        if abs(value-1)<mp.mpf('1e-55'):
            # A vacuum symplectic mode is an exact algebraic factor, residual retained below.
            terms.append(mp.mpf(0));vacuum_residuals.append(mp.nstr(value-1,65))
        else:terms.append(g((value-1)/2))
    return terms,vacuum_residuals


def physical_model(source,m1,mh,xi,efficiency,electronic,deterministic=False):
    VA,C,w=map(M,(source['V_A'],source['C'],source['w']))
    m1,mh,xi,e,n=map(M,(m1,mh,xi,efficiency,electronic))
    t=m1 if deterministic else mh*mh
    variance=mp.mpf(0) if deterministic else m1-t
    excess=m1*xi;fading=variance*VA;noise=fading+excess
    V=1+VA;W=1+m1*VA+excess;Z=2*mp.sqrt(t)*C-mp.sqrt(2*w*noise)
    matrix=mp.matrix([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
    delta=V*V+W*W-2*Z*Z;D=(V*W-Z*Z)**2
    nu1=mp.sqrt((delta+mp.sqrt(delta*delta-4*D))/2);nu2=mp.sqrt((delta-mp.sqrt(delta*delta-4*D))/2)
    numerical=spectrum(matrix);closed=sorted([nu1,nu2])
    formula_residual=max(abs(x-y) for x,y in zip(numerical,closed))
    if formula_residual>mp.mpf('1e-55'):raise ValueError('Independent closed/matrix spectrum disagreement')
    ab_terms,vac_ab=entropy_spectrum([nu1,nu2]);Sab=sum(ab_terms)
    Wb=e*W+1-e+2*n
    if e==1 and n==0:
        conditional=[V-Z*Z/(W+1)];conditional_matrix=mp.matrix([[conditional[0],0],[0,conditional[0]]])
    else:
        if e==1:raise ValueError('Appendix finite-efficiency audit excludes singular electronic-only ancilla')
        v=1+2*n/(1-e);c=mp.sqrt(v*v-1);u,s=mp.sqrt(e),mp.sqrt(1-e)
        # Direct analytic A,F,G blocks, not the production beam/purification helpers.
        afg=mp.zeros(6);corr=mp.zeros(6,2)
        for q,sign in ((0,1),(1,-1)):
            afg[q,q]=V;afg[q+2,q+2]=(1-e)*W+e*v;afg[q+4,q+4]=v
            afg[q,q+2]=afg[q+2,q]=-s*Z*sign
            afg[q+2,q+4]=afg[q+4,q+2]=u*c*sign
            corr[q,q]=u*Z*sign;corr[q+2,q]=u*s*(v-W);corr[q+4,q]=s*c*sign
        conditional_matrix=afg-corr*corr.T/(Wb+1)
        conditional=spectrum(conditional_matrix)
    conditional_terms,vac_cond=entropy_spectrum(conditional);Sconditional=sum(conditional_terms)
    chi=Sab-Sconditional;bound=2*g((W-1)/2)
    sd=1+n+e*noise/2
    npmat=np.array(matrix.tolist(),float);npomega=np.kron(np.eye(2),[[0,1],[-1,0]])
    minimum_uncertainty=float(np.linalg.eigvalsh(npmat+1j*npomega).min())
    checks=dict(moment_order=0<=t<=m1<=1,W_identity=abs(W-(1+t*VA+noise))<mp.mpf('1e-55'),spectrum=all(x>=1-mp.mpf('1e-55') for x in [nu1,nu2]+conditional),uncertainty=minimum_uncertainty>=-TOL,holevo_physical_entropy_bound=-mp.mpf('1e-55')<=chi<=bound+mp.mpf('1e-55'))
    result=dict(m1=m1,mhalf=mh,eta_f=t,fading_variance=variance,xi_ch=xi,m_xi=excess,fading_excess_output=fading,N_eff=noise,xi_f=noise/t if t else None,C=C,w=w,V=V,W_pre=W,Z=Z,source_side_Z=2*C,Z_signal=2*mp.sqrt(t)*C,Z_penalty=mp.sqrt(2*w*noise),lambda_1=nu1,lambda_2=nu2,conditional_eigenvalues=conditional,S_AB_terms=ab_terms,S_AB=Sab,conditional_entropy_terms=conditional_terms,conditional_entropy=Sconditional,chi_BE=chi,Bob_entropy_upper=bound/2,chi_upper=bound,chi_bound_margin=bound-chi,signal_output=t*VA,source_modulation_output=m1*VA,V_B2=Wb,sigma2_complex=sd,variance_per_real_quadrature=sd/2,eta_B=e,nu_B=n,closed_matrix_spectrum_residual=formula_residual,minimum_uncertainty_eigenvalue=minimum_uncertainty,checks=checks,exact_vacuum_mode_residuals=vac_ab+vac_cond,Gamma_AB=matrix,conditional_covariance=conditional_matrix)
    if VA>0:
        nbar=VA/2;c1=mh*C;c2=mh*nbar;nB=(m1*VA+excess)/2
        denys=2*c1-2*mp.sqrt(w*(nB-c2*c2/nbar))
        result.update(nbar=nbar,Denys_c1=c1,Denys_c2=c2,Denys_nB=nB,Denys_residual_variance=nB-c2*c2/nbar,Denys_general_Z=denys,Denys_Z_mapping_residual=abs(denys-Z))
    return result


def to_json(value):
    if isinstance(value,mp.matrix):return [[float(value[i,j]) for j in range(value.cols)] for i in range(value.rows)]
    if isinstance(value,mp.mpf):return float(value)
    if isinstance(value,dict):return {k:to_json(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [to_json(v) for v in value]
    if isinstance(value,np.generic):return value.item()
    return value


def high_precision(value):
    if isinstance(value,mp.mpf):return mp.nstr(value,65)
    if isinstance(value,mp.matrix):return [[mp.nstr(value[i,j],65) for j in range(value.cols)] for i in range(value.rows)]
    if isinstance(value,dict):return {k:high_precision(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [high_precision(x) for x in value]
    return to_json(value)


def full_complex_MI(p,alpha,gain,variance,order):
    """Direct 256-state two-dimensional GH integration of likelihood ratios."""
    nodes,w=np.polynomial.hermite.hermgauss(order);z=(nodes[:,None]+1j*nodes[None,:]).reshape(-1)
    weights=(w[:,None]*w[None,:]/math.pi).reshape(-1);mu=gain*alpha;lp=np.log(p)
    total=0.
    for i in range(len(p)):
        integral=0.
        for start in range(0,len(z),128):
            noises=z[start:start+128];y=mu[i]+math.sqrt(variance)*noises
            distances=np.abs(y[:,None]-mu[None,:])**2/variance
            denominator=logsumexp(lp[None,:]-distances,axis=1)
            ratio=-np.abs(noises)**2-denominator
            integral+=float(np.dot(weights[start:start+128],ratio))
        total+=p[i]*integral
    return total/math.log(2)


def real_integral_MI(probabilities,levels,variance):
    """Independent output-noise adaptive quadrature, not an entropy-difference GH helper."""
    lp=np.log(probabilities);sd=math.sqrt(variance/2);total=0.;error=0.
    for i,p in enumerate(probabilities):
        def integrand(z):
            exponents=-.5*(z+(levels[i]-levels)/sd)**2
            ratio=-.5*z*z-logsumexp(lp+exponents)
            return math.exp(-z*z/2)/math.sqrt(2*math.pi)*ratio/math.log(2)
        value,err=quad(integrand,-12,12,epsabs=1e-12,epsrel=1e-10,limit=160)
        total+=p*value;error+=p*err
    return total,error


def independent_MI(source,t,noise,efficiency,electronic,full=False):
    p=np.asarray(source['probabilities']);alpha=np.array([complex(*z) for z in source['amplitudes']]);gain=math.sqrt(float(t)*efficiency)
    variance=1+electronic+efficiency*float(noise)/2
    real,ri=np.unique(alpha.real,return_inverse=True);imag,qi=np.unique(alpha.imag,return_inverse=True)
    grid=np.zeros((len(real),len(imag)));np.add.at(grid,(ri,qi),p)
    pr,pq=grid.sum(axis=1),grid.sum(axis=0)
    factor_error=float(np.max(np.abs(grid-pr[:,None]*pq[None,:])))
    if factor_error>1e-14:raise ValueError('Independent product-QAM factorization failed')
    if gain==0:value,error=0.,0.
    else:
        a,ea=real_integral_MI(pr,gain*real,variance);b,eb=real_integral_MI(pq,gain*imag,variance);value,error=a+b,ea+eb
    snr=gain*gain*float(np.sum(p*np.abs(alpha)**2))/variance;capacity=math.log1p(snr)/math.log(2)
    hx=float(-np.sum(p*np.log2(p)))
    if not -TOL<=value<=min(hx,capacity)+TOL:raise ValueError('Independent MI violates entropy/capacity bound')
    orders=[]
    if full:
        orders=[dict(order=o,I_AB=full_complex_MI(p,alpha,gain,variance,o)) for o in (16,32,48)]
        if abs(orders[-1]['I_AB']-orders[-2]['I_AB'])>1e-9 or abs(orders[-1]['I_AB']-value)>1e-9:raise ValueError('Independent 2D and adaptive MI disagree')
    return dict(I_AB=value,quadrature_error=error,H_X=hx,Gaussian_input_capacity_upper=capacity,SNR=snr,capacity_margin=capacity-value,PMF_factorization_residual=factor_error,full_2D_GH=orders,gaussian_surrogate_only=True)


def independent_pdf(raw,moments):
    B=raw['A0']*raw['eta_atm'];d=(raw['w_eq']/(2*raw['sigma_s']))**2
    logC1=raw['rho']**2/raw['sigma_s']**2+.5*raw['sigma_R2']*d*(1+d)
    c3=1/math.sqrt(32*raw['rho']**2*raw['sigma_s']**2/raw['w_eq']**4+2*raw['sigma_R2'])
    mu=6*raw['rho']**2/raw['w_eq']**2+.5*raw['sigma_R2']*(1+2*d)
    def log_density(y):return math.log(d/2)+logC1-d*math.log(B)+d*y+math.log(erfc(c3*(y-math.log(B)+mu)))
    def integrate(q):
        def f(y):
            x=log_density(y)+q*y
            return math.exp(x) if x>-745 else 0.
        return quad(f,-math.inf,0,epsabs=2e-13,epsrel=2e-13,limit=250)
    mass,em=integrate(0);one,e1=integrate(1);half,eh=integrate(.5)
    m1=raw['P1']*one/mass;mh=raw['P1']*half/mass
    return dict(B=B,chi_squared=d,log_C1=logC1,C3=c3,mu=mu,raw_active_retained_mass=mass,raw_total_mass=raw['P0']+raw['P1']*mass,AoA_atom=raw['P0'],physical_mass=raw['P0']+raw['P1'],independent_mean_eta=m1,independent_mean_sqrt_eta=mh,mean_eta_residual=m1-moments['mean_eta'],mean_sqrt_eta_residual=mh-moments['mean_sqrt_eta'],quadrature_error_bounds=dict(mass=em,mean_eta=e1,mean_sqrt_eta=eh),new_renormalization_applied=False,law='Independently integrates existing active-conditioned [0,1] law with unchanged AoA atom')


def source_audit(source):
    p=np.array(source['probabilities']);alpha=np.array([complex(*z) for z in source['amplitudes']]);levels=np.arange(16)-7.5;grid=(levels[:,None]+1j*levels[None,:]).reshape(-1)
    expected=np.exp(-source['nu_raw']*np.abs(grid)**2);expected/=expected.sum()
    expected_alpha=grid*math.sqrt(source['V_A']/(2*np.dot(expected,np.abs(grid)**2)))
    # Compare the actual label ordering as well as normalization and energy.
    return dict(probability_sum=float(p.sum()),minimum_probability=float(p.min()),normalization_residual=float(p.sum()-1),energy=2*float(np.dot(p,np.abs(alpha)**2)),energy_residual=2*float(np.dot(p,np.abs(alpha)**2))-source['V_A'],mean_amplitude=[float(np.dot(p,alpha).real),float(np.dot(p,alpha).imag)],PMF_reconstruction_residual=float(np.max(np.abs(p-expected))),amplitude_reconstruction_residual=float(np.max(np.abs(alpha-expected_alpha))),H_X=float(-np.dot(p,np.log2(p))),source_payload_sha256=source['source_payload_sha256'],ensemble_hash=source['ensemble_hash'],C=source['C'],w=source['w'],Cw_new_oracle_run=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();out=args.output
    if (out/'independent_audit.json').exists():raise RuntimeError('Completed independent audit is immutable')
    inputs=json.loads((out/'audit_inputs.json').read_text(encoding='utf-8'));probe=json.loads((out/'production_probe.json').read_text(encoding='utf-8'))
    results=[];high=[];checks=[];comparisons=[];failures=[];start=time.perf_counter()
    def check(name,condition,detail=None):
        row=dict(check=name,status='CURRENTLY_VERIFIED_PASS' if condition else 'FAIL',detail=detail);checks.append(row)
        if not condition:failures.append(row)
    pmf=[source_audit(x) for x in inputs['sources']]
    for i,a in enumerate(pmf):check('source_'+str(i),abs(a['energy_residual'])<1e-12 and abs(a['normalization_residual'])<1e-12 and a['PMF_reconstruction_residual']<1e-13 and a['amplitude_reconstruction_residual']<1e-12,a)
    pdf=independent_pdf(inputs['reference_state']['clear_raw_channel'],inputs['reference_state']['moments'])
    check('independent_PDF_moments',max(abs(pdf[k]) for k in ('mean_eta_residual','mean_sqrt_eta_residual'))<1e-10,pdf)
    for entry in probe['results']:
        sid,label,det=entry['source_id'],entry['case'],entry['detector'];source=inputs['sources'][sid];receiver=inputs[det]
        if label=='reference_fading':
            mm=inputs['reference_state']['moments'];m1,mh,xi=mm['mean_eta'],mm['mean_sqrt_eta'],mm['xi_ch'];constant=False
        else:
            t=.25 if label.startswith('pure_loss') else float(label.split('fixed_channel_')[1]);m1,mh=t,math.sqrt(t);xi=0. if label.startswith('pure_loss') else inputs['reference_state']['moments']['xi_ch'];constant=True
        model=physical_model(source,m1,mh,xi,receiver['eta_B'],receiver['nu_B'],constant)
        mi=independent_MI(source,model['eta_f'],model['N_eff'],receiver['eta_B'],receiver['nu_B'],full=label=='reference_fading')
        model.update(mi);model['beta_I_AB']=M(inputs['beta_rec'])*M(mi['I_AB']);model['K_raw']=model['beta_I_AB']-model['chi_BE']
        meta=dict(source_id=sid,case=label,detector=det)
        for name,status in model['checks'].items():check('_'.join(map(str,(sid,label,det,name))),bool(status))
        production=entry['result'];residuals={}
        mapping={'m1':'mean_eta','mhalf':'mean_sqrt_eta','eta_f':'T_eff','W_pre':'W_pre','Z':'Z_star','xi_f':'xi_eff','chi_BE':'chi_BE','I_AB':'I_AB','K_raw':'K_raw'}
        for k,v in mapping.items():
            if model[k] is not None:residuals[k]=float(model[k])-production[v]
        check('_'.join(map(str,(sid,label,det,'production_comparison'))),max(abs(v) for v in residuals.values())<1e-9,residuals)
        comparisons.append(dict(meta,residuals=residuals));results.append(dict(meta,**to_json(model)));high.append(dict(meta,**high_precision(model)))
        print('AUDITED',sid,label,det,'CHI',float(model['chi_BE']),'BOUND',float(model['chi_upper']),flush=True)
    # Exact coherent vacuum boundary, separately for zero and nonzero channel excess.
    vacuum=dict(V_A=0.,C=0.,w=0.)
    vacuum_cases=[]
    for xi in (0.,inputs['reference_state']['moments']['xi_ch']):
        for name in ('primary_detector','trusted_detector'):
            receiver=inputs[name];m=physical_model(vacuum,.25,.5,xi,receiver['eta_B'],receiver['nu_B'],True)
            check('coherent_vacuum_'+str(xi)+'_'+name,all(m['checks'].values()))
            vacuum_cases.append(dict(detector=name,xi_ch=xi,I_AB=0.,K_raw=-float(m['chi_BE']),**to_json(m)))
    modulation=[];source=inputs['sources'][0]
    for VA in (1e-2,1e-4,1e-8,0.):
        scaled=dict(source,V_A=VA,amplitudes=(np.array(source['amplitudes'])*math.sqrt(VA/source['V_A'])).tolist())
        for name in ('primary_detector','trusted_detector'):
            receiver=inputs[name];mm=inputs['reference_state']['moments'];noise=(mm['mean_eta']-mm['mean_sqrt_eta']**2)*VA+mm['mean_eta']*mm['xi_ch']
            mi=independent_MI(scaled,mm['mean_sqrt_eta']**2,noise,receiver['eta_B'],receiver['nu_B'])
            modulation.append(dict(V_A=VA,detector=name,scope='MI-only source-amplitude limit; no Cw interpolation or new exact-source claim',**mi))
    for name in ('primary_detector','trusted_detector'):
        seq=[r['I_AB'] for r in modulation if r['detector']==name];check('no_modulation_MI_limit_'+name,all(a>=b-TOL for a,b in zip(seq,seq[1:])) and seq[-1]==0.)
    result=dict(status='CURRENTLY_VERIFIED_PASS' if not failures else 'FAILED',security_status='UNVALIDATED_SECURITY_MODEL',mathematical_scope='Physical entropy bound and covariance/detection identities under stated model assumptions',production_code_edited=False,full_P1_P3_run=False,checks=len(checks),failures=failures,MP_digits=mp.mp.dps,physical_entropy_bound_failures=sum(x['status']=='FAIL' and 'holevo_physical_entropy_bound' in x['check'] for x in checks),independent_imports_exclude_production_helpers=True,elapsed_seconds=time.perf_counter()-start,source_audits=pmf,independent_pdf=pdf,results=results,vacuum_cases=vacuum_cases,no_modulation_MI=modulation,production_comparisons=comparisons,checks_table=checks)
    (out/'independent_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');(out/'high_precision_decomposition.json').write_text(json.dumps(high,indent=2)+'\n',encoding='utf-8')
    fields=('source_id','case','detector','m1','mhalf','eta_f','fading_variance','xi_ch','m_xi','fading_excess_output','N_eff','xi_f','C','w','V','W_pre','Z','lambda_1','lambda_2','S_AB','conditional_entropy','chi_BE','Bob_entropy_upper','chi_upper','chi_bound_margin','I_AB','beta_I_AB','K_raw','Gaussian_input_capacity_upper')
    with (out/'independent_results.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in results)
    with (out/'checks.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=('check','status','detail'));writer.writeheader();writer.writerows(checks)
    print('INDEPENDENT_AUDIT',result['status'],'CHECKS',len(checks),'FAILURES',len(failures),flush=True)

if __name__=='__main__':main()
