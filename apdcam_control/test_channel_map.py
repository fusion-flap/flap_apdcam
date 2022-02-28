# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 21:59:55 2022

@author: Zoletnik
"""
import numpy as np

import flap_apdcam.apdcam_control as apdcam_control

def test_channel_map():
    
    camera_types =    ['4x32','4x32','8x16','8x16','8x8','8x8','8x8','4x16','4x16','4x16','8x16A']
    camera_versions = [     0,     1,     0,    1,     0,    1,    2,     0,     1,     2,      1]
    rows =            [    32,    32,    16,   16,     8,    8,    8,     16,   16,    16,     16]
    columns =         [     4,     4,     8,    8,     8,    8,    8,      4,    4,     4,      8]
    for camera_type,camera_version,column, row in zip(camera_types,camera_versions,columns, rows):
        m = apdcam_control.apdcam10g_channel_map(camera_type=camera_type,camera_version=camera_version)
        if ((m.shape[0] != column) or (m.shape[1] !=row)):
            raise ValueError("Invalid shape of channel map. Camera_type:{:s}, version:{:d}, shape:({:d},{:d})".\
                              format(camera_type,camera_version,m.shape[0],m.shape[1])
                            )
        if (len(np.nonzero(np.diff(np.sort(m.flatten())) != 1)[0]) != 0):
            raise ValueError("Error in  channel map. Camera_type:{:s}, version:{:d}.".\
                              format(camera_type,camera_version)
                            )
        print("Channel map for camera type '{:s}', version {:} OK.".format(camera_type,camera_version))
test_channel_map()
        
    