# Script for generating 2D plots of electron trajectories with option for plotting force

from math import e
import numpy as np
import matplotlib.colors as col
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d import Axes3D
import pdb
from scipy.optimize import curve_fit

from numpy.core.fromnumeric import size
plt.rcParams.update({'font.size': 16})

plotYForce = True # Plot transverse force with trajectories, not useful for many trajectories
plotZForce = True # Plot force along WF propagation

#large_size = 12

#plt.rc('ytick', labelsize=large_size)
#plt.rc('axes', labelsize=large_size)

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

        

def plot(x_dat,y_dat,z_dat,xi_dat,Fx_dat,Fy_dat,Fz_dat,px_dat,py_dat,pz_dat,sim_name,shape_name,s1,s2,noElec,fname):

    #def objective(x, a, b):
       # return a * e**x + b
    
    #for i in range(0, noElec):
            #y_dat[i,:] = [y/0.65 for y in y_dat[i,:]]
           # popt, _ = curve_fit(objective, x_dat[i,:], y_dat[i,:])
            #a, b = popt
   # print('y =%.5f * e**(x) + %.5f' % (a, b))

# 2D: Z-X, constrained to blowout regime, changed to Y-Z
    fig1 = plt.figure(1)
    ax1 = plt.axes()
    ax1.set_xlabel("X ($c/\omega_p$)")    # For betatron test Changed x axis to Z
    ax1.set_ylabel("Z ($c/\omega_p$)")    # For betatron test, Changed y axis to Y
    ax1.set_xlim(-3,3)                    # For betatron test, changed from -3 to 3 to 0 to 600 (making x axis Z instead of X), 200 to zoom in for betatron wavelength
    #ax1.set_ylim(44, 46)
    #ax1.set_ylim(-3,3)
    ax1.tick_params(axis='y', labelcolor='k')
    ax1.set_title("Electron Trajectories through Blowout Regime")

    for i in range(0, noElec):
        ax1.plot(x_dat[i,:], z_dat[i,:], 'k', label='$X-Z Trajectory') # Want vertical axis as y ; Changed order of x_dat and z_dat to give X-Z trajectory, then replaced x with y

    if (plotZForce):
        ax1_f = ax1.twinx()
        ax1_f.set_ylabel("$F_x$ ($m_e c \omega_p$)")
        #ax1_f.set_ylim(-0.3,0.3)
        ax1_f.yaxis.label.set_color('C0')
        ax1_f.tick_params(axis='y', labelcolor='C0', colors='C0')

        for i in range(0, noElec):
            ax1_f.plot(x_dat[i,:], Fx_dat[i,:], 'C0', label='X Force') # For betatron test, Changed to F_x for radial

        fig1.legend(bbox_to_anchor=(0.88, 0.94), bbox_transform=plt.gcf().transFigure)

