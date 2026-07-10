"""
showFullEvolution.py

Cleaned full-evolution plotting module for QuEP electron probe data.

Main purpose
------------
1. Take final probe coordinates/momenta after the plasma interaction.
2. Project the probe ballistically to chosen screen locations.
3. Make weighted 2D density plots of Z vs Y at those screens.

This version removes the repeated fig5/fig6/fig7/fig8/fig9 blocks and replaces
all of them with one reusable plotting helper.
"""

import copy
import importlib
import math
import sys

import matplotlib as mpl
mpl.use("Agg")  # Non-interactive backend for scripts / HPC jobs
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 15})

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C = 299_892_458  # Speed of light in vacuum [m/s]

# -----------------------------------------------------------------------------
# User-adjustable plotting settings
# -----------------------------------------------------------------------------

# Screen locations in mm. These are the x locations where the probe is plotted.
X_SCREENS_MM = [0, 5, 10, 25, 50, 75, 100, 40, 200, 300, 400, 500]

# Choose color scheme. Only one should normally be True.
USE_WB = False
USE_VIRIDIS = False
USE_BUPU = False
USE_JET = True

# Histogram / axis settings.
BINS_Z = 1250
BINS_Y = 400
Z_LIMITS = (39.2,50)
Y_LIMITS = (-1.5, 1.5)
VMAX = 10

# Each tuple is: (screen indices, output suffix, y-axis limits, y-bins scale)
# Example: [0, 1, 2] means plot X_SCREENS_MM[0], X_SCREENS_MM[1], X_SCREENS_MM[2].
PLOT_GROUPS = [
    ([0, 1, 2], "prog1", Y_LIMITS, 1.0),
    ([3, 4, 5], "prog2", Y_LIMITS, 0.25),
    ([6, 7, 8], "prog3", Y_LIMITS, 0.5),
    ([9, 10, 11], "prog4", Y_LIMITS, 1.0),
]

# If you only want the old final plot behavior, use this instead:
# PLOT_GROUPS = [([3, 4, 5], "prog5", (-1.5, 1.5), 1.0)]


# -----------------------------------------------------------------------------
# Coordinate / motion helpers
# -----------------------------------------------------------------------------

def returnXi(z, t0):
    """
    Convert z to xi for the secondary top axis.

    Important: this keeps your original formula: xi = z - C*t0.
    If z and t0 are already normalized plasma units, this may need to be changed
    to xi = z - t0 instead.
    """
    return z - t0


def returnZ(xi, t0):
    """
    Convert xi back to z for the secondary top axis.

    This is the inverse of returnXi.
    """
    return xi + t0


def gamma_from_momentum(p):
    """Return relativistic gamma from normalized momentum magnitude."""
    return math.sqrt(1.0 + p**2)


def velocity_from_momentum(p_component, p_total):
    """Return normalized velocity component from normalized momentum."""
    return p_component / gamma_from_momentum(p_total)


def getBallisticTraj(x_0, y_0, xi_0, z_0, px, py, pz, x_screen):
    """
    Project one particle from its final plasma position to a screen location.

    The particle is assumed to drift ballistically after leaving the plasma.
    The x location is fixed by the screen; y and z are advanced using momentum
    ratios py/px and pz/px.
    """
    if px == 0:
        raise ZeroDivisionError("px is zero, so ballistic projection in x is undefined.")

    dx = x_screen - x_0

    # Straight-line projection using slopes from momentum ratios.
    y_screen = y_0 + dx * (py / px)
    z_screen = z_0 + dx * (pz / px)

    # Estimate elapsed time during the ballistic drift.
    p_total = math.sqrt(px**2 + py**2 + pz**2)
    vx = velocity_from_momentum(px, p_total)
    vy = velocity_from_momentum(py, p_total)
    vz = velocity_from_momentum(pz, p_total)
    v_total = math.sqrt(vx**2 + vy**2 + vz**2)

    distance = math.sqrt(
        (x_screen - x_0) ** 2
        + (y_screen - y_0) ** 2
        + (z_screen - z_0) ** 2
    )
    dt = distance / v_total

    # Keep your original xi update logic.
    xi_screen = xi_0 + dx * (pz / px) + dt

    return y_screen, xi_screen, z_screen


