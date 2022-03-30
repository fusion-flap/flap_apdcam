# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import matplotlib.pyplot as plt
import time
import math
import os
import re
    
import flap
import flap_apdcam
flap_adpcam.register()

def show_apdcam(camera_type=None,camera_version=1,datapath='data',timerange=None,pixel_layout=True,
                figure=None,figsize=(20,16)):
    """
    Show the signals as ADCs.

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
    pixel_layout: boolean
        If True show signals in pixel arrangement. Otherwise as ADCs.
    datapath : string, optional
        The data directory. The default is data.
    timerange: two-element list of floats. optional
        The default is None, full timerange.
    Returns
    -------
    None.

    """


    if (figure is None):
        plt.figure(figsize=figsize) 
        plt.rcParams['figure.titlesize'] = 10
        plt.rcParams['lines.linewidth'] = 4
        plt.rcParams['axes.linewidth'] = 3
        plt.rcParams['axes.labelsize'] = 10  
        plt.rcParams['axes.titlesize'] = 10
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['xtick.major.size'] = 10
        plt.rcParams['xtick.major.width'] = 2
        plt.rcParams['xtick.minor.width'] = 2
        plt.rcParams['xtick.minor.size'] = 5
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['ytick.major.width'] = 2
        plt.rcParams['ytick.major.size'] = 10
        plt.rcParams['ytick.minor.width'] = 2
        plt.rcParams['ytick.minor.size'] = 5
        plt.rcParams['legend.fontsize'] = 12
    ls = os.listdir(datapath)
    re_string = "Channel_[0-9]+3.dat"
    chlist=[]
    for l in ls:
        if re.match(re_string,l):
            chlist.append(int(l[8:11]))
    chlist.sort()
    chnum = len(chlist)
    if (chnum == 0):
        raise ValueError("No data found. Wrong datanatpath?")
    if ((chnum != 64) and (chnum != 128)):
        raise ValueError("Incorrect number of data files in '{:s}. Should be either 64 or 128.".format(datapath))
    chlist = np.array(chlist)
    if (len(np.nonzero(np.diff(np.sort(chlist) != 1)[0]) != 0)):
        raise ValueError("Incorrect data file names.")
    if (camera_type is not None):
        chmap = 
    if (chnum == 128):
        nrow = 16
        ncol = 8
    elif (chnum == 64):
        nrow = 8
        ncol = 8
    else:
        nrow = round(math.sqrt(chnum))
        ncol = int(chnum / nrow)
    while (nrow*ncol < chnum):
        nrow = nrow + 1
    for irow in range(nrow):
        for icol in range(ncol):
            try:
                common_ax
                common_ax = plt.subplot(nrow,ncol,icol + irow * ncol + 1,sharex=common_ax,sharey=common_ax)
            except NameError:
                plt.subplot(nrow,ncol,icol + irow * ncol + 1)
            ch = icol + irow * ncol + 1
            if (ch > chnum):
                break
            chname = 'ADC'+str(icol + irow * ncol + 1)
            if (timerange is None):
                coord = None
            else:
                coord = {'Time':timerange}
            d = flap.get_data('APDCAM',name=chname,coordinates=coord,options={'Datapath':datapath})
            t,tmin,tmax = d.coordinate('Time',options={'Change':True})
            plt.plot(t,d.data)
            plt.title(chname)
            plt.ylim(0,16383)
            if (irow == nrow - 1):
                plt.xlabel('Time [s]')
    plt.suptitle(datapath)
    plt.tight_layout()
    plt.show()    
    plt.pause(0.1)
    time.sleep(1)

#show_apdcam(datapath='c:/Users/Zoletnik/Root/tmp/example_shot',chnum=64)