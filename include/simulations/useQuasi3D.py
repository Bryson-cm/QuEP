'''
# This file retrieves the fields from OSIRIS Quasi3D data files stored within the data/ folder.
# Expresses EM fields in azimuthal harmonics up to the first order
# Functions that MUST be updated for any new simulation (i.e. Called in either main.py or eProbe.py) are designated with three asterisks ***
# All other functions are used for either reading out data or plotting results
'''

# import sys
import h5py as h5
import numpy as np
import math
# import pdb

# Coordinate System
# z   - Direction of laser propagation (longitudinal)
# xi  - Position along z relative to wavefront
# r   - Cylindrical coordinate around z
# phi - Cylindrical coordinate around z, define phi = 0 along x
# x   - Direction of transverse probe
# y   - Direction perpendicular to transverse probe

# Modes
# mode = 0 refers to LWF effects only
# mode = 1 refers to laser effects only
# mode = any other integer uses LWF + laser effects

# Definition of Constants
M_E = 9.109e-31                       # Electron rest mass in kg
EC = 1.60217662e-19                   # Electron charge in C
EP_0 = 8.854187817e-12                # Vacuum permittivity in C/(V m)
C = 299892458                         # Speed of light in vacuum in m/s


Quasi_ID = None
Quasi_data_dir = None
Quasi_density = None
Quasi_propagation_speed = 1.0
Quasi_dt = None
Quasi_dt_safety_factor = 0.5
_reference_grid_info = None

Laser_A_enabled = False

Laser_xi_start = None
Laser_xi_end = None

Laser_xi_index_min = None
Laser_xi_index_max = None

Laser_A_ready = False

A1_M1_Re = None
A2_M1_Re = None
A3_M1_Re = None
A1_M1_Im = None
A2_M1_Im = None
A3_M1_Im = None

dA1_M1_Re_dxi = None
dA2_M1_Re_dxi = None
dA3_M1_Re_dxi = None
dA1_M1_Im_dxi = None
dA2_M1_Im_dxi = None
dA3_M1_Im_dxi = None

dA1_M1_Re_dr = None
dA3_M1_Re_dr = None
dA1_M1_Im_dr = None
dA3_M1_Im_dr = None



def configure(init):
    global Quasi_ID
    global Quasi_data_dir
    global Quasi_density
    global Quasi_propagation_speed
    global Quasi_dt
    global Quasi_dt_safety_factor
    global _reference_grid_info

    global Laser_A_enabled
    global Laser_xi_start
    global Laser_xi_end
    global Laser_A_ready

    Quasi_ID = init.quasi_id
    
    Quasi_data_dir = getattr(init, "quasi_data_dir", "data/OSIRIS/Quasi3D")
    Quasi_density = init.quasi_density
    Quasi_propagation_speed = getattr(init, "quasi_propagation_speed", 1.0)
   
    Quasi_dt = getattr(init, "dt", None)
    Quasi_dt_safety_factor = getattr(init, "dt_safety_factor", 0.5)
    
    # Laser vector-potential mode is automatically enabled whenever
    # the requested force calculation includes the laser.
    simulation_mode = getattr(init, "mode", 0)
    Laser_A_enabled = simulation_mode != 0

    # User may optionally restrict the laser-A calculation to a specific xi range.
    # If neither bound is provided, the full xi window is used.
    has_laser_start = hasattr(init, "laser_xi_start")
    has_laser_end = hasattr(init, "laser_xi_end")

    if has_laser_start != has_laser_end:
        raise ValueError(
            "Please provide both laser_xi_start and laser_xi_end, "
            "or omit both to use the full xi window."
        )
    if has_laser_start and has_laser_end:
        Laser_xi_start = min(init.laser_xi_start, init.laser_xi_end)
        Laser_xi_end = max(init.laser_xi_start, init.laser_xi_end)
    else:
        Laser_xi_start = None
        Laser_xi_end = None

    _reference_grid_info = None
    Laser_A_ready = False
    
    load_data()

    if Laser_A_enabled:
        buildLaserVectorPotential()

def qpath(stem):
    if Quasi_ID is None:
        raise ValueError("useQuasi3D has not been configured. Call configure(init) first.")
    return f"{Quasi_data_dir}/{stem}-{Quasi_ID}.h5"

def getField(fpath): 
    with h5.File(fpath, "r") as f:
        datasetNames = [n for n in f.keys()]
        field = datasetNames[-1]
        return f[field][:].astype(float)


def getTime(): # ***
    with h5.File(qpath("b1_cyl_m-0-re"), "r") as f:
        return f.attrs["TIME"][0]
 

def getPlasDensity(): 
    if Quasi_density is None:
        raise ValueError("quasi_density must be set in the input file.")
    return Quasi_density
