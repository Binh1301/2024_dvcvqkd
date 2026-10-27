"""Original-height geometry/noise boundary and clearly uncalibrated height comparisons."""
from scipy.optimize import brentq
import search as s


def refresh_original_detector_source(selection):
    """Use the winner of the final same-channel catalog for the negative gap."""
    import csv
    old=selection['recommendations'][0];par=s.parameters(old)
    local=[r for r in s.ROWS if s.parameters(r)==par]
    best=max(local,key=lambda r:r['K_raw'])
    if best['ensemble_hash']==old['ensemble_hash']:return selection
    s.save('selection_phase2.json',selection)
    c=s.source(best);label=old['configuration']
    coarse=s.evaluate(c,par,'A_final_catalog_winner',256,32)
    fine=s.evaluate(c,par,'A_final_catalog_winner',512,48);delta=abs(fine['I_AB']-coarse['I_AB'])
    assert delta<2e-6
    selection['recommendations'][0]={**fine,'configuration':label,'observed_MI_change':delta}
    def load(name):
        with (s.OUT/name).open() as f:return list(csv.DictReader(f))
    robust=[r for r in load('robustness.csv') if r['configuration']!=label]
    for fa in [.8,.9,1.,1.1,1.2]:
        for fh in [.8,.9,1.,1.1,1.2]:
            p=list(par);p[4]*=fa;p[5]*=fh
            robust.append({**s.evaluate(c,p,'A_final_catalog_robustness',256,32),'configuration':label,'angular_factor':fa,'horizontal_factor':fh})
    weather=[r for r in load('weather_sensitivity.csv') if r['configuration']!=label]
    for vis,tau in [(23,.92),(15,.89),(5,.75)]:
        p=list(par);p[8]=tau
        weather.append({**s.evaluate(c,p,'A_final_catalog_weather',512,48),'configuration':label,'visibility_km':vis})
    curves=[r for r in load('figure_data.csv') if r['configuration']!=label]
    for axis,name,values in [(2,'zenith',[0.,5.,10.,15.,20.,25.,30.]),(6,'efficiency',[.8,.85,.9,.95,.98,1.]),
        (7,'noise',[.0135,.01,.005,.002,.001,.0005,0.]),(3,'divergence',s.DIV),(4,'pointing',s.JT)]:
        for value in values:
            p=list(par);p[axis]=value
            curves.append({**s.evaluate(c,p,'A_final_catalog_figure_'+name,256,32),'configuration':label,'figure':name})
    convergence=[r for r in s.read(s.OUT/'convergence.json') if r['configuration']!=label]
    convergence.append(dict(configuration=label,orders=[[256,32],[512,48]],observed_MI_change=delta,K_after_2changes=fine['K_raw']-2*.95*delta))
    s.write('robustness.csv',robust);s.write('weather_sensitivity.csv',weather);s.write('figure_data.csv',curves)
    s.save('convergence.json',convergence);s.save('selection.json',selection)
    s.write('table_4_SKR_decomposition.csv',[selection['baseline']]+selection['recommendations'])
    return selection


