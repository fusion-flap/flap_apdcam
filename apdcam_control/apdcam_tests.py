# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 18:38:55 2023

Test programs for APDCAM software.

@author: Sandor Zoletnik
         sandor.zoletnik@fusioninstruments.com
"""

try:
    from .APDCAM10G_control import *
except ImportError:
    from flap_apdcam.apdcam_control.APDCAM10G_control import *

def testRcv():
    c = APDCAM10G_regCom()
    ret = c.startReceiveAnswer()
    if ret != "" :
        print("Could not start UDP read. (err:%s)" % ret)
        return
    err = c.sendCommand(APDCAM10G_codes_v1.OP_SETSAMPLECOUNT,bytes(10),sendImmediately=True)
    err,d = c.getAnswer()
    if (err != "") :
        print("Error:%d" % err)
        return
    if d == None :
        print("No answer received")
    else :
        print("Answer received (%d bytes)" % len(d))
    c.close()    
      
def testPdiRead():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        del c
        return
    card = [2,8]
    add = [c.codes_PC.PC_REG_HVON,0]
    l = [0,10]
    ad = [False, True]
    err, data = c.readPDI(card,add,l,arrayData=ad)   
#    err, data = c.readPDI(c.codes_PC.PC_CARD,c.codes_PC.PC_REG_HVON,1,arrayData=False)
    print("Operation result: %s" % err)
    if data != None :
        n_ans = len(data)
        for i in range(n_ans) :
            print("Data #%d" % i)
            d = data[i]
            if type(d) is bytes:
                s = ""
                for i in range(len(d)) :
                    s = s+" "+str(d[i]) 
                print(s)
            else:
                print(d)
    c.close()         

def testReadStatus():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if (ret != ""):
        print(ret)
        return
    for count in range(100000):
        err = c.readStatus()
        if (err != ""):
            print("Cycle {:d}, error: {:s}".format(count,err))
            break
        time.sleep(0.01)
        if (count % 100 == 0):
            print("Cycle {:d}".format(count))                    
    c.close()     
     
def testPdiWrite():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        del c
        return
    
    err = c.writePDI([8,9],[0xAE,0xAE],[12345,bytes([0x01,0x03])],numberOfBytes=[2,2],arrayData=[False,True],waitTime=10,noReadBack=False)
    #d = 3
    #err = c.writePDI(c.codes_PC.PC_CARD,c.codes_PC.PC_REG_HVON,d,numberOfBytes=1,arrayData=False)

    if (err == "") :
        print("Write operation successful.")
    else:
        print("Write error: %s" % err)
    del c         

def test_socket():
    import socket
    recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recvSocket.bind((b'127.0.0.0', 9999))
    UDP_data = b"ABCD"
    APDCAM_IP = b"10.123.13.102"
    ret = recvSocket.sendto(UDP_data, (APDCAM_IP, APDCAM10G_regCom.APDCAM_PORT))
    print(ret)

def testSend():
    c = APDCAM10G_regCom()    
    ret = c.startReceiveAnswer()
    if ret != "" :
        print("Could not start UDP read. (err:%s)" % ret)
        c.close()
        return

    cardAddress = 8
    registerAddress = 0
    numberOfBytes = 10
    userData = bytes([cardAddress])\
      +bytes([registerAddress//256*256*256])\
      +bytes([registerAddress//256*256])+bytes([registerAddress//256])\
      +bytes([registerAddress%256])\
      +bytes([numberOfBytes//256])+bytes([numberOfBytes%256])           
    err = c.sendCommand(APDCAM10G_regCom.OP_READPDI,userData,sendImmediately=True)
    if (err != ""):
        print(err)
    else:
        print("Successful readPDI send.")
     
    c.close()

def testSendUDP():
# Tests data UDP recever from camera
    c = APDCAM10G_regCom()
    ret = c.startReceiveAnswer()
    if ret != "" :
        print("Could not start UDP read. (err:%s)" % ret)
        c.close()
        return
    # Stop streams
    err = c.sendCommand(APDCAM10G_codes_v1.OP_SETSTREAMCONTROL,bytes([0]),sendImmediately=False)
    # Samplediv=1024
    err = c.sendCommand(APDCAM10G_codes_v1.OP_PROGRAMSAMPLEDIVIDER,bytes([4,0]),sendImmediately=False)
    # 1024 samples
    err = c.sendCommand(APDCAM10G_codes_v1.OP_SETSAMPLECOUNT,bytes([0,0,0,0,4,0]),sendImmediately=False)
    # Start stream 1 
    err = c.sendCommand(APDCAM10G_codes_v1.OP_SETSTREAMCONTROL,bytes([1]),sendImmediately=True)
    if (err != "") :
        print("Error starting streams: %s" % err)
    c.close()
    
def testDataCollect():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        del c
        return
    print("Firmware: "+c.status.firmware.decode('utf-8'))
    apdcam_data = APDCAM10G_data()
    apdcam_data.stopStream(c)
    if (c.versionCode == 0) :
        # Samplediv
        print("Version code 0")
        err = c.sendCommand(APDCAM10G_codes_v1.OP_PROGRAMSAMPLEDIVIDER,bytes([0,5]),sendImmediately=False)
        # samples
        err = c.sendCommand(APDCAM10G_codes_v1.OP_SETSAMPLECOUNT,bytes([0,0,0,1,0,0]),sendImmediately=True)
        #apdcam_data.setOctet(1000)
        apdcam_data.startReceive(c,[True, True, False, False])
        apdcam_data.startStream(c,[True, True, False, False])
    else:
        #stop all data
        print("Version code 1")
        op = bytes([0xC0])
        trigdelay = bytes([0,0,0,0])
        samplecount = bytes([0,0,0,1,0,0])
        err = c.sendCommand(APDCAM10G_codes_v2.OP_SETG1TRIGGERMODULE,op+trigdelay+samplecount,sendImmediately=True)
        if (err != ""):
            print(err)
            return
        err = c.sendCommand(APDCAM10G_codes_v2.OP_SETG2GATEMODULE,bytes([0]),sendImmediately=True)
        if (err != ""):
            print(err)
            return
        apdcam_data.startReceive(c,[False, True, False, False])
        apdcam_data.startStream(c,[False, True, False, False])
        # Start with SW trigger
        trigdelay = bytes([0,0,0,0])
        samplecount = bytes([0,0,0,1,0,0])
        err = c.sendCommand(APDCAM10G_codes_v2.OP_SETG1TRIGGERMODULE,op+trigdelay+samplecount,sendImmediately=True)
        if (err != ""):
            print(err)
            return
         
        
    counter = 1
    while 1 :
        err,data = apdcam_data.getData(0)
        if (err =="") :
            if (counter == 1):
                print("First packet")
            packet_counter = int.from_bytes(data[8:14],'big') 
            print(packet_counter)
            if (packet_counter != counter) :
                print("Error in packet counter: %d (exp: %d)" % (int.from_bytes(data[8:14],'big'), counter))
            counter = counter+1    
        else :
            #print("Error: %s" % err)
            break
    print("Received {:d} packets".format(counter-1))    
    del apdcam_data
    c.close()
    
def testConnect():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if (ret != ""):
        print(ret)
        return
    print("Firmware: "+c.status.firmware.decode('utf-8'))
    print("No ADCs: %d" % len(c.status.ADC_address))
    if (len(c.status.ADC_address) != 0):
        print("Addresses:")
        print(c.status.ADC_address)       
    c.close()
    
def stopData():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Firmware: "+c.status.firmware.decode('utf-8'))
    apdcam_data = APDCAM10G_data()
    apdcam_data.stopStream(c)
    del apdcam_data
    c.close()

def testTimer():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Firmware: "+c.status.firmware.decode('utf-8'))
    c.clearAllTimers()
    ts = APDCAM_onetimer()
    c.CAMTIMER.clockDiv = 20000
    c.CAMTIMER.outputEnable = 8
    c.CAMTIMER.outputPolarity = 0
    c.CAMTIMER.outputArmedState = 0
    c.CAMTIMER.outputIdleState = 0
    ts.delay = 0
    ts.pulseOn = 3000
    ts.pulseOff = 20
    ts.numberOfPulses = 1
    ts.channelEnable = 8
    n = c.allocateTimer(ts)
    if (n < 1):
        print("Error allocating timer.")
        return
    print("Timer allocated to :%d" % n)
    err = c.loadTimerSetup()
    if (err != ""):
        print(err)
        return
    err = c.timerIdle()
    if (err != ""):
        print(err)
        return
    time.sleep(0.01)
    err = c.timerArm()
    if (err != ""):
        print(err)
        return
    time.sleep(0.01)
    err = c.timerRun()
    if (err != ""):
        print(err)
        return
    print("Timer started")

    
def testInterface():
    c = APDCAM10G_regCom()
    err = c.getInterface()
    if (err == ""):
        print(c.interface)
    else:
        print(err)
def testMeasure():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    err,warning = c.measure(numberOfSamples=100000,sampleDiv=10,bits=14,waitForResult=0,externalTriggerPolarity=0)
    if (err != ""):
        print("Error starting measurement:"+err)
        c.close()
        return
    else:
        print("Measurement started")
    while (1):
        err,stat,warning = c.measurementStatus()
        if (err != ""):
            print(err)
        if (warning != ""):
            print(warning)
        if (stat == "Finished" ):
            print("Measurement fininshed.")
            break
        
    err = c.writeConfigFile()
    if (err != ""):
        print("Error in writeConfigFile:"+err)
    else:
        print("Config file written.")

    del c
        
def testStream():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    c.writeStreamData()
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
   
def testClock():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    err = c.setClock(APDCAM10G_regCom.CLK_INTERNAL)
    if (err == ""):
        print("Internal clock set OK.")
    else:
        print("Error setting internal clock:"+err)
        c.close
        return
    err,f,source = c.getAdcClock()
    if (err == ""):
        print("Clock frequency: {:f}[MHz]".format(f))
        if (source == APDCAM10G_regCom.CLK_INTERNAL):
            print("Clock source internal.")
        else:
            print("Clock source external.")     
    else:
        print("Error reading clock frequency:"+err)
        c.close
        return
    err = c.setClock(APDCAM10G_regCom.CLK_EXTERNAL,extmult=4,extdiv=2)
    if (err == ""):
        print("EXTERNAL clock set OK.")
    else:
        print("Error setting external clock:"+err)
        c.close
        return
    time.sleep(1)
    err,f,source = c.getAdcClock()
    if (err == ""):
        print("Clock frequency: {:f}[MHz]".format(f))
        if (source == APDCAM10G_regCom.CLK_INTERNAL):
            print("Clock source internal.")
        else:
            print("Clock source external.")     

    else:
        print("Error reading clock frequency:"+err)
        c.close
        return
def readStreamSetting():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    err = c.readStatus()
    if (err != ''):
        print(err)
        return
    code = c.codes_CC
    for i in range(4):
        octet = int.from_bytes(c.status.CC_settings[code.CC_REGISTER_UDPOCTET1+16*i:code.CC_REGISTER_UDPOCTET1+2+16*i],'big',signed=False)
        ip = c.status.CC_settings[code.CC_REGISTER_IP1+16*i:code.CC_REGISTER_IP1+4+16*i]
        port = int.from_bytes(c.status.CC_settings[code.CC_REGISTER_UDPPORT1+16*i:code.CC_REGISTER_UDPPORT1+2+16*i],'big',signed=False)
        print("{:d}...octet:{:d} IP:{:d}.{:d}.{:d}.{:d}  port:{:d}".format(i+1,octet,ip[0],ip[1],ip[2],ip[3],port))
    c.close()
    del c
    
def resetStream3():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    c.resetStream3()
    c.close()
    del c    
        
def hardTestComm_core(apd,threadNo):
    """ This is called by hardTestComm()
    """
    import random
    random.seed()
    
    err_counter = 0
    for i in range(100000):
        v = random.randint(1,4)
        if (v == 1):
            card=8
            reg = apd.codes_ADC.ADC_REG_MAXVAL11
            numberOfBytes = 20
            arrayData = True
            err,data = apd.readPDI(card,reg,numberOfBytes=numberOfBytes,arrayData=arrayData)
            print("Thread(err:{:d}) {:d}/{:d}...readPDI({:d},{:d},numberOfBytes={:d},arrayData{:d})"\
                   .format(err_counter,threadNo,i,card,reg,numberOfBytes,arrayData))
            if (err != ""):
                print("   Thread {:d}/{:d}   error: ******>{:s}<******".format(threadNo,i,err))
                err_counter += 1
            if (err == ""):
                print("   Thread {:d}/{:d}   data:".format(threadNo,i,)+str(data[0]))
        elif (v == 2):
            card=8
            reg = apd.codes_ADC.ADC_REG_MAXVAL11
            numberOfBytes = 20
            arrayData = True
            data = bytearray(range(20))
            err = apd.writePDI(card,reg,data,numberOfBytes=numberOfBytes,arrayData=arrayData)
            print("Thread(err:{:d}) {:d}/{:d}...writePDI({:d},{:d},data,numberOfBytes={:d},arrayData{:d})".format(err_counter,threadNo,i,card,reg,numberOfBytes,arrayData))
            if (err != ""):
                print("   Thread {:d}/{:d}   error: ******>{:s}<******".format(threadNo,i,err))
        elif (v == 3):
            err = apd.readStatus()
            print("Thread(err:{:d} {:d}/{:d}...readStatus()".format(err_counter,threadNo,i))
            if (err != ""):
                print("   Thread {:d}/{:d}   error: ******>{:s}<******".format(threadNo,i,err))
        elif (v == 4):
            err = apd.syncADC()
            print("Thread(err:{:d} {:d}/{:d}...syncADC()".format(err_counter,threadNo,i))
            if (err != ""):
                print("   Thread {:d}/{:d}   error: ******>{:s}<******".format(threadNo,i,err))
            
        w = random.random()
        time.sleep(w/10)            
    
def hardTestComm():
    """ This is to test a lot of communications from different streams
    """    
    apd = APDCAM10G_regCom()
    ret = apd.connect()
    if ret != "" :
        print("%s" % ret)
        apd.close()
        return
    print("Connected. Firmware: "+apd.status.firmware.decode('utf-8'))
    
    print("Starting thread 1")
    thr1 = threading.Thread(target=hardTestComm_core,args=(apd,1))
    thr1.start()
    
    print("Starting in main program (thread 2)")
    hardTestComm_core(apd,2)
    
    apd.close()
    del apd        

def dumpStatus():
    apd = APDCAM10G_regCom()
    ret = apd.connect()
    if ret != "" :
        print("%s" % ret)
        apd.close()
        return
    print("Connected. Firmware: "+apd.status.firmware.decode('utf-8'))
#    err = apd.readStatus()
#    if (err != ''):
#        print(err)
#        return
    code = apd.codes_CC
    print("Stream status:")
    for i in range(4):
        octet = int.from_bytes(apd.status.CC_settings[code.CC_REGISTER_UDPOCTET1+16*i:code.CC_REGISTER_UDPOCTET1+2+16*i],'big',signed=False)
        ip = apd.status.CC_settings[code.CC_REGISTER_IP1+16*i:code.CC_REGISTER_IP1+4+16*i]
        port = int.from_bytes(apd.status.CC_settings[code.CC_REGISTER_UDPPORT1+16*i:code.CC_REGISTER_UDPPORT1+2+16*i],'big',signed=False)
        print("  {:d}...octet:{:d} IP:{:d}.{:d}.{:d}.{:d}  port:{:d}".format(i+1,octet,ip[0],ip[1],ip[2],ip[3],port))
    clockstat = int(apd.status.CC_settings[code.CC_REGISTER_CLOCK_CONTROL])
    cstat = "Clock source: "
    if ((clockstat & 4) != 0):
        cstat += "<External> "
    else:
        cstat += "<Internal> "
    if ((clockstat & 8) != 0):
        cstat += "<Auto External>"
    print(cstat)
    if ((clockstat & 16) != 0):
        print("Sample clock: <External>")
    else:
        print("Sample clock: <Internal>")
    trigstat = int(apd.status.CC_settings[code.CC_REGISTER_TRIGSTATE])  
    tstat = "Trigger: "
    if ((trigstat & 1) != 0):
        tstat += "<External +> "
    if ((trigstat & 2) != 0):
        tstat += "<External -> "
    if ((trigstat & 4) != 0):
        tstat += "<Internal> "
    if ((trigstat & 64) != 0):
        tstat += "<DT> "
    print(tstat)
    
    samplecount = int.from_bytes(apd.status.CC_settings[code.CC_REGISTER_SAMPLECOUNT:code.CC_REGISTER_SAMPLECOUNT+6],'big',signed=False)
    print("Sample count:{:d}".format(samplecount))
    txcount = int.from_bytes(apd.status.CC_variables[code.CC_REGISTER_STREAM_TX_FRAMES:code.CC_REGISTER_STREAM_TX_FRAMES+4],'little',signed=False)
    print("Transmitted UDP frames:{:d}".format(txcount))

def testUDPMeasure():
    c = APDCAM10G_regCom()
    ret = c.connect()
    if ret != "" :
        print("%s" % ret)
        c.close()
        return
    print("Connected. Firmware: "+c.status.firmware.decode('utf-8'))
    err,warning = c.measure(numberOfSamples=100000,data_receiver='Python')
#    err,warning = c.measure(numberOfSamples=10000)
    if (err != ""):
        print("Error starting measurement:"+err)
        c.close()
        return

#testReadStatus()   
#testPdiRead()
#testPdiWrite()
#testSend()
#testSendUDP()     
#testDataCollect()
#testConnect()
#testTimer()
#testInterface() 
#testMeasure()
#testStream()
#testClock()
#resetStreams()
#readStreamSetting()
#hardTestComm()

testUDPMeasure()