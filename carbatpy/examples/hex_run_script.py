# -*- coding: utf-8 -*-
"""
Example script for a (simple) counter flow heat exchamnger evaluation
Reading from an input yaml file
calculating, plotting and writimg the results to new files and storing them with 
date and time in a results directory. The main result are now stored as an
excel file (see heat_exchanger.he_state())

(within carbatpy)
Created on Sat May  6 10:02:19 2023

@author: atakan 
"""

import components.heat_exchanger as h_ex
from components.heat_exchanger import st_heat_exchanger_input
import pandas as pd
import os
import shutil
from datetime import datetime

directory_path = os.path.dirname(os.path.abspath(__file__))
resultsDir = "results"


# Name of the yaml-file
y_file_name0 = "st_hex_parameters_file1"
y_file_name = os.path.join(directory_path, y_file_name0)
T0 = 298.15

# read the yaml file as input
neu = h_ex.st_heat_exchanger_input.read_yaml(y_file_name+".yaml")

# new heat exchanger with the parameters from the file
hex2 = h_ex.counterflow_hex(*neu.all_out())

# solve the boundary value problem for the heat exchanger
res = hex2.he_bvp_solve()
print(f"Solution found: {res.success},  {res.message}")

# plotting and evalution:
# evaluate results (and plot)
f1, f2, ds, dq = hex2.he_state(res, 6, y_file_name+"calc")


# also adding the input to the Excel file as a new sheet
zzz = pd.DataFrame(dict((key, value) for (key, value) in neu.__dict__.items()))
mode ="w"
if os.path.exists(y_file_name+".xlsx"): mode ="a"
with pd.ExcelWriter(y_file_name+".xlsx", mode=mode) as writer:
    zzz.to_excel(writer, sheet_name="input")


ex_in = hex2.exergy_entering()
print("Entropy production rate: %2.2e W/K, exergy loss rate %3.3f W, dq %3.2f"
      % (ds, ds * T0, dq))
print("Exergy flow rate, entering: %3.3f W" % (ex_in))

# copying the results to a results directory, including date and time
now = datetime.now()
dt_string = now.strftime("_%Y_%m_%d_%H_%M_%S")
resDir = os.path.join(directory_path, resultsDir)

len_fn =len(y_file_name0)
dircont = os.listdir(directory_path)
for file in dircont:
    allparts = file.split(".")
    if len(allparts) > 1:
        nbase, nend = allparts
        print(nbase,y_file_name0 )
        if nbase[:len_fn] == y_file_name0:
            fname = nbase+dt_string+"."+nend
            resDir0 = os.path.join(resDir, fname)
            if nend == "yaml":
                shutil.copy(file, resDir0)
            else:
                shutil.move(file, resDir0)
