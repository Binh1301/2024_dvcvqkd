"""Verify saved artifacts without rerunning any simulation or creating files."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.ibrahim_stationary_cloud import StationaryCloudConfig, SpectralDomain, relative_intensity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest=json.loads((OUT/"artifact_hashes.json").read_text(encoding="utf-8"))
    for path,value in manifest.items():
        assert sha(OUT/path)==value,f"artifact hash: {path}"
    protected=json.loads((OUT/"protected_inputs.json").read_text())
    for path,value in protected.items():
        assert sha(ROOT/path)==value,f"protected input: {path}"
    receipt=json.loads((OUT/"design_receipt.json").read_text(encoding="utf-8"))
    finalization=json.loads((OUT/"finalization_receipt.json").read_text(encoding="utf-8"))
    for path,value in receipt["producer_hashes"].items():
        original=OUT/finalization["initial_producer_snapshots"][path] if path in finalization["initial_producer_snapshots"] else ROOT/path
        assert sha(original)==value,f"initial producer: {path}"
        assert sha(ROOT/path)==finalization["current_producer_hashes"][path],f"current producer: {path}"
    assert sha(ROOT/"configs/ibrahim_stationary_cloud.json")==receipt["config_sha256"]
    settings=receipt["settings"]
    c=StationaryCloudConfig(**settings["simulation"])
    domain=SpectralDomain(c)
    report=json.loads((OUT/"validation.json").read_text())
    data=np.load(OUT/"cloud_fields.npz",allow_pickle=False)
    ens=np.load(OUT/"ensemble_validation.npz",allow_pickle=False)
    for name in ("metrics","temporal","eulerian","covariance_initial","covariance_final","covariance_target"):
        assert np.isfinite(ens[name]).all(),f"nonfinite ensemble array: {name}"
    assert report["status"]=="CURRENTLY_VERIFIED_PASS" and not report["failed_checks"]
    assert len(report["checks"])==67 and all(ch["passed"] for ch in report["checks"])
    assert len(ens["seeds"])>=10 and len(set(ens["seeds"]))==len(ens["seeds"])
    for name in ("X","intensity","diagnostic_mask"):
        assert data[name].shape==(c.slots,c.ny,c.nx)
        assert np.isfinite(data[name]).all()
    np.testing.assert_array_equal(data["time_s"],np.arange(c.slots)*c.dt_s)
    assert data["diagnostic_mask"].dtype==np.uint8
    meta=json.loads(str(data["metadata_json"]))
    gamma=meta["gamma_fixed"]
    assert gamma==np.quantile(data["X"][0],1-c.initial_fraction,method="linear")
    np.testing.assert_array_equal(data["diagnostic_mask"],data["X"]>gamma)
    np.testing.assert_array_equal(data["intensity"],relative_intensity(data["X"],c))
    assert (data["intensity"]>=0).all()
    np.testing.assert_allclose(data["X"].mean((1,2)),ens["metrics"][0,:,0],atol=1e-14)
    np.testing.assert_allclose(data["X"].var((1,2)),ens["metrics"][0,:,1],atol=1e-14)
    np.testing.assert_array_equal(data["diagnostic_mask"].mean((1,2)),ens["metrics"][0,:,3])
    np.testing.assert_allclose(ens["covariance_target"],domain.covariance(),atol=1e-15)
    assert abs(ens["covariance_target"][0,0]-1)<1e-14
    assert abs(report["expected_crop_population_variance"]-domain.expected_crop_variance())<1e-14
    for check in report["checks"]:
        assert abs(check["estimate"]-check["target"])<=4*check["independent_seed_se"]+1e-10
    assert domain.boundary_receipt()==report["boundary"]
    assert report["boundary"]["status"]==report["numerical"]["status"]=="CURRENTLY_VERIFIED_PASS"
    assert report["numerical"]["one_slot_x_displacement_m"]==-5
    assert report["numerical"]["eight_slot_x_displacement_m"]==-40
    assert report["numerical"]["spectral_max_covariance_error_relative_to_variance"]<1e-10
    assert report["numerical"]["packet_positive_control_peak_in_observation"]>.9
    tests=(OUT/"unit_tests.log").read_bytes()
    tests=tests.decode("utf-16" if tests.startswith(b"\xff\xfe") else "utf-8-sig")
    assert "Ran 11 tests" in tests and "OK" in tests and "FAILED (" not in tests
    exports=[]
    for path in sorted(OUT.glob("figure_*.png")):
        with Image.open(path) as image:
            assert min(image.info["dpi"])>399
            exports.append({"file":path.name,"pixels":list(image.size),"dpi":image.info["dpi"]})
    assert len(exports)==6 and len(list(OUT.glob("figure_*.pdf")))==6
    with Image.open(OUT/"cloud_1000_slots.gif") as animation:
        assert animation.n_frames==c.slots
        assert animation.info["duration"]==50
        gif_frames=animation.n_frames
        for k in (0,400,999):
            animation.seek(k)
            pixels=np.asarray(animation.convert("RGB"))[34:,200:,:]
            expected=np.repeat(np.repeat(np.flipud(data["diagnostic_mask"][k]),4,axis=0),4,axis=1)*255
            np.testing.assert_array_equal(pixels,np.repeat(expected[:,:,None],3,axis=2))
    return {"status":"CURRENTLY_VERIFIED_PASS","scope":"read-only artifact and source verification; no simulation rerun",
            "sealed_artifacts":len(manifest),"protected_existing_files":len(protected),"focused_tests":11,
            "ensemble_checks":67,"independent_seeds":len(ens["seeds"]),"gif_frames":gif_frames,"PNG_exports":exports}


if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
