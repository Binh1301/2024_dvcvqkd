import csv
import json
import unittest
import numpy as np
from src.eq14_cloud_diagnostic import Eq14Diagnostic,BatchedEq14,catalog_maximum,ROOT


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=Eq14Diagnostic();cls.context=cls.model.context(0.)
        cls.batch=BatchedEq14(cls.model.sources)

    def test_saved_clear_winner_replayed(self):
        r=catalog_maximum(self.model,self.batch,self.context,0.)
        self.assertAlmostEqual(r['K_raw'],.0007960878080861267,places=13)
        self.assertEqual(r['catalog_size'],212)
        self.assertEqual(r['unavailable_sources_excluded_by_upper_bound'],len(self.model.missing))
        json.dumps(r,allow_nan=False)

    def test_cloud_once_and_detector_term_unscaled(self):
        s=self.model.sources[0];r=self.model.evaluate(s,self.context,10.)
        m=self.context['moments'];expected=.1*((m['m1']-m['mh']**2)*s['VA']+.0186*m['m1'])+.005*m['M0']
        self.assertAlmostEqual(r['N_effective'],expected,places=14)
        self.assertAlmostEqual(r['t'],.1*m['mh']**2,places=14)

    def test_screening_matches_full_archived_catalog(self):
        for a in [.1,1.]:
            expected=max(self.model.evaluate(s,self.context,a)['K_raw'] for s in self.model.sources)
            actual=catalog_maximum(self.model,self.batch,self.context,a)
            self.assertLessEqual(abs(expected-actual['K_raw']),1e-10)


if __name__=='__main__':unittest.main()
