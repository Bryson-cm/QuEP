import matplotlib.pyplot as plt
import numpy as np

# Data
x_values = np.array([0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 
                     0.2, 0.2, 0.2, 0.2, 0.2, 0.25, 0.25, 0.25, 0.25, 0.25, 0.3, 0.3, 0.3, 0.3, 0.3, 
                     0.35, 0.35, 0.35, 0.35, 0.35, 0.4, 0.4, 0.4, 0.4, 0.4, 0.45, 0.45, 0.45, 0.45, 
                     0.45, 0.5, 0.5, 0.5, 0.5, 0.5, 0.55, 0.55, 0.55, 0.55, 0.55, 0.6, 0.6, 0.6, 0.6, 
                     0.6])
y_values = np.array([1.155809489, 1.368191181, 1.605305997, 1.867214169, 2.153283415, 1.158311283, 1.371942466,
                     1.612498535, 1.877769702, 2.167954466, 1.157643706, 1.376079663, 1.61863099, 1.888431111,
                     2.183060336, 1.155814077, 1.378121811, 1.627081932, 1.90144204, 2.20241273, 1.153061397,
                     1.381659857, 1.637248119, 1.919027913, 2.228257639, 1.150168407, 1.386869315, 1.651290371,
                     1.943052451, 2.262150958, 1.14786326, 1.395312637, 1.671545619, 1.976708464, 2.309939419,
                     1.148029264, 1.409568596, 1.700458943, 2.023877493, 2.377057797, 1.153617536, 1.433664262,
                     1.747280948, 2.093432766, 2.471544767, 1.168814577, 1.477272345, 1.82054418, 2.200497467,
                     2.61800894, 1.207366998, 1.557971976, 1.948666682, 2.381292643, 2.856979844, 1.304350215,
                     1.730374957, 2.207816721, 2.73523579, 3.313816554])

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
plt.title('Longitudinal Focal Length vs Initial Height', color=axis_color)

plt.show()