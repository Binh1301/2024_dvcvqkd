"""Focused forensic checks; no source moments or SKR calculations."""
import csv
import json
import unittest

from forensics import OUT, PRIOR, ROOT, decoded, provenance, read, sha


class ForensicChecks(unittest.TestCase):
    def test_inventory_preserves_all81_identities_and_values(self):
        with (PRIOR/'pilot_source_verification.csv').open(encoding='utf-8',newline='') as f:
            previous=list(csv.DictReader(f))
        with (OUT/'pilot_source_evidence.csv').open(encoding='utf-8',newline='') as f:
            current=list(csv.DictReader(f))
        self.assertEqual(len(current),81)
        for before,after in zip(previous,current):
            for key in ['family','VA_hex','nu_raw_hex','ensemble_hash','source_path','source_sha256','C','w']:
                self.assertEqual(before[key],after[key],key)
            self.assertEqual(float(after['nu_repo']).hex(),(42.5*float.fromhex(after['nu_raw_hex'])).hex())
            if after['source_path']:self.assertEqual(sha(ROOT/after['source_path']),after['source_sha256'])
        missing=next(r for r in current if not r['source_path'])
        self.assertEqual(missing['VA_hex'],'0x1.9ffff84830112p+0')
        self.assertEqual(missing['expected_ensemble_hash'],read(PRIOR/'source_job_preflight.json')['ensemble_hash'])
        self.assertEqual(missing['C'],'');self.assertEqual(missing['w'],'')

    def test_no_false_upgrade_or_missing_receipt_invalidation(self):
        summary=read(OUT/'readiness_summary.json')
        self.assertEqual(summary['counts'],dict(VERIFIED_EXACT=6,VERIFIED_BY_ALTERNATIVE_EVIDENCE=1,INSUFFICIENT_EVIDENCE=74,INVALID=0))
        self.assertEqual(summary['upgraded_sources'],0)
        self.assertFalse(summary['PHASE_B_STRICT_READY'])
        self.assertEqual(summary['fixed_MB_status'],'INSUFFICIENT_EVIDENCE')
        self.assertEqual(summary['existing_sources_missing_evidence'],73)
        self.assertIsNone(provenance.alternative_ladder({},dict(C=1.,w=0.,support_size=256)))

    def test_saved_tool_envelope_decoder_never_executes_code(self):
        values=list(decoded([{'type':'input_text','text':json.dumps(dict(output=json.dumps(dict(rank=256))))}]))
        self.assertTrue(any(isinstance(v,dict) and v.get('rank')==256 for v in values))
        payload="__import__('os').system('false')"
        self.assertEqual(list(decoded(payload)),[payload])

    def test_saved_cpu_activity_is_distinct_from_numerical_convergence(self):
        timeline=read(OUT/'uniform_cpu_timeline.json')
        values=[r['user_cpu_seconds'] for r in timeline['observations'] if 'user_cpu_seconds' in r]
        self.assertEqual(len(timeline['observations']),9)
        self.assertEqual(values,sorted(values))
        self.assertEqual(values[0],535.4375);self.assertEqual(values[-1],2380.421875)
        self.assertEqual(timeline['numerical_precision_stage'],'NOT_RECORDED')
        diagnosis=read(OUT/'uniform_diagnostic_checks.json')
        self.assertEqual(diagnosis['expensive_Cw_calls'],0)
        self.assertEqual(diagnosis['exact_bottleneck_within_worker'],'UNKNOWN')

    def test_immutable_git_evidence_does_not_add_unverified_sources(self):
        recovered=read(OUT/'expanded_evidence_scan.json')['recovered']
        self.assertEqual(len(recovered),2)
        for item in recovered:
            self.assertEqual(item['source_hash'],'bb78529d69b136fcead347ea7eb2cfa7b2feb34832ef6e78ba4cf719cc0abb13')
            self.assertTrue(item['origin'].startswith('git:'))
            self.assertEqual(sha(OUT/item['snapshot']),item['sha256'])
        self.assertEqual(sha(PRIOR/'experiment_spec_v1.json'),'4868392f68af9be5b52b684dac1a23d4242e4cf44a871d4e66944349aa874d21')


if __name__=='__main__':unittest.main(verbosity=2)
