#This line will create betatron_example.py input file in the subfolder 'input'.

simulation_name = 'QUASI3D'  
#Explanation in README file. All simulations should have this as simulation name

shape = 'single'    
#betatron test only uses a singlular electron. See other options in README file for other sims

iterations = 40000
#Iterations refers to the amount of times the code is run. The input conditions are put into equations using main.py.
#A high number of iterations will have less space between each 't' value used which will have increased clarity in graphs

mode = -1 
#mode 0 is the wakefield, mode 1 is the laser, mode -1 is both. Betatron is to see electron in wakefield
#(optional) If calculations includes laser, include the region of laser (not needed if mode =0)
# Order does not matter; the code will sort them.
# laser_xi_start = -16
# laser_xi_end = -1.5

fname = "ATF_1D_lens.npz"
#main.py will put the data from the simulation into this file. name it whatever you want your data file to be

debugmode = True
#debugmode should only be true for single electron simulations (I'm not actually sure why)


# Probe centered at the following initial coordinates (in c/w_p):
#See figure 3.1 in Evan Trommer's thesis. The goal is to put the electron in line with the peak of the second bump of the field
#so while xi_c here is fairly fixed y_c can be any range of values still within the bubble
x_c = 1 #
y_c = 0.5 #
xi_c = -7

# Initial momentum
#set initial transverse momentum to zero and pz_0=20 (or any other number)
px_0 = 110  
py_0 = 0
pz_0 = 0

# Screen Distances (from z-axis of plasma cell, in mm):
x_s = [10, 50, 100, 250, 500]

# Shape Parameters (Radius or Side Length, in c/w_p):
s1 = 1 # In y
s2 = 1 # In xi

# Densities
#you only have a single electron so there should just be one when you count on any axis
ydensity = 1
xidensity = 1
xdensity = 1 # Probe width - single layer
resolution = None 

#Simulation specific parameters
simulation_name = "QUASI3D"
quasi_id = "000130"
quasi_data_dir = "data/OSIRIS/Quasi3D"
quasi_density = 1e21 #in m^-3
quasi_propagation_speed = 1.0
dt_safety_factor = 0.1 #this is multiplied by dz
