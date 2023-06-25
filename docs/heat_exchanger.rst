
Heat Exchanger evaluation
=========================

A very basic heat exchanger class and a slightly better counter flow heat 
exchangers class is defined and functions to set their values and to calculate 
the change in properties along the heat exchanger are calculated using a 
boundary value problem solver. For the counterflow heat exchanger one shell 
and a number of inner tubes can be defined. One class is defined to read the 
input parameters from a YAML-File and to pass them to the heat excahnger class. 
The results are plotted and stored (also to an Excel file). Finally a 
run-script for the calculation is given as an example, which reads the 
data from the yaml-file, starts the heat-exchanger calculations and stores 
everything. The hex_run_script.py file should be a good starting point.
   
.. autoclass:: components.heat_exchanger.heat_exchanger
    :members:
    :no-members:
    
.. autoclass:: components.heat_exchanger.counterflow_hex
    :members:
    :no-members:

    
.. autoclass:: components.heat_exchanger.st_heat_exchanger_input
    :members:
    :no-members: