# -*- coding: utf-8 -*-
"""
Heat exchanger base class and counterflow heat exchanger class are introduced
For the first, only the maximum possible heat flow rate s evaluated.
For the counterflow heat exchanger at the moment the boundary value problem 
is solved with constant overall heat transfer coefficient  along the axial 
coordinate is implemented, together with some graphical output.

Fluid properties stem from REFPROP or CoolProp, the low-level interface is used.
Planned are the convection coefficienets along the axial coordinate 
shall be evaluated using appropriate Nu-correlations 
optimization will be implemented (Entropy minimization)
perhaps pressure drop will be implemented to the bvp

if nothing else given: counterflow/double-pipe
if nothing else is said given: steady state

Created on Sun Oct  2 16:27:20 2022

@author: atakan

"""
import numpy as np
import CoolProp.CoolProp as CP
from fluid_properties_rp import tp, hp, hp_v, hp_exergy, setRPFluid
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt
from time import time
import yaml
from fluid_properties_rp import _fl_properties_names
import pandas as pd
import os
props = "REFPROP"


class heat_exchanger:

    # Heat exchanger base class

    def __init__(self, fluids, mass_flows, pressures, enthalpies, UA=10,
                 calc_type="const", name="HEX_0"):
        """
        Initializing the heat exchanger with fluids, mass flow rates etc.
        at the moment pressures are constant.

        Parameters
        ----------
        fluids : list 
            two coolProp or RefPROP-Fluid abstract states (for low level).
        mass_flows : list or numpy-array length 2
            both mass flows.
        pressures : list or numpy-array length 2
            initial pressures of each fluid.
        enthalpies : list or numpy-array length 2
            initial enthalpies of each fluid.
        UA : float
            overall heat transfer coefficient times area, 
            as constant (for simple calculations), default = 10.
        calc_type : string
            if "const" = does not vary along heat exchanger (default)
            if "calc" = calculated from Nusselt correlation 
            along heat exchanger
        name : string.
            name of the heat-exchanger, default = "HEX_0"

        Returns
        -------
        None.

        """
        self.fluids = fluids
        self.mass_flows = mass_flows
        self.pressures = pressures
        self.enthalpies = enthalpies
        self.UA = UA
        self.calc_type = calc_type
        self.name = name

    def q_max(self, option=0):
        """
        Maximum possible heat transfer for an isobaric, adiabatic 
        heat exchanger

        Parameters
        ----------
        option : innteger, optional
            controls the output. The default is 0.

        Returns
        -------
        heatflow rate : float
            if option is 0.
        also theoretical max. heatflorates of both fluids : numpy.array len(2)
        the properties of both theoretical states 
        at the exit (T, p, h, v, s, q) : numpy.array (2,6)
            if option is 1

        """

        state_variables = np.zeros((2, 6))
        final_states = np.zeros((2, 6))
        q_dot = np.zeros((2))
        verbose = False
        for n in range(2):  # get initial states (Temperatures)
            state_variables[n, :] = hp(self.enthalpies[n], self.pressures[n],
                                       self.fluids[n], props=self.props,
                                       composition=self.compositions[n],
                                       RP=self.RP[n])
        final_states[0, :] = tp(state_variables[1, 0], state_variables[0, 1],
                                self.fluids[0], props=self.props,
                                composition=self.compositions[0],
                                RP=self.RP[0])
        final_states[1, :] = tp(state_variables[0, 0], state_variables[1, 1],
                                self.fluids[1], props=self.props,
                                composition=self.compositions[1],
                                RP=self.RP[1])
        # print("final states:", final_states)
        for n in range(2):
            q_dot[n] = self.mass_flows[n] * (final_states[n, 2]
                                             - state_variables[n, 2])

        if np.abs(q_dot[0]) > np.abs(q_dot[1]):
            q_max = q_dot[1]
        else:
            q_max = q_dot[0]
        if verbose:
            print("Max. heat flow rates of both fluids: %3.2f W, %3.2f W" %
                  (q_dot[0], q_dot[1]))
        if option == 0:
            return q_max
        if option == 1:
            return q_max, q_dot, final_states


