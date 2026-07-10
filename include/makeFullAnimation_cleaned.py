"""
makeFullAnimation.py

Cleaned animation-frame plotting module for QuEP electron probe data.

This version intentionally uses the same secondary-axis style as
showFullEvolution_cleaned.py:

    returnXi(z, t0) = z - t0
    returnZ(xi, t0) = xi + t0
    secondary_xaxis(..., functions=(lambda z: returnXi(z, t0), ...))

No axis_offset variable is used, and index-mp.py does not need to change.
"""

import copy
import os
import time
import sys
import importlib
import matplotlib as mpl
mpl.use("Agg")  # Non-interactive backend for scripts / HPC jobs
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 12})
plt.rcParams["figure.constrained_layout.use"] = True

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C = 299_892_458  # Speed of light in vacuum [m/s]

# -----------------------------------------------------------------------------
# User-adjustable plotting settings
# -----------------------------------------------------------------------------

USE_WB = False
USE_VIRIDIS = False
USE_BUPU = False
USE_JET = True

# Animation screen locations in mm.
# np.linspace(xstart_mm, xend_mm, number_of_frames) is used below.
XSTART_MM = 0.0
XEND_MM = 150.0
NUMBER_OF_FRAMES = 1000

# Z/Y plot limits in normalized units c/omega_p.
# These are set to match the style/range used in showFullEvolution_cleaned.py.
# Change these if your run is centered somewhere else.
Z_LIMITS = (44,45.2)
Y_LIMITS = (-1.5, 1.5)

# Histogram bin spacing in normalized units c/omega_p.
BIN_RESOLUTION_Z = 0.012
BIN_RESOLUTION_Y = 0.012

CMIN = 1
VMIN = 0
VMAX = 10
FPS = 20

# Stored in prepare() and also attached to cmap so multiprocessing workers
# can recover the same t0 without changing index-mp.py unpacking/call signatures.
_T0_FOR_SECONDARY_AXIS = None
_FACECOLOR = "white"

_MIN_X_MM = None
_MIN_WIDTH = None

# -----------------------------------------------------------------------------
# Coordinate helpers: same method as showFullEvolution_cleaned.py
# -----------------------------------------------------------------------------

def returnXi(z, t0):
    """Convert z to xi for the secondary top axis: xi = z - t0."""
    return z - t0


def returnZ(xi, t0):
    """Convert xi back to z for the secondary top axis: z = xi + t0."""
    return xi + t0


