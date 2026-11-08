"""Versioned reference aircraft: derive constants, diagnose components and speeds.

The existing propulsion_power remains the authoritative total-power evaluator.
This module does not modify a mission configuration or execute a QKD model.
"""
import numpy as np
from scipy.optimize import minimize_scalar
from .config import load_config
from .propulsion import PropulsionParams, propulsion_power


def load_reference(path) -> dict:
    """Derive power coefficients from raw, explicitly versioned aircraft data."""
    config = load_config(path)
    a = config['aircraft']
    if not config.get('name') or not config.get('source'):
        raise ValueError('A reference name and source provenance are required')
    for name, value in a.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
            raise ValueError(f'Aircraft {name} must be positive and finite')
    if int(a['blade_count']) != a['blade_count']:
        raise ValueError('Blade count must be an integer')
    if not np.isclose(a['rotor_tip_speed_m_s'], a['rotor_angular_speed_rad_s']*a['rotor_radius_m'], rtol=1e-12, atol=1e-12):
        raise ValueError('Rotor tip speed must match angular speed times radius')
    rho, area, weight = a['air_density_kg_m3'], a['rotor_disc_area_m2'], a['weight_N']
    tip = a['rotor_tip_speed_m_s']
    p0 = a['blade_profile_drag_coefficient']/8*rho*a['rotor_solidity']*area*tip**3
    pi = (1+a['induced_power_correction_factor'])*weight**1.5/np.sqrt(2*rho*area)
    v0 = np.sqrt(weight/(2*rho*area))
    policy = config['induced_velocity_policy']
    if policy not in ('derived', 'table_value'):
        raise ValueError('Induced velocity policy must be derived or table_value')
    used = float(v0) if policy=='derived' else a['mean_induced_velocity_hover_m_s']
    params = PropulsionParams(P0=float(p0), Pi=float(pi), U_tip=tip, v0=used,
                              d0=a['fuselage_drag_ratio'], rho=rho, s=a['rotor_solidity'],
                              A=area, v_max=a['maximum_speed_m_s'])
    return dict(config=config, params=params,
                derived=dict(P0_W=float(p0), Pi_W=float(pi), hover_power_W=float(p0+pi),
                             v0_derived_m_s=float(v0), v0_used_m_s=used,
                             v0_table_m_s=a['mean_induced_velocity_hover_m_s'],
                             disc_area_pi_R2_m2=float(np.pi*a['rotor_radius_m']**2),
                             induced_velocity_policy=policy))


def power_components(speed, params: PropulsionParams) -> dict:
    """Three Eq.(12) components in W; stable induced term, validated total reused."""
    total = propulsion_power(speed, params)
    v = np.asarray(speed, float)
    ratio = v**2/(2*params.v0**2)
    return dict(blade_profile_W=params.P0*(1+3*v**2/params.U_tip**2),
                induced_W=params.Pi/np.sqrt(np.hypot(1., ratio)+ratio),
                parasite_W=.5*params.d0*params.rho*params.s*params.A*v**3,
                total_W=total)


def characteristic_speeds(params: PropulsionParams, *, grid_samples=20001,
                          xatol=1e-10) -> dict:
    """Grid-bracketed numerical ME/MR minima; no continuous global certificate.

    Refine every sampled local minimum, compare endpoints, and check the final
    objective against the complete grid. MR excludes zero, where P(v)/v diverges.
    """
    if isinstance(grid_samples, bool) or int(grid_samples)!=grid_samples or grid_samples<3:
        raise ValueError('Grid samples must be an integer >=3')
    if not np.isfinite(xatol) or xatol<=0:
        raise ValueError('Optimizer xatol must be positive and finite')
    grid = np.linspace(0, params.v_max, int(grid_samples))
    powers = propulsion_power(grid, params)
    result = {}
    for kind in ('ME', 'MR'):
        if kind=='ME':
            values = powers
            objective = lambda v: float(propulsion_power(v, params))
            candidates = [(0., float(values[0])), (params.v_max, float(values[-1]))]
        else:
            values = np.r_[np.inf, powers[1:]/grid[1:]]
            objective = lambda v: float(propulsion_power(v, params))/v if v>0 else np.inf
            candidates = [(float(grid[1]), float(values[1])), (params.v_max, float(values[-1]))]
        local = np.flatnonzero((values[1:-1] <= values[:-2]) & (values[1:-1] <= values[2:]))+1
        for index in local:
            solved = minimize_scalar(objective, bounds=(grid[index-1], grid[index+1]),
                                     method='bounded', options={'xatol': xatol})
            if not solved.success or not np.isfinite(solved.fun):
                raise RuntimeError(f'{kind} bounded optimization failed: {solved.message}')
            candidates.append((float(solved.x), float(solved.fun)))
        speed, value = min(candidates, key=lambda item: (item[1], item[0]))
        best_grid = int(np.argmin(values))
        passed = bool(value <= float(values[best_grid])+1e-9)
        if not passed:
            raise RuntimeError(f'{kind} optimizer is worse than its dense-grid reference')
        result[kind] = dict(speed_m_s=speed, objective_value=value,
                            objective_units='W' if kind=='ME' else 'J/m',
                            power_W=float(propulsion_power(speed, params)),
                            grid_speed_m_s=float(grid[best_grid]), grid_objective_value=float(values[best_grid]),
                            grid_check_passed=passed, refined_grid_minima=len(local))
    result['method'] = 'Bounded refinement of every grid local minimum plus endpoints; dense-grid objective check'
    result['grid_samples'] = int(grid_samples)
    result['grid_spacing_m_s'] = float(grid[1]-grid[0])
    result['optimizer_xatol_m_s'] = float(xatol)
    return result