#     if (Quasi_ID == '000130'):
#         return 1e21
#     elif (Quasi_ID == '000067'):
#         return 1.1e16
#     else:
#         return 3e23

def getPropagationSpeed(): # Define the group velocity of the laser
    return Quasi_propagation_speed
#     if (Quasi_ID == '000130'):
#         return 1.000 #THIS IS INCORRECT, JUST FOR TESTING
#     elif (Quasi_ID == '000067'):
#         return 0.9958959
#     else:
#         return 1

def getPlasFreq(): 
    N_0 = getPlasDensity()
    return math.sqrt(EC**2 * N_0 / (M_E * EP_0))

def _get_reference_grid_info():
    """
    Read and cache reference grid information from the B1 m=0 file.
    The reference file is used only to infer the grid geometry:
    axis bounds, number of grid points, and grid spacing.
    """
    global _reference_grid_info

    if _reference_grid_info is not None:
        return _reference_grid_info

    with h5.File(qpath("b1_cyl_m-0-re"), "r") as f:
        datasetNames = [n for n in f.keys()]
        field = datasetNames[-1]

        field_shape = f[field].shape
        a1_bounds = f["AXIS"]["AXIS1"][:]
        a2_bounds = f["AXIS"]["AXIS2"][:]

    # Field data is written as Field_dat[r, z]
    nr = field_shape[0]
    nz = field_shape[1]

    dz = (a1_bounds[1] - a1_bounds[0]) / nz
    dr = (a2_bounds[1] - a2_bounds[0]) / nr

    _reference_grid_info = {
        "a1_bounds": a1_bounds,
        "a2_bounds": a2_bounds,
        "nr": nr,
        "nz": nz,
        "dz": dz,
        "dr": dr,
    }
    return _reference_grid_info

def getGridSpacing():
    """
    Return longitudinal and radial grid spacing.
    Returns
    -------
    dz : float
        Longitudinal grid spacing.
    dr : float
        Radial grid spacing.
    """
    grid = _get_reference_grid_info()
    return grid["dz"], grid["dr"]

def axes():
    """
    Retrieve xi and r axes, accounting for the staggered mesh.
    xiaxis_1 is used for E1, B1.
    xiaxis_2 is used for E2, E3, B2, B3.
    raxis_1 is used for E2, B2.
    raxis_2 is used for E1, E3, B1, B3.
    """
    grid = _get_reference_grid_info()

    a1_bounds = grid["a1_bounds"]
    a2_bounds = grid["a2_bounds"]
    nr = grid["nr"]
    nz = grid["nz"]
    dz = grid["dz"]
    dr = grid["dr"]

    t0 = getTime()

    z_bounds_1 = [a1_bounds[0], a1_bounds[1]]
    z_bounds_2 = [a1_bounds[0] - dz / 2, a1_bounds[1] + dz / 2]

    r_bounds_1 = [a2_bounds[0], a2_bounds[1] + dr / 2]
    r_bounds_2 = [a2_bounds[0] - dr / 2, a2_bounds[1] + dr]

    xiaxis_1 = np.linspace(
        z_bounds_1[0] - t0,
        z_bounds_1[1] - t0,
        nz
    )

    xiaxis_2 = np.linspace(
        z_bounds_2[0] - t0,
        z_bounds_2[1] - t0,
        nz
    )

    raxis_1 = np.linspace(
        r_bounds_1[0],
        r_bounds_1[1],
        nr
    )

    raxis_2 = np.linspace(
        r_bounds_2[0],
        r_bounds_2[1],
        nr
    )
    return xiaxis_1, xiaxis_2, raxis_1, raxis_2

def getDt():
    """
    Return the timestep for probe integration.
    If the user provides dt in the input file, use that value.
    Otherwise, estimate dt from the field grid spacing using
    dt_safety_factor * min(dz, dr).
    """
    if Quasi_dt is not None:
        return Quasi_dt

    dz, dr = getGridSpacing()

    return Quasi_dt_safety_factor * abs(dz)


def getBoundCond(): # ***
    """
    Define when the electron leaves the simulation domain.
    Returns
    -------
    list
        [xi_min, xi_max, r_max]
    """
    grid = _get_reference_grid_info()

    a1_bounds = grid["a1_bounds"]
    a2_bounds = grid["a2_bounds"]
    dr = grid["dr"]

    t0 = getTime()

    xi_min = a1_bounds[0] - t0
    xi_max = a1_bounds[1] - t0
    r_max = a2_bounds[1] + dr / 2

    return [xi_min, xi_max, r_max]


