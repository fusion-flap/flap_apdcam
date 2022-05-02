# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 20:46:10 2022

Creates a list of possible channel names for an APDCAM.

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
         
"""

def apdcam_channel_list(chmap):
    """
    Creates a channel name list from the channel map. 
    
    
    Parameters
    ----------
    chmap : Numpy array
        The channel map.
        
    
    Returns
    -------
    chlist: list of strings
       This is a onedimensional list of possible channel names (APD-r-c and ADCxx).
    
    """
    
    if (chmap.ndim == 1):
        chlist = ['ADC'+str(ch) for ch in chmap]
        for i in range(len(chmap)):
            chlist.append('APD-'+str(i+1))
    else:
        chlist = ['ADC'+str(ch) for ch in chmap.flatten()]
        for ir in range(chmap.shape[0]):
            for ic in range(chmap.shape[1]):
                chlist.append('APD-{:d}-{:d}'.format(ir + 1, ic + 1))
                    
    return chlist