def main():
    if (s.OUT/'geometry_boundary.json').exists():raise FileExistsError('Preserve completed extension')
    selection=s.read(s.OUT/'selection.json');phase1=s.read(s.OUT/'phase1.json');s.initialize()
    selection=refresh_original_detector_source(selection)
    conditional=[]
    for index in [4,5]:
        row=phase1['B_catalog_best'][index];par=list(s.parameters(row));par[7]=.001
        best=s.catalog(tuple(par),'height_changed_detector_'+str(index));conditional.append(best)
    B=next(r for r in selection['recommendations'] if r['configuration']=='B_detector_assisted')
    c=s.source(B);par=s.parameters(B);grid=[];roots=[];statuses=[]
    for angle in [0.,5.,10.,15.,20.,25.,30.]:
        for noise in [0.,.0005,.001,.002,.005,.010,.0135]:
            p=list(par);p[2]=angle;p[7]=noise
            grid.append(s.evaluate(c,p,'geometry_noise_figure',256,32))
        def objective(noise):
            p=list(par);p[2]=angle;p[7]=noise
            return s.evaluate(c,p,'geometry_noise_boundary',256,32)['K_raw']
        lo,hi=objective(0.),objective(.0135)
        if lo*hi<0:
            root=brentq(objective,0.,.0135,xtol=1e-10)
            p=list(par);p[2]=angle;p[7]=root
            node=s.evaluate(c,p,'geometry_noise_boundary',256,32)
            roots.append(dict(zenith_deg=angle,L_km=node['L_km'],epsilon_det_crit=root,K_residual=node['K_raw'],source_hash=c['ensemble_hash'],scope='EXACT_NODE_ROOT_FIXED_SOURCE_AND_OPTICS_ORIGINAL_HEIGHTS'))
        else:statuses.append(dict(zenith_deg=angle,K_at_zero_noise=lo,K_at_original_noise=hi,status='NO_SIGN_CHANGE'))
    worst=[];divergence_roots=[]
    import csv
    with (s.OUT/'robustness.csv').open() as f:robust=list(csv.DictReader(f))
    matched=[]
    for r in selection['recommendations']:
        label=r['configuration'];par=s.parameters(r);c=s.source(r)
        stress=min((x for x in robust if x['configuration']==label),key=lambda x:float(x['K_raw']))
        p=tuple(float(stress[k]) for k in s.FIELDS)
        fine=s.evaluate(c,p,'worst_robustness_fine',512,48)
        assert abs(fine['I_AB']-float(stress['I_AB']))<2e-6
        worst.append({**fine,'configuration':label,'observed_MI_change_from_256':abs(fine['I_AB']-float(stress['I_AB']))})
        local=[x for x in s.ROWS if s.parameters(x)==par]
        common={x['VA'] for x in local if x['family']=='Uniform'}&{x['VA'] for x in local if x['family']=='MB'}
        va=min(common,key=lambda v:abs(v-r['VA']))
        uni=max((x for x in local if x['family']=='Uniform' and x['VA']==va),key=lambda x:x['K_raw'])
        mb=max((x for x in local if x['family']=='MB' and x['VA']==va),key=lambda x:x['K_raw'])
        matched.append(dict(configuration=label,VA=va,Uniform_K=uni['K_raw'],MB_K=mb['K_raw'],delta_K_same_VA=mb['K_raw']-uni['K_raw'],nu_raw=mb['nu_raw'],Uniform_hash=uni['ensemble_hash'],MB_hash=mb['ensemble_hash']))
        if r['K_raw']>0:
            for target in [0.,1e-4]:
                def divergence_objective(div):
                    p=list(par);p[3]=div
                    return s.evaluate(c,p,'divergence_threshold',256,32)['K_raw']-target
                if divergence_objective(par[3])*divergence_objective(233.)<0:
                    root=brentq(divergence_objective,par[3],233.,xtol=1e-8)
                    divergence_roots.append(dict(configuration=label,variable='divergence_urad',target_K=target,root=root,residual=divergence_objective(root),source_hash=c['ensemble_hash'],scope='FIXED_SOURCE_OTHERS_FIXED_NOT_GLOBAL'))
    s.write('height_changed_detector_comparisons.csv',conditional)
    s.write('geometry_detector_grid.csv',grid);s.write('geometry_detector_roots.csv',roots)
    s.write('geometry_detector_root_status.csv',statuses);s.write('robustness_worst_fine.csv',worst)
    s.write('divergence_thresholds.csv',divergence_roots)
    s.write('same_energy_shaping.csv',matched);s.write('all_evaluations.csv',s.ROWS)
    s.save('geometry_boundary.json',dict(status='CURRENTLY_VERIFIED_PASS',geometry_noise_grid_nodes=len(grid),noise_roots=len(roots),conditional_height_contexts=len(conditional),source_hash=B['ensemble_hash'],no_altitude_threshold_certification=True))
    print('GEOMETRY EXTENSION COMPLETE',len(s.ROWS),flush=True)


if __name__=='__main__':main()