# Return cylindrical Electric field components
# E1 - z
# E2 - r
# E3 - phi
def load_data():
    global xiaxis_1, xiaxis_2, raxis_1, raxis_2
    global E1_M0, E2_M0, E3_M0
    global E1_M1_Re, E2_M1_Re, E3_M1_Re
    global E1_M1_Im, E2_M1_Im, E3_M1_Im
    global B1_M0, B2_M0, B3_M0
    global B1_M1_Re, B2_M1_Re, B3_M1_Re
    global B1_M1_Im, B2_M1_Im, B3_M1_Im
    xiaxis_1, xiaxis_2, raxis_1, raxis_2 = axes()
    E1_M0 = getE1_M0()
    E2_M0 = getE2_M0()
    E3_M0 = getE3_M0()
    E1_M1_Re = getE1_M1_Re()
    E2_M1_Re = getE2_M1_Re()
    E3_M1_Re = getE3_M1_Re()
    E1_M1_Im = getE1_M1_Im()
    E2_M1_Im = getE2_M1_Im()
    E3_M1_Im = getE3_M1_Im()
    B1_M0 = getB1_M0()
    B2_M0 = getB2_M0()
    B3_M0 = getB3_M0()
    B1_M1_Re = getB1_M1_Re()
    B2_M1_Re = getB2_M1_Re()
    B3_M1_Re = getB3_M1_Re()
    B1_M1_Im = getB1_M1_Im()
    B2_M1_Im = getB2_M1_Im()
    B3_M1_Im = getB3_M1_Im()

def setLaserRegionFromInput():
    """
    Convert the laser xi region into xi-grid indices.

    If laser_xi_start and laser_xi_end are provided in the input file,
    that range is used.

    If they are omitted, the full available xi window is used.

    Returns
    -------
    tuple
        (j_min, j_max), where both indices are inclusive.
    """
    global Laser_xi_index_min
    global Laser_xi_index_max
    global Laser_xi_start
    global Laser_xi_end

    xi_min_grid = min(xiaxis_2[0], xiaxis_2[-1])
    xi_max_grid = max(xiaxis_2[0], xiaxis_2[-1])

    # If user did not specify a laser region, use the full xi window.
    if Laser_xi_start is None or Laser_xi_end is None:
        xi_start = xi_min_grid
        xi_end = xi_max_grid
    else:
        if Laser_xi_end < xi_min_grid or Laser_xi_start > xi_max_grid:
            raise ValueError(
                f"Requested laser xi region [{Laser_xi_start}, {Laser_xi_end}] "
                f"does not overlap field xi range [{xi_min_grid}, {xi_max_grid}]."
            )

        # Clip requested region to available grid.
        xi_start = max(Laser_xi_start, xi_min_grid)
        xi_end = min(Laser_xi_end, xi_max_grid)

    # Store the actual region used.
    Laser_xi_start = xi_start
    Laser_xi_end = xi_end

    j_min = int(np.searchsorted(xiaxis_2, xi_start, side="left"))
    j_max = int(np.searchsorted(xiaxis_2, xi_end, side="right")) - 1

    j_min = max(j_min, 0)
    j_max = min(j_max, len(xiaxis_2) - 1)

    if j_min >= j_max:
        raise ValueError(
            f"Laser xi region is too small after clipping: "
            f"indices {j_min}, {j_max}."
        )

    Laser_xi_index_min = j_min
    Laser_xi_index_max = j_max

    print("Using laser vector-potential region:")
    print("  xi range:", Laser_xi_start, Laser_xi_end)
    print("  index range:", Laser_xi_index_min, Laser_xi_index_max)

    return j_min, j_max

def integrateAFromE(E, xaxis, j_min, j_max):
    """
    Calculate vector potential component A from electric field component E.

    Assumes laser phase velocity is 1, so:

        E = dA/dxi

    The integration assumes A = 0 ahead of the laser at high xi,
    and integrates backward from high xi to low xi.

    Parameters
    ----------
    E : ndarray
        Electric field component, shape (nr, nxi).
    xaxis : ndarray
        xi-axis corresponding to E.
    j_min, j_max : int
        Inclusive index bounds of laser region.

    Returns
    -------
    A : ndarray
        Vector potential component with same shape as E.
    """
    A = np.zeros_like(E)

    for j in range(j_max - 1, j_min - 1, -1):
        dxi = xaxis[j + 1] - xaxis[j]

        A[:, j] = (
            A[:, j + 1]
            - 0.5 * (E[:, j + 1] + E[:, j]) * dxi
        )

    return A

