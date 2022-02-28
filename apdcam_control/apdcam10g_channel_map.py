# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 12:51:00 2022

@author: Zoletnik
"""
import numpy as np

def apdcam10g_channel_map(camera_type=None,camera_version=1):
    """
    Returns a 2D matrix with the ADC channel numbers as one looks onto the detector.

    Parameters
    ----------
    camera_type : string
        The camera type. Possible values:
            4x32: 4 columns, 32 rows
            8x8: 8x8 pixels
            4x16: 4 columns, 16 rows
            8x16: 8 columns, 16 rows (4 S8550 detectors horizontolly in one column)
            8x16A: 8 columns, 16 rows (4 S8550 detectors verticallally tiled)
            FC: 64 channel fibre coupled (returns 1x64 array)
    camera_version : int, optional
        The detector panel and amplifier version. The default is 1.
            0: 2014 version
            1: 2016 version
            2: Hybrid (2016 detector with 2014 amplifiers) 

    Raises:
        ValueError: Unkniwn camera type of version
    Returns
    -------
    channel_map: Numpy array of ints
        The ADC channel numbers as one looks onto the detector from the camera front.
        channel_map[0,0] is upper left corner
        channel_map[nr,nc] is lower right corner if nr is number of rows, nc is number of columns

    """
    
    if (camera_type == "4x32"):
        channel_map = np.ndarray((32,4),int)
        if (camera_version == 0):
            chmap = np.array([[ 20, 90, 75, 76],
                              [ 18, 92,  1,  2],
                              [ 70, 69, 29, 31],
                              [ 16, 15, 87, 85],
                              [ 19, 17,  4,  3],
                              [ 89, 91, 74, 73],
                              [ 13, 14, 30, 88],
                              [ 71, 72, 32, 86],
                              [ 54,128,104,103],
                              [ 56,126, 46, 45],
                              [ 41, 42,123,121],
                              [ 99,100, 49, 51],
                              [ 53, 55, 47, 48],
                              [127,125,101,102],
                              [ 98, 97,124, 50],
                              [ 44, 43,122, 52], 
                              [116, 58,107,108],
                              [114, 60, 33, 34],
                              [ 38, 37, 61, 63],
                              [112,111,119,117],
                              [115,113, 36, 35],
                              [ 57, 59,106,105],
                              [109,110, 62,120],
                              [ 39, 40, 64,118],
                              [ 22, 96,  8,  7],
                              [ 24, 94, 78, 77],        
                              [  9, 10, 27, 25],  
                              [ 67, 68, 81, 83],
                              [ 21, 23, 79, 80],
                              [ 95, 93,  5,  6],
                              [ 66, 65, 28, 82],
                              [ 12, 11, 26, 84]
                             ])
            return np.transpose(chmap)
        elif (camera_version == 1):
            chmap = np.array([[ 59, 38,125,100],
                              [115,110, 53, 44],
				   			  [ 60, 37,126, 99],
							  [116,109, 54, 43],
							  [ 40, 57, 98,127],
							  [112,113, 42, 55],
							  [ 39, 58, 97,128],
							  [111,114, 41, 56],
							  [ 24,  9, 18, 15],
							  [ 96, 65, 90, 71],   
							  [ 23, 10, 17, 16],
							  [ 95, 66, 89, 72],
							  [ 11, 22, 13, 20],
							  [ 67, 94, 69, 92],
							  [ 12, 21, 14, 19],
							  [ 68, 93, 70, 91],
							  [ 27,  6, 29,  4],
							  [ 83, 78, 85, 76],
							  [ 28,  5, 30,  3],
							  [ 84, 77, 86, 75],
							  [  8, 25,  2, 31],
							  [ 80, 81, 74, 87],
							  [  7, 26,  1, 32],
							  [ 79, 82, 73, 88],
							  [120,105, 50, 47],
							  [ 64, 33,122,103],
							  [119,106, 49, 48],
							  [ 63, 34,121,104],
							  [107,118, 45, 52],
							  [ 35, 62,101,124],
							  [108,117, 46, 51],
							  [ 36, 61,102,123]
						     ])
            return np.transpose(chmap)
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_type))

    elif (camera_type == "8x8"):
        pass
    elif (camera_type == "8x16"):  
        channel_map = np.ndarray((16,8),int)
        if (camera_version == 0):
            chmap = np.array([[ 14, 70, 18, 20, 30, 32, 76,  3],
                              [ 69, 13, 17, 19, 29,  4, 31, 75],
                              [ 72, 89, 15, 91, 85, 87,  2, 74],
                              [ 16, 71, 90, 92, 86, 88, 73,  1],
                              [ 97, 41, 56, 54,124,122,103, 48],
                              [ 42, 98, 55, 53,123, 47,121,104],
                              [ 43,127,100,125, 51, 49, 45,101],
                              [ 99, 44,128,126, 52, 50,102, 46],
                              [110, 38,114,116, 62, 64,108, 35],
                              [ 37,109,113,115, 61, 36, 63,107],
                              [ 40, 57,111, 59,117,119, 34,106],
                              [112, 39, 58, 60,118,120,105, 33],
                              [ 65,  9, 24, 22, 28, 26,  7, 80],
                              [ 10, 66, 23, 21, 27, 79, 25,  8],
                              [ 11, 95, 68, 93, 83, 81, 77,  5],
                              [ 67, 12, 96, 94, 84, 82,  6, 78]
                              ])
            return np.transpose(chmap)
        elif (camera_version == 1):
            pass
  
           
    elif (camera_type == "8x16A"):
        pass
    elif (camera_type == "FC"):
        pass  
    else:
        raise ValueError('Unknown camera type:"{:s}"'.format(camera_type))