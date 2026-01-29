#Input file for a probe travelling through the blowout regime in simulation '000130'
#Created on: 6/13/2022

simulation_name = 'QUASI3D'
shape = 'single'
# dt = 0.005, 150000
iterations = 500000
mode = 0 #0 is just wake fields, 1 is laser fields, -1 for both
fname = "betatron_test.npz" # Originally wakefield_test.npz
debugmode = True

# Probe centered at the following initial coordinates (in c/w_p):
x_c = 0.0 # Start within region of field # 2.4 = maximum x_c
y_c = 0.15
xi_c = -8.5

# Initial momentum
px_0 = 0 # Make sure it goes towards the screen!
py_0 = 0
pz_0 = 20 # Only moving in driver direction

# Screen Distances (from z-axis of plasma cell, in mm):
x_s = [10, 50, 100, 250, 500]

# Shape Parameters (Radius or Side Length, in c/w_p): For this test, equal and 1
s1 = 1 # In y
s2 = 1 # In xi

# Densities: Single Electron
ydensity = 1
xidensity = 1
xdensity = 1 # Probe width - single layer
resolution = None
