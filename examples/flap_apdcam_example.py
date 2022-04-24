# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 16:40:23 2022

Example code for reading APDCAM data into flap and plotting

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

import matplotlib.pyplot as plt
import numpy as np

import flap
import flap_apdcam
flap_apdcam.register()

datapath = input("Enter datapath:")
print()
while True:
    ctypes, cversions = flap_apdcam.apdcam_types_versions()
    txt = ctypes[0]
    for ct in ctypes[1:]:
        txt += ", "+ct
    print("Enter camera type. Possible types: {:s}".format(txt))
    camera_type = input("Camera type:")
    try:
        ctypes.index(camera_type)
        break
    except ValueError:
        print("!!! Invalid camera type!!!")
plt.close('all')
# Reading a single pixel, data in digits
signal=flap.get_data('APDCAM',name='APD-1-1',options={'Datapath':datapath,'Camera type':camera_type})
# Plotting it vs time
signal.plot()
plt.pause(1)

# Reading all pixels, data in volts
signal=flap.get_data('APDCAM',name='APD-*',options={'Datapath':datapath,'Camera type':camera_type, 'Scaling':'Volt'})
# Plotting all signals on fixed scale between 0 and maximum
print("Plotting all signals, be patient.")
plt.figure(figsize=(20,20))
yrange = [0,np.amax(signal.data) * 1.05]
signal.plot(plot_type='grid xy',axes=['Row','Column','Time'],options={'Y range':yrange})
plt.pause(1)

plt.figure()
# PLotting the mean signal as an image, autscale
signal.plot(plot_type='image',summing={'Time':'Mean'},axes=['Row','Column'])