# -----------------------------------------------------------------------------
# Simulation / plotting helpers
# -----------------------------------------------------------------------------

def get_simulation_module(sim_name):
    """Return the correct simulation module based on sim_name."""
    sim_name = sim_name.upper()

    if sim_name == "OSIRIS_CYLINSYMM":
        import include.simulations.useOsiCylin as sim
    elif sim_name == "QUASI3D":
        import include.simulations.useQuasi3D as sim
    elif sim_name == "FBPIC":
        import include.simulations.useFBPIC as sim
    else:
        raise ValueError(f"Simulation name unrecognized: {sim_name}")

    return sim


def get_colormap():
    """Choose the colormap and background color from the global flags."""
    if USE_WB:
        return plt.cm.binary, "white"

    if USE_VIRIDIS:
        return plt.cm.viridis, "#30013b"

    if USE_BUPU:
        return plt.cm.BuPu, "white"

    if USE_JET:
        cmap = copy.copy(plt.get_cmap("jet"))
        cmap.set_under(color="white")
        return cmap, "white"

    return plt.cm.gist_gray, "white"


def normalize_screen_positions(x_screens_mm, plasma_frequency):
    """
    Convert screen locations from mm to normalized plasma units c/omega_p.
    """
    return np.asarray(x_screens_mm, dtype=float) * plasma_frequency * 1e-3 / C


def build_screen_slices(
    x_f,
    y_f,
    xi_f,
    z_f,
    px_f,
    py_f,
    pz_f,
    x_screens_norm,
    plasma_bnds,
    no_elec,
):
    """
    Build y, xi, and z arrays for every requested screen.

    If a screen is outside the plasma bounds, the particle is projected
    ballistically. If the screen is still inside the plasma bounds, this keeps
    the final plasma-exit coordinates.
    """
    n_screens = len(x_screens_norm)

    yslice = np.empty((n_screens, no_elec))
    xislice = np.empty((n_screens, no_elec))
    zslice = np.empty((n_screens, no_elec))

    for i, x_screen in enumerate(x_screens_norm):
        screen_outside_plasma = abs(x_screen) > plasma_bnds[2]

        for j in range(no_elec):
            if screen_outside_plasma:
                yslice[i, j], xislice[i, j], zslice[i, j] = getBallisticTraj(
                    x_f[j], y_f[j], xi_f[j], z_f[j],
                    px_f[j], py_f[j], pz_f[j],
                    x_screen,
                )
            else:
                yslice[i, j] = y_f[j]
                xislice[i, j] = xi_f[j]
                zslice[i, j] = z_f[j]

    return yslice, xislice, zslice


def add_secondary_xi_axis(ax, t0):
    """
    Add a top xi axis to a z-axis plot.

    Matplotlib secondary-axis functions must accept exactly one argument.
    The lambda functions pass in t0 without causing the missing-argument error.
    """
    secax = ax.secondary_xaxis(
        "top",
        functions=(
            lambda z: returnXi(z, t0),
            lambda xi: returnZ(xi, t0),
        ),
    )
    secax.set_xlabel(r"$\xi$ ($c/\omega_p$)")
    return secax