def buildLaserVectorPotential():
    """
    Build laser vector potential components by integrating the M1 electric fields.

    A1 is A_z.
    A2 is A_r.
    A3 is A_phi.

    The resulting A arrays are used to compute laser B fields from curl(A).
    """
    global Laser_A_ready

    global A1_M1_Re, A2_M1_Re, A3_M1_Re
    global A1_M1_Im, A2_M1_Im, A3_M1_Im

    global dA1_M1_Re_dxi, dA2_M1_Re_dxi, dA3_M1_Re_dxi
    global dA1_M1_Im_dxi, dA2_M1_Im_dxi, dA3_M1_Im_dxi

    global dA1_M1_Re_dr, dA3_M1_Re_dr
    global dA1_M1_Im_dr, dA3_M1_Im_dr

    j_min, j_max = setLaserRegionFromInput()

    # Integrate E = dA/dxi, assuming laser phase velocity = 1.
    A1_M1_Re = integrateAFromE(E1_M1_Re, xiaxis_1, j_min, j_max)
    A1_M1_Im = integrateAFromE(E1_M1_Im, xiaxis_1, j_min, j_max)

    A2_M1_Re = integrateAFromE(E2_M1_Re, xiaxis_2, j_min, j_max)
    A2_M1_Im = integrateAFromE(E2_M1_Im, xiaxis_2, j_min, j_max)

    A3_M1_Re = integrateAFromE(E3_M1_Re, xiaxis_2, j_min, j_max)
    A3_M1_Im = integrateAFromE(E3_M1_Im, xiaxis_2, j_min, j_max)

    # Derivatives with respect to xi.
    dA1_M1_Re_dxi = np.gradient(A1_M1_Re, xiaxis_1, axis=1, edge_order=2)
    dA1_M1_Im_dxi = np.gradient(A1_M1_Im, xiaxis_1, axis=1, edge_order=2)

    dA2_M1_Re_dxi = np.gradient(A2_M1_Re, xiaxis_2, axis=1, edge_order=2)
    dA2_M1_Im_dxi = np.gradient(A2_M1_Im, xiaxis_2, axis=1, edge_order=2)

    dA3_M1_Re_dxi = np.gradient(A3_M1_Re, xiaxis_2, axis=1, edge_order=2)
    dA3_M1_Im_dxi = np.gradient(A3_M1_Im, xiaxis_2, axis=1, edge_order=2)

    # Radial derivatives needed for curl(A).
    dA1_M1_Re_dr = np.gradient(A1_M1_Re, raxis_2, axis=0, edge_order=2)
    dA1_M1_Im_dr = np.gradient(A1_M1_Im, raxis_2, axis=0, edge_order=2)

    dA3_M1_Re_dr = np.gradient(A3_M1_Re, raxis_2, axis=0, edge_order=2)
    dA3_M1_Im_dr = np.gradient(A3_M1_Im, raxis_2, axis=0, edge_order=2)

    Laser_A_ready = True

def reconstructM1(F_re, F_im, phi):
    """
    Reconstruct an m=1 scalar/cylindrical component at azimuth phi.
    """
    return F_re * math.cos(phi) + F_im * math.sin(phi)


def dphiReconstructM1(F_re, F_im, phi):
    """
    Reconstruct d/dphi of an m=1 scalar/cylindrical component.
    If F = F_re cos(phi) + F_im sin(phi), then
    dF/dphi = -F_re sin(phi) + F_im cos(phi).
    """
    return -F_re * math.sin(phi) + F_im * math.cos(phi)


def isInLaserRegion(xi):
    """
    Return True if xi is inside the user-specified laser region.
    """
    if Laser_xi_start is None or Laser_xi_end is None:
        return False

    return Laser_xi_start <= xi <= Laser_xi_end  

def getE1_M0():
    return getField(qpath("e1_cyl_m-0-re"))

def getE2_M0():
    return getField(qpath("e2_cyl_m-0-re"))

def getE3_M0():
    return getField(qpath("e3_cyl_m-0-re"))

# def getE1_M0():
#     return getField('data/OSIRIS/Quasi3D/e1_cyl_m-0-re-'+ Quasi_ID + '.h5')

def getE1_M1_Re():
    return getField(qpath("e1_cyl_m-1-re"))
    
def getE2_M1_Re():
    return getField(qpath("e2_cyl_m-1-re"))

def getE3_M1_Re():
    return getField(qpath("e3_cyl_m-1-re"))

def getE1_M1_Im():
    return getField(qpath("e1_cyl_m-1-im"))

def getE2_M1_Im():
    return getField(qpath("e2_cyl_m-1-im"))

def getE3_M1_Im():
    return getField(qpath("e3_cyl_m-1-im"))

# Return Magnetic Field components
# B1 - z
# B2 - r
# B3 - phi

def getB1_M0():
    return getField(qpath("b1_cyl_m-0-re"))
    
def getB2_M0():
    return getField(qpath("b2_cyl_m-0-re"))

def getB3_M0():
    return getField(qpath("b3_cyl_m-0-re"))

