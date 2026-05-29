# Here is where the initial conditions of the electron probe are defined
# This filename is the input parameter of the eProbe.py file

simulation_name = 'QUASI3D'
shape = 'single'
# dt = 0.005, 150000
iterations = 500000
mode = 0
fname = "single_arbitrary_eta_05.npz"
debugmode = True

# Probe centered at the following initial coordinates (in c/w_p):
x_c = -2.4 # Start within region of field # 2.4 = maximum x_c
y_c = 0.3
xi_c = -8.2 #-12.3 # Makes Z_0 = 39.7 since t0 ~ 51.99

# Initial momentum
px_0 = 1000 # Make sure it goes towards the screen!
py_0 = 0
pz_0 = 1830

# Screen Distances (from z-axis of plasma cell, in mm):
x_s = [10, 50, 100, 250, 500]

# Shape Parameters (Radius or Side Length, in c/w_p):
s1 = 1 # In y
s2 = 1 # In xi

# Densities
ydensity = 1
xidensity = 1
xdensity = 1 
resolution = 0.002

