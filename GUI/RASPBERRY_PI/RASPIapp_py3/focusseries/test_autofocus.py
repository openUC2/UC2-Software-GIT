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

mypath = './'
sharpness = []

for file in glob.glob(os.path.join(mypath, "*.tif")):
    im = plt.imread(file)
    im = gaussian_filter(im, 5) #convolve(image, mykernel)
    mysharpness = np.std(im)
    sharpness.append(mysharpness)
    print(mysharpness)
    mymetric =  (im[:,:,0]-im[:,:,1])**2+(im[:,:,1]-im[:,:,2])**2+(im[:,:,0]-im[:,:,2])**2
    plt.imshow(mymetric), plt.show()
    print(np.mean(mymetric))
    
    
plt.plot(np.array(sharpness))
