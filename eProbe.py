import math
import numpy as np
from tqdm import tqdm
from DebugObjectModule import DebugObject

_worker_sim = None

def init_worker(sim_name, input_fname):
    global _worker_sim
    import importlib
    init = importlib.import_module(input_fname)
    if sim_name.upper() == 'OSIRIS_CYLINSYMM':
        import include.simulations.useOsiCylin as sim
    elif sim_name.upper() == 'QUASI3D':
        import include.simulations.useQuasi3D as sim
    elif sim_name.upper() == 'FBPIC':
        import include.simulations.useFBPIC as sim
    else:
        raise ValueError(f"Simulation name unrecognized: {sim_name}")
    sim.configure(init)
    _worker_sim = sim

def Gamma(p):
        return math.sqrt(1.0 + p**2)

def Velocity(px,ptot):
    # Returns relativistic velocity from momentum
    return px / Gamma(ptot)

def sortVelocity(x,y,vx,vy,vr):
    # Obtain proper sign of velocity based on quadrant
    if (x >= 0 and y >= 0):                  # Quadrant 1
        if (vx >= 0 and vy >= 0):
            return vr
        elif (vx < 0 and vy < 0):
            return -1.0 * vr
        elif (abs(vx) > abs(vy)):
            if vx > 0:
                return vr
            else:
                return -1.0 * vr
        elif (abs(vy) > abs(vx)):
            if vy > 0:
                return vr
            else:
                return -1.0 * vr
    elif (x < 0 and y >= 0):                 # Quadrant 2
        if (vx <= 0 and vy >= 0):
                return vr
        elif (vx > 0 and vy < 0):
                return -1.0 * vr
        elif (abs(vx) > abs(vy)):
            if vx > 0:
                return -1.0 * vr
            else:
                return vr
        elif (abs(vy) > abs(vx)):
            if vy > 0:
                return vr
            else:
                return -1.0 * vr
    elif (x < 0 and y < 0):                   # Quadrant 3
        if (vx >= 0 and vy >= 0):
            return -1.0 * vr
        elif (vx < 0 and vy < 0):
            return vr
        elif (abs(vx) > abs(vy)):
            if vx > 0:
                return -1.0 * vr
            else:
                return vr
        elif (abs(vy) > abs(vx)):
            if vy > 0:
                return vr
            else:
                return -1.0 * vr
    elif (x >= 0 and y < 0):                 # Quadrant 4
        if (vx >= 0 and vy <= 0):
            return vr
        elif (vx < 0 and vy > 0):
            return -1.0 * vr
        elif (abs(vx) > abs(vy)):
            if vx > 0:
                return vr
            else:
                return -1.0 * vr
        elif (abs(vy) > abs(vx)):
            if vy > 0:
                return -1.0 * vr
            else:
                return vr

def Momentum(x,y,xi,dt,px,py,pz,mode): 
    # Returns the new momentum after dt, in units of c in the axis direction
    sim = _worker_sim
    if sim is None:
        raise RuntimeError("Simulation module has not been initialized.")

    p = math.sqrt(px**2 + py**2 + pz**2)
    vx = Velocity(px, p)
    vy = Velocity(py, p)
    vz = Velocity(pz, p)
    r = math.sqrt(x**2 + y**2)
    vr = math.sqrt(vx**2 + vy**2)
    vr = sortVelocity(x, y, vx, vy, vr)
    if (r > 0):
        vphi = vr/r
    else:
        vphi = 0

    Fx = -1.0 * (sim.EField(2, x, y, xi, r, vx, vy, vz, vr, vphi, mode) + sim.BForce(2, x, y, xi, r, vx, vy, vz, vr, vphi, mode))
    Fy = -1.0 * (sim.EField(3, x, y, xi, r, vx, vy, vz, vr, vphi, mode) + sim.BForce(3, x, y, xi, r, vx, vy, vz, vr, vphi, mode))
    Fz = -1.0 * (sim.EField(1, x, y, xi, r, vx, vy, vz, vr, vphi, mode) + sim.BForce(1, x, y, xi, r, vx, vy, vz, vr, vphi, mode))

    px = px + Fx * dt
    py = py + Fy * dt
    pz = pz + Fz * dt
    p = math.sqrt(px**2 + py**2 + pz**2)
    gam = Gamma(p)
    return px, py, pz, p, gam, Fx, Fy, Fz

