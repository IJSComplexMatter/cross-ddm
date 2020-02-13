# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 14:26:13 2020

@author: PolarBear2017
"""

import numpy as np
import matplotlib.pyplot as plt
from cddm import k_select
from scipy.optimize import curve_fit

def fitfunc_single(x,r1,A,B):
    return A*(np.exp(-x*r1))+B

N=512.
pixelsize=0.137
fft_pixelsize=2*np.pi/(N*pixelsize)

x=np.load("x_live.npy")
logdata=np.load("logdata_live.npy")

x=x*128e-6

plt.figure(2)
kdata = k_select(logdata, phi = 0, sector = 5, kstep = 1)
    
p0 = np.array([380.,2.2e-7,1e-7])
rate = []
K=[]

for k, corr in kdata: 
    k=k*fft_pixelsize
    K.append(k)
    p,c = curve_fit(fitfunc_single,x,corr,p0)
    rate.append(p[0])
    plt.semilogx(x,fitfunc_single(x,p[0],p[1],p[2]),'--',linewidth=1)
    #rate.append(0)
    plt.semilogx(x, corr, label = k)
    
    
#plt.legend()
    
plt.figure(3) 
ks=np.array(K)**2
plt.plot(ks,rate,alpha=1)

plt.show()
