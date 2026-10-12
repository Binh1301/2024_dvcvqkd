import unittest
from scripts import resume_theta10_D55_mb_batch3_after_ac as resume


class ResumeContract(unittest.TestCase):
    def test_skip_all_attempted_sources_and_keep_original_budget(self):
        points=[{'raw_current_cache_key':str(i)} for i in (1,2,3)]
        self.assertEqual([i for i,p in resume.unattempted_points(points,[{'cache_key':'1','status':'PROCESS_FAILURE'}])],[2,3])
        self.assertEqual([i for i,p in resume.unattempted_points(points,[{'cache_key':'1'},{'cache_key':'2','status':'TIMEOUT'}])],[3])
        self.assertEqual(resume.probe_limit(6000,1000),3600)
        self.assertEqual(resume.probe_limit(1000,100),420)
        self.assertLess(resume.probe_limit(1000,999),0)
        self.assertEqual(resume.run.PAIRS[2],(.16531250000000003,5.5))


if __name__ == '__main__':
    unittest.main()
