"""Saved-data and IEEE export calculations; no new source moments or full MB run."""
import copy
import unittest
import numpy as np
from src.mobility_results_package import (load_existing,cumulative_normalized,tradeoff_metrics,
    projected_cloud_footprint,boundary_audit,fading_omissions,verify_series,reconstructed_winners)
from scripts.run_mobility_skr_experiment import SCHEMES,validate_settings
from src.uav_mobility import path_intersections


class NumericalPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=load_existing()

    def test_existing_summary_reconstructed_without_hardcoding(self):
        self.assertEqual(self.data["validation"]["status"],"CURRENTLY_VERIFIED_PASS")
        for summary in self.data["summary"]:
            rates=[float(r["usable_skr"]) for r in self.data["series"] if r["scheme"]==summary["scheme"]]
            self.assertAlmostEqual(float(summary["average_skr_bits_per_use"]),np.mean(rates),places=12)

    def test_normalized_cumulative_endpoint_equals_average(self):
        rows=cumulative_normalized(self.data["series"],30)
        self.assertEqual(len(rows),4*31)
        for summary in self.data["summary"]:
            group=[r for r in rows if r["scheme"]==summary["scheme"]]
            self.assertEqual(group[0]["cumulative_normalized_skr"],0.)
            self.assertEqual(group[-1]["time_s"],600.)
            self.assertAlmostEqual(group[-1]["cumulative_normalized_skr"],float(summary["average_skr_bits_per_use"]),places=12)
            self.assertTrue(all(b["cumulative_normalized_skr"]>=a["cumulative_normalized_skr"] for a,b in zip(group,group[1:])))

    def test_cumulative_missing_slot_rejected(self):
        with self.assertRaises(ValueError):cumulative_normalized(self.data["series"][:-1],30)

    def test_cloud_projection_matches_cloud_altitude_intersections(self):
        settings=self.data["settings"];g=settings["geometry"]
        points=validate_settings(settings)
        intersections=path_intersections(points,g["hap_horizontal_m"],g["h_hap_m"],g["h_uav_m"],settings["cloud"]["altitude_m"])
        for time in (0.,180.,320.,400.,580.):
            actual=np.array(settings["cloud"]["initial_center_m"])+time*np.array(settings["cloud"]["velocity_m_per_s"])
            projected,radius=projected_cloud_footprint(settings,actual)
            expected=np.linalg.norm(intersections-actual,axis=1)<=settings["cloud"]["radius_m"]
            shown=np.linalg.norm(points-projected,axis=1)<=radius
            np.testing.assert_array_equal(expected,shown)
            self.assertNotEqual(radius,settings["cloud"]["radius_m"])

    def test_tradeoff_ratios_use_actual_summary(self):
        metric=tradeoff_metrics(self.data["summary"])
        s3,s4=self.data["summary"][2:]
        self.assertAlmostEqual(metric["S4_SKR_retained_vs_S3_percent"],100*float(s4["average_skr_bits_per_use"])/float(s3["average_skr_bits_per_use"]),places=12)
        self.assertAlmostEqual(metric["S4_flight_distance_reduction_vs_S3_percent"],100*(1-float(s4["total_flight_distance_m"])/float(s3["total_flight_distance_m"])),places=12)

    def test_summary_tampering_is_not_suppressed(self):
        summary=copy.deepcopy(self.data["summary"]);summary[2]["average_skr_bits_per_use"]="0.123"
        with self.assertRaises(ValueError):verify_series(self.data["settings"],self.data["series"],summary)

    def test_trajectory_coordinate_tampering_rejected(self):
        series=copy.deepcopy(self.data["series"]);series[-1]["x_m"]="951.0"
        with self.assertRaises(ValueError):verify_series(self.data["settings"],series,self.data["summary"])

    def test_boundary_audit_mean_matches_stationary_optimum(self):
        rows,audit=boundary_audit(self.data)
        self.assertEqual(len(rows),100)
        winner=audit["stationary_best"]
        self.assertAlmostEqual(winner["predicted_stationary_mean"],float(self.data["summary"][1]["average_skr_bits_per_use"]),places=12)
        self.assertTrue(winner["on_grid_boundary"])
        self.assertNotEqual(audit["no_cloud_counterfactual_best"]["position_index"],winner["position_index"])

    def test_omitted_noise_and_Bob_variance_identity(self):
        for row in fading_omissions(self.data):
            self.assertGreaterEqual(row["N_fading_omitted"],0.)
            self.assertAlmostEqual(row["b_full"]-row["b_adopted"],row["b_difference"],places=12)
            self.assertAlmostEqual(row["b_difference"],row["N_fading_omitted"]+row["channel_output_noise_difference"],places=12)
            self.assertGreaterEqual(row["Z_adopted"],row["Z_full_noise_algebra"])

    def test_negative_uniform_utility_and_missing_winner_fail_closed(self):
        rows=[]
        for j in range(100):
            for blocked in (False,True):
                rows.append(dict(position_index=j,blocked=blocked,nu_raw=0.,V_A=1.,C=1.,w=.1,
                    SKR=-.01 if blocked else .02,T_eff=.1,ensemble_hash="fixture",objective_key=f"{j}:{blocked}"))
        table=reconstructed_winners(rows)
        self.assertEqual(table[0][1]["SKR"],-.01)
        with self.assertRaises(ValueError):reconstructed_winners(rows[:-1])


if __name__=="__main__":unittest.main()
