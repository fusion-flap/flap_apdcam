#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C APDCAM10G Firmware test
reated on Mon Jul  2 15:46:13 2018

@author: apdcam
"""


def firmware_test(card=8) :
    import APDCAM10G_control
    
    c = APDCAM10G_control.APDCAM10G_regCom()
    

    ret = c.startReceiveAnswer()
    if ret != "" :
        print("Could not start UDP read. (err:%s)" % ret)
        del c
        return
    err, data = c.readPDI(card,0,7,arrayData=1)
    if (err != "") :
        print("Error: %s" % err)
        return
    data = data[0]
    if ((data[0] & 0xE0) != 0x20) :
        print("No ADC found at address %d" % card)
        return
    mc_version = "{:d}.{:d}".format(data[1],data[2])
    fw_version = "{:d}.{:d}".format(data[5],data[6])
    print("ADC versions, MC:{:s}, FW:{:s}".format(mc_version,fw_version))
    
    apdcam_data = APDCAM10G_control.APDCAM10G_data()
    apdcam_data.stopStream(c)
    # Samplediv
    err = c.sendCommand(APDCAM10G_regCom.OP_PROGRAMSAMPLEDIVIDER,bytes([0,5]),sendImmediately=False)
    # samples
    err = c.sendCommand(APDCAM10G_regCom.OP_SETSAMPLECOUNT,bytes([0,0,0,1,0,0]),sendImmediately=True)
    #apdcam_data.setOctet(1000)
    apdcam_data.startReceive(c,[True, False, False, False])
    apdcam_data.startStream(c,[True, False, False, False])
    counter = 1
    while 1 :
        err,data = apdcam_data.getData(0)
        if (err =="") :
            if (counter == 1):
                print("First packet")
            packet_counter = int.from_bytes(data[8:14],'big') 
            if (packet_counter != counter) :
                print("Error in packet counter: %d (exp: %d)" % (int.from_bytes(data[8:14],'big'), counter))
            counter = counter+1    
        else :
            #print("Error: %s" % err)
            break
    print("Received %d packets" % counter)    
    del apdcam_data

    
    
    
    del c
     
 
          
firmware_test()

