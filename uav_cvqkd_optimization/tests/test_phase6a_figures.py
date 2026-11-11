import copy
from pathlib import Path
import json
import numpy as np
import pytest
from uav_qkd import phase6a_figures as f


@pytest.fixture(scope='module')
def bundle():return f.load_bundle(f.SOURCE)


def test_data_time_units_and_full_prefix_validation(bundle):
    assert bundle['dt']==10 and bundle['slots']==100
    assert f.snapshot_index(bundle,300)==30
    assert f.snapshot_index(bundle,1000)==100
    with pytest.raises(ValueError):f.snapshot_index(bundle,999)
    assert bundle['validation']['prefix_rows']==800
    for run in bundle['report']['runs']:
        a,b=run['solutions']['P1'],run['solutions']['P2']
        assert a['path_indices']==b['path_indices']
        assert a['average_skr_bits_s']==b['key_bits']/1000


def test_non_linear_saved_key_curve_and_terminal_match(bundle):
    t,key=f.key_history(bundle,'Pareto DP','P2')
    assert len(t)==101 and t[-1]==1000 and key[-1]==pytest.approx(77040.10777990881)
    assert key[50]==0 and key[80]>0
    assert not np.allclose(key,key[-1]*t/t[-1])


def test_corrupt_prefix_or_objective_is_rejected(bundle):
    bad=copy.deepcopy(bundle['report']);bad['runs'][0]['solutions']['P2']['series'][10]['key_bits']=42
    with pytest.raises(ValueError,match='prefix'):f.validate_quantities(bad,bundle['arrays'])
    bad=copy.deepcopy(bundle['report']);bad['runs'][0]['solutions']['P1']['objective_value']*=1000
    with pytest.raises(ValueError,match='objective'):f.validate_quantities(bad,bundle['arrays'])
    bad=copy.deepcopy(bundle['report']);bad['runs'][0]['solutions']['P2']['series'][0]['x_m']=1
    with pytest.raises(ValueError,match='coordinate'):f.validate_quantities(bad,bundle['arrays'])


def test_reconstructed_los_at_saved_graph_nodes(bundle):
    positions=bundle['arrays']['positions']
    masks=f.los_maps(bundle,[300,1000],positions)
    np.testing.assert_array_equal(masks,bundle['arrays']['z'][[29,99]])
    assert masks.shape==(2,121)


def test_no_sweep_means_no_fake_figure6(bundle,tmp_path):
    with pytest.raises(ValueError,match='two|budget'):f.load_energy_sweep([f.SOURCE])
    paths=list(f.ROOT.glob('results/**/sensitivities.csv'))
    assert paths
    with pytest.raises(ValueError):f.load_energy_sweep([paths[0]])


def test_plot5_and7_match_saved_terminals(bundle):
    fig5=f.plot_fig5(bundle)
    lines=fig5.axes[0].lines
    assert len(lines)==4
    for line,run in zip(lines,bundle['report']['runs']):
        assert line.get_ydata()[-1]==run['solutions']['P2']['key_bits']
    fig7=f.plot_fig7(bundle)
    for collection,run in zip(fig7.axes[0].collections,bundle['report']['runs']):
        np.testing.assert_allclose(collection.get_offsets()[0],
            [run['solutions']['P2']['energy_j']/1000,run['solutions']['P2']['key_bits']])
    f.plt.close(fig5);f.plt.close(fig7)


def test_snapshot_figure_text_does_not_collide_with_ticks(bundle):
    f.configure_style()
    fig=f.plot_fig4(bundle,np.ones((3,50,50),dtype=np.int8))
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    for text in fig.texts:
        for ax in fig.axes:
            for tick in ax.get_xticklabels():
                assert not text.get_window_extent(renderer).overlaps(tick.get_window_extent(renderer))
    f.plt.close(fig)
    fig=f.plot_fig5(bundle)
    assert fig.axes[0].get_legend().get_title().get_text()=='P2 trajectories'
    f.plt.close(fig)


def test_output_preservation(tmp_path):
    d=tmp_path/'figures';d.mkdir();(d/'old.txt').write_text('keep')
    with pytest.raises(FileExistsError):f.validate_output(d)
    with pytest.raises(ValueError):f.validate_output(f.SOURCE)


def test_future_sweep_quantities_and_nonbudget_compatibility(bundle):
    # In-memory software fixture only: never exported as a simulation result.
    higher=copy.deepcopy(bundle);higher['arrays']['budget']*=1.1
    bundles=f.validate_sweep([higher,bundle])
    fig=f.plot_fig6(bundles)
    for ax,obj in zip(fig.axes,('P1','P2')):
        for line,m in zip(ax.lines,f.METHODS):
            assert line.get_ydata()[0]==f.run_for(bundle,m)['solutions'][obj]['objective_value']
    f.plt.close(fig)
    higher['arrays']['m0']*=2
    with pytest.raises(ValueError,match='non-budget'):f.validate_sweep([bundle,higher])
