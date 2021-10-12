# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import flap
import flap_apdcam
import matplotlib.pyplot as plt
import time
import math

flap_apdcam.register()

    
def show_apdcam(chnum=None,datapath='data',timerange=None):
    """
    Show the signals as ADCs.

    Parameters
    ----------
    chnum: int
        Number of channels.
    datapath : string, optional
        The data directory. The default is data.
    timerange: two-element list of floats. optional
        The default is None, full timerange.
    Returns
    -------
    None.

    """

    if (chnum is None):
        raise ValueError('chnum must be set.')
    plt.close('all')
    plt.figure(figsize=(20,16)) 
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

    nrow = round(math.sqrt(chnum))
    ncol = int(chnum / nrow)
    while (nrow*ncol < chnum):
        nrow = nrow + 1
    for irow in range(nrow):
        for icol in range(ncol):
            plt.subplot(nrow,ncol,icol + irow * ncol + 1)
            chname = 'ADC'+str(icol + irow * ncol + 1)
            if (timerange is None):
                coord = None
            else:
                coord = {'Time':timerange}
            d = flap.get_data('APDCAM',name=chname,coordinates=coord,options={'Datapath':datapath})
            d.plot(axes='Time')
            plt.title(chname)
            plt.yrange=[0,16363]
    plt.suptitle(datapath)
    plt.tight_layout()
    plt.show()    
    plt.pause(0.1)
    time.sleep(1)

show_apdcam(datapath='c:/Users/Zoletnik/Root/tmp/example_shot',chnum=64)