def add_secondary_xi_axis(ax, t0):
    """
    Add a top xi axis to a z-axis plot.

    Matplotlib secondary-axis functions must accept exactly one argument,
    so t0 is supplied through lambda functions. This matches the method used
    in showFullEvolution_cleaned.py.
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


# -----------------------------------------------------------------------------
# Motion helpers
# -----------------------------------------------------------------------------

def Gamma(p):
    return np.sqrt(1.0 + p**2)


def Velocity(p_component, p_total):
    """Return normalized relativistic velocity component."""
    return p_component / Gamma(p_total)


def getBallisticTraj(x_0, y_0, z_0, px, py, pz, x_screen):
    """
    Project particles ballistically to a screen at x_screen.

    This preserves the original vectorized behavior: x_0, y_0, z_0, px, py,
    and pz may be NumPy arrays.
    """
    px_safe = np.where(px == 0, np.nan, px)
    dx = x_screen - x_0
    y_screen = y_0 + dx * (py / px_safe)
    z_screen = z_0 + dx * (pz / px_safe)
    return y_screen, z_screen

def get_beam_width(y_plot, weights):
    """
    Return full beam width using only unmasked particles.

    Masked particles have weight = 0, so they are ignored.
    Full width = max(y) - min(y)
    """
    y_plot = np.asarray(y_plot, dtype=float)
    weights = np.asarray(weights, dtype=float)

    good = (
        np.isfinite(y_plot)
        & np.isfinite(weights)
        & (weights > 0)
    )

    if np.sum(good) == 0:
        return np.nan

    y_good = y_plot[good]

    return np.max(y_good) - np.min(y_good)
def calculate_min_width_once(
    x_f,
    y_f,
    z_f,
    px_f,
    py_f,
    pz_f,
    w,
    plasma_bnds,
    xs_norm,
    screen_dists,
):
    """
    Calculate the minimum beam width once before making frames.
    """

    min_width = np.inf
    min_x = np.nan

    for i in range(len(xs_norm)):

        if abs(xs_norm[i]) > plasma_bnds[2]:
            y_plot, z_plot = getBallisticTraj(
                x_f, y_f, z_f,
                px_f, py_f, pz_f,
                xs_norm[i],
            )
        else:
            y_plot = y_f

        width = get_beam_width(y_plot, w)

        if width < min_width:
            min_width = width
            min_x = screen_dists[i]

    return min_x, min_width
# -----------------------------------------------------------------------------
# Plot setup helpers
# -----------------------------------------------------------------------------

def get_simulation_module(sim_name):
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
    if USE_WB:
        return plt.cm.binary, "white"

    if USE_VIRIDIS:
        return plt.cm.viridis, "white"

    if USE_BUPU:
        return plt.cm.BuPu, "white"

    if USE_JET:
        cmap = copy.copy(plt.get_cmap("jet"))
        cmap.set_under(color="white")
        return cmap, "white"

    return plt.cm.gist_gray, "white"


def normalize_screen_positions(screen_dists_mm, plasma_frequency):
    """Convert screen locations from mm to normalized units c/omega_p."""
    return np.asarray(screen_dists_mm, dtype=float) * plasma_frequency * 1e-3 / C


def make_bin_edges(limits, spacing):
    """Create histogram bin edges that include the upper limit."""
    lo, hi = limits
    return np.arange(lo, hi + spacing, spacing)


# -----------------------------------------------------------------------------
# Main entry points used by index-mp.py
# -----------------------------------------------------------------------------

def prepare(sim_name, shape_name, noObj, rand):
    """Prepare shared plotting parameters for animation frame generation."""
    global _T0_FOR_SECONDARY_AXIS, _FACECOLOR



    sim = get_simulation_module(sim_name)
    input_module = str(sys.argv[1])
    init = importlib.import_module(input_module)
    sim.configure(init)

    t0 = sim.getTime()
    plasma_frequency = sim.getPlasFreq()
    plasma_bnds = sim.getBoundCond()

    screen_dists = list(np.linspace(XSTART_MM, XEND_MM, NUMBER_OF_FRAMES))
    xs_norm = normalize_screen_positions(screen_dists, plasma_frequency)
    slices = len(screen_dists)

    bin_edges_z = make_bin_edges(Z_LIMITS, BIN_RESOLUTION_Z)
    bin_edges_y = make_bin_edges(Y_LIMITS, BIN_RESOLUTION_Y)

    cmap, facecolor = get_colormap()
    _T0_FOR_SECONDARY_AXIS = t0
    _FACECOLOR = facecolor

    # Attach metadata to cmap because cmap is already passed into plotmp().
    # This keeps index-mp.py unchanged while still giving multiprocessing
    # workers the t0 needed for the secondary xi axis.
    try:
        cmap._quep_t0 = t0
        cmap._quep_facecolor = facecolor
    except Exception:
        pass

    # Kept for compatibility with your existing index-mp unpacking style.
    yslice = np.empty([noObj])
    zslice = np.empty([noObj])

    path = os.getcwd()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    new_path = os.path.join(path, f"animation-{timestr}-{rand}")
    os.makedirs(new_path, exist_ok=False)

    zmin, zmax = Z_LIMITS
    ymin, ymax = Y_LIMITS

    # IMPORTANT: keep this return signature exactly compatible with index-mp.py.
    return (
        plasma_bnds,
        slices,
        xs_norm,
        yslice,
        zslice,
        bin_edges_z,
        bin_edges_y,
        cmap,
        CMIN,
        VMIN,
        VMAX,
        zmin,
        zmax,
        ymin,
        ymax,
        FPS,
        new_path,
        screen_dists,
    )


def plotmp(
    i,
    x_f,
    y_f,
    z_f,
    px_f,
    py_f,
    pz_f,
    w,
    xden,
    plasma_bnds,
    xs_norm,
    yslice,
    zslice,
    bin_edges_z,
    bin_edges_y,
    cmap,
    cmin,
    vmin_,
    vmax_,
    zmin,
    zmax,
    ymin,
    ymax,
    new_path,
    screen_dists,
):
    """Create and save one animation frame."""
    fig, ax = plt.subplots(1, figsize=(8, 5), dpi=600)

    # Project positions at this x screen. If the screen is still inside the
    # plasma bounds, keep the final plasma-exit coordinates, matching the
    # original behavior.
    if abs(xs_norm[i]) > plasma_bnds[2]:
        y_plot, z_plot = getBallisticTraj(x_f, y_f, z_f, px_f, py_f, pz_f, xs_norm[i])
    else:
        y_plot = y_f
        z_plot = z_f

    beam_width = get_beam_width(y_plot,w)
     
    global _MIN_X_MM, _MIN_WIDTH

    if _MIN_X_MM is None:
        _MIN_X_MM, _MIN_WIDTH = calculate_min_width_once(
            x_f,
            y_f,
            z_f,
            px_f,
            py_f,
            pz_f,
            w,
            plasma_bnds,
            xs_norm,
            screen_dists,
        )

    min_x_mm = _MIN_X_MM    
    min_width = _MIN_WIDTH

    h = ax.hist2d(
        z_plot[:],
        y_plot[:],
        weights=w[:],
        bins=(bin_edges_z, bin_edges_y),
        cmap=cmap,
        vmin=vmin_,
        vmax=vmax_,
        cmin=cmin,
    )

    # ax.text(
    #     zmin + 0.02 * (zmax - zmin),
    #     ymax - 0.20 * (ymax - ymin),
    #     f"x = {screen_dists[i]:.4f} mm",
    #     horizontalalignment="left",
    #     fontsize=10,
    #     color="black",
    # )

    # ax.text(
    #     zmin + 0.02 * (zmax - zmin),
    #     ymax - 0.32 * (ymax - ymin),
    #     f"beam width = {beam_width:.4f}",
    #     horizontalalignment="left",
    #     fontsize=10,
    #     color="black",
    # )
    ax.text(
        zmin + 0.02 * (zmax - zmin),
        ymax - 0.20 * (ymax - ymin),
        f"x = {screen_dists[i]:.4f} mm\n"
        f"beam width = {beam_width:.4f}\n"
        f"minimum x = {min_x_mm:.4f} mm",
        horizontalalignment="left",
        fontsize=10,
        color="black",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )
    # Recover t0 using the same lambda method as showFullEvolution_cleaned.py,
    # without changing the existing plotmp() call in index-mp.py.
    t0_for_axis = getattr(cmap, "_quep_t0", _T0_FOR_SECONDARY_AXIS)
    facecolor = getattr(cmap, "_quep_facecolor", _FACECOLOR)

    if t0_for_axis is None:
        # Last fallback for non-multiprocessing cases where prepare() was not called.
        # If your simulation module is not configured, this will fail loudly instead
        # of silently drawing the wrong secondary axis.
        raise RuntimeError(
            "t0 was not available for the secondary xi axis. Run prepare() before plotmp(), "
            "or pass t0 by attaching it to the cmap as done in prepare()."
        )

    ax.set_xlim(zmin, zmax)
    ax.set_ylim(ymin, ymax)
    ax.set_facecolor(facecolor)
    ax.set_xlabel(r"Z ($c/\omega_p$)")
    ax.set_ylabel(r"Y ($c/\omega_p$)")

    add_secondary_xi_axis(ax, t0_for_axis)

    cbar = plt.colorbar(h[3], ax=ax, orientation="horizontal")
    cbar.set_label("Electron Density")

    filenumber = "{:05.1f}".format(screen_dists[i]).replace(".", "-").replace("-", "m", 1) if screen_dists[i] < 0 else "{:05.1f}".format(screen_dists[i]).replace(".", "-")
    filename = os.path.join(new_path, f"progression-x-{filenumber}mm.png")
    fig.savefig(filename, dpi=600, transparent=False)
    plt.close(fig)
