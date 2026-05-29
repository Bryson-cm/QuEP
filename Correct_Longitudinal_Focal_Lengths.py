import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO

# Raw data
data = """y	f
0.05	1.368191181
0.05	1.483622901
0.05	1.543716759
0.05	1.605305997
0.05	1.668794776
0.05	1.733485364
0.05	1.867214169
0.1	1.371942466
0.1	1.489121676
0.1	1.549996363
0.1	1.612498535
0.1	1.676484145
0.1	1.742219651
0.1	1.877769702
0.15	1.376079663
0.15	1.494518674
0.15	1.555756343
0.15	1.61863099
0.15	1.683854812
0.15	1.750477325
0.15	1.888431111
0.2	1.378121811
0.2	1.499592143
0.2	1.562591345
0.2	1.627081932
0.2	1.692348024
0.2	1.760387127
0.2	1.90144204
0.25	1.381659857
0.25	1.506007287
0.25	1.570794901
0.25	1.637248119
0.25	1.705073126
0.25	1.774019731
0.25	1.919027913
0.3	1.386869315
0.3	1.515125673
0.3	1.582474242
0.3	1.651290371
0.3	1.721489846
0.3	1.792917101
0.3	1.943052451
0.35	1.395312637
0.35	1.529449632
0.35	1.59967902
0.35	1.671545619
0.35	1.744468246
0.35	1.820004076
0.35	1.976708464
0.4	1.409568596
0.4	1.55160875
0.4	1.625800737
0.4	1.700458943
0.4	1.778752246
0.4	1.858794113
0.4	2.023877493
0.45	1.433664262
0.45	1.586691252
0.45	1.66549951
0.45	1.747280948
0.45	1.830915165
0.45	1.916219885
0.45	2.093432766
0.5	1.477272345
0.5	1.644797312
0.5	1.731997291
0.5	1.82054418
0.5	1.912693913
0.5	2.006965378
0.5	2.200497467
0.55	1.557971976
0.55	1.748691754
0.55	1.84776629
0.55	1.948666682
0.55	2.053765454
0.55	2.160801865
0.55	2.381292643
0.6	1.730374957
0.6	1.961423093
0.6	2.082987491
0.6	2.207816721
0.6	2.335002471
0.6	2.465083032
0.6	2.73523579"""

# Read into a DataFrame
df = pd.read_csv(StringIO(data), sep='\t')

# Group and process
grouped = df.groupby('y')
y_vals, medians, err_closest, err_middle, err_farthest = [], [], [], [], []

for y_val, group in grouped:
    f_vals = group['f'].values
    median = np.median(f_vals)
    y_vals.append(y_val)
    medians.append(median)

    deviations = np.abs(f_vals - median)
    sorted_indices = np.argsort(deviations)

    err_closest.append(np.max(deviations[sorted_indices[:2]]))
    err_middle.append(np.max(deviations[sorted_indices[2:5:2]]))
    err_farthest.append(np.max(deviations[sorted_indices[-2:]]))

# Conversion factor
conversion_factor = 0.168098899

# Helper function for plotting
def plot_error_graph(y, f, errors, title, marker_style):
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Primary y-axis
    ax1.errorbar(y, f, yerr=errors, fmt=marker_style, capsize=5, label='Focal Length Error')
    ax1.set_title(title, fontsize=14)
    ax1.set_xlabel(r'Initial Height $y_0/r_b$ (c/$\omega_p$)', fontsize=12)
    ax1.set_ylabel(r'Focal Length $f$ (c/$\omega_p$)', fontsize=12)
    ax1.grid(True)

    # Secondary y-axis
    ax2 = ax1.twinx()
    ax2.set_ylabel(r'Focal Length $f$ (mm)', fontsize=12)
    ax2.set_ylim(ax1.get_ylim()[0] * conversion_factor, ax1.get_ylim()[1] * conversion_factor)

    plt.tight_layout()
    plt.show()

# Plot 1: Closest
plot_error_graph(y_vals, medians, err_closest,
                 "Longitudinal Focal Lengths vs. Initial Height\n(2.5 Percent Error in Angle)", 'o-')

# Plot 2: Middle
plot_error_graph(y_vals, medians, err_middle,
                 "Longitudinal Focal Lengths vs. Initial Height\n(5 Percent Error in Angle)", 's-')

# Plot 3: Farthest
plot_error_graph(y_vals, medians, err_farthest,
                 "Longitudinal Focal Lengths vs. Initial Height\n(10 Percent Error in Angle)", '^-')