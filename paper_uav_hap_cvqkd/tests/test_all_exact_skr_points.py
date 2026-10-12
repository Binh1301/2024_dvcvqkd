"""Check relative performance classifications using only arithmetic/stored rows."""
import unittest
from unittest.mock import patch
from scripts import export_theta10_D55_all_exact_skr_points as export


class AllExactPointsTests(unittest.TestCase):
    def test_current_catalog_all_rows_and_threshold_counts(self):
        entries = export.stored.read(export.stored.INPUT / 'objective_checkpoint.json')
        ref = next(e for e in entries if e['L_km'] == export.stored.REF)
        roster = {export.stored.pair(r) for r in ref['rows']}
        self.assertEqual(len(roster), 151)
        self.assertEqual(export.missing_combinations(entries, roster), [])
        result = [export.classify(e['rows'], e['L_km']) for e in entries]
        self.assertEqual(sum(map(len, result)), 3926)
        rows = export.classify(ref['rows'], ref['L_km'])
        self.assertEqual([r['rank'] for r in rows], list(range(1,152)))
        self.assertEqual(rows[0]['SKR'], .07798099387393764)
        self.assertEqual([r['count_including_best'] for r in export.threshold_counts(rows)], [4,9,17])
        near = [r for r in rows if r['near_optimal'] == 'YES']
        self.assertEqual(max(r['delta_nu'] for r in near), .0006250000000000144)
        self.assertEqual(max(r['delta_VA'] for r in near), .025000000000000355)
        for entry, classified in zip(entries, result):
            best = max(r['SKR'] for r in entry['rows'])
            self.assertTrue(all(r['K_best'] == best for r in classified))

    def test_nonpositive_best_is_undefined_and_negative_candidates_preserved(self):
        for k in (0., -1.):
            rows = export.classify([dict(nu_raw=.165,V_A=5.5,SKR=k)], 22.)
            self.assertEqual(rows[0]['relative_loss_fraction'], '')
            self.assertEqual(rows[0]['relative_loss_percent'], '')
            self.assertEqual(rows[0]['near_optimal'], 'UNDEFINED')
            self.assertEqual(rows[0]['SKR'], k)
        rows = export.classify([dict(nu_raw=.165,V_A=5.5,SKR=1.),dict(nu_raw=.2,V_A=5.5,SKR=-1.)],22.)
        self.assertEqual(rows[1]['relative_loss_percent'],200.)
        self.assertEqual(rows[1]['SKR'],-1.)

    def test_inclusive_threshold(self):
        rows = [dict(relative_loss_status='DEFINED',relative_loss_fraction=1e-5)]
        self.assertEqual([r['count_including_best'] for r in export.threshold_counts(rows)], [0,1,1])

    def test_missing_combination_is_reported(self):
        row = dict(nu_raw=.165,V_A=5.5,SKR=1.)
        with patch.object(export.stored,'DISTANCES',[20.,21.]):
            missing=export.missing_combinations([dict(L_km=20.,rows=[row])],{export.stored.pair(row)})
        self.assertEqual(len(missing),1)
        self.assertEqual(missing[0]['L_km'],21.)
        self.assertEqual(missing[0]['status'],'MISSING')

    def test_output_cannot_be_overwritten(self):
        with patch.object(export,'OUT',export.PREVIOUS),patch.object(export.stored,'load_verified') as load:
            with self.assertRaises(SystemExit):
                export.main()
            load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
