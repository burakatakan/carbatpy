# -*- coding: utf-8 -*-
"""
machines and NTU heat exchangers
Created on Mon Oct 31 15:45:47 2022

@author: atakan
"""


import CoolProp.CoolProp as CP

import fluid_properties_rp as fprop
import numpy as np

_props = "REFPROP"
_units = 21

class machine:
    """ Base Class for machines (compressors and expanders)"""
    def __init__(self, mdot, hin, pin, pout, eta_s, 
                 fluid, composition=[1.0], option=1, units =_units, 
           props=_props):
        """
        Base class for machines (expanders and compressors) will be calculated 
        with different property modules (like REFEPROP)

        Parameters
        ----------
        mdot : float
            mass flow rate in kg/s.
        hin : float
            specific enthalpy of the fluid at the entrance in J/kg.
        pin : float
            pressure at the entrance in Pa.
        pout : float
            pressure at the exit in Pa.
        eta_s : float
            isentropic efficiency.
        fluid : depends on property model (props)
            fluid or fluid mixture (name).
        composition : depends on property model, optional
            molar composition of the fluid mixture. The default is [1.0].
        option : integer, optional
           if more properties are needed, this option is passed to the evaluation
           of the property model. The default is 1.
        units : integer, optional
            important: the units of the model has to be set to SI units (J, kg, Pa, K).
            The default is _units.
        props : String, optional
            either "REFPROP", "TREND" or "CoolProp", only the first is implemented 
            so far. The default is _props ("REFPROP").

        Returns
        -------
        None.
        But the exit state, specific work and power are evaluated in the 
        derived classes

        """
        
        n_properties = 6
        self.m_dot =mdot
        self.h_in =hin
        self.p_in =pin
        
        self. eta_s = eta_s
        self.state = np.zeros((2,n_properties))
        self.composition =composition
        self.option = option
        self.units = units
        self.props = props
        self.fluid = fluid
        self.p_out = pout

        self.state[0, :] = fprop.hp(self.h_in, self.p_in, self.fluid, 
                                         self.composition, 
                               option=self.option, units =self.units, 
                               props=self.props)
        self.state_iso = fprop.sp(self.state[0, 4], self.p_out, 
                               self.fluid, self.composition, 
                                self.option, self.units, self.props)  # isentropic
        
class compressor(machine):
    def __init__(self, mdot, hin, pin, pout, eta_s, 
                 fluid, composition=[1.0], option=1, units =_units, 
                 props=_props):
        super().__init__( mdot, hin, pin, pout, eta_s, 
                     fluid, composition, option, units, 
                     props)
    
        self.sp_work = (self.state_iso[ 2] - self.state[0, 2]) / self.eta_s
        self.power = self.sp_work  *self.m_dot
        
        self.state[1, :] = fprop.hp(self.state[0, 2] + self.sp_work, self.p_out,  
                                    self.fluid, 
                               self.composition, 
                                self.option, units =self.units, 
                                props=self.props)
        

class expander(machine):
    def __init__(self, mdot, hin, pin, pout, eta_s, 
                 fluid, composition=[1.0], option=1, units =_units, 
                 props=_props):
        super().__init__( mdot, hin, pin, pout, eta_s, 
                     fluid, composition, option, units, 
                     props)
    
        self.sp_work = (self.state_iso[ 2] - self.state[0, 2]) * self.eta_s
        self.power = self.sp_work  * self.m_dot
        
        self.state[1, :] = fprop.hp(self.state[0, 2] + self.sp_work, self.p_out,  
                                    self.fluid, 
                               self.composition, 
                                self.option, units =self.units, 
                                props=self.props)
        
     
class heat_exchangerNTU:
            """ not finished, perjaps not even needed, the other class for heat 
            exchangers which solves the ode may be more favorable ..."""
            def __init__(self, mdot, hin, pin, pout, U, area, 
                         fluid, composition=[1.0], option=1, units =_units, 
                   props=_props):
                n_properties = 6
                self.m_dot = mdot
                self.h_in = hin
                self.p_in = pin
                
                self. U = U
                self.area = area
                self.state = np.zeros((2,2, n_properties))
                self.composition =composition
                self.option = option
                self.units = units
                self.props = props
                self.fluid = fluid
                self.p_out = pout # unused
                for nf in range(2):
                    self.state[nf,0, :] = fprop.hp(self.h_in[nf], 
                                                   self.p_in[nf], 
                                                   self.fluid[nf], 
                                                   self.composition[nf], 
                                                   self.option, 
                                                   self.units[nf], 
                                                   self.props[nf])
        
if __name__ == "__main__":
    a =compressor(.001,2.67494768e+06,1e5,3e5,0.75,"Water",[1.0])
    b =expander(.001,a.state[1,2],3e5,1e5,0.75,"Water",[1.0])
    print("Powerinput and output for Water compression and expansion from 1 \
          to 3 bar with isentropic efficiencies of 75%, (should be:283.7602\
                            -171.835...:\n",a.power, b.power)

