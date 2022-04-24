# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 22:26:24 2022

APDCAM types and versions
For APDCAM see: fusioninstruments.com

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

def apdcam_types_versions():
    """
    Returns the possible camera types and versions. 
    

    Returns
    -------
    camera_types: list of strings
        The list of possible camera types
    camera_version: list of lists
        For each camera type lists the possible version numbers
    """
    
    camera_types = [#APDCAM-10G:
                    'APDCAM-10G_4x32',   # 4x32 pixel
                    'APDCAM-10G_8x8',    # 8x8 pixel
                    'APDCAM-10G_4x16',   # 4x16 pixel, subarray of 4x32
                    'APDCAM-10G_8x16',   # 8x16 pixel, 8 pixel in one S8550 array
                    'APDCAM-10G_8x16A',  # 8x16 pixel, 8 pixxels in two S8550 arrays
                    #APDCAM-1G: 
                    'APDCAM-1G',         # Standard APDCAM-1G (Horizontal array)
                    'APDCAM-1G_90',      #APDCAM-1G with sensor rotated 90 degree CCW
                    'APDCAM-1G_180',     #APDCAM-1G with sensor rotated 180 degree CCW
                    'APDCAM-1G_270'      # APDCAM-1G with sensor rotated 270 degree CCW
                    ]
    camera_versions = [#APDCAM-10G:
                        [1,0,2],   # 4x32 pixel
                        [1,0,2],   # 8x8 pixel
                        [1,0,2],   # 4x16 pixel, subarray of 4x32
                        [1,0,2],   # 8x16 pixel, 8 pixel in one S8550 array
                        [1]    ,   # 8x16 pixel, 8 pixxels in two S8550 arrays
                        #APDCAM-1G: 
                        [],        # Standard APDCAM-1G (Horizontal array)
                        [],        #APDCAM-1G with sensor rotated 90 degree CCW
                        [],        #APDCAM-1G with sensor rotated 180 degree CCW
                        []         # APDCAM-1G with sensor rotated 270 degree CCW
                      ]   
    return camera_types, camera_versions
    