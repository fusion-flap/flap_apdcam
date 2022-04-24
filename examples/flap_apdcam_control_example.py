# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 16:40:23 2022

Example of controlling APDCAM-10G

!!! The APDTest program should be compiled in flap_apdcam/apdcam_control/APDTest_10G:
    make clean
    make all
!!!

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

import flap
import flap_apdcam
import flap_apdcam.apdcam_control as apdcam_control

# To register the APDCAM data source in flap
flap_apdcam.register()

def apdcam_control_example(camera_type = 'APDCAM-10G_8x16A'):
    # Creating an APDCAM control class variable
    apdcam = apdcam_control.APDCAM10G_regCom()
    # Connecting to the camera with the default address
    print("Connecting...")
    ret = apdcam.connect()
    if (ret != ""):
        print("{:s}".format(ret))
        apdcam.close()
        return
    
    err = apdcam.readStatus()
    print("Connected. Number of channels: {:d}.".format(len(apdcam.status.ADC_address)))
    
    # Enabling HV
    ret = apdcam.enableHV()
    if (ret != ""):
        print("Error enabling HV.")
        return
    
    # Switching on detector HVs. It is assumed that the value is already set.
    for i in range(4):
        ret = apdcam.HVon(i + 1)
        if (ret != ""):
            print("Error switching on HV{:d}.".format(i + 1))
            return
    
    #Setting up measurement parameters
    # Measuring with all channels
    channel_masks = [0xffffffff,0xffffffff,0xffffffff,0xffffffff] 
    
    #Samplerate 1 MHz
    samplerate = 1 # MHz
    sampleDiv = int(round(20 / samplerate)) # ADC sample rate is normally 20 MHz
    
    # Measurement lengt 0.1 s
    meas_length = 0.1
    numberOfSamples = int(round(meas_length * samplerate * 1E6))
    
    # Software trigger
    externalTriggerPolarity = None
     
    #Startting measurement. Placing data in directory 'data'
    # This will return when the measurement is done
    # To return when it has been started set waitForResult to False and use apdcam.measurementStatus()
    err, warning = apdcam.measure(numberOfSamples=numberOfSamples,
                                  channelMasks=channel_masks,
                                  sampleDiv=sampleDiv,
                                  datapath="data",
                                  bits=14,
                                  waitForResult=True,
                                  externalTriggerPolarity=externalTriggerPolarity,
                                  triggerDelay=0
                                  )
    if (warning != ''):
        print("Warning in APDCAM measurement: {:S}".format(warning))
    if (err != ""):
        print("Error in APDCAM measurement: {:S}".format(err))
        return
    
    apdcam.close()
    
    # Reading a single pixel, data in digits
    datapath = 'data'
    signal=flap.get_data('APDCAM',name='APD-1-1',options={'Datapath':datapath,'Camera type':camera_type})
    # Plotting it vs time
    signal.plot()
    

apdcam_control_example()     