class counterflow_hex(heat_exchanger):
    def __init__(self, fluids, mass_flows, pressures, enthalpies, length,
                 diameters, U=10., no_tubes=1, no_points=100, props="REFPROP",
                 compositions=[[1.0], [1.0]], calc_type="const", name="HEX_0",
                 units=21):
        """
        Counter flow heat exchanger class initialization, for double-pipe 
        heat exchangers
        or having no_tubes tubes inside. Now geometrical parameters and 
        a convection coefficient are needed.
        no_points is the initial division of the length for solving the bvp

        Parameters
        ----------
        fluids : TYPE list (of strings for REFPROP)
            two coolProp or Refprop-Fluid names.
        mass_flows : TYPE list or numpy-array length 2
            both mass flows.
        pressures : list or numpy-array length 2
            initial pressures of each fluid.
        enthalpies : list or numpy-array length 2
            initial enthalpies of each fluid.
        length : float
            heat exchanger length in m.
        diameters : array length 2
            inner diameters of inner tubes and outer tube unit:m.
        U : float, optional
            overall heat transfer coefficient in W /( K m2). The default is 10.
        no_tubes : integer, optional
            number of inner tubes. The default is 1.
        no_points : integer
            No of initial points along x, for solving the bvp.     
        calc_type : string
            if "const" = does not vary along heat exchanger (default)
            if "calc" = calculated from Nusselt correlation 
            along heat exchanger
        name : string.
            name of the heat-exchanger, default = "HEX_0"
        composition s: list of lists
            in each list the mole fraction of each compound in each fluid is
            listed. Two pure fluids: [[1.0],[1.0]
        props : "REFPROP or "CoolProp""
            module to evaluate fluid properties
        units : integer
            selection of units (for REFPROP, generally SI)



        Returns
        -------
        None.

        """
        calculate = True
        self.fluids = fluids
        self.fluid_names = fluids  # when changing fluids to "" (later)

        self.compositions = compositions
        self.props = props
        self.units = units
        self.mass_flows = mass_flows
        self.pressures = pressures
        self.enthalpies = enthalpies
        self.length = length
        self.diameters = diameters  # only inner diameter is used!
        self.U = U
        self.no_tubes = no_tubes
        self.no_points = no_points
        self.calc_type = calc_type
        self.name = name
        self.x = np.linspace(0, length, no_points)
        self.perimeter = self.diameters[0] * np.pi * self.no_tubes
        self.area = self.length * self.perimeter
        self.UA = self.area * self.U
        if calculate:
            import sys
            from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary as modwf
            
            from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary as modsf
            self.RP = [setRPFluid(self.fluids[0],modwf,'RPPREFIX'), 
                       setRPFluid(self.fluids[1], modsf,'RPPREFIXs')]
            # IF This is set, the entering state of the first fluidof the heat exchanger seems to be wrong
            
            qm, qd, f_states = self.q_max(1)
            self.min_flow = np.where(qd == qm)[0][0]
            
            self.qm_specific = qm / self.mass_flows[self.min_flow]
            self.h_in = np.linspace(self.enthalpies[0],  # maximum changes in enthalpy
                                    self.enthalpies[0] + qm, no_points)
            self.h_out = np.linspace(self.enthalpies[1] - qm,
                                     self.enthalpies[1], no_points)
            self.fluids = ["", ""]

    def energy(self, x, h):
        """
        energy balance for solving the boundary value problem
        couples the energy changes of each fluid with the convective heat 
        transfer between both fluids.
        At the moment the convection coefficient from the heat exchanger 
        is used;
        this shall be evaluated later as a function of local
        heat exchanger parameters.


        Parameters
        ----------
        x : float
            position in m.
        h : numpy array length (2)
            specific enthalpies of the two fluids at the given position, 
            each in J/kg.

        Returns
        -------
        dh : numpy array length 2
            both changes in specific enthalpy in positive x-direction in J/(kg m).

        """
        Ti = np.zeros((2,len(x)))
        for i in range(2):
            T = hp_v(h[i], self.pressures[i], self.fluids[i], units=self.units,
                         props=self.props, option=1, composition=self.compositions[i],
                         RP=self.RP[i])[0]
            Ti[i,:] =T
            # print(i,self.fluids[i], self.compositions[i])

        q_konv = Ti[1,:]-Ti[0,:]

        dh0 = self.U * self.perimeter / self.mass_flows[0] * q_konv
        dh1 = self.U * self.perimeter / self.mass_flows[1] * q_konv
        return np.array([dh0, dh1])

    def bc(self, ha, hb):
        """
        two boundary conditions for bvp-solver (scipy.integrate) needed
        here: the enthalpies of the inner fluid at x=0 and the enthalpy of 
        the outer fluid at the end of the heat exchanger at x=length

        Parameters
        ----------
        ha : numpy array
            enthalpies of the inner fluid along the x-coordinate.
        hb : numpy array
            enthalpies of the outer fluid along the x-coordinate.

        Returns
        -------
        numpy array of length 2
           the difference to the prescribed entrance conditions, should both 
           get zero, if succesful.

        """

        return np.array([ha[0] - self.enthalpies[0],
                         hb[1] - self.enthalpies[1]])

    def he_bvp_solve(self):
        """
        solving the boundary volume problem (scipy) for the counter-flow
        heat exchanger

        Returns
        -------
        result : dictionary
           see scipy documentation, e.g. success (did it find a solution,
                                                  the x and y values)

        """
        y = np.zeros((2, self.no_points))
        y[0, :] = self.enthalpies[0]
        y[1, :] = self.enthalpies[1]

        result = solve_bvp(self.energy, self.bc, self.x, y, tol=5e-3,
                           max_nodes=1000)
        return result

    def he_state(self, result, option=0, fname="hex_result"):
        """
        After solving the bvp-Problem for the evaluation of 
        all temperatures, enthalpies, entropies etc. 
        along the counterflow heat exchanger 
        and plotting T if option >1

        Parameters
        ----------
        result : TYPE
            DESCRIPTION.
        option : TYPE, optional
            DESCRIPTION. The default is 0.
        fname : string
            filename (without ending for storing the figure and the numbers)

        Returns
        -------
        if success == True
        states_0 numpy array
           resolved state variables for the inner tube(s).
        states_1 numpy array
           resolved state variables for the outer tube.
        ds float
            entropy production rate of the heat exchanger (W/(K).
        dh2 float
            enthalpy change rate of the second fluid in the heat 
            exchanger (W), equal to the heat flow rate.

        """
        verbose = False
        if result.success:
            states_0 = hp_v(result.y[0], self.pressures[0],
                            self.fluids[0], props=self.props, units=self.units,
                            composition=self.compositions[0],
                            RP=self.RP[0])
            states_1 = hp_v(result.y[1], self.pressures[1],
                            self.fluids[1], props=self.props, units=self.units,
                            composition=self.compositions[1],
                            RP=self.RP[1])
            s0 = states_0[4]
            s1 = states_1[4]
            if option > 5:
                fi, ax = plt.subplots(1, 2)
                ax[0].plot(result.x, states_0[0])
                ax[0].plot(result.x, states_1[0])
                ax[0].set_xlabel("length / m")
                ax[0].set_ylabel("temperature / K")
                ax[1].plot((states_0[2]-states_0[2][-1]) *
                           self.mass_flows[0], states_0[0])
                ax[1].plot((states_1[2]-states_1[2][-1]) *
                           self.mass_flows[1], states_1[0])
                ax[1].set_xlabel("H_dot / W")
                ax[1].set_ylabel("temperature / K")
                # fi.show()
                fi.savefig(fname+".png")
            ds = (s0[-1] - s0[0]) * self.mass_flows[0] + \
                 (s1[0] - s1[-1]) * self.mass_flows[1]
            dh2 = (states_1[2][0] - states_1[2][-1]) * self.mass_flows[1]

            if option > 0:
                if verbose:
                    print("Entropy production rate:%3.4f W/K" % (ds))
            # Print all to an Excel-File:
            res0 = {"ds": ds, "dq": dh2}
            nx, ny = np.shape(states_0)
            alles = np.zeros((2*nx + 1, ny))
            alles[0, :] = result.x
            alles[1:nx+1] = states_0
            alles[nx+1:] = states_1
            names=["x"]  # unique  column-names:
            for ext in["_fl1","_fl2"]: 
                for m in _fl_properties_names[:6]: 
                    names.append(m+ext)

            pd0 = pd.DataFrame(alles.T, columns=names)
            # zzz = pd.DataFrame(dict( (key, value) for (key, value) in self.__dict__.items()))
            res0 = pd.DataFrame(res0, ["total"])
            mode ="w"
            if os.path.exists(fname+".xlsx"): mode ="a"
            
            try:
                with pd.ExcelWriter(fname+".xlsx", mode= mode) as writer:
                    pd0.to_excel(writer, sheet_name="results")
                    # zzz.to_excel(writer, sheet_name="input")
                    res0.to_excel(writer, sheet_name="overallRes")
            except:
                with pd.ExcelWriter(fname+".xlsx", mode="w") as writer:
                    pd0.to_excel(writer, sheet_name="results")
                    # zzz.to_excel(writer, sheet_name="input")
                    res0.to_excel(writer, sheet_name="overallRes")

            return states_0, states_1, ds, dh2
        else:
            if verbose:
                print("Error: bvp-problem not solved succesfully!",
                      result.message)
            return -1, -1, -1

    def exergy_entering(self):
        """
        Calculate the exergyflow rates of both fluids entering 
        the heat exchanger. For exergy loss calculations and efficiencies. 

        Returns
        -------
        ex : float
           exergy flow rate in W.

        """
        ex = 0
        for n in range(2):
            ex += hp_exergy(self.enthalpies[n], self.pressures[n],
                            self.fluids[n], props=self.props,
                            RP=self.RP[n])\
                * self.mass_flows[n]
        return ex


