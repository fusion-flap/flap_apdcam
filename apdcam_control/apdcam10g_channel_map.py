# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 12:51:00 2022

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
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
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_type))
        return np.transpose(chmap)

    elif (camera_type == "8x8"):
        channel_map = np.ndarray((8,8),int)
        if (camera_version == 0):
            chmap = np.array([[33, 9,24,22,60,58,39,16],
                              [10,34,23,21,59,15,57,40],
                              [11,63,36,61,19,17,13,37],
                              [35,12,64,62,20,18,38,14],
                              [46, 6,50,52,30,32,44, 3],
                              [ 5,45,49,51,29, 4,31,43],
                              [ 8,25,47,27,53,55, 2,42],
                              [48, 7,26,28,54,56,41, 1]
                              ])
        elif(camera_version == 1):
             chmap = np.array([[33, 9,63,64,58,57,39,16],
                               [10,34,23,24,18,15,17,40],
                               [11,62,36,61,59,60,13,37],
                               [35,12,22,21,19,20,38,14],
                               [46, 6,52,51,53,54,44, 3],
                               [ 5,45,28,27,29, 4,30,43],
                               [ 8,49,47,50,56,55, 2,42],
                               [48, 7,25,26,32,31,41, 1]
                               ])
        elif(camera_version == 2):
             chmap = np.array([[42,41,56,54,17,19, 2, 3],
                               [43,44,55,53,18, 1,20, 4],
                               [39,60,38,58,29,31,14,13],
                               [40,37,59,57,30,32,15,16],
                               [ 8, 7,24,22,49,51,48,45],
                               [ 5, 6,23,21,50,47,52,46],
                               [12,28, 9,26,61,63,36,35],
                               [11,10,27,25,62,64,33,34]
                               ])
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_type))
        return np.transpose(chmap)
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
        elif (camera_version == 1):
            chmap = np.array([[110, 38,116,115, 53, 54, 44, 99],
                              [ 37,109, 60, 59,125,100,126, 43],
                              [ 40,113,111,114, 56, 55, 98, 42],
                              [112, 39, 57, 58,128,127, 41, 97],
                              [ 65,  9, 95, 96, 90, 89, 71, 16],
                              [ 10, 66, 23, 24, 18, 15, 17, 72],
                              [ 11, 94, 68, 93, 91, 92, 13, 69],
                              [ 67, 12, 22, 21, 19, 20, 70, 14],
                              [ 78,  6, 84, 83, 85, 86, 76,  3],
                              [  5, 77, 28, 27, 29,  4, 30, 75],
                              [  8, 81, 79, 82, 88, 87,  2, 74],
                              [ 80,  7, 25, 26, 32, 31, 73,  1],
                              [ 33,105, 63, 64,122,121,103, 48],
                              [106, 34,119,120, 50, 47, 49,104],
                              [107, 62, 36, 61,123,124, 45,101],
                              [ 35,108,118,117, 51, 52,102, 46]
                              ])
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_type))
        return np.transpose(chmap)
    elif (camera_type == "4x16"):  
        channel_map = np.ndarray((16,4),int)
        if (camera_version == 0):
            chmap = np.array([[22,64,40,39],
                              [24,62,14,13],
                              [ 9,10,59,57],
                              [35,36,17,19],
                              [21,23,15,16],
                              [63,61,37,38],
                              [34,33,60,18],
                              [12,11,58,20],
                              [52,26,43,44],
                              [50,28, 1, 2],
                              [ 6, 5,29,31],
                              [48,47,55,53],
                              [51,49, 4, 3],
                              [25,27,42,41],
                              [45,46,30,56],
                              [ 7, 8,32,54]
                              ])
        elif (camera_version == 1):
            chmap = np.array([[ 24,  9, 18, 15],
							  [ 64, 33, 58, 39],   
							  [ 23, 10, 17, 16],
							  [ 63, 34, 57, 40],
							  [ 11, 22, 13, 20],
							  [ 35, 62, 37, 60],
							  [ 12, 21, 14, 19],
							  [ 36, 61, 38, 59],
							  [ 27,  6, 29,  4],
							  [ 51, 46, 53, 44],
							  [ 28,  5, 30,  3],
							  [ 52, 45, 54, 43],
							  [  8, 25,  2, 31],
							  [ 48, 49, 42, 55],
							  [  7, 26,  1, 32],
							  [ 47, 50, 41, 56]							 
						     ])
        elif (camera_version == 2):
            chmap = np.array([[61,47,26, 6],
                              [62,48,25, 5],
                              [63,45,28, 8],
                              [64,46,27, 7],
                              [36,51,12,24],
                              [35,52,11,23],
                              [34,49,10,22],
                              [33,50, 9,21],
                              [29, 1,58,41],
                              [30, 2,57,42],
                              [31, 3,60,43],
                              [32, 4,59,44],
                              [14,19,38,56],
                              [13,20,37,55],
                              [16,17,40,54],
                              [15,18,39,53]
                              ])
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_type))
        return np.transpose(chmap)
    elif (camera_type == "8x16A"):
        channel_map = np.ndarray((16,8),int)
        if (camera_version == 1):
            chmap = np.array([[ 91, 19, 14, 70, 76,  4, 29, 85],
                              [ 20, 92, 69, 16,  3, 75, 86, 31],
                              [ 17, 89, 13, 72,  2, 74, 30, 87],
                              [ 18, 90, 15, 71,  1, 73, 32, 88],
                              [ 56,128, 41, 97,103, 47,122, 50],
                              [ 55,126, 42, 98,104, 45,121, 49],
                              [127, 54, 43, 99, 48,101,124, 52],
                              [ 53,125,100, 44,102, 46, 51,123],
                              [ 59,115,110, 38,108, 36, 61,117],
                              [116, 60, 37,112, 35,107,118, 63],
                              [113, 57,109, 40, 34,106, 62,119],
                              [114, 58,111, 39, 33,105, 64,120],
                              [ 24, 96,  9, 65,  7, 79, 26, 82],
                              [ 23, 94, 10, 66,  8, 77, 25, 81],
                              [ 95, 22, 11, 67, 80,  5, 28, 84],
                              [ 21, 93, 68, 12,  6, 78, 83, 27]
                              ])
        else:
            raise ValueError("Version {:d} is not possible for camera type '{:s}'.".format(camera_version,camera_type))
        return np.transpose(chmap)
    elif (camera_type == "FC"):
        chmap = np.arange(64,dtype=int) + 1 
        return chmap
    else:
        raise ValueError('Unknown camera type:"{:s}"'.format(camera_type))
        
