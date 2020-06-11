#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:09:04 2020

@author: bene
"""

import glob
import matplotlib.pyplot as plt
from scipy import ndimage
import os
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import curve_fit

# Define model function to be used to fit to the sharpness above:
def gauss(x, mu, sigma):
    return np.exp(-(x-mu)**2/(2.*sigma**2))

mypath = './'
ydata = []

for file in sorted(glob.glob(os.path.join(mypath, "*.tif")),key=os.path.getmtime):
    print(file)
    im = plt.imread(file)
    im = im[:,:,0]
    im = gaussian_filter(im,10) #convolve(image, mykernel)
    myydata = np.std(im)
    ydata.append(myydata)
    print(myydata)

# preprocess 
ydata = np.array(ydata)[1:] 
ydata -= np.min(ydata)
ydata /= np.max(ydata)
xdata = np.linspace(0, 1, ydata.shape[0])

# %%
# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [1/2, 1.]

coeff, var_matrix = curve_fit(gauss, xdata, ydata, p0=p0)
coeff
# Get the fitted curve
hist_fit = gauss(xdata, coeff[0], coeff[1])

plt.plot(xdata, ydata, label='raw data')
plt.plot(xdata, hist_fit, label='Fitted ydata')
plt.show()