class st_heat_exchanger_input:

    # Heat exchanger base class

    def __init__(self, fluids, mass_flows, pressures, enthalpies, length, d_in,
                 U, no_tubes, no_points,
                 props, composition,
                 calc_type="const", name="HEX_0", units=21):
        """

        New class for writing and reading the shell and tube heat excahnger 
        parameters to  a YAML file and shall be used to call the counterflow
        heatexchanger with.

        Initializing the heat exchanger with fluids, mass flow rates etc.
        at the moment pressures are constant.
        everything in SI units (K, m, kg, s, Pa, J etc.)
        Below: if lists of length 2 are needed, the first is for the internal 
        fluid/tube, the second for the other.

        Parameters
        ----------
        fluids : list of strings
            two coolProp or RefPROP-Fluid names (for low level).
        mass_flows : list floats length 2
            both mass flows.
        pressures : list of floats length 2
            initial pressures of each fluid.
        enthalpies : list of floats, length 2
            initial enthalpies of each fluid.
        U : float
            overall heat transfer coefficient 
            as constant (for simple calculations), default = 10.
        calc_type : string
            if "const" = does not vary along heat exchanger (default)
            if "calc" = calculated from Nusselt correlation 
            along heat exchanger
        name : string.
            name of the heat-exchanger, default = "HEX_0"
        no_tubes : integer
            number of tubes within the single shell
        no_points : integer
            number of points (discretization) for the boundary 
            value problem to solve
        d_in : list of two floats
            inner diameters of the internal and the external tube
        length : float
            lngth of the heat exchanger
        composition : list of 2 lists of floats
            the compostion (mole fractions) of the two fluids
        props : string
            which property model to use ("REFPROP", "CoolProp", ...)
        units : integer
            as required for refprop (so far 21 means SI-mass units)

        Returns
        -------
        None.

        """
        self.fluids = fluids
        self.mass_flows = mass_flows
        self.pressures = pressures
        self.enthalpies = enthalpies

        self.calc_type = calc_type
        self.heat_transfer_coefficient = U
        self.name = name
        # self.temperature_in = Tin
        self.no_tubes = no_tubes
        self.no_points = no_points
        self.d_in = d_in
        self.length = length
        self.composition = composition
        self.props = props
        self.name = name
        self.units = units

    def write_yaml(self, fname="st_hex_parameters_file.yaml"):
        """
        Write a yaml file

        Parameters
        ----------
        fname : string, optional
            file name. The default is "st_hex_parameters_file.yaml".

        Returns
        -------
        None.

        """

        with open(fname, mode="wt", encoding="utf-8") as file:
            yaml.dump(self, file)

    def read_yaml(fname="st_hex_parameters_file.yaml"):
        """
        read a yaml file

        Parameters
        ----------
        fname : string, optional
            file name. The default is "out_fileN.yaml".

        Returns
        -------
        neu : instance of st_heat_exchanger_input
            to be used as input.

        """
        with open(fname, mode="rt", encoding="utf-8") as file:
            neu = yaml.unsafe_load(file)
            return neu

    def all_out(self):
        """
        format the list output in such a way that it can be used as input 
        for the counterflow heat exchanger.
        If the latter should be modified, this has to be modified too!

        Returns
        -------
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.

        """
        return (self.fluids, self.mass_flows, self.pressures, self.enthalpies,
                self.length, self.d_in, self.heat_transfer_coefficient,
                self.no_tubes, self.no_points, self.props, self.composition,
                self.calc_type, self.name,
                self.units)

    def read_hex_file(fn, out, all_out=False):
        """
        Reads an Excel File with information about heat exchangers, fluids etc.
        is used within carbatpy and the module heat_exchanger (see there for the
        specific output)

        Parameters
        ----------
        fn : string
            name of an excel-file with at least 4 sheets as mentioned above, which 
            list the variable names, values and further parameters and comments.
        out : string 
            only "HEXSimple" implemented so far, for the simple heat exchanger 
            calculations with actual fluid properties in a counterflow 
            configuration.
        all_out : boolean
            if True a list with 4 Instances with variable names and values are 
            returned together with all local variables (dictionaries) for usage
            in other modules.

        Returns
        -------
        list 
            if HEXSimple: a list with the required values for setting up the problem
            if (internally).
            if all_out is True, see above.

        """

        druck = False  # printing?
        xl = pd.ExcelFile(fn, engine='openpyxl')   # Einlesen
        if druck:
            print(f"sheet names in {fn}: {xl.sheet_names}")

        data = []
        dfs = []
        outputs = []

        for sheet in xl.sheet_names:
            blatt0 = sheet    # erstes Blatt in der Datei
            df1 = xl.parse(blatt0)
            dfs.append(df1)
            # d = df1.to_numpy()
            # data.append(d)
            n_app = ""
            c_names = df1.columns
            dict_list = locals()[blatt0] = [v.dropna().to_dict()
                                            for k, v in df1.iterrows()]
            bi = locals()[blatt0+"_Instance"] = type(blatt0, (object,), {})
            if blatt0 == "Geometry":
                Geometry_Instance = bi
            elif blatt0 == "Fluid_1":
                Fluid1_Instance = bi
            elif blatt0 == "Fluid_2":
                Fluid2_Instance = bi
            elif blatt0 == "Problem_description":
                Problem_description = bi
            else:
                print(f"Warning: sheet {blatt0} is not used!")

            fluids = []
            # print(blatt0, dict_list)

            for di in dict_list:
                # name a class using a string
                # add an attribute name from a strng
                setattr(bi, di["variable_name"], di)

            if sheet[:3] == 'Flu':

                fl_names = []
                compo = []

                fluid_no = bi.number_compounds["value"]
                for ii in range(fluid_no):
                    fname = getattr(bi, "fl"+str(ii+1))
                    fl_names.append(fname['name_fluid'])

                    compo.append(float(fname["value"]))
                    if druck:
                        print(ii, compo, 'fl'+str(ii+1), fl_names)

                if fluid_no > 1:
                    if druck: print(fl_names, "---")
                    fluids = "*".join(fl_names)

                else:
                    fluids = fl_names[0]
                state_in = tp(float(bi.T_in["value"]),
                              float(bi.p_in["value"]),
                              fluids, compo, props=bi.props["value"])
                # print(state_in)
                enthalpy = state_in[2]

                test = hp(enthalpy,
                          float(bi.p_in["value"]),
                          fluids, compo, props=bi.props["value"])

                
                setattr(bi, "composition_all", compo)
                setattr(bi, "fluidNamesREFPROP", fluids)
                setattr(bi, "enthalpy", enthalpy)
                dict_list.append({"composition_all": compo,
                                 "fluidNamesREFPROP": fluids})

            outputs.append(bi)

        xl.close()
        if all_out:
            return outputs, locals()

        elif out == "HEXsimple":  # BA Reihnfolge prüfen
            if Fluid1_Instance.props["value"] == Fluid2_Instance.props["value"]:
                props = Fluid1_Instance.props["value"]
            else:
                print(
                    f"Props should be the same for both fluids, check input file {fn}")
                props = "Error!"

            outputHex = [[Fluid1_Instance.fluidNamesREFPROP,
                          Fluid2_Instance.fluidNamesREFPROP],
                         [Fluid1_Instance.m_dot["value"],
                         Fluid2_Instance.m_dot["value"]],
                         [Fluid1_Instance.p_in["value"],
                         Fluid2_Instance.p_in["value"]],
                         [Fluid1_Instance.enthalpy,
                         Fluid2_Instance.enthalpy],
                         Geometry_Instance.length["value_1"],
                         [Geometry_Instance.d_in["value_1"],
                         Geometry_Instance.d_in["value_2"]],
                         Geometry_Instance.U["value_1"],
                         Geometry_Instance.tubes["value_1"],
                         Geometry_Instance.no_points["value_1"],
                         props,
                         [Fluid1_Instance.composition_all,
                         Fluid2_Instance.composition_all],
                         Geometry_Instance.calc_type["value_1"],
                         Geometry_Instance.hex_name["value_1"],
                         Fluid1_Instance.units["value"]
                         ]
            hexin = st_heat_exchanger_input(*outputHex,)
            # all what is needed for heat_exchanger.counterflow_hex
            print("Properties from input file (Excel):\n", outputHex)
            return hexin  # outputHex

        else:
            print(f"{out} is not implemented yet!")