def getArrayForm(x_dat_, y_dat_, z_dat_, xi_dat_,
                 Fx_dat_, Fy_dat_, Fz_dat_,
                 px_dat_, py_dat_, pz_dat_):
    """
    Convert debug-mode trajectory lists into 2D arrays with shape
    (n_particles, n_steps).

    For single-particle debug mode, n_particles = 1.
    """
    n_steps = len(x_dat_)
    den = 1

    x_dat = np.empty([den, n_steps])
    y_dat = np.empty([den, n_steps])
    z_dat = np.empty([den, n_steps])
    xi_dat = np.empty([den, n_steps])

    Fx_dat = np.empty([den, n_steps])
    Fy_dat = np.empty([den, n_steps])
    Fz_dat = np.empty([den, n_steps])

    px_dat = np.empty([den, n_steps])
    py_dat = np.empty([den, n_steps])
    pz_dat = np.empty([den, n_steps])

    x_dat[0, :] = x_dat_
    y_dat[0, :] = y_dat_
    z_dat[0, :] = z_dat_
    xi_dat[0, :] = xi_dat_

    Fx_dat[0, :] = Fx_dat_
    Fy_dat[0, :] = Fy_dat_
    Fz_dat[0, :] = Fz_dat_

    px_dat[0, :] = px_dat_
    py_dat[0, :] = py_dat_
    pz_dat[0, :] = pz_dat_

    return x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat

def getTrajectory(x_0,y_0,xi_0,px_0,py_0,pz_0,t0,iter,plasma_bnds,
                  mode,debugmode, x_s):
# Returns array of x, y, xi, z, and final x, y, xi, z, px, py, pz
    sim = _worker_sim
    if sim is None:
        raise RuntimeError("Simulation module has not been initialized.")
    
    propspeed = sim.getPropagationSpeed()

    t = t0                       # Start time in 1/w_p
    # dt = 0.005 #0.005            # Time step in 1/w_p
    dt = sim.getDt()  
    xn = x_0                     # Positions in c/w_p
    yn = y_0
    xin = xi_0
    zn = xin + t0*propspeed # PLACE TO ADD MULTIPLIER TO t0 for group velocity
    rn = math.sqrt(xn**2 + yn**2)

    px = px_0                    # Momenta in m_e c
    py = py_0
    pz = pz_0

    ### DEBUGGING ###
    Debug = None # Create empty Debug object variable
    if debugmode == True: 
        print("Using Debug Mode...")
        x_f, y_f, xi_f, z_f, px_f, py_f, pz_f = [],[],[],[],[],[],[] # Final positions-momenta of particle
        x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat = [],[],[],[],[],[],[],[],[],[]
    #################

    # Iterate through position and time using a linear approximation
    for i in range(0, iter):
        # Determine new momentum and velocity from this position
        # If electron leaves sim boundaries, quit tracking
        if (xin < plasma_bnds[0] or xin > plasma_bnds[1] or rn > plasma_bnds[2]):
            if debugmode == True:
                print("Tracking quit due to particle leaving cell")
                x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat = getArrayForm(x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat)
                Debug = DebugObject(x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat)
                print("Debug object created...")
            return xn, yn, xin, zn, px, py, pz, Debug
        
        px, py, pz, p, gam, Fx, Fy, Fz = Momentum(xn, yn, xin, dt, px, py, pz, mode)
        vxn = Velocity(px, p)
        vyn = Velocity(py, p)
        vzn = Velocity(pz, p)

        # Log data in arrays if in debug mode
        if debugmode == True:
            x_dat.append(xn)
            y_dat.append(yn)
            z_dat.append(zn)
            xi_dat.append(xin)
            Fx_dat.append(Fx)
            Fy_dat.append(Fy)
            Fz_dat.append(Fz)
            px_dat.append(px)
            py_dat.append(py)
            pz_dat.append(pz)
        
        xn += vxn * dt
        yn += vyn * dt
        zn += vzn * dt
        rn = math.sqrt(xn**2 + yn**2)

        t += dt
        xin = zn - t*propspeed
        

        
        

    print("Tracking quit due to more than ", iter, " iterations in plasma")
    
    if debugmode == True:
        x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat = getArrayForm(x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat)
        Debug = DebugObject(x_dat, y_dat, z_dat, xi_dat, Fx_dat, Fy_dat, Fz_dat, px_dat, py_dat, pz_dat)
        print("Debug object created...")

    return xn, yn, xin, zn, px, py, pz, Debug