def getB1_M1_Re():
    return getField(qpath("b1_cyl_m-1-re"))

def getB2_M1_Re():
    return getField(qpath("b2_cyl_m-1-re"))

def getB3_M1_Re():
    return getField(qpath("b3_cyl_m-1-re"))

def getB1_M1_Im():
    return getField(qpath("b1_cyl_m-1-im"))

def getB2_M1_Im():
    return getField(qpath("b2_cyl_m-1-im"))

def getB3_M1_Im():
    return getField(qpath("b3_cyl_m-1-im"))

def getchargeElectrons_M0():
    return getField(qpath("charge_cyl_m-electrons-0-re"))

def getchargeElectrons_M1_Re():
    return getField(qpath("charge_cyl_m-electrons-1-re"))

def getchargeElectrons_M1_Im():
    return getField(qpath("charge_cyl_m-electrons-1-im"))

def getchargeIons_M0():
    return getField(qpath("charge_cyl_m-ions-0-re"))

def getchargeIons_M1_Re():
    return getField(qpath("charge_cyl_m-ions-1-re"))

def getchargeIons_M1_Im():
    return getField(qpath("charge_cyl_m-ions-1-im"))


def getPhi(x,y):
    return math.atan2(y,x) # From -pi to pi

def find_nearest_index(array,value):
    # idx = np.searchsorted(array, value, side="right")
    # if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
    #     return idx-1
    # else:
    #     return idx
    if value < array[0] or value > array[-1]:
        raise ValueError(
            f"Value {value} is outside axis range [{array[0]}, {array[-1]}]"
        )
    idx = np.searchsorted(array, value, side="right")
    if idx == len(array):
        return len(array) - 1
    if idx > 0 and abs(value - array[idx - 1]) < abs(value - array[idx]):
        return idx - 1
    return idx