def make_evolution_plot(
    screen_indices,
    output_filename,
    yslice,
    zslice,
    weights,
    t0,
    shape_name,
    cmap,
    facecolor,
    y_limits=(-6, 6),
    bins_y=BINS_Y,
):
    """
    Make one stacked evolution plot for selected screen indices.
    """
    n_panels = len(screen_indices)
    fig, axs = plt.subplots(
        n_panels,
        sharex=True,
        sharey=True,
        figsize=(8, 3.2 * n_panels),
        dpi=600,
    )

    # Make axs iterable even if n_panels == 1.
    axs = np.atleast_1d(axs)

    fig.suptitle(f"Progression of {shape_name} EProbe")

    hist = None
    
    for ax, screen_idx in zip(axs, screen_indices):
        hist = ax.hist2d(
            zslice[screen_idx, :],
            yslice[screen_idx, :],
            weights=weights,
            bins=(BINS_Z, bins_y),
            cmap=cmap,
            vmin=1,
            vmax=VMAX,
        )

        ax.set_title(f"X = {X_SCREENS_MM[screen_idx]} mm")
        ax.set_xlim(*Z_LIMITS)
        ax.set_ylim(*y_limits)
        ax.set_facecolor(facecolor)

    axs[-1].set_xlabel(r"Z ($c/\omega_p$)")
    axs[len(axs) // 2].set_ylabel(r"Y ($c/\omega_p$)")

    # Leave space on the right side for the colorbar
    fig.subplots_adjust(right=0.82, hspace=0.35)

    # Create a separate colorbar axis outside the plots
    cax = fig.add_axes([0.85, 0.15, 0.03, 0.70])
    #              [left, bottom, width, height]

    cbar = fig.colorbar(
    hist[3],
    cax=cax,
    orientation="vertical"
    )

    cbar.set_label("Electron Density")

    add_secondary_xi_axis(axs[0], t0)

    #fig.tight_layout()
    fig.savefig(output_filename, dpi=600, transparent=False)
    plt.close(fig)


# -----------------------------------------------------------------------------
# Main entry point used by index-mp.py
# -----------------------------------------------------------------------------

def plot(
    x_f,
    y_f,
    xi_f,
    z_f,
    px_f,
    py_f,
    pz_f,
    t0,
    w,
    sim_name,
    shape_name,
    noElec,
    iter,
    fig_name,
):
    """
    Plot the full post-plasma probe evolution.

    This function keeps the same call signature as the original code so that
    index-mp.py does not need to change.
    """
    print("Beginning Full Evolution Module")

    # Load and configure the correct simulation backend.
    sim = get_simulation_module(sim_name)
    input_module = str(sys.argv[1])
    init = importlib.import_module(input_module)
    sim.configure(init)

    plasma_frequency = sim.getPlasFreq()
    plasma_bnds = sim.getBoundCond()
    shape_name = shape_name.capitalize()

    # Convert requested screen locations from mm to normalized simulation units.
    x_screens_norm = normalize_screen_positions(X_SCREENS_MM, plasma_frequency)

    # Calculate particle positions at each screen.
    yslice, xislice, zslice = build_screen_slices(
        x_f=x_f,
        y_f=y_f,
        xi_f=xi_f,
        z_f=z_f,
        px_f=px_f,
        py_f=py_f,
        pz_f=pz_f,
        x_screens_norm=x_screens_norm,
        plasma_bnds=plasma_bnds,
        no_elec=noElec,
    )

    cmap, facecolor = get_colormap()

    # Create each requested plot group.
    for screen_indices, suffix, y_limits, y_bin_scale in PLOT_GROUPS:
        # Skip groups that refer to screen indices that do not exist.
        if max(screen_indices) >= len(X_SCREENS_MM):
            print(f"Skipping {suffix}: screen index is outside X_SCREENS_MM.")
            continue

        output_filename = f"{fig_name}_{suffix}.png"
        bins_y = max(1, int(BINS_Y * y_bin_scale))

        make_evolution_plot(
            screen_indices=screen_indices,
            output_filename=output_filename,
            yslice=yslice,
            zslice=zslice,
            weights=w,
            t0=t0,
            shape_name=shape_name,
            cmap=cmap,
            facecolor=facecolor,
            y_limits=y_limits,
            bins_y=bins_y,
        )

        print(f"Saved {output_filename}")
