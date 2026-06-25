#Use this file to imput what post processing tests you want to utalize in the code. 

#Name of the Output animation/figures/plots 
fig_name = "test1"

useWeights_x = False                 # NOT CURRENTLY IN USE - LEAVE FALSE - Use weights in x-direction
useWeights_y = False                  # Use gaussian weights in y-direction
useWeights_xi = False                 # Use gaussian weights in xi-direction

skipWeightingCalc = False            # Skip weighting calculation and use imported pre-calculated weights
saveWeights = True                 # Save weights to .npz file (Remember to move to ./data directory!)

# Masking Options:
useMasks_xi = False                 # Use masks in xi-direction (Vertical; done during weighting)
useMasks_y = False                  # Use masks in y-direction (Horizontal; done during weighting)
useMasks_x = False                  # NOT CURRENTLY IN USE - LEAVE FALSE - Use masks in x-direction (transverse; done during weighting)

# Plotting Scripts
showQuickEvolution = True           # View evolution of probe after leaving plasma at inputted x_s in scatter plots # Use for low density probes
showFullEvolution = False             # View full evolution of probe at hardcoded locations in colored histograms # Use for high density probes
makeFullAnimation = False
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