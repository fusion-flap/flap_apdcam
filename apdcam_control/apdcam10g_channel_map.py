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

# if (modversion eq 1) then begin
# map[0,0] =    59
#   map[0,1] =    38
#   map[0,2] =    125
#   map[0,3] =    100
#   map[1,0] =    115
#   map[1,1] =    110
#   map[1,2] =    53
#   map[1,3] =    44
#   map[2,0] =    60
#   map[2,1] =    37
#   map[2,2] =    126
#   map[2,3] =    99
#   map[3,0] =    116
#   map[3,1] =    109
#   map[3,2] =    54
#   map[3,3] =    43
#   map[4,0] =    40
#   map[4,1] =    57
#   map[4,2] =    98
#   map[4,3] =    127
#   map[5,0] =    112
#   map[5,1] =    113
#   map[5,2] =    42
#   map[5,3] =    55
#   map[6,0] =    39
#   map[6,1] =    58
#   map[6,2] =    97
#   map[6,3] =    128
#   map[7,0] =    111
#   map[7,1] =    114
#   map[7,2] =    41
#   map[7,3] =    56
#   map[8,0] =    24
#   map[8,1] =    9
#   map[8,2] =    18
#   map[8,3] =    15
#   map[9,0] =    96
#   map[9,1] =    65
#   map[9,2] =    90
#   map[9,3] =    71
#   map[10,0] =     23
#   map[10,1] =     10
#   map[10,2] =     17
#   map[10,3] =     16
#   map[11,0] =     95
#   map[11,1] =     66
#   map[11,2] =     89
#   map[11,3] =     72
#   map[12,0] =     11
#   map[12,1] =     22
#   map[12,2] =     13
#   map[12,3] =     20
#   map[13,0] =     67
#   map[13,1] =     94
#   map[13,2] =     69
#   map[13,3] =     92
#   map[14,0] =     12
#   map[14,1] =     21
#   map[14,2] =     14
#   map[14,3] =     19
#   map[15,0] =     68
#   map[15,1] =     93
#   map[15,2] =     70
#   map[15,3] =     91
#   map[16,0] =     27
#   map[16,1] =     6
#   map[16,2] =     29
#   map[16,3] =     4
#   map[17,0] =     83
#   map[17,1] =     78
#   map[17,2] =     85
#   map[17,3] =     76
#   map[18,0] =     28
#   map[18,1] =     5
#   map[18,2] =     30
#   map[18,3] =     3
#   map[19,0] =     84
#   map[19,1] =     77
#   map[19,2] =     86
#   map[19,3] =     75
#   map[20,0] =     8
#   map[20,1] =     25
#   map[20,2] =     2
#   map[20,3] =     31
#   map[21,0] =     80
#   map[21,1] =     81
#   map[21,2] =     74
#   map[21,3] =     87
#   map[22,0] =     7
#   map[22,1] =     26
#   map[22,2] =     1
#   map[22,3] =     32
#   map[23,0] =     79
#   map[23,1] =     82
#   map[23,2] =     73
#   map[23,3] =     88
#   map[24,0] =     120
#   map[24,1] =     105
#   map[24,2] =     50
#   map[24,3] =     47
#   map[25,0] =     64
#   map[25,1] =     33
#   map[25,2] =     122
#   map[25,3] =     103
#   map[26,0] =     119
#   map[26,1] =     106
#   map[26,2] =     49
#   map[26,3] =     48
#   map[27,0] =     63
#   map[27,1] =     34
#   map[27,2] =     121
#   map[27,3] =     104
#   map[28,0] =     107
#   map[28,1] =     118
#   map[28,2] =     45
#   map[28,3] =     52
#   map[29,0] =     35
#   map[29,1] =     62
#   map[29,2] =     101
#   map[29,3] =     124
#   map[30,0] =     108
#   map[30,1] =     117
#   map[30,2] =     46
#   map[30,3] =     51
#   map[31,0] =     36
#   map[31,1] =     61
#   map[31,2] =     102
#   map[31,3] =     123
#   return,map
# endif ; modversion 1

# end

    elif (camera_type == "8x8"):
        pass
    elif (camera_type == "8x16"):  
        pass
    elif (camera_type == "8x16A"):
        pass
    elif (camera_type == "FC"):
        pass  
    else:
        raise ValueError('Unknown camera type:"{:s}"'.format(camera_type))