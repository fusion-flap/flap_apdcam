# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 22:26:24 2022

APDCAM types and versions
For APDCAM see: fusioninstruments.com

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

def apdcam_types_versions(family=None):
    """
    Returns the possible camera types and versions. 
    
    Parameters
    ----------
    family: string or None
        '10G' : Return only 10G cameras
        '1G' : Return only 1G cameras
        None: return all types

    Returns
    -------
    camera_types: list of strings
        The list of possible camera types
    camera_version: list of lists
        For each camera type lists the possible version numbers
    """
    
    camera_types_10G = [#APDCAM-10G:
                        'APDCAM-10G_4x32',   # 4x32 pixel
                        'APDCAM-10G_8x8',    # 8x8 pixel
                        'APDCAM-10G_4x16',   # 4x16 pixel, subarray of 4x32
                        'APDCAM-10G_8x16',   # 8x16 pixel, 8 pixel in one S8550 array
                        'APDCAM-10G_8x16A',  # 8x16 pixel, 8 pixxels in two S8550 arrays
                        'APDCAM-10G_FC'      # 64 individual detectors
                        ]
    camera_types_1G = [#APDCAM-1G:
                       'APDCAM-1G',         # Standard APDCAM-1G (Horizontal array)
                       'APDCAM-1G_90',      #APDCAM-1G with sensor rotated 90 degree CCW
                       'APDCAM-1G_180',     #APDCAM-1G with sensor rotated 180 degree CCW
                       'APDCAM-1G_270'      # APDCAM-1G with sensor rotated 270 degree CCW
                       ]
    
    camera_versions_10G = [#APDCAM-10G:
                           [1,0,2],   # 4x32 pixel
                           [1,0,2],   # 8x8 pixel
                           [1,0,2],   # 4x16 pixel, subarray of 4x32
                           [1,0,2],   # 8x16 pixel, 8 pixel in one S8550 array
                           [1]    ,   # 8x16 pixel, 8 pixels in two S8550 arrays
                           [1]    ,   # 64 individual detectors
                           ]   
    camera_versions_1G = [#APDCAM-1G:
                           [],        # Standard APDCAM-1G (Horizontal array)
                           [],        #APDCAM-1G with sensor rotated 90 degree CCW
                           [],        #APDCAM-1G with sensor rotated 180 degree CCW
                           []         # APDCAM-1G with sensor rotated 270 degree CCW
                           ]
         
    if (family is None):
        return camera_types_10G + camera_types_1G, camera_versions_10G + camera_versions_1G
    elif (family == '10G'):
        return camera_types_10G, camera_versions_10G
    elif (family == '1G'):
        return camera_types_1G, camera_versions_1G

        
    