# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 21:59:55 2022

@author: Zoletnik
"""
import numpy as np

import flap_apdcam.apdcam_control as apdcam_control

def test_channel_map():
    
    camera_types = ['4x32','4x32']
    camera_versions = [0, 1]
    for camera_type,camera_version in zip(camera_types,camera_versions):
        m = apdcam_control.apdcam10g_channel_map(camera_type=camera_type,camera_version=camera_version)
        if ((m.shape[0] != 4) or (m.shape[1] != 32)):
            raise ValueError("Invalid shape of channel map. Camera_type:{:s}, version:{:d}, shape:({:d},{:d})".\
                              format(camera_type,camera_version,m.shape[0],m.shape[1])
                            )
        if (len(np.nonzero(np.diff(np.sort(m.flatten())) != 1)[0]) != 0):
            raise ValueError("Error in  channel map. Camera_type:{:s}, version:{:d}.".\
                              format(camera_type,camera_version)
                            )
        print("Channel map for camera type '{:s}', version {:} OK.".format(camera_type,camera_version))
test_channel_map()
        
    