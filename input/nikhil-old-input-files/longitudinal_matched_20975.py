#Input file for a probe travelling through the blowout regime in simulation '000130'
#Created on: 6/13/2022

simulation_name = 'QUASI3D'
shape = 'single'
# dt = 0.005, 150000
iterations = 500000
mode = 0 #0 is just wake fields, 1 is laser fields, -1 for both
fname = "longitudinal_matched_20975.npz"
debugmode = True

# Probe centered at the following initial coordinates (in c/w_p):
x_c = -2.0 # Start within region of field # 2.4 = maximum x_c
y_c = 0.20
xi_c = -8.2110679932235 # This is the xi such that when electron reaches x = 0, xi = -8.3 (inside wakefield)

# Initial momentum
px_0 = 9.4872408560496 # Make sure it goes towards the screen! ; Did calculation to have v_z = 0.9958959 (group velocity of LWFA) and have total gamma (total p in normalized units) be about 108 to match LWFA gamma
py_0 = 0
pz_0 = 107.65401041595  # Did calculation to have v_z = 0.9958959 (group velocity of LWFA) and have total gamma (total p in normalized units) be about 108 to match LWFA gamma

# Screen Distances (from z-axis of plasma cell, in mm):
x_s = [10, 50, 100, 250, 500]

# Shape Parameters (Radius or Side Length, in c/w_p):
s1 = 1 # In y
s2 = 1 # In xi

# Densities
ydensity = 1
xidensity = 1
xdensity = 1 # Probe width - single layer
resolution = None
