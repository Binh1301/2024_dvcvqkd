"""Bounded adapter and literal-objective checks; never calculate source moments."""
import copy
import itertools
import json

import mpmath as mp
import numpy as np
import unittest
from unittest.mock import patch

from src import manuscript_mobility as mm


def load_settings():
    return json.loads((mm.ROOT/'configs/manuscript_mobility.json').read_text())


class ManuscriptMobilityTests(unittest.TestCase):
    def test_config_geometry_and_exact_grouping(self):
        settings = load_settings()
        assert mm.validate_config(settings).shape == (100, 2)
        positions, geometries = mm.geometry_table(settings)
        assert len(positions) == 100 and len(geometries) == 60
        assert [g['geometry_id'] for g in geometries] == [f'g{i:03d}' for i in range(60)]
        for row in positions:
            rep = next(g for g in geometries if g['geometry_id'] == row['geometry_id'])
            assert (row['horizontal_squared_hex'], row['zenith_hex'], row['distance_km']) == (rep['horizontal_squared_hex'], rep['zenith_hex'], rep['distance_km'])
        for section, key, value in [('optical','receiver_diameter_m',.55), ('security','R',2), ('numerical','GH_orders',[32,64]), ('mission','slots',29), ('cloud','probability',.5), ('optimization','deployment_cost_included',True)]:
            bad = copy.deepcopy(settings); bad[section][key] = value
            with self.assertRaises(ValueError): mm.validate_config(bad)


    def test_raw_winner_negative_ties_and_invalid(self):
        rows = [dict(K_raw=-.2, nu_raw=.2, VA=2., ensemble_hash='b'), dict(K_raw=-.1, nu_raw=.3, VA=1., ensemble_hash='a'), dict(K_raw=-.1, nu_raw=.2, VA=2., ensemble_hash='c')]
        assert mm.select_winner(rows) is rows[-1]
        for rows_bad in [[], [dict(rows[0],K_raw=float('nan'))], [dict(rows[0],VA=0)]]:
            with self.assertRaises(ValueError): mm.select_winner(rows_bad)


    def test_catalog_and_frozen_reference(self):
        settings = load_settings()
        catalog = mm.load_catalog(settings)
        assert len(catalog) == 233
        assert sum(c['family']=='MB' for c in catalog) == 197
        assert len({c['ensemble_hash'] for c in catalog}) == 233
        fixed = next(c for c in catalog if c['family']=='MB' and c['nu_raw']==.165 and c['VA']==5.475)
        mp.mp.dps = 80
        ch = mm.channel_at_angle(30.)
        row, model = mm.evaluate_source(fixed,ch)
        reference = json.loads((mm.ROOT/'results/manuscript_homodyne_noise_recheck_20261019/result.json').read_text())['model']
        for new, old in [('I_AB_2D','I_AB'),('K_raw','K'),('N','eta_f_xi_f'),('chi_BE','chi_BE')]:
            self.assertAlmostEqual(row[new],reference[old],delta=2e-13)
        uniform = next(c for c in catalog if c['family']=='Uniform' and c['VA']==.05)
        other,_ = mm.evaluate_source(uniform,ch)
        assert other['N'] != row['N']
        assert model['physical'] and row['GH_max_difference'] < 2e-13
        for section,key,value in [('MB','sha256','0'*64), ('Uniform','count',35)]:
            bad=copy.deepcopy(settings);bad['source_rosters'][section][key]=value
            with self.assertRaises(ValueError):mm.load_catalog(bad)


    def test_greedy_scaling_causal_prefix_and_graph(self):
        positions=np.array([[0.,0.],[1.,0.],[2.,0.]])
        distance=np.abs(np.arange(3)[:,None]-np.arange(3)[None,:]).astype(float)
        graph=distance<=1
        # Nt*lambda makes staying preferable: a missing Nt would move.
        assert mm.greedy_step([0,.5,10],0,distance,graph,slots=4,penalty_bits_per_use=.2,reference_distance_m=1)==0
        assert mm.greedy_step([1,1,1],None,distance,graph,slots=4,penalty_bits_per_use=0,reference_distance_m=1)==0
        S=np.array([[2,0,8,1],[0,3,0,1],[0,5,2,1]],float)
        kw=dict(slot_duration_s=1,max_speed_m_per_s=1,penalty_bits_per_use=.1,reference_distance_m=1)
        a=mm.greedy_trajectory(S,positions,**kw)
        future=S.copy();future[:,2:]=100
        b=mm.greedy_trajectory(future,positions,**kw)
        assert np.array_equal(a['path'][:2],b['path'][:2])
        assert np.all(distance[a['path'][:-1],a['path'][1:]]<=1)
        with self.assertRaises(ValueError):mm.greedy_step([-1,0,1],None,distance,graph,slots=4,penalty_bits_per_use=0,reference_distance_m=1)


    def check_dp_literal_recursion_and_exhaustive(self,speed,penalty):
        positions=np.array([[0.,0.],[1.,0.],[2.,0.]])
        S=np.array([[1,0,2,1],[0,4,0,2],[2,0,3,0]],float)
        kw=dict(slot_duration_s=1,max_speed_m_per_s=speed,penalty_bits_per_use=penalty,reference_distance_m=1)
        summaries,paths,series=mm.compare_paths(S,np.zeros_like(S,dtype=bool),positions,**kw)
        scores=[S[np.array(path),np.arange(4)].mean()-penalty*sum(abs(np.diff(path))) for path in itertools.product(range(3),repeat=4) if all(abs(np.diff(path))<=speed)]
        dp=next(r for r in summaries if r['strategy']=='DP')
        self.assertAlmostEqual(dp['objective_bits_per_use'],max(scores),delta=1e-12)
        F=S[:,0].copy()
        d=np.abs(np.arange(3)[:,None]-np.arange(3)[None,:])
        for n in range(1,4): F=S[:,n]+np.max(np.where(d<=speed,F[:,None]-4*penalty*d,-np.inf),axis=0)
        self.assertAlmostEqual(dp['objective_bits_per_use'],F.max()/4,delta=1e-12)
        assert len(series)==12 and set(paths)=={'Stationary','Greedy','DP'}


    def test_cloud_degenerate_and_single_slot(self):
        p=np.array([[0.,0.],[1.,0.]])
        kw=dict(slot_duration_s=1,max_speed_m_per_s=1,penalty_bits_per_use=.1,reference_distance_m=1)
        for S,C in [(np.zeros((2,4)),np.ones((2,4),bool)), (np.zeros((2,1)),np.zeros((2,1),bool)), (np.ones((2,4)),np.zeros((2,4),bool))]:
            summaries,_,_=mm.compare_paths(S,C,p,**kw)
            for row in summaries:
                assert row['availability']==float(np.any(S>0))
                assert row['total_distance_m']==0
        with self.assertRaises(ValueError):mm.compare_paths(np.ones((2,1)),np.ones((2,1),bool),p,**kw)
        with self.assertRaises(ValueError):mm.compare_paths(np.zeros((2,1)),np.ones((2,1)),p,**kw)
        schedule=mm.lambda_schedule(np.zeros(2),p,1)
        assert schedule['values']==[0.] and schedule['representative']==0 and schedule['lambda_hi']==0
        assert mm.lambda_schedule(np.array([1.,2.]),p,1)['lambda_hi']==4

    def test_dp(self):
        for speed,penalty in [(0,0),(1,0),(1,.2),(1,100)]:
            with self.subTest(speed=speed,penalty=penalty):
                self.check_dp_literal_recursion_and_exhaustive(speed,penalty)

    def test_catalog_rejects_wrong_payload_identity(self):
        settings=load_settings()
        real_reader=mm.read_csv
        for key, value in [('V_A','6.01'),('C','1.0'),('w','1.0'),('ensemble_hash','0'*64),('source_payload_sha256','0'*64)]:
            def altered(path):
                rows=real_reader(path)
                if 'family' in rows[0]:
                    next(row for row in rows if row['family']=='MB')[key]=value
                return rows
            with self.subTest(key=key),patch.object(mm,'read_csv',side_effect=altered):
                with self.assertRaises(ValueError): mm.load_catalog(settings)
        real_sha=mm.sha
        with patch.object(mm,'sha',side_effect=lambda p:'0'*64 if str(p).endswith('source_roster.csv') else real_sha(p)):
            with self.assertRaises(ValueError): mm.load_catalog(settings)

    def test_exact_grouping_does_not_round_distance(self):
        original=mm.link_geometry
        def changed(*args):
            distance,angle=original(*args)
            # Break a symmetry only by one representable binary64 distance.
            distance[80]=np.nextafter(distance[80],float('inf'))
            return distance,angle
        with patch.object(mm,'link_geometry',side_effect=changed):
            with self.assertRaises(ValueError): mm.geometry_table(load_settings())

    def test_greedy_has_no_future_slot_access(self):
        positions=np.array([[0.,0.],[1.,0.],[2.,0.]])
        S=np.arange(12,dtype=float).reshape(3,4)
        original=mm.greedy_step
        calls=[]
        def observed(rates_now,previous_index,*args,**kwargs):
            assert np.array_equal(rates_now,S[:,len(calls)])
            assert np.asarray(rates_now).ndim==1
            calls.append(previous_index)
            return original(rates_now,previous_index,*args,**kwargs)
        with patch.object(mm,'greedy_step',side_effect=observed):
            mm.greedy_trajectory(S,positions,slot_duration_s=1,max_speed_m_per_s=1,
                                 penalty_bits_per_use=.1,reference_distance_m=1)
        assert len(calls)==4 and calls[0] is None

    def test_invalid_graph_and_dimensions(self):
        distance=np.array([[0.,1.],[1.,0.]])
        graph=np.ones((2,2),bool)
        kw=dict(slots=4,penalty_bits_per_use=.1,reference_distance_m=1)
        for bad in [dict(slots=0),dict(slots=True),dict(penalty_bits_per_use=-1),dict(reference_distance_m=0)]:
            with self.assertRaises(ValueError):mm.greedy_step([0,1],0,distance,graph,**dict(kw,**bad))
        for bad_graph in [np.ones((2,2)),np.array([[1,0],[1,1]],bool),np.zeros((2,2),bool)]:
            with self.assertRaises(ValueError):mm.greedy_step([0,1],0,distance,bad_graph,**kw)


if __name__=='__main__': unittest.main()