def EField(axis, x, y, xi, r, vx=-1, vy=-1, vz=-1, vr=-1, vphi=-1, mode=-1): # ***
    """
    # axis = 1 refers to z-axis field
    # axis = 2 refers to x-axis field
    # axis = 3 refers to y-axis field
    # mode = 0 refers to LWF effects only
    # mode = 1 refers to laser effects only
    # mode = any other integer uses LWF + laser effects

    """
    phi = getPhi(x, y)
    cos = math.cos(phi)
    sin = math.sin(phi)

    # Interpolate M0 electric fields.
    E1_0 = interp2(E1_M0, xiaxis_1, raxis_2, xi, r)
    E2_0 = interp2(E2_M0, xiaxis_2, raxis_1, xi, r)
    E3_0 = interp2(E3_M0, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 real electric fields.
    E1_1_re = interp2(E1_M1_Re, xiaxis_1, raxis_2, xi, r)
    E2_1_re = interp2(E2_M1_Re, xiaxis_2, raxis_1, xi, r)
    E3_1_re = interp2(E3_M1_Re, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 imaginary electric fields.
    E1_1_im = interp2(E1_M1_Im, xiaxis_1, raxis_2, xi, r)
    E2_1_im = interp2(E2_M1_Im, xiaxis_2, raxis_1, xi, r)
    E3_1_im = interp2(E3_M1_Im, xiaxis_2, raxis_2, xi, r)

    if mode == 0:
        if axis == 1:
            return E1_0
        elif axis == 2:
            return E2_0 * cos - E3_0 * sin
        elif axis == 3:
            return E3_0 * cos + E2_0 * sin

    elif mode == 1:
        if axis == 1:
            return E1_1_re * cos + E1_1_im * sin
        elif axis == 2:
            return (
                E2_1_re * cos**2
                - E3_1_re * cos * sin
                + E2_1_im * cos * sin
                - E3_1_im * sin**2
            )
        elif axis == 3:
            return (
                E3_1_re * cos**2
                + E2_1_re * cos * sin
                + E3_1_im * cos * sin
                + E2_1_im * sin**2
            )

    else:
        if axis == 1:
            return E1_0 + E1_1_re * cos + E1_1_im * sin
        elif axis == 2:
            return (
                E2_0 * cos
                - E3_0 * sin
                + E2_1_re * cos**2
                - E3_1_re * cos * sin
                + E2_1_im * cos * sin
                - E3_1_im * sin**2
            )
        elif axis == 3:
            return (
                E3_0 * cos
                + E2_0 * sin
                + E3_1_re * cos**2
                + E2_1_re * cos * sin
                + E3_1_im * cos * sin
                + E2_1_im * sin**2
            )

def BForce(axis, x, y, xi, r, vx=-1, vy=-1, vz=-1, vr=-1, vphi=-1, mode=-1): # ***
    """
    # axis = 1 refers to z-axis field
    # axis = 2 refers to x-axis field
    # axis = 3 refers to y-axis field
    """
    phi = getPhi(x, y)
    cos = math.cos(phi)
    sin = math.sin(phi)

    # Interpolate M0 magnetic fields.
    B1_0 = interp2(B1_M0, xiaxis_1, raxis_2, xi, r)
    B2_0 = interp2(B2_M0, xiaxis_2, raxis_1, xi, r)
    B3_0 = interp2(B3_M0, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 real magnetic fields.
    B1_1_re = interp2(B1_M1_Re, xiaxis_1, raxis_2, xi, r)
    B2_1_re = interp2(B2_M1_Re, xiaxis_2, raxis_1, xi, r)
    B3_1_re = interp2(B3_M1_Re, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 imaginary magnetic fields.
    B1_1_im = interp2(B1_M1_Im, xiaxis_1, raxis_2, xi, r)
    B2_1_im = interp2(B2_M1_Im, xiaxis_2, raxis_1, xi, r)
    B3_1_im = interp2(B3_M1_Im, xiaxis_2, raxis_2, xi, r)

    if mode == 0:
        Bz = B1_0
        Bx = B2_0 * cos - B3_0 * sin
        By = B3_0 * cos + B2_0 * sin

    elif mode == 1:
        Bz = B1_1_re * cos + B1_1_im * sin
        Bx = (
            B2_1_re * cos**2
            - B3_1_re * cos * sin
            + B2_1_im * cos * sin
            - B3_1_im * sin**2
        )
        By = (
            B3_1_re * cos**2
            + B2_1_re * cos * sin
            + B3_1_im * cos * sin
            + B2_1_im * sin**2
        )

    else:
        Bz = B1_0 + B1_1_re * cos + B1_1_im * sin
        Bx = (
            B2_0 * cos
            - B3_0 * sin
            + B2_1_re * cos**2
            - B3_1_re * cos * sin
            + B2_1_im * cos * sin
            - B3_1_im * sin**2
        )
        By = (
            B3_0 * cos
            + B2_0 * sin
            + B3_1_re * cos**2
            + B2_1_re * cos * sin
            + B3_1_im * cos * sin
            + B2_1_im * sin**2
        )

    if axis == 1:
        return vx * By - vy * Bx
    elif axis == 2:
        return vy * Bz - vz * By
    elif axis == 3:
        return -1.0 * (vx * Bz - vz * Bx)
    

def BField(axis, x, y, xi, r, vx=-1, vy=-1, vz=-1, vr=-1, vphi=-1, mode=-1):
    """
    Return interpolated magnetic field component.

    Currently not used by the trajectory pusher, which uses BForce().
    Kept for diagnostics and possible plotting.
    
    Return the magnetic field component at particle position.

    axis = 1 returns Bz
    axis = 2 returns Bx
    axis = 3 returns By

    Uses bilinear interpolation on the staggered Quasi3D field grids.
    """
    phi = getPhi(x, y)
    cos = math.cos(phi)
    sin = math.sin(phi)

    # Interpolate M0 magnetic fields.
    B1_0 = interp2(B1_M0, xiaxis_1, raxis_2, xi, r)
    B2_0 = interp2(B2_M0, xiaxis_2, raxis_1, xi, r)
    B3_0 = interp2(B3_M0, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 real magnetic fields.
    B1_1_re = interp2(B1_M1_Re, xiaxis_1, raxis_2, xi, r)
    B2_1_re = interp2(B2_M1_Re, xiaxis_2, raxis_1, xi, r)
    B3_1_re = interp2(B3_M1_Re, xiaxis_2, raxis_2, xi, r)

    # Interpolate M1 imaginary magnetic fields.
    B1_1_im = interp2(B1_M1_Im, xiaxis_1, raxis_2, xi, r)
    B2_1_im = interp2(B2_M1_Im, xiaxis_2, raxis_1, xi, r)
    B3_1_im = interp2(B3_M1_Im, xiaxis_2, raxis_2, xi, r)

    if mode == 0:
        Bz = B1_0
        Bx = B2_0 * cos - B3_0 * sin
        By = B3_0 * cos + B2_0 * sin

    elif mode == 1:
        Bz = B1_1_re * cos + B1_1_im * sin

        Bx = (
            B2_1_re * cos**2
            - B3_1_re * cos * sin
            + B2_1_im * cos * sin
            - B3_1_im * sin**2
        )

        By = (
            B3_1_re * cos**2
            + B2_1_re * cos * sin
            + B3_1_im * cos * sin
            + B2_1_im * sin**2
        )

    else:
        Bz = B1_0 + B1_1_re * cos + B1_1_im * sin

        Bx = (
            B2_0 * cos
            - B3_0 * sin
            + B2_1_re * cos**2
            - B3_1_re * cos * sin
            + B2_1_im * cos * sin
            - B3_1_im * sin**2
        )

        By = (
            B3_0 * cos
            + B2_0 * sin
            + B3_1_re * cos**2
            + B2_1_re * cos * sin
            + B3_1_im * cos * sin
            + B2_1_im * sin**2
        )

    if axis == 1:
        return Bz
    elif axis == 2:
        return Bx
    elif axis == 3:
        return By
    else:
        raise ValueError("axis must be 1, 2, or 3")

def BFieldLaserFromA(axis, x, y, xi, r):
    """
    Return laser magnetic field component computed from curl(A).

    axis = 1 returns Bz
    axis = 2 returns Bx
    axis = 3 returns By
    """
    if not Laser_A_ready:
        raise RuntimeError(
            "Laser vector potential has not been built. "
            "Set laser_A_enabled = True in the input file or call buildLaserVectorPotential()."
        )

    if not isInLaserRegion(xi):
        return 0.0

    phi = getPhi(x, y)
    cos = math.cos(phi)
    sin = math.sin(phi)

    r_eff = max(abs(r), 1e-12)

    # Interpolate A_z and its phi derivative.
    Az_re = interp2(A1_M1_Re, xiaxis_1, raxis_2, xi, r)
    Az_im = interp2(A1_M1_Im, xiaxis_1, raxis_2, xi, r)

    dphi_Az = dphiReconstructM1(Az_re, Az_im, phi)

    # Interpolate A_r and its phi derivative.
    Ar_re = interp2(A2_M1_Re, xiaxis_2, raxis_1, xi, r)
    Ar_im = interp2(A2_M1_Im, xiaxis_2, raxis_1, xi, r)

    dphi_Ar = dphiReconstructM1(Ar_re, Ar_im, phi)

    # Interpolate A_phi.
    Aphi_re = interp2(A3_M1_Re, xiaxis_2, raxis_2, xi, r)
    Aphi_im = interp2(A3_M1_Im, xiaxis_2, raxis_2, xi, r)

    Aphi = reconstructM1(Aphi_re, Aphi_im, phi)

    # Interpolate derivatives.
    dxi_Aphi_re = interp2(dA3_M1_Re_dxi, xiaxis_2, raxis_2, xi, r)
    dxi_Aphi_im = interp2(dA3_M1_Im_dxi, xiaxis_2, raxis_2, xi, r)
    dxi_Aphi = reconstructM1(dxi_Aphi_re, dxi_Aphi_im, phi)

    dxi_Ar_re = interp2(dA2_M1_Re_dxi, xiaxis_2, raxis_1, xi, r)
    dxi_Ar_im = interp2(dA2_M1_Im_dxi, xiaxis_2, raxis_1, xi, r)
    dxi_Ar = reconstructM1(dxi_Ar_re, dxi_Ar_im, phi)

    dr_Az_re = interp2(dA1_M1_Re_dr, xiaxis_1, raxis_2, xi, r)
    dr_Az_im = interp2(dA1_M1_Im_dr, xiaxis_1, raxis_2, xi, r)
    dr_Az = reconstructM1(dr_Az_re, dr_Az_im, phi)

    dr_Aphi_re = interp2(dA3_M1_Re_dr, xiaxis_2, raxis_2, xi, r)
    dr_Aphi_im = interp2(dA3_M1_Im_dr, xiaxis_2, raxis_2, xi, r)
    dr_Aphi = reconstructM1(dr_Aphi_re, dr_Aphi_im, phi)

    # Cylindrical curl components.
    Br = dphi_Az / r_eff - dxi_Aphi

    Bphi = dxi_Ar - dr_Az

    Bz = (Aphi + r_eff * dr_Aphi - dphi_Ar) / r_eff

    # Convert cylindrical B to Cartesian B.
    Bx = Br * cos - Bphi * sin
    By = Bphi * cos + Br * sin

    if axis == 1:
        return Bz
    elif axis == 2:
        return Bx
    elif axis == 3:
        return By
    else:
        raise ValueError("axis must be 1, 2, or 3")
    

def BForceLaserFromA(axis, x, y, xi, r, vx=-1, vy=-1, vz=-1, vr=-1, vphi=-1):
    """
    Return v cross B for the laser, using B = curl(A).
    """
    Bz = BFieldLaserFromA(1, x, y, xi, r)
    Bx = BFieldLaserFromA(2, x, y, xi, r)
    By = BFieldLaserFromA(3, x, y, xi, r)

    if axis == 1:
        return vx * By - vy * Bx
    elif axis == 2:
        return vy * Bz - vz * By
    elif axis == 3:
        return vz * Bx - vx * Bz
    else:
        raise ValueError("axis must be 1, 2, or 3")

def interp2(field, xaxis, raxis, xi, r):
    """
    Bilinear interpolation of a 2D field array Field[r, xi].

    Parameters
    ----------
    field : ndarray
        2D array with shape (len(raxis), len(xaxis)).
    xaxis : ndarray
        xi-axis corresponding to the second index of field.
    raxis : ndarray
        radial axis corresponding to the first index of field.
    xi : float
        xi location where field is evaluated.
    r : float
        radial location where field is evaluated.

    Returns
    -------
    float
        Bilinearly interpolated field value.
    """
    if xi < xaxis[0] or xi > xaxis[-1]:
        raise ValueError(
            f"xi={xi} is outside axis range [{xaxis[0]}, {xaxis[-1]}]"
        )

    if r < raxis[0] or r > raxis[-1]:
        raise ValueError(
            f"r={r} is outside axis range [{raxis[0]}, {raxis[-1]}]"
        )

    # Find lower cell indices.
    ix = np.searchsorted(xaxis, xi) - 1
    ir = np.searchsorted(raxis, r) - 1

    # Clamp to valid interpolation cells.
    ix = max(0, min(ix, len(xaxis) - 2))
    ir = max(0, min(ir, len(raxis) - 2))

    x0 = xaxis[ix]
    x1 = xaxis[ix + 1]
    r0 = raxis[ir]
    r1 = raxis[ir + 1]

    # Avoid divide-by-zero in pathological cases.
    if x1 == x0:
        wx = 0.0
    else:
        wx = (xi - x0) / (x1 - x0)

    if r1 == r0:
        wr = 0.0
    else:
        wr = (r - r0) / (r1 - r0)

    f00 = field[ir,     ix]
    f01 = field[ir,     ix + 1]
    f10 = field[ir + 1, ix]
    f11 = field[ir + 1, ix + 1]

    return (
        (1 - wr) * (1 - wx) * f00
        + (1 - wr) * wx * f01
        + wr * (1 - wx) * f10
        + wr * wx * f11
    )

def chargeElectrons(axis,x,y,xi,r,vx=-1,vy=-1,vz=-1,vr=-1,vphi=-1,mode=-1): # ***
# axis = 1 refers to z-axis field
# axis = 2 refers to x-axis field
# axis = 3 refers to y-axis field
# mode = 0 refers to LWF effects only
# mode = 1 refers to laser effects only
# mode = any other integer uses LWF + laser effects
    phi = getPhi(x,y)
    cos = math.cos(phi)
    sin = math.sin(phi)
    xiDex1 = find_nearest_index(xiaxis_1, xi)
    xiDex2 = find_nearest_index(xiaxis_2, xi)
    rDex1 = find_nearest_index(raxis_1, r)
    rDex2 = find_nearest_index(raxis_2, r)
    # Return chargeElectrons
    if (mode == 0):
        if (axis == 1):
            return chargeElectrons_M0[rDex2, xiDex1]
    elif (mode == 1):
        if (axis == 1):
            return chargeElectrons_M1_Re[rDex2, xiDex1]*cos + chargeElectrons_M1_Im[rDex2, xiDex1]*sin
    else:
        if (axis == 1):
            return chargeElectrons_M0[rDex2, xiDex1] + chargeElectrons_M1_Re[rDex2, xiDex1]*cos + chargeElectrons_M1_Im[rDex2, xiDex1]*sin


def chargeIons(axis,x,y,xi,r,vx=-1,vy=-1,vz=-1,vr=-1,vphi=-1,mode=-1): # ***
# axis = 1 refers to z-axis field
# axis = 2 refers to x-axis field
# axis = 3 refers to y-axis field
# mode = 0 refers to LWF effects only
# mode = 1 refers to laser effects only
# mode = any other integer uses LWF + laser effects
    phi = getPhi(x,y)
    cos = math.cos(phi)
    sin = math.sin(phi)
    xiDex1 = find_nearest_index(xiaxis_1, xi)
    xiDex2 = find_nearest_index(xiaxis_2, xi)
    rDex1 = find_nearest_index(raxis_1, r)
    rDex2 = find_nearest_index(raxis_2, r)
    # Return chargeIons
    if (mode == 0):
        if (axis == 1):
            return chargeIons_M0[rDex2, xiDex1]
    elif (mode == 1):
        if (axis == 1):
            return chargeIons_M1_Re[rDex2, xiDex1]*cos + chargeIons_M1_Im[rDex2, xiDex1]*sin
    else:
        if (axis == 1):
            return chargeIons_M0[rDex2, xiDex1] + chargeIons_M1_Re[rDex2, xiDex1]*cos + chargeIons_M1_Im[rDex2, xiDex1]*sin