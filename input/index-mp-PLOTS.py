#Use this file to imput what post processing tests you want to utalize in the code. 

#Name of the Output animation/figures/plots 
fig_name = "200000-SW-Run" #Name of the output animation/figures/plots

useWeights_x = False              # NOT CURRENTLY IN USE - LEAVE FALSE - Use weights in x-direction
useWeights_y = False           # Use gaussian weights in y-direction
useWeights_xi = False          # Use gaussian weights in xi-direction

skipWeightingCalc = False            # Skip weighting calculation and use imported pre-calculated weights
saveWeights = False                 # Save weights to .npz file (Remember to move to ./data directory!)

# Masking Options:
useMasks_xi = True              # Use masks in xi-direction (Vertical; done during weighting)
useMasks_y = True          # Use masks in y-direction (Horizontal; done during weighting)
useMasks_x = False                  # NOT CURRENTLY IN USE - LEAVE FALSE - Use masks in x-direction (transverse; done during weighting)

# Plotting Scripts
showQuickEvolution = False  # View evolution of probe after leaving plasma at inputted x_s in scatter plots # Use for low density probes
showFullEvolution = False# View full evolution of probe at hardcoded locations in colored histograms # Use for high density probes
makeFullAnimation = True   # Make full animation of probe evolution at hardcoded locations in colored histograms # Use for high density probes
writeHistData = False

# Gaussian Weighting Testing
plotWeightsx = False                  # Plot w vs xi (ONLY for single line of particles in x-dir)
plotWeightsy = False                  # Plot w vs y (ONLY for single line of particles in y-dir)
plotWeightsxi = False                  # Plot w vs y (ONLY for single line of particles in xi-dir)
plotWeightsxiy = False                 # Plots initial particle density map
plotWeights3D = False                  # Plots y, xi, and 2D cross section

# DEBUG PLOTTING
plot2DTracks = False                 # View 2D projections of trajectories (SET ALL OTHERS TO FALSE & ONLY USE FOR SINGLE PARTICLE)
findFocal = True
plot3DTracks = False
findW = False