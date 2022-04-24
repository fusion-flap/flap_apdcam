# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 12:51:00 2022

APD pixel to ADC channel maps for various APDCAM devices
 
@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""
import numpy as np

def apdcam_channel_map(sensor_rotation=0):
    """
    Returns a 2D matrix with the ADC channel numbers as one looks onto the detector.

    Parameters
    ----------
    sensor_rotation: float or int
        The sensor rotation in the camera [deg] conterclockwise. 
        0, 90, 180, 270 is possible.
    Returns
    -------
    channel_map: Numpy array of ints
        The ADC channel numbers as one looks onto the detector from the camera front.
        channel_map[0,0] is upper left corner
        channel_map[nr,nc] is lower right corner if nr is number of rows, nc is number of columns

    """
    if ((sensor_rotation != 0) and (sensor_rotation != 90) and (sensor_rotation != 180) and (sensor_rotation != 270)):
        raise ValueError("sensor_rotation can be only 0, 90, 180 or 270.")
    chmap = np.array([[18,19,15,14],
                      [20,17,13,12],
                      [21,22,16,11],
                      [23,24,10, 9],
                      [25,26, 8, 7],
                      [27,32, 6, 5],
                      [28,29, 1, 4],
                      [30,31, 3, 2]
                     ])
    chmap = chmap.astype(int)
    chmap = np.transpose(chmap)
    if (sensor_rotation == 0):
        return chmap
    if (sensor_rotation == 90):
       chmap_rot = np.rot90(chmap) 
       chmap_rot = ((chmap_rot + 8 - 1) % 32) + 1
       return chmap_rot
    if (sensor_rotation == 180):
       chmap_rot = np.rot90(chmap) 
       chmap_rot = np.rot90(chmap_rot) 
       chmap_rot = ((chmap_rot + 16 - 1) % 32) + 1
       return chmap_rot    
    if (sensor_rotation == 180):
       chmap_rot = np.rot90(chmap) 
       chmap_rot = np.rot90(chmap_rot) 
       chmap_rot = np.rot90(chmap_rot) 
       chmap_rot = ((chmap_rot + 24 - 1) % 32) + 1
       return chmap_rot
