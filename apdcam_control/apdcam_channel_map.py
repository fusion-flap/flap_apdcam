# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 12:51:00 2022

@author: Zoletnik
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
    if ((sensor_rotation != 0) and (sensor_rotation != 90)):
        raise ValueError("sensor_rotation can be only 0 or 90.")
    chmap = np.array([[18,20,21,23],
                      [25,27,28,30],
                      [19,17,22,24],
                      [26,32,29,31],
                      [15,13,16,10],
                      [ 8, 6, 1, 3],
                      [14,12,11, 9],
                      [ 7, 5, 4, 2]
                     ])
    chmap = np.transpose(chmap)
    nrot = int(round(sensor_rotation / 90))
    for i in range(nrot):
        chmap = np.rot90(chmap)
    return chmap
