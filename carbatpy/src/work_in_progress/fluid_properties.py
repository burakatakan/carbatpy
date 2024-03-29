# -*- coding: utf-8 -*-
"""
functions to obtain fluid properties from cool prop using the low level interface

Created on Wed Dec  9 17:37:20 2020

@author: atakan
"""


import numpy as np
import CoolProp.CoolProp as CP


def mdot_area_function(m_dot, diameter):
    area = np.pi * (diameter / 2)**2
    m_dot_area = m_dot / area
    return m_dot_area, area


def ht_properties_sat(p, fluid):
    """
    Properties needed for integration at given p and h for heat transfer.

    Parameters
    ----------
    p : float
        pressure in Pa.

    fluid :   an AbstractState in coolprop.

    Returns
    -------
    alle : numpy array (2,4)
        includes: tranport properies in saturated state at given pressure p
         of liquid (0,:) and vapor(1,:),
        densities,viscosities, cp, thermal conductivity

        all in SI units.

    """

    props_all = np.zeros((2,4))
    for phase in [0,1]:
        fluid.update(CP.PQ_INPUTS, p, phase)
        reihe = [CP.iDmass, CP.iCpmass, CP.iviscosity, CP.iconductivity]
        props = [fluid.keyed_output(k) for k in reihe]
        props_all[phase,:] = props[:]

    return props_all


def ht_properties_satV(p, h, fluid): # unbenutzte vektorisierung
    _n = len(p)
    alle = np.zeros((14, 2, _n))
    for _i in range(_n):
        alle[:, :, _i] = ht_properties_sat(p[_i], h[_i], fluid)
    return alle


def properties(p, h, fluid):
    """
    Properties needed for integration at given p and h, single phase.

    Parameters
    ----------
    p : float
        pressure in Pa.
    h : float
        specific enthalpy in J/kg.
    fluid :   an AbstractState in coolprop.

    Returns
    -------
    alle : numpy array
        includes: T, p , quality, specific enthalpy,entropy
        densities,
        viscosities, cp , conductivity,phase prandtl-number
        at the defined state (p,h)
        all in SI units.

    """
    fluid.update(CP.HmassP_INPUTS, h, p)
    reihe = [CP.iT, CP.iQ, CP.iSmass, CP.iDmass, CP.iPrandtl, CP.iPhase,
             CP.iconductivity, CP.iCpmass, CP.iviscosity]
    props = [fluid.keyed_output(k) for k in reihe]
    _temp, x, s, rho, prandtl, phase, lambda_s, cp, mu = props[:]
    alle = [_temp, p, x, h,  s, rho, mu,
            cp, lambda_s, phase, prandtl]

    return alle
name_properties = ["temperature", "p", "x", "h",  "s", "rho", "mu",
        "cp", "lambda_s", "phase", "prandtl"]

def properties_V(p, h, fluid):
    """ Vectorization of the single phase properties function"""
    _n = len(p)
    alle = np.zeros((11, _n))
    for _i in range(_n):
        alle[:, _i] = properties(p[_i], h[_i], fluid)
    return alle

if __name__ == "__main__":
        
    _vielPrint__ = False
    
    
    x_0 = 1.
    p_0 = 20e5     # Anfangsdruck Pa
    
    fluid_a = "n-Propane"  # Working fluid
    temp_sur = 283
    p_sur = 1.0135e5
    
    p_c = CP.PropsSI('Pcrit', fluid_a)
    temp_0 = CP.PropsSI('T', 'P', p_0, 'Q', x_0, fluid_a) 
    
    h_0 = CP.PropsSI('H', 'P', p_0, 'T', temp_0 + 1, fluid_a)
    working_fluid = CP.AbstractState("BICUBIC&HEOS", fluid_a)
    mm = ht_properties_sat(1e6, working_fluid)
    # Sekundärfluid --------------------------------
    fluid_s = "Water"
    secondary_fluid = CP.AbstractState("BICUBIC&HEOS", fluid_s)
    p_s = 4e5
    temp_0_s = 283.
    h_0_s = CP.PropsSI('H', 'P', p_s, 'T', temp_0_s, fluid_s)
    h_end = CP.PropsSI('H', 'P', p_sur, 'T', temp_0_s, fluid_a)
    print( properties(p_s, h_0_s, secondary_fluid))
    