# 2D: Y-X
    fig2, ax2 = plt.subplots(1,figsize=(15,10),dpi=300)
    fig2.subplots_adjust(right=0.75)

    for i in range(0, noElec):
        #y_dat[i,:] = [y/0.65 for y in y_dat[i,:]]
        ax2.plot(x_dat[i,:], y_dat[i,:], 'k', label='Y-X Electron Trajectory') # Want vertical axis as y
        ax2.set_xlim(-3,3)          # Changed from -10 to 10 to -0.00001 to 0.0001 in betatron test fit with y offset instead of x
        ax2.set_ylim(-0.2,0.65)          # Added y limit to correct bad scale fitting
    
   
    ax2.set_xlabel("X ($c/\omega_p$)")
    ax2.set_ylabel("Y/$R_b$ ($c/\omega_p$)")
    ax2.set_title("Electron Trajectory through Blowout Regime")
    
    

    if (plotYForce):
        Fy_ax = ax2.twinx()
        px_ax = ax2.twinx()
        py_ax = ax2.twinx()
        pz_ax = ax2.twinx()
        #y_ax = ax2.twinx()
        #Fy1_ax = ax2.twinx()
        #Fy2_ax = ax2.twinx()
        

        px_ax.spines["right"].set_position(("axes",1.1))
        make_patch_spines_invisible(px_ax)
        px_ax.spines["right"].set_visible(True)
        py_ax.spines["right"].set_position(("axes",1.2))
        make_patch_spines_invisible(py_ax)
        py_ax.spines["right"].set_visible(True)
        pz_ax.spines["right"].set_position(("axes",1.3))
        make_patch_spines_invisible(pz_ax)
        pz_ax.spines["right"].set_visible(True)
        #y_ax.spines["right"].set_position(("axes",1.4))
        #make_patch_spines_invisible(y_ax)
        #y_ax.spines["right"].set_visible(True)
        #Fy1_ax.spines["right"].set_position(("axes",1.5))
        #make_patch_spines_invisible(Fy1_ax)
        #Fy1_ax.spines["right"].set_visible(True)
        #Fy2_ax.spines["right"].set_position(("axes",1.6))
        #make_patch_spines_invisible(Fy2_ax)
        #Fy2_ax.spines["right"].set_visible(True)

        for i in range(0, noElec):
            Fy_ax.plot(x_dat[i,:], Fy_dat[i,:], 'C0', label='Transverse Electric Force, $F_y$')     #Changed Transverse force from Y to X in Betatron test with y offset
            #Fy_ax.set_ylim(-0.13,0.01)
            px_ax.plot(x_dat[i,:], px_dat[i,:], 'C1', label='Momentum in X')
            py_ax.plot(x_dat[i,:], py_dat[i,:], 'C2', label='Momentum in Y')
            #py_ax.set_ylim(-1.75,0)  # To see full range of p_y better
            pz_ax.plot(x_dat[i,:], pz_dat[i,:], 'C3', label='Momentum in Z')
            x = np.linspace(-3, 3, 1000)
            #y =-0.03138 * e**(x) + 0.23168
            #y_ax.plot(x, y, 'C4', label='Y Fit')
            #y_ax.set_ylim(-0.2,0.65)
            #Fy1_ax.plot(x, -y/2, 'C5', label='Fy Fit')
            #Fy1_ax.set_ylim(-0.13,0.01)
            #Fy2_ax.plot(x_dat[i,:], -0.475*y_dat[i,:], 'C6', label='Fy if K = 0.5')

            
          

        Fy_ax.set_ylabel("$F_y$ ($m_e c \omega_p$)")
        px_ax.set_ylabel("$p_x (m_e c)$")
        py_ax.set_ylabel("$p_y (m_e c)$")
        pz_ax.set_ylabel("$p_z (m_e c)$")
        #y_ax.set_ylabel("$Y$ (c \omega_p$)")
        #Fy1_ax.set_ylabel("$Fy Fit$ ($m_e c \omega_p$)")
        #Fy2_ax.set_ylabel("$Fy K$ ($m_e c \omega_p$)")
       

        Fy_ax.yaxis.label.set_color('C0')
        px_ax.yaxis.label.set_color('C1')
        py_ax.yaxis.label.set_color('C2')
        pz_ax.yaxis.label.set_color('C3')
        #y_ax.yaxis.label.set_color('C4')
        #Fy1_ax.yaxis.label.set_color('C5')
        #Fy2_ax.yaxis.label.set_color('C6')
       

        tkw = dict(size=4, width=1.5)
        ax2.tick_params(axis='y', colors='k', **tkw)
        Fy_ax.tick_params(axis='y', colors='C0', **tkw)
        px_ax.tick_params(axis='y', colors='C1', **tkw)
        py_ax.tick_params(axis='y', colors='C2', **tkw)
        pz_ax.tick_params(axis='y', colors='C3', **tkw)
        #y_ax.tick_params(axis='y', colors='C4', **tkw)
        #Fy1_ax.tick_params(axis='y', colors='C5', **tkw)
        #Fy2_ax.tick_params(axis='y', colors='C5', **tkw)
        ax2.tick_params(axis='x', **tkw)

        ax2.grid()
        fig2.legend(bbox_to_anchor=(0.3, 0.8), bbox_transform=plt.gcf().transFigure)


    
    
        
    
   
    ax2.set_xlabel("X ($c/\omega_p$)")
    ax2.set_ylabel("Y/$R_b$ ($c/\omega_p$)")
    ax2.set_title("Electron Trajectory through Blowout Regime")







    fig1.tight_layout()
    #fig1.show()
    fig1.savefig(f"eProbe-Trajectories1_{fname}.png",transparent=False) # Added this line to also have image of figure 1
    fig2.tight_layout()
    fig2.savefig(f"eProbe-Trajectories_{fname}.png",transparent=False)



