"""Positive scalar interval bound for lambda_min; no eigensolve or C,w evaluation."""
from decimal import Decimal, localcontext, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction
import math
import time

import mpmath as mp
import checkpoint_wrapper as cw


def decimal_fraction(value, rounding, precision):
    with localcontext() as context:
        context.prec = precision; context.rounding = rounding
        return Decimal(value.numerator) / Decimal(value.denominator)


def lower_bound(p, alpha, groups, precision=80):
    weights = [Fraction.from_float(float(p[g[0]])) for g in groups]
    z = [(Fraction.from_float(float(alpha[g[0]].real)),
          Fraction.from_float(float(alpha[g[0]].imag))) for g in groups]
    energy = [x*x+y*y for x,y in z]
    nodes = [(x**4-6*x*x*y*y+y**4, 4*x*y*(x*x-y*y)) for x,y in z]
    assert len(set(nodes)) == len(nodes) and all(t > 0 for t in energy)
    # e<3 and 0<=|z|^2<=ceil(max energy), so no transcendental interval is needed.
    maximum = max(energy); exponent = (maximum.numerator + maximum.denominator - 1)//maximum.denominator
    exp_upper = Decimal(3**int(exponent))
    upper = [Decimal(0) for _ in range(4)]
    for k in range(len(groups)):
        coefficients = [Decimal(1)]
        denominator = Decimal(1)
        for j in range(len(groups)):
            if j == k:
                continue
            node_norm_upper = decimal_fraction(energy[j]**2, ROUND_CEILING, precision)
            distance_squared = (nodes[k][0]-nodes[j][0])**2 + (nodes[k][1]-nodes[j][1])**2
            distance_lower = decimal_fraction(distance_squared, ROUND_FLOOR, precision)
            assert distance_lower > 0
            with localcontext() as context:
                context.prec = precision; context.rounding = ROUND_FLOOR
                denominator *= distance_lower
            with localcontext() as context:
                context.prec = precision; context.rounding = ROUND_CEILING
                new = [Decimal(0)] * (len(coefficients)+1)
                for n, coefficient in enumerate(coefficients):
                    new[n] += coefficient*node_norm_upper; new[n+1] += coefficient
                coefficients = new
        for sector in range(4):
            with localcontext() as context:
                context.prec = precision; context.rounding = ROUND_FLOOR
                positive_denominator = (Decimal(4) * decimal_fraction(weights[k], ROUND_FLOOR, precision) *
                    decimal_fraction(energy[k], ROUND_FLOOR, precision)**sector * denominator)
            with localcontext() as context:
                context.prec = precision; context.rounding = ROUND_CEILING
                numerator = sum(coefficient*coefficient*Decimal(math.factorial(sector+4*n))
                                for n,coefficient in enumerate(coefficients))
                upper[sector] += exp_upper*numerator/positive_denominator
    result=[]
    for sector,value in enumerate(upper):
        power=value.adjusted()+1
        # Exact comparison to a power of ten, rather than a rounded logarithm.
        assert value < Decimal('1e'+str(power)) and value > 0
        result.append(dict(Fock_photon_sector=sector, Gram_sector=(-sector)%4,
            inverse_Frobenius_squared_upper_bound=str(value),
            certified_lambda_min_lower_bound='1e-'+str(power), bound_decimal_digits=precision))
    return result


def fock_tail_upper(p, alpha, groups, cutoff=256, precision=80):
    total = Decimal(0); maximum = Decimal(0)
    for group in groups:
        k = group[0]
        x, y = Fraction.from_float(float(alpha[k].real)), Fraction.from_float(float(alpha[k].imag))
        t = decimal_fraction(x*x+y*y, ROUND_CEILING, precision)
        with localcontext() as context:
            context.prec = precision; context.rounding = ROUND_CEILING
            power = Decimal(1)
            for _ in range(cutoff):
                power *= t
            ratio_upper = t/Decimal(cutoff+1)
        with localcontext() as context:
            context.prec = precision; context.rounding = ROUND_FLOOR
            denominator = Decimal(math.factorial(cutoff))*(Decimal(1)-ratio_upper)
        assert denominator > 0
        with localcontext() as context:
            context.prec = precision; context.rounding = ROUND_CEILING
            # exp(-t)<=1; deliberately loose, with no transcendental arithmetic.
            bound = power/denominator
            maximum = max(maximum, bound)
            total += Decimal(4)*Decimal.from_float(float(p[k]))*bound
    return dict(Fock_cutoff=cutoff, maximum_coherent_tail_upper_bound=str(maximum),
                weighted_Gram_tail_trace_upper_bound=str(total),
                spectral_norm_G_minus_G_Fock_upper_bound=str(total),
                method='Positive Poisson geometric tail; exp(-energy)<=1; directed Decimal rounding',
                numerical_precision=precision, Cw_truncation_error_certified=False)


def main():
    wall,cpu=time.perf_counter(),time.process_time()
    p,alpha,groups=cw.input_source(cw.PRIOR/'inputs/Winner_MB.npz')
    certificate=lower_bound(p,alpha,groups)
    # Independent small-case eigenvalues from the previous Fock implementation.
    sanity=[]
    for name in ['Uniform_4','MB_16']:
        p0,a0,g0=cw.input_source(cw.PRIOR/'inputs'/(name+'.npz'))
        bounds=lower_bound(p0,a0,g0,60)
        receipts=[r for r in cw.read(cw.PRIOR/'job_receipts.json')
                  if r['source']==name and r['method']=='A' and r['digits']>16]
        saved=cw.read(cw.PRIOR/receipts[0]['output'])
        n=receipts[0]['NF']//4
        with mp.workdps(90):
            for bound in bounds:
                r=bound['Fock_photon_sector']
                # Compare only true positive small-source modes, excluding the Fock nullspace.
                positive=[mp.mpf(x) for x in saved['spectrum'][r*n:(r+1)*n] if mp.mpf(x)>mp.mpf('1e-50')]
                assert positive and min(positive)>mp.mpf(bound['certified_lambda_min_lower_bound'])
        sanity.append(dict(source=name,comparison='PASS; independent saved Fock eigenspectrum'))
    cw.atomic_json(cw.OUT/'spectral_lower_bound_certificate.json',dict(
        status='CERTIFIED_ANALYTIC_SCALAR_LOWER_BOUND', result_scope='DIAGNOSTIC_ONLY',
        source_ensemble_hash=cw.read(cw.PRIOR/'inputs/source_metadata.json')[0]['ensemble_hash'],
        input_sha256=cw.sha(cw.PRIOR/'inputs/Winner_MB.npz'),
        input_p_alpha='Exact Fraction.from_float binary64 values; no rounding of nodes/distances',
        method='Lagrange inverse norm majorant; correctly directed Decimal arithmetic; e<3',
        sectors=certificate, certified_Fock_Gram_tail=fock_tail_upper(p,alpha,groups),
        small_saved_spectrum_sanity=sanity,
        full_support_Cw_certified=False, unresolved_Cw_error_bound=None,
        new_eigendecompositions=0, new_Cw_computations=0,
        wall_seconds=time.perf_counter()-wall, CPU_seconds=time.process_time()-cpu,
        producer_sha256=cw.sha(__file__)))
    print(certificate)


if __name__=='__main__':main()
