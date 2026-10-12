import unittest
from scripts import continue_theta10_D55_ao_phase2a_after_ac as resume


class Phase2AResume(unittest.TestCase):
    def test_skip_attempted_keys_and_keep_absolute_budget(self):
        points=resume.run.points()
        self.assertEqual([i for i,p in resume.unattempted(points,[{'cache_key':points[0]['source_cache_key'],'status':'PROCESS_FAILURE'}])],[2,3])
        self.assertEqual([i for i,p in resume.unattempted(points,[{'cache_key':points[0]['source_cache_key']},{'cache_key':points[1]['source_cache_key'],'status':'TIMEOUT'}])],[3])
        self.assertEqual(resume.run.budget_limit(137345.75,136345.75),520)
        self.assertLess(resume.run.budget_limit(137345.75,137345.75),0)
        self.assertIs(resume.run.ao,resume.run.prep.audit.baseline.ao)


if __name__=='__main__':
    unittest.main()
