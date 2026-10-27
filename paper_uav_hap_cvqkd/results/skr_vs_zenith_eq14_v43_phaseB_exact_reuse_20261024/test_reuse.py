"""Focused reuse-policy and unchanged-equation regression checks."""
import copy
import inspect
import unittest
from unittest.mock import patch

from inventory import OUT,ROOT,PRIOR,canonical,read,rows,sha,with_ensemble
import diagnostic_model
import run


class ReuseChecks(unittest.TestCase):
    def test_inventory_retains81_and_missing_uniform(self):
        current=rows(OUT/'pilot_source_coverage.csv');old=rows(PRIOR/'pilot_source_verification.csv')
        self.assertEqual(len(current),81)
        for before,after in zip(old,current):
            for key in ['VA_hex','nu_raw_hex','ensemble_hash','source_path','source_sha256','C','w','classification']:
                self.assertEqual(before[key],after[key])
        self.assertEqual(sum(r['diagnostic_eligible']=='True' for r in current),80)
        missing=next(r for r in current if r['diagnostic_eligible']=='False')
        self.assertEqual(missing['VA_hex'],'0x1.9ffff84830112p+0');self.assertEqual(missing['C'],'')

    def test_correlation_and_holevo_are_the_canonical_function_objects(self):
        self.assertIs(diagnostic_model.components,canonical.components)
        self.assertIs(diagnostic_model.correlation_eq14,canonical.correlation_eq14)
        self.assertEqual(list(inspect.signature(diagnostic_model.evaluate).parameters),['source','context','protocol'])

    def test_diagnostic_matches_canonical_on_two_verified_sources(self):
        _,sources=run.load_sources();protocol=read(PRIOR/'protocol.json')
        context=read(ROOT/'results/skr_vs_zenith_eq14_v43_20261024/channel_preflight.json')[0]
        context['protocol_sha256']=sha(PRIOR/'protocol.json')
        for source in [next(s for s in sources if s['family']=='Uniform' and s['VA']==va) for va in [.25,8.]]:
            before=(source['C'].hex(),source['w'].hex(),source['classification'])
            reference=canonical.evaluate(source,context,protocol)
            actual=diagnostic_model.evaluate(source,context,protocol)
            for key in ['eta_f','xi_f','Z_manuscript_eq14','I_AB','chi_BE','K_raw']:
                self.assertEqual(reference[key],actual[key],key)
            self.assertEqual(before,(source['C'].hex(),source['w'].hex(),source['classification']))

    def test_explicit_diagnostic_permission_does_not_change_source_class(self):
        _,sources=run.load_sources();protocol=read(PRIOR/'protocol.json')
        source=next(s for s in sources if s['classification']=='INSUFFICIENT_EVIDENCE')
        original=source['classification']
        # Invalid context must fail before all numerical components, even in diagnostic mode.
        with patch.object(diagnostic_model,'components',side_effect=AssertionError('Premature calculation')):
            with self.assertRaises(ValueError):diagnostic_model.evaluate(source,{},protocol)
        self.assertEqual(source['classification'],original)
        bad=dict(source,classification='INVALID')
        with self.assertRaises(ValueError):diagnostic_model.evaluate(bad,{},protocol)

    def test_negative_values_and_evidence_separation(self):
        protocol=read(PRIOR/'protocol.json')
        base=dict(zenith_deg=0,numerical_status='CURRENTLY_VERIFIED_PASS',source_evidence_class='VERIFIED_EXACT')
        data=[dict(base,family='Uniform',ensemble_hash='u',K_raw=-.2),
              dict(base,family='MB',ensemble_hash=protocol['fixed_MB']['ensemble_hash'],K_raw=-.1,source_evidence_class='INSUFFICIENT_EVIDENCE')]
        normal=run.select(data,protocol);strict=run.select(data,protocol,strict=True)
        self.assertEqual([r['K_raw'] for r in normal],[-.2,-.1,-.1])
        self.assertEqual(strict[1]['numerical_status'],'NO_EVALUABLE_SOURCE')
        self.assertEqual(strict[2]['K_raw'],-.2)


if __name__=='__main__':unittest.main(verbosity=2)
