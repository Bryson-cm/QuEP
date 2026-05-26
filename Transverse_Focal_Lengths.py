import matplotlib.pyplot as plt
import numpy as np

# Data
x_values = np.array([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6])
y_values = np.array([169.2840296, 171.2624697, 173.9063867, 177.3919858, 182.2653176, 188.3922892, 196.7511017, 207.8545887, 223.1069997, 244.7927936, 278.072947, 339.2181298])

# Create a plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Unique heights
unique_heights = np.unique(x_values)

# Prepare lists for central values and error bars
central_values = []
lower_error = []
upper_error = []

# For each unique height, calculate the central value and the error bars
for height in unique_heights:
    indices = np.where(x_values == height)
    values_at_height = y_values[indices]
    
    central_value = np.mean(values_at_height)
    central_values.append(central_value)
    
    # The error bars are the maximum deviation from the central value
    max_deviation = np.max(np.abs(values_at_height - central_value))
    lower_error.append(max_deviation)
    upper_error.append(max_deviation)

# Convert lists to numpy arrays for plotting
central_values = np.array(central_values)
lower_error = np.array(lower_error)
upper_error = np.array(upper_error)

# Set colors to black for the axes, but blue for the points
axis_color = 'black'
point_color = 'blue'

# Plot the central values with error bars
ax1.errorbar(unique_heights, central_values, yerr=[lower_error, upper_error], fmt='o', color=point_color, label='Focal Length f (c/ω_p)', markersize=8)

# Set the labels for the left axis with LaTeX for subscripts
ax1.set_xlabel(r'Initial Height $y_0 / r_b$ (c/$\omega_p$)', color=axis_color)
ax1.set_ylabel(r'Focal Length $f$ (c/$\omega_p$)', color=axis_color)
ax1.tick_params(axis='y', labelcolor=axis_color)
ax1.tick_params(axis='x', labelcolor=axis_color)

# Create a second vertical axis on the right with the same color
ax2 = ax1.twinx()

# Scale the central values to mm for the right vertical axis
central_values_mm = central_values * 0.168098899
lower_error_mm = lower_error * 0.168098899
upper_error_mm = upper_error * 0.168098899

# Plot the central values in mm with error bars
ax2.errorbar(unique_heights, central_values_mm, yerr=[lower_error_mm, upper_error_mm], fmt='x', color=point_color, label='Focal Length f (mm)', markersize=8)

# Set the labels for the right axis with LaTeX for subscripts
ax2.set_ylabel(r'Focal Length $f$ (mm)', color=axis_color)
ax2.tick_params(axis='y', labelcolor=axis_color)

# Display the plot
fig.tight_layout()
plt.title('Transverse Focal Length vs Initial Height', color=axis_color)

plt.show()