if __name__ == "__main__":

    T0 = 283.  # K
    props = "REFPROP"  # "CoolProp"  or "REFPROP"
    mdot = [.012, .0213]  # kg/s for both fluids
    # heat transfer coefficient through the wall (from total resistance)
    alpha = 500
    Tin = [354, 290]  # initial fluid temperatures, assuming single phae each!
    p = [5e5, 4.e5]  # pressure for each fluid, Pa
    tubes = 12
    d_in = 1.e-2
    A_min = tubes * np.pi * (d_in/2)**2
    d_out_min = np.sqrt(A_min / np.pi) * 2
    diameters = [d_in, float(d_out_min * 1.25)]  # m
    no_points = 100
    length = 4.  # m
    # with open("out_fileN.yaml", mode="wt", encoding="utf-8") as file:
    #     yaml.dump(T0, file)
    #     yaml.dump(props, file)
    #     yaml.dump_all((mdot,Tin), file)

    if props == "CoolProp":
        # Isobutane (hot) and water (cold)
        fl_names = ["ISOBUTANE", "NONANE"]
        fl1 = CP.AbstractState("REFPROP", fl_names[0])
        # fl1.set_mole_fractions([0.5,0.5])
        # fl1.build_phase_envelope("")
        # pe_fl1 = fl1.get_phase_envelope_data()
        fl2 = CP.AbstractState("BICUBIC&HEOS", fl_names[1])
        fl = [fl1, fl2]   # which fluids?
        compositions = [[1], [1.]]
    if props == "REFPROP":
        fl1 = "Propane * Pentane"
        fl2 = "Water"
        compositions = [[.6, .4], [1.]]
        # fl = fl_names
        fl = [fl1, fl2]

    #  evaluate enthalpies and maximum possible enthalpy changes:
    ha_in = tp(Tin[0], p[0], fl[0], props=props,
               composition=compositions[0])[2]  # state of fluid 1 left
    hb_in = tp(Tin[1], p[1], fl[1], props=props,
               composition=compositions[1])[2]  # state of fluid 2 right (at L)
    ha_outMax = tp(Tin[1], p[0], fl[0], props=props,
                   composition=compositions[0])[2]  # state of fluid 1 left
    hb_outMax = tp(Tin[0], p[1], fl[1], props=props,
                   composition=compositions[1])[2]  # state of fluid 2 right (at L)

    neu = st_heat_exchanger_input(fl, mdot, p, [float(ha_in), float(hb_in)],
                                  length, diameters, alpha, tubes, no_points,
                                  props, compositions)
    neu.write_yaml("st_hex_parameters_fileN.yaml")
    t0 = time()
    heat_ex = counterflow_hex(fl, mdot, p, [ha_in, hb_in],
                              length, diameters, U=alpha, no_tubes=tubes,
                              props=props, compositions=compositions)  # assign parameters
    hex2 = counterflow_hex(*neu.all_out())

    t1 = time()
    res = heat_ex.he_bvp_solve()  # solve the heat exchanger problem
    tf = time()

    print("time:", tf-t0, tf-t1)
    f1, f2, ds, dq = heat_ex.he_state(
        res, 6, "new.x")  # evaluate results (and plot)
    ex_in = heat_ex.exergy_entering()
    print("Entropy production rate: %2.2e W/K, exergy loss rate %3.3f W, dq %3.2f"
          % (ds, ds * T0, dq))
    print("Exergy flow rate, entering: %3.3f W" % (ex_in))
