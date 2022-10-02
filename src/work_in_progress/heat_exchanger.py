# -*- coding: utf-8 -*-
"""
Heat exchangers
simple NTU with constant convection coefficient 
and
solving the bvp along an axial coordinate

if nothing else given: counterflow/double-pipe
if nothing else is said given: steady state

Created on Sun Oct  2 16:27:20 2022

@author: atakan
"""
import numpy as np
import CoolProp.CoolProp as CP
from fluid_properties_hl import tp, hps, xp, xT

class heat_exchanger:
    # Heat exchanger base class
    
    def __init__(self, fluids, mass_flows, pressures, enthalpies, name="HEX_0"):
        """
        

        Parameters
        ----------
        fluids : TYPE list 
            two coolProp-Fluid names.
        mass_flows : TYPE list or numpy-array length 2
           both mass flows.
        pressures : list or numpy-array length 2
            initial pressures of each fluid.
        enthalpies : list or numpy-array length 2
            initial pressures of each fluid.
        name: string.
            name of the heat-exchanger, default = "HEX_0"

        Returns
        -------
        None.

        """
        self.fluids = fluids
        self.mass_flows = mass_flows
        self.pressures = pressures
        self.enthalpies = enthalpies
        self.name = name
    
    def q_max(self):
        """ maximum possible heat transfer for isobaric, adiabatic 
        heat exchanger
        As it is programmed now, saturated final states are not considered"""
        
        state_variables = np.zeros((2,6))
        final_states = np.zeros((2,6))
        q_dot = np.zeros((2))
        
        for n in range(2): # get initial states (Temperatures)
            state_variables[n,:] = hps(self.enthalpies[n],self.pressures[n], 
                                       self.fluids[n])
        final_states[0,:] = tp(state_variables[1, 0],state_variables[0, 1], 
                             self.fluids[0])
        final_states[1,:] = tp(state_variables[0, 0],state_variables[1, 1], 
                             self.fluids[1])
        for n in range(2):
            q_dot[n] = self.mass_flows[n] * (final_states[n, 2] 
                                             - state_variables[n, 2])
        
        if np.abs(q_dot[0]) > np.abs(q_dot[1]):
            q_max = q_dot[1]
        else: q_max = q_dot[0]
        print (q_dot)
        return q_max
            
        
    
if __name__  == "__main__":
    mdot=np.array((.0029711, .0351)) # kg/s for both fluids
    alpha = 500  # heat transfer coefficient through the wall (from total resistance)
    fl =["ISOBUTANE","Water"]   # which fluids?
    Tin = [354, 313]
    p = [6.545e5, 4.e5]  # pressure for each fluid, Pa
    ha_in=tp(Tin[0], p[0], fl[0])[2]  # state of fluid 1 left
    hb_in=tp(Tin[1],p[1],fl[1])[2]  # state of fluide 2 right (at L)
    ha_outMax = tp(Tin[1],p[0],fl[0])[2]  # state of fluid 1 left
    hb_outMax = tp(Tin[0],p[1],fl[1])[2]  # state of fluide 2 right (at L)
    heat_ex = heat_exchanger(fl, mdot, p, [ha_in,hb_in])
    qm = heat_ex.q_max()
    print (qm)
    pass
