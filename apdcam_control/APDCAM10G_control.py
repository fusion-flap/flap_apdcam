# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 19:34:00 2018

APDCAM-10G register access functions

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

import threading
import time
import copy
import subprocess
import xml.etree.ElementTree as ET
import socket
import os
import numpy as np

def DAC_ADC_channel_mapping():
    """ returns the ADC channel numbers (1...32) for each of the 32 DAC channel numbers     
    """
    return [30, 32, 31, 1, 2, 3 ,14 ,4 , 16, 13, 21, 19, 17, 20, 15, 18, 22, 24, 23, 9, 10, 11, 12, 6, 8, 5, 29, 25, 27, 28, 7, 26]

class APDCAM10G_codes_v1:
    """ Instruction codes and other defines for V1 of the 10G communication card
    """    
    # Opcodeswr
    # General instructions:
    OP_NOP=0x0000
    OP_LASTINSTRUCTION=0x0001
    OP_WAIT=0x0002
    OP_RESET=0x0003
    OP_LOCK=0x0004
    OP_UNLOCK=0x0005
    OP_SENDACK=0x0006
    OP_READSDRAM=0x0007

    #Configuration instructions:
    OP_SETSERIAL=0x0010
    OP_SETTYPE=0x0011
    OP_SETNAME=0x0012c
    OP_SETUSERTEXT=0x0013
    OP_SETCOMPANY=0x0014
    OP_SETHOSTNAME=0x0015
    OP_SETCONFIGURATION=0x0016
    OP_IMPORTSETTINGS=0x001E
    OP_SAVESETTINGS=0x001F
    
    #Network instructions:
    OP_SETMAC=0x0020
    OP_SETIP=0x0021
    OP_SETIPV4NETMASK=0x0022
    OP_SETIPV4GATEWAY=0x0023
    OP_SETARPREPORTPERIOD=0x0024
    OP_SETMACMODE=0x0025
    
    #Control Instructions
    OP_PROGRAMBASICPLL=0x0100
    OP_PROGRAMEXTDCM=0x0101
    OP_SETCLOCKCONTROL=0x0102
    OP_SETCLOCKENABLE=0x0103
    OP_PROGRAMSAMPLEDIVIDER=0x0104
    OP_SETSPAREIO=0x0105
    OP_SETXFP=0x0106
    OP_PROGRAMSERIALPLL=0x0107
    
    #Streamer instructions
    OP_SETSTREAMCONTROL=0x0110
    OP_SETUDPTESTCLOCKDIVIDER=0x0111
    OP_SETMULTICASTUDPSTREAM=0x0112
    OP_SETMULTICASTUDPSTREAM_LEN=9
    OP_SETUDPSTREAM=0x0113
    OP_SETUDPSTREAM_LEN=15
    OP_SETSAMPLECOUNT=0x0114
    OP_SETTRIGGER=0x0115
    OP_SETTRIGGER_LEN=5
    OP_CLEARTRIGGERSTATUS=0x0116
    OP_SETSATACONTROL=0x0117
    
    #CAMTimer instructions
    OP_SETCTCONTROL=0x0120
    OP_SETCTOUTPUT=0x0121
    OP_SETCTCLKDIV=0x0122
    OP_SETCTTIMER=0x0123
    OP_SETCTIDLE=0x0124
    OP_SETCTARMED=0x0125
    OP_SETCTRUNNING=0x0126
        
    #SCB instructions
    OP_SCBWRITECA=0x0060
    OP_SCBWRITERA=0x0061
    OP_SCBREADCA=0x0062
    OP_SCBREADRA=0x0063
    
    #Parallel Data Interface instructions:
    OP_WRITEPDI=0x0068
    OP_READPDI=0x0069
    
    #Storage Flash instructions
    OP_FLCHIPERASE=0x0070
    OP_FLBLOCKERASE=0x0071
    OP_FLBLOCKERASEW=0x0072
    OP_FLPROGRAM=0x0073
    OP_FLREAD=0x0074
    
    #Firmware Upgrade and Test instructions
    OP_LOADFUP=0x0800
    OP_STARTFUP=0x0801
    OP_SHORTBEEP=0x0810
    
    #**************************AnswerCodes
    AN_ACK=0xFF00
    AN_SDRAMPAGE=0xFF01
    AN_SCBDATA=0xFF02
    AN_FLASHPAGE=0xFF03
    AN_PDIDATA=0xFF04
    
    # These addresses are valid for DIT+Settings block 
    # The address is calculated from the Settings table as <byte address>-7+71
    # DATATYPE inndicates which block the variable is in (0: settings, 1: variables)
    CC_REGISTER_FIRMWARE = 17-7
    CC_DATATYPE_FIRMWARE = 0
    CC_REGISTER_MAN_SERIAL = 55-7
    CC_DATATYPE_MAN_SERIAL = 0
    CC_REGISTER_DEV_SERIAL = 58-7+71-7
    CC_DATATYPE_DEV_SERIAL = 0
    CC_REGISTER_CLOCK_CONTROL = 263-7+71-7
    CC_DATATYPE_CLOCK_CONTROL = 0
    CC_REGISTER_CLOCK_ENABLE = 264-7+71-7
    CC_DATATYPE_CLOCK_ENABLE = 0
    CC_REGISTER_EXT_DCM_MULT = 270-7+71-7
    CC_DATATYPE_EXT_DCM_MULT = 0
    CC_REGISTER_EXT_DCM_DIV = 271-7+71-7
    CC_DATATYPE_EXT_DCM_DIV = 0
    CC_REGISTER_BASE_PLL_MULT = 265-7+71-7
    CC_DATATYPE_BASE_PLL_MULT = 0
    CC_REGISTER_BASE_PLL_DIV_ADC = 267-7+71-7
    CC_DATATYPE_BASE_PLL_DIV_ADC = 0
    CC_REGISTER_TRIGSTATE = 282-7+71-7
    CC_DATATYPE_TRIGSTATE = 0
    CC_REGISTER_TRIGDELAY = 283-7+71-7
    CC_DATATYPE_TRIGDELAY = 0    
    CC_REGISTER_SERIAL_PLL_DIV = 288-7+71-7
    CC_DATATYPE_SERIAL_PLL_DIV = 0
    CC_REGISTER_SERIAL_PLL_MULT = 287-7+71-7
    CC_DATATYPE_SERIAL_PLL_MULT = 0
    CC_REGISTER_SAMPLEDIV = 272-7+71-7
    CC_DATATYPE_SAMPLEDIV = 0
    CC_REGISTER_SAMPLECOUNT = 276-7+71-7
    CC_DATATYPE_SAMPLECOUNT = 0
    CC_REGISTER_SATACONTROL = 292-7+71-7
    CC_DATATYPE_SATACONTROL = 0
    CC_REGISTER_UDPOCTET1 = 311-7+71-7
    CC_DATATYPE_UDPOCTET1 = 0
    CC_REGISTER_UDPMAC1 = 313-7+71-7
    CC_DATATYPE_UDPMAC1 = 0
    CC_REGISTER_IP1 = 320-7+71-7
    CC_DATATYPE_IP1 = 0
    CC_REGISTER_UDPPORT1 = 323-7+71-7
    CC_DATATYPE_UDPPORT1 = 0
    CC_REGISTER_CAMCONTROL = 495-7+71-7
    CC_DATATYPE_CAMCONTROL = 0
    CC_REGISTER_CAMOUTPUT = 499-7+71-7
    CC_DATATYPE_CAMOUTPUT = 0
    CC_REGISTER_CAMCLKDIV = 497-7+71-7
    CC_DATATYPE_CAMCLKDIV = 0
    CC_REGISTER_CAMSETTIMER = 375-7+71-7
    CC_DATATYPE_CAMSETTIMER = 0
    CC_REGISTER_CAMONTIME = 379-7+71-7
    CC_DATATYPE_CAMONTIME = 0
    CC_REGISTER_CAMOFFTIME = 381-7+71-7
    CC_DATATYPE_CAMOFFTIME = 0
    CC_REGISTER_CAMNROFPULSES = 383-7+71-7
    CC_DATATYPE_CAMNROFPULSES = 0
    CC_CAMTIMER_OFFSET = 12

    # These addresses are valid for Variables block 
    # For the Variables registers the address is calculated from the Variables table as <byte address>   
    CC_REGISTER_BOARDTEMP = 276-7
    CC_DATATYPE_BOARDTEMP = 1
    CC_REGISTER_MAXBOARDTEMP = 302-7
    CC_DATATYPE_MAXBOARDTEMP = 1
    CC_REGISTER_33V = 279-7
    CC_DATATYPE_33V = 1
    CC_REGISTER_25V = 281-7
    CC_DATATYPE_25V = 1
    CC_REGISTER_12VXC = 283-7
    CC_DATATYPE_12VXC = 1
    CC_REGISTER_12VST = 285-7
    CC_DATATYPE_12VST = 1
    CC_REGISTER_PLLSTAT = 194-7
    CC_DATATYPE_PLLSTAT = 1
    CC_REGISTER_EXTCLKFREQ = 196-7
    CC_DATATYPE_EXTCLKFREQ = 1
    CC_REGISTER_STATUS = 215-7
    CC_DATATYPE_STATUS = 1
    CC_REGISTER_STREAM_TX_FRAMES = 127 - 7
    CC_DATATYPE_STREAM_TX_FRAMES = 1

  
class APDCAM10G_codes_v2:
    """ Instruction codes and other defines for V2 (Firmware 105 and up) 
    of the 10G communication card
    """
    # Opcodes
    # General instructions:
    OP_NOP=0x0000
    OP_LASTINSTRUCTION=0x0001
    OP_WAIT=0x0002
    OP_RESET=0x0003
    OP_LOCK=0x0004
    OP_UNLOCK=0x0005
    OP_SENDACK=0x0006
    OP_READSDRAM=0x0007

    #Configuration instructions:
    OP_SETSERIAL=0x0010
    OP_SETTYPE=0x0011
    OP_SETNAME=0x0012
    OP_SETUSERTEXT=0x0013
    OP_SETCOMPANY=0x0014
    OP_SETHOSTNAME=0x0015
    OP_SETCONFIGURATION=0x0016
    OP_IMPORTSETTINGS=0x001E
    OP_SAVESETTINGS=0x001F
    
    #Network instructions:
    OP_SETMAC=0x0020
    OP_SETIP=0x0021
    OP_SETIPV4NETMASK=0x0022
    OP_SETIPV4GATEWAY=0x0023
    OP_SETARPREPORTPERIOD=0x0024
    OP_SETMACMODE=0x0025
    
    #Control Instructions
    OP_PROGRAMBASICPLL=0x0100
    OP_PROGRAMEXTDCM=0x0101
    OP_SETCLOCKCONTROL=0x0102
    OP_SETCLOCKENABLE=0x0103
    OP_PROGRAMSAMPLEDIVIDER=0x0104
    OP_SETSPAREIO=0x0105
    OP_SETXFP=0x0106
    OP_PROGRAMSERIALPLL=0x0107
    OP_SETEIOCLKDIV = 0x0108
    
    #Streamer instructions
    OP_SETSTREAMCONTROL=0x0110
    OP_SETUDPTESTCLOCKDIVIDER=0x0111
    OP_SETMULTICASTUDPSTREAM=0x0112
    OP_SETMULTICASTUDPSTREAM_LEN=9
    OP_SETUDPSTREAM=0x0113
    OP_SETUDPSTREAM_LEN=15
    OP_SETG1TRIGGERMODULE=0x0114
    OP_SETG2GATEMODULE=0x0115
    OP_CLEARTRIGGERSTATUS=0x0116
    OP_SETSATACONTROL=0x0117
    
    #CAMTimer instructions
    OP_SETCTCONTROL=0x0120
    OP_SETCTOUTPUT=0x0121
    OP_SETCTCLKDIV=0x0122
    OP_SETCTTIMER=0x0123
    OP_SETCTIDLE=0x0124
    OP_SETCTARMED=0x0125
    OP_SETCTRUNNING=0x0126
        
    #SCB instructions
    OP_SCBWRITECA=0x0060
    OP_SCBWRITERA=0x0061
    OP_SCBREADCA=0x0062
    OP_SCBREADRA=0x0063
    
    #Parallel Data Interface instructions:
    OP_WRITEPDI=0x0068
    OP_READPDI=0x0069
    
    #Storage Flash instructions
    OP_FLCHIPERASE=0x0070
    OP_FLBLOCKERASE=0x0071
    OP_FLBLOCKERASEW=0x0072
    OP_FLPROGRAM=0x0073
    OP_FLREAD=0x0074
    
    #Firmware Upgrade and Test instructions
    OP_LOADFUP=0x0800
    OP_STARTFUP=0x0801
    OP_SHORTBEEP=0x0810

    #**************************AnswerCodes
    AN_ACK=0xFF00
    AN_SDRAMPAGE=0xFF01
    AN_SCBDATA=0xFF02
    AN_FLASHPAGE=0xFF03
    AN_PDIDATA=0xFF04

class APDCAM10G_ADCcodes_v1 :  
    """ Register addresses and other defines for the 10G ADC board V1
    """
    ADC_REG_MC_VERSION = 0x01
    ADC_REG_SERIAL = 0x03
    ADC_REG_FPGA_VERSION = 0x05
    ADC_REG_STATUS1 = 0x08
    ADC_REG_STATUS2 = 0x09
    ADC_REG_TEMP = 0x0A
    ADC_REG_CONTROL = 0x0B
    ADC_REG_DSLVCLKMUL = 0x0C
    ADC_REG_DSLVCLKDIV = 0x0D
    ADC_REG_DVDD33 = 0x0E
    ADC_REG_DVDD25 = 0x10
    ADC_REG_AVDD33 = 0x12
    ADC_REG_AVDD18 = 0x14
    ADC_REG_CHENABLE1 = 0x16
    ADC_REG_CHENABLE2 = 0x17
    ADC_REG_CHENABLE3 = 0x18
    ADC_REG_CHENABLE4 = 0x19
    ADC_REG_RINGBUFSIZE = 0x1A
    ADC_REG_RESOLUTION = 0x1C
    ADC_REG_AD1TESTMODE = 0x28
    ADC_REG_AD2TESTMODE = 0x29
    ADC_REG_AD3TESTMODE = 0x2A
    ADC_REG_AD4TESTMODE = 0x2B
    ADC_REG_MAXVAL11 = 0x70
    ADC_REG_ACTSAMPLECH1 = 0xB0
    ADC_REG_ACTSAMPLECH2 = 0xB4
    ADC_REG_ACTSAMPLECH3 = 0xB8
    ADC_REG_ACTSAMPLECH4 = 0xBC
    ADC_REG_DAC1 = 0x30
    ADC_REG_OVDLEVEL = 0xC0
    ADC_REG_OVDSTATUS = 0xC2
    ADC_REG_OVDTIME = 0xc3
    ADC_REG_RESET = 0x25
    ADC_REG_COEFF_01 = 0xD0
    ADC_REG_COEFF_INT = 0xDA
    ADC_REG_BPSCH1 = 0x1D
    ADC_REG_ERRORCODE = 0x24
    
    INT_TRIG_POSITIVE = 0
    INT_TRIG_NEGATIVE = 1
    

class APDCAM_PCcodes_v1 :
    """ Register addresses and other defines for the APDCAM control board
    """
    PC_CARD = 2
    PC_REG_BOARD_SERIAL = 0x0100
    PC_REG_FW_VERSION = 0x0002
    PC_REG_HV1SET = 0x56
    PC_REG_HV2SET = 0x58
    PC_REG_HV1MON = 0x04
    PC_REG_HV2MON = 0x06
    PC_REG_HV1MAX = 0x102
    PC_REG_HV2MAX = 0x104
    PC_REG_HVENABLE = 0x60
    PC_REG_HVON = 0x5E
    PC_REG_SHSTATE = 0x82
    PC_REG_SHMODE = 0x80
    PC_REG_TEMP_SENSOR_1 = 0x0C
    PC_REG_TEMP_CONTROL_WEIGHTS_1 = 0x10A
    PC_REG_FAN1_CONTROL_WEIGHTS_1 = 0x12A
    PC_REG_FAN2_CONTROL_WEIGHTS_1 = 0x14A
    PC_REG_FAN3_CONTROL_WEIGHTS_1 = 0x16A
    PC_REG_FAN1_SPEED = 0x6C
    PC_REG_FAN1_TEMP_SET = 0x72
    PC_REG_FAN1_TEMP_DIFF = 0x74
    PC_REG_FAN2_TEMP_LIMIT = 0x76
    PC_REG_FAN3_TEMP_LIMIT = 0x78
    PC_REG_PELT_CTRL = 0x2C
    PC_REG_DETECTOR_TEMP_SET = 0x6A
    PC_REG_P_GAIN = 0x50
    PC_REG_I_GAIN = 0x52
    PC_REG_D_GAIN = 0x54
    PC_REG_RESET = 0x84
    PC_REG_FACTORY_WRITE = 0x88
    PC_REG_ERRORCODE = 0x86
    PC_REG_CALLIGHT = 0x7A
    PC_IRQ_POWER_PID_ENABLE = 0x64
    PC_REG_PELT_MANUAL = 0x4e

class APDCAM_onetimer:
    """ Settings of one timer in CAMTIMER
    """
    def __init__(self):
        self.delay = 0
        self.numberOfPulses = 0
        self.pulseOn = 0
        self.pulseOff = 0
        self.channelEnable = bytes([0])
        # Used for managing the allocation of timers
        self.used = False  
        
class APDCAM_timer:
    """ This contains the APDCAM CAMTIMER settings and methods.
        All methods operate on the data in memory. Use the loadSetup
        method to load the settings to APDCAM.
    """
    MODE_RETURN_IDLE = 0
    MODE_RETURN_ARMED = 1
    MODE_RETURN_RUN = 2
    RISING_EDGE = 0
    FALLING_EDGE = 1
    
    def __init__(self):
        self.clockDiv = 0
        self.extTriggerEnable = False
        self.intTriggerEnable = False
        self.extTriggerPolarity = APDCAM_timer.RISING_EDGE
        self.mode = APDCAM_timer.MODE_RETURN_IDLE
        onetimer = APDCAM_onetimer()
        self.timers = []
        for i in range(10):
            self.timers.append(onetimer)
        self.outputEnable = 0
        self.outputPolarity = 0
        self.outputArmedState = 0
        self.outputIdleState = 0
   
class measurePara_class:
    def __init__(self):
        self.numberOfSamples=0
        self.channelMasks=0
        self.sampleDiv=0,
        self.bits=0
        self.externalTriggerPolarity=None
        self.internalTrigger=False
        self.triggerDelay = 0

class apdcamXml:
    def __init__(self,filename):
        self.filename = filename
        self.sections = []
        self.sectionElements = []
        self.top = None
        
    def createHead(self,device):
        self.top = ET.Element('General',attrib={"Version":"1.0", "Device":device})

    def addElement(self,section=None,element=None,value=None,unit=None,comment=None, value_type=None):
        if (section == None) or (element == None) or (value == None):
            return "apdcamXml.addElement: Missing input data"
        

        if (type(value) == int):
            value_str = str(value)  
            type_str = 'long'
        elif (type(value) == float):
            value_str = str(value)
            type_str = "float"
        elif (type(value) == str):
            value_str = value
        else:
            return " apdcamXml.addElement: unsuitable input data type"

        if (value_type != None):
            type_str = value_type
            
        if (unit == None):
            unit_str = "none"
        else:
            unit_str = unit
                
        try:
            section_index = self.sections.index(section)
            s = self.sectionElements[section_index]
        except:
            s = ET.SubElement(self.top, section)
            self.sections.append(section)
            self.sectionElements.append(s)
            section_index = len(self.sectionElements)-1
        
        if (comment == None):
            child = ET.SubElement(s, element, attrib={"Value":value_str, "Unit":unit_str,"Type":type_str,})
        else:    
            child = ET.SubElement(s, element, attrib={"Value":value_str, "Unit":unit_str,"Type":type_str,\
                                                  "Comment":comment})

    def writeFile(self):
        ET.ElementTree(self.top).write(self.filename)
                
    
class APDCAM10G_status :
    """ This class stores data read from APDCAM10G
    """
    def __init__(self):
        self.firmware = ""
        # List of ADC addresses
        self.ADC_address = [] 
        self.ADC_serial = []
        self.ADC_FPGA_version = []
        self.ADC_MC_version = []
        self.PC_serial = None
        self.PC_FW_version = None
        self.HV_set = [0,0,0,0]
        self.HV_act = [0,0,0,0]
        self.temps = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]      
        self.ref_temp = 0.0
        self.extclock_valid = False
        self.extclock_freq = 0.0  # kHz
        self.CC_settings = None
        self.CC_variables = None
        
class APDCAM10G_regCom:
    """ This class is for reading/writing APDCAM-10G registers and sending commands
        Create an instance and call the connect() method
        before reading/writing registers, this starts the UDP packet read.
        When the instance is deleted the UDP read is stopped and registers
        cannot be read/written any more.
        For receiving measurement data create an APDCAM10G_data instance.
    """ 
    # The port where UPD is sent
    # This can be any port except HTTP
    APDCAM_PORT=23 
    # The maximum UDP size for register read/write
    MAX_UDP_DATA = 1472
    
    CLK_INTERNAL = 0
    CLK_EXTERNAL = 1
    def __init__(self):
        self.APDCAM_IP = "10.123.13.102"
        self.commPort = 9997 # this is the receiving port
        self.answerTimeout = 100 # ms
        self.commSocket = None
        self.pdiReadWaitTime = 1 # Default wait time between two read operations in one UDP command [ms]
        self.pdiWriteWaitTime = 1 # Default wait time between two write operations in one UDP command [ms]
        self.UDP_data = None  # This will collect UDP commands before sending them
        self.status = APDCAM10G_status()
        self.measurePara = measurePara_class()
        self.versionCode = None;  # code for firmware type 0: before 105, 1: from 105
        self.HV_conversion_out = [0.12, 0.12, 0.12, 0.12] # V/digit
        self.HV_conversion_in = [0.12, 0.12, 0.12, 0.12] # V/digit
        self.lock = threading.RLock()
        self.repeatNumber=5 # Number of times a read/write operation is repeated before an error is indicated
        self.CAMTIMER = APDCAM_timer()
        
    def connect(self,ip="10.123.13.102"):
        """ Connect to the camera and start the answrer reading socket
        Returns and error message or ""
        """
        if (type(ip) is str):
            _ip = bytearray(ip,encoding='ASCII')
        elif(type(ip) is bytes):
            _ip = ip
        else:
            raise ValueError("Invalid IP address for camera. Should be sting or bytearray.")
        self.APDCAM_IP = ip
        err = APDCAM10G_regCom.startReceiveAnswer(self)
        if (err != "") :
            self.close()
            return "Error connecting to camera: "+err
        err = APDCAM10G_regCom.readStatus(self,dataOnly=True)
        if (err != ""):
            self.close()
            return "Error connecting to camera: "+err
        #Extracting camera information
        d = self.status.CC_settings 
        self.status.firmware = d[APDCAM10G_codes_v1.CC_REGISTER_FIRMWARE:APDCAM10G_codes_v1.CC_REGISTER_FIRMWARE+14]
        if (self.status.firmware[0:11] != b"BSF12-0001-"):
            err = "Unknown camera firmware."
            self.close()
            return err
        v = int(self.status.firmware[11:14])
        if (v < 105):
            self.versionCode = 0
        else:
            self.versionCode = 1        
        
        if (self.versionCode == 0) :
            self.codes_CC = APDCAM10G_codes_v1()
            self.codes_ADC = APDCAM10G_ADCcodes_v1()
            self.codes_PC = APDCAM_PCcodes_v1()
        else:
            self.codes_CC = APDCAM10G_codes_v2()
            self.codes_ADC = APDCAM10G_ADCcodes_v1()
            self.codes_PC = APDCAM_PCcodes_v1()
        
        self.status.ADC_address = []
        self.status.ADC_serial = []
        self.status.ADC_FPGA_version = []
        self.status.ADC_MC_version = []
        check_address_list = [8,9,10,11]
        err,data = self.readPDI(check_address_list,[0,0,0,0],[7,7,7,7],arrayData = [True, True, True, True])
        if (err != ""):
            self.close()
            return err
        for i in range(len(check_address_list)):
            d = data[i]
            if ((d[0] & 0xf0) == 0x20) :
                self.status.ADC_address.append(check_address_list[i])
                self.status.ADC_serial.append(int.from_bytes(d[3:5],byteorder='little',signed=False))
                self.status.ADC_FPGA_version.append(str(int.from_bytes([d[5]],'little',signed=False))+\
                                        "."+str(int.from_bytes([d[6]],'little',signed=False)))
                self.status.ADC_MC_version.append(str(int.from_bytes([d[1]],'little',signed=False))+\
                                        "."+str(int.from_bytes([d[1]],'little',signed=False)))
        if (len(self.status.ADC_address) == 0) :
            self.close()
            return "No ADC board found."
        
        err,data = self.readPDI([self.codes_PC.PC_CARD,self.codes_PC.PC_CARD],\
                                [0,self.codes_PC.PC_REG_BOARD_SERIAL],\
                                [7,2],\
                                arrayData = [True,False])
        if (err != ""):
            self.close()
            return err
        d = data[0]
        if ((d[0] & 0xf0) == 0x40) :
            self.status.PC_serial = data[1]
            self.status.PC_FW_version = "{:4.2f}".format(float(int.from_bytes(d[2:4],'little',signed=False))/100)
        else :
            self.close()
            return "No control board found."
        
        err = self.syncADC()
        if (err != ""):
            self.close()
            return err
        err = self.getInterface()
#        if (err != ""):
#            self.close()
#            return err
        return ""
        
    def close(self):
        if self.commSocket != None:
            self.commSocket.close()
        self.commSocket = None    
            
    def setIP(self,IP):
        self.APDCAM_IP = IP
        
    def getIP(self):
        return self.APDCAM_IP

    def startReceiveAnswer(self):
        """Starts the receiver socket
            Returns "" or error message
        """
        
        # Return is socket already allocated
        if self.commSocket != None:
            return ""
        try:
            self.commSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as se:
            self.commSocket = Null
            return se.args[1]
        try:
            self.commSocket.bind((b'0.0.0.0', self.commPort))
        except socket.error as se :
            self.commSocket = None
            return se.args[1]
        self.commSocket.setblocking(1)  # non blocking receive
        self.commSocket.settimeout(self.answerTimeout/1000.)  

        return ""
    
    def getAnswer(self):
        
        """ Get an answer sent by APDCAM-10G in one UDP packet
            Returns err, data.
            err: Error string or ""
            data: bytes of data
        """
        if (self.commSocket == None):
            return "APDCAM is not connected.",None
        try:
            data = self.commSocket.recv(APDCAM10G_regCom.MAX_UDP_DATA)
        except socket.timeout:
            return "",None
        except socket.error as se:
            return se.args[1],None
        return "", data
    
    
    def sendCommand(self,opCode,userData,sendImmediately=True):
        """
        Will create DDToIP command and add to existing UDP command package
        Will immadiately send UDP if SendImmadiately is not False
        If opCode is None then will add no data just send if sendImmediately is set True
        
        Parameters
        ----------
        opCode: int or bytes 
            The operation code OP_... (see class APDCAM10G_codes_...)
        userData: bytearray
            The user data for the operation. Set None of no data.
        sendImmediately: bool
            If True send immediately
        
        Return values
        -------------
        str
            "" If no error
            "Too much data": Too much data, cannot fit into present UDP packet
            "No data to send"
            Other error text relating to network
        """
        import socket
        
        self.lock.acquire()
        # if there is now half-written UDP packet starting a new
        if self.UDP_data == None :
            self.UDP_data = b"DDToIP"+b"Fusion Instrum."+bytes([3])
        if opCode != None :
            UDP_command_block = bytes([opCode//256])+bytes([opCode%256])
            if (userData != None) :    
                c_len = len(userData)
                UDP_command_block += bytes([c_len//256])+bytes([c_len%256])+userData
            else :
                UDP_command_block += bytes(2)
            self.UDP_data += UDP_command_block
        if sendImmediately == False :
            self.lock.release()
            return ""
        if self.UDP_data == None :
            self.lock.release()
            return "No data to send"        
        try:
            ndat = self.commSocket.sendto(self.UDP_data, (self.APDCAM_IP, APDCAM10G_regCom.APDCAM_PORT))
        except socket.error as se:
            self.lock.release()
            return se.args[1]
        if (ndat != len(self.UDP_data)) :
            self.UDP_data = None
            self.lock.release()
            return "Could not send all data."
        self.UDP_data = None
        time.sleep(0.01)
        self.lock.release()
        return ""
 
    def readCCdata(self,dataType=0):
        """ Reads the Settings or the Variables data block from the 10G (CC) card. 
        Stores the result in self.status.CC_settings or self.status.CC_variables.
        dataType: 0: Settings
                  1: Variables
                  
        Returns error text or ""
        """
        
        if (dataType == 0) :
            dataCode = 2 # DIT & Settings
        else :
            dataCode = 3 #Variables
        userData =bytes([0,dataCode])
        self.lock.acquire()
        for rep in range(self.repeatNumber) :
            err = APDCAM10G_regCom.sendCommand(self,APDCAM10G_codes_v1.OP_SENDACK,userData,sendImmediately=True)
            if (err != ""):
                time.sleep(0.001)
                print("repeat readCCdata/1 {:d}".format(rep))
                continue
            err1, d = APDCAM10G_regCom.getAnswer(self)
            if (err != "" or d == None):
                time.sleep(0.1)
                self.clearAnswerQueue()
                #print("Error radCCdata/2:"+err)
                #print("repeat readCCdata/2 {:d}".format(rep))
                continue
            d = d[22:len(d)]
            resp_command = int.from_bytes(d[0:2],'big',signed=False)
            if (resp_command != APDCAM10G_codes_v1.AN_ACK) :
                err1 = "readCCdata/3 Invalid response by camera (wrong command:{:X}).".format(resp_command)
                #print(err1)
                #print("repeat readCCdata/3 {:d}".format(rep))
                time.sleep(0.1)
                self.clearAnswerQueue()
                continue
            if ((d[4] != 0) or (d[5] != dataCode)) : 
                err1 = "readCcdata/4 Invalid answer from camera (wrong data block: {:d}).".format(int(d[5]))
                #print(err1)
                #print("repeat readCCdata/4 {:d}".format(rep))
                time.sleep(0.1)
                self.clearAnswerQueue()
                continue
            d = d[6:len(d)]            
            break
        # end of for cycle over repeats
        self.lock.release()
        
        if err != "" :
            return "Error (readCCdata):"+err
        if (err1 != "") or (d == None) :
            if (err1 == "") :
                err1  = "Error (readCCdata): Timeout." 
            return "Error (readCCdata):"+err1    
        if (dataType == 0) :
            self.status.CC_settings = d
        else :
            self.status.CC_variables = d
        return ""
        
    
    
    def readStatus(self,dataOnly=False,HV_repeat=1):
        """Reads the status of APDCAM (Settings and Variables tables and some Control
        card and ADC data and stores in the status variable which is an APDCAM10G_status class.
        
        Returns an error text or ""
        """
        # Read DIT and Settings
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        
         # Read variables data from the 10G card
        err = self.readCCdata(dataType=1)
        if (err != ""):
            return err
        if (dataOnly):
            return ""
        
        self.status.extclock_valid = self.status.CC_variables[self.codes_CC.CC_REGISTER_PLLSTAT] & 2**3 != 0
        freq = self.status.CC_variables[self.codes_CC.CC_REGISTER_EXTCLKFREQ:self.codes_CC.CC_REGISTER_EXTCLKFREQ+2]       
        self.status.extclock_freq = int.from_bytes(freq,'big',signed=False)
        self.status.CCTemp = int(self.status.CC_variables[self.codes_CC.CC_REGISTER_BOARDTEMP])
        # Reading data from the Control card
        c = self.codes_PC.PC_CARD
        cards = [c,c,c,c]
        regs = [self.codes_PC.PC_REG_HV1SET,\
                self.codes_PC.PC_REG_HV1MON,\
                self.codes_PC.PC_REG_TEMP_SENSOR_1,\
                self.codes_PC.PC_REG_DETECTOR_TEMP_SET]
                
        err, data = APDCAM10G_regCom.readPDI(self,cards,regs,[8,8,32,2],arrayData=[True,True,True,False])
        if err != "" :
            return err
        d = data[0]
        for i in range(4):
            self.status.HV_set[i] = (d[0+i*2]+d[1+i*2]*255)*self.HV_conversion_out[i]
        d = data[2]
        for i in range(16):
            self.status.temps[i] = (d[0+i*2]+d[1+i*2]*255)*0.1
        self.status.ref_temp = data[3]*0.1

        d = data[1]
        for i in range(4):
            self.status.HV_act[i] = (d[0+i*2]+d[1+i*2]*255)*self.HV_conversion_in[i]          
        if (HV_repeat > 1):
            for i in range(HV_repeat-1):  
                err, data = APDCAM10G_regCom.readPDI(self,self.codes_PC.PC_CARD,self.codes_PC.PC_REG_HV1MON,8,arrayData=True)
                if err != "" :
                    return err
                d = data[0]
                for j in range(4):
                    self.status.HV_act[j]  += (d[0+j*2]+d[1+j*2]*255)*self.HV_conversion_in[j]   
            for j in range(4):
                self.status.HV_act[j] /= HV_repeat        
        return ""
       
    def clearAnswerQueue(self):
        """ Reads answers from the camera until a timeout occurs.
        This is used for clearing the answers if an error happened
        Returns an error text or ""
        """
        while 1 :
            err, d = APDCAM10G_regCom.getAnswer(self)
            if (err != ""):
                return err
            if (d == None):
                return ""
    
    def FactoryReset(self,reset_bool):
        """
        Do factory reset for all components of the camera.

        Parameters
        ----------
        reset_bool : bool
            Does reset only if this is True.

        Returns
        -------
        str
            Error string or ""

        """
        if (self.commSocket is None):
            return "Not connected."
        if (not (reset_bool)):
            return
        # Read the SATA state is it will be changed by the factory reset in V1
        err,dual_SATA_state = self.getDualSATA()
        if (err != ""):
            return err
        # Reset the ADCs
        n_adc = len(self.status.ADC_address)
        reg = [self.codes_ADC.ADC_REG_RESET]*n_adc
        data = [0xcd]*n_adc
        err = self.writePDI(self.status.ADC_address,reg,data,\
                            numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=True)
        if (err != ""):
            return err
        time.sleep(2)
        data = [0]*n_adc
        err = self.writePDI(self.status.ADC_address,reg,data,\
                            numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=True)
        if (err != ""):
            return err
        #Reset the control card
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_RESET,0xcd,\
                            numberOfBytes=1,arrayData=False,noReadBack=True)
        if (err != ""):
            return err

        time.sleep(2)
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_RESET,0,\
                            numberOfBytes=1,arrayData=False,noReadBack=True)
        if (err != ""):
            return err

        err = self.sendCommand(self.codes_CC.OP_RESET,bytearray([0,0x07,0xd0]),sendImmediately=True)
        if (err != ""):
           return err
        time.sleep(5)
        err = self.setDualSATA(dual_SATA_state=dual_SATA_state)
        if (err != ""):
            err = "Could not set dual SATA setting to original state after reset. Camera was not on default address?"
        return ""


    def readPDI(self,cardAddress=None,registerAddress=None,numberOfBytes=None,arrayData=None,byteOrder=None,waitTime=None):       
        """Reads data through the Parallel Data Interface (PDI). Can do multiple reads in succession.
            Waits a given time after each read. Returns data in a list, each element is the result 
            of one read operation. Returns data either as array of bytes or integer, as defined by the
            arrayData and byteOrder input.

            INPUT:
                cardAddress: Card addresses (one or more)
                registerAddress: Register start address (list length should be equal to cardAddress length)
                numberOfBytes: Read length (list length should be equal to cardAddress length)
                arrayData : For each read operation sets whether the data should be returned as one 
                            integer or byte array. False: return integer, True: return byte array.
                            Default is that all reads are integer.
                byteOrder: defines the byte order for converting to integer. 
                            List with 'MSB' or LSB' elements. LSB means LSB first.  Default is LSB.         
                waitTime: Wait time between register read commands in ms. Will insert a wait command
                          between the read commands and also after the last one. If 0 no wait commands will be generated.
          Returns error text and data in list of bytarrays       
        """ 
        
        #Ensuring that input values are not modified
        cardAddress = copy.deepcopy(cardAddress)
        registerAddress = copy.deepcopy(registerAddress)
        numberOfBytes = copy.deepcopy(numberOfBytes)
        arrayData =  copy.deepcopy(arrayData)
        byteOrder = copy.deepcopy(byteOrder)


        if type(cardAddress) is not list:
            cardAddress = [cardAddress]
        if type(registerAddress) is not list:
            registerAddress = [registerAddress]
        if type(numberOfBytes) is not list:
            numberOfBytes = [numberOfBytes]
        n_read = len(cardAddress)
        if (arrayData == None) :
            arrayData = []
            for i in range(n_read) :
                arrayData.append(False)
        if (byteOrder == None) :
            byteOrder = []
            for i in range(n_read) :
                byteOrder.append('LSB')
        if type(arrayData) is not list:
            arrayData = [arrayData]
        if type(byteOrder) is not list:
            byteOrder = [byteOrder]

        if (len(registerAddress) != n_read) or (len(numberOfBytes) != n_read) or \
           (len(arrayData) != n_read) or (len(byteOrder) != n_read) :
            return "Inconsistent input lists.",None

        if waitTime != None :
            w = waitTime
        else:
            w = self.pdiReadWaitTime
            
        err = ""
        data = None
        
        self.lock.acquire()
        for rep in range(self.repeatNumber) :
#            print("readPDI repeat %d" % rep)
            for i in range(n_read):
                userData = bytes([cardAddress[i]])+registerAddress[i].to_bytes(4,'big',signed=False)+\
                           numberOfBytes[i].to_bytes(2,'big',signed=False) 
                err = APDCAM10G_regCom.sendCommand(self,APDCAM10G_codes_v1.OP_READPDI,userData,sendImmediately=False)
                if err != "" :
                    self.lock.release()
                    return err,None
                if (w != 0) :
                    userData = w.to_bytes(2,'big',signed=False)
                    err = APDCAM10G_regCom.sendCommand(self,APDCAM10G_codes_v1.OP_WAIT,userData,sendImmediately=False)
                    if err != "" :
                        self.lock.release()
                        return err,None 
            err = APDCAM10G_regCom.sendCommand(self,None,None,sendImmediately=True)
            if err != "" :
                time.sleep(0.001)
                continue
            data = []
            for i in range(n_read):
                err, d = APDCAM10G_regCom.getAnswer(self)
                if (err == "") and (d != None) :
                    # Data arrived
                    d = d[22:len(d)]
                    if (d[0] != 0xff) or (d[1] !=  0x04) :
                        err = "Invalid response by camera (READPDI, {:X})".format(int.from_bytes(d[0:2],'big',signed=False))
                        break
                    dlen = d[2]*256+d[3]
                    if (dlen != numberOfBytes[i]) :
                        err = "Number for bytes received is different from requested."
                        break
                    d = d[4:len(d)]
                    if (arrayData[i] == False ) :
                        if (byteOrder[i] == "MSB") :
                            d = int.from_bytes(d,'big',signed=False)
                        else :
                            d = int.from_bytes(d,'little',signed=False)
                    data.append(d)
                else:
                    #No data arrived
                    if (err == "") :
                        err  = "Timeout."
                    #print(err)
                    break
            # End of for cycle to read answers
            if (err != "") :
                time.sleep(0.1)
                self.clearAnswerQueue()
                #print(err)
                #print("repeat readPDI/1 {:d}".format(rep))
                continue
            break  # If we get here the read operation was successful
        # End of for cycle over repeats
#        print("End readPDI")
        self.lock.release()
        if (err != ""):
            err =  "Error (readPDI):"+err
        return err,data
   # end of readPDI 
  
    def writePDI(self,cardAddress=None,registerAddress=None,data=None,numberOfBytes=None,\
             arrayData=None,byteOrder=None,waitTime=None, noReadBack=False):       
        """Writes data through the Parallel Data Interface (PDI). Can do multiple writes in succession.
            Waits a given time after each write. Accepts data either as array of bytes or integer, as defined by the
            arrayData and byteOrder input.
    
            INPUT:
                cardAddress: Card addresses (list, one or more address) 
                registerAddress: Register start address list (list length should be equal to cardAddress length)
                data: Data to write. If it is a list should be the same length as cardAddress. Each element is either
                      an integer or bytearray.
                numberOfBytes: Write length for each write operation. 
                               (List length should be equal to cardAddress length)
                               If all writes are arrayData then this is optional.
                arrayData : For each write operation sets whether the data should be inteprepted as one 
                                integer or byte array. False: integer, True: byte array.
                                Default is that all data are integer. If arrayData == False
                                then the integer is converted to a byte array of numberOfBytes 
                byteOrder: defines tyhe byte order for converting from integer to register data. 
                       List with 'MSB' or LSB' elements. LSB means LSB first.  Default is LSB.          
                waitTime: Wait time between register write commands in ms. Will insert a wait command
                      between the read commands and also after the last one. If 0 no wait commands will be generated.
                noReadBack: if True will read back the written data and compare to the input   
            Returns error text      
        """ 
        # Ensuring that input values are not modified
        cardAddress = copy.deepcopy(cardAddress)
        registerAddress = copy.deepcopy(registerAddress)
        data = copy.deepcopy(data) 
        numberOfBytes = copy.deepcopy(numberOfBytes)
        arrayData =  copy.deepcopy(arrayData)
        byteOrder = copy.deepcopy(byteOrder)
        
        if type(cardAddress) is not list:
            cardAddress = [cardAddress]
        n_write = len(cardAddress)        
        if type(registerAddress) is not list:
            registerAddress = [registerAddress]    
        if (type(data) is not list) :
            data = [data]
        if (arrayData == None):
            arrayData = []
            for i in range(n_write) :
                arrayData.append(False)
        if (type(arrayData) is not list) :
            arrayData = [arrayData]
        if (len(registerAddress) != n_write) or (len(arrayData) != n_write)\
            or (len(data) != n_write) :
                return "Error in writePDI: Inconsistent input lists."
        for i in range(n_write) :
            if (arrayData[i] == False) and (numberOfBytes == None) :
                return "Error in writePDI: If arrayData[i] is False numberOfBytes[i] should be set."
        # Here we can be sure that either all operations are arrayData or numberOfBytes is set    
        if (numberOfBytes == None) :
            # This means all operations are arrayData
            numberOfBytes = []
            for i in range(n_write) :
                if (not (type(data[i]) is bytearray)):
                    return "Error in writePDI: If arrayData[i] is True data[i] should be bytearray type."
                numberOfBytes.append(len(data[i]))
        if (type(numberOfBytes) is not list) :
            numberOfBytes = [numberOfBytes]
        if (byteOrder == None) :
            byteOrder = []
            for i in range(n_write) :
                byteOrder.append('LSB')
        if type(byteOrder) is not list:
            byteOrder = [byteOrder]
        if (len(numberOfBytes) != n_write) or (len(byteOrder) != n_write) :
                return "Error in writePDI: Inconsistent input lists."

        if waitTime != None :
            w = waitTime
        else:
            w = self.pdiWriteWaitTime
            
        err = ""
     
        self.lock.acquire()
        for rep in range(self.repeatNumber) :  
#            print("writePDI repeat %d" % rep)
            for i in range(n_write):
                userData = bytes([cardAddress[i]])+registerAddress[i].to_bytes(4,'big',signed=False)
                if (arrayData[i] == False) :
                    if (byteOrder[i] == 'MSB') :
                        userData = userData + \
                                    data[i].to_bytes(numberOfBytes[i], 'big', signed=False)
                    else :
                        userData = userData + \
                                    data[i].to_bytes(numberOfBytes[i], 'little', signed=False)
                else:
                    userData = userData + bytearray(data[i])
                    
                err = APDCAM10G_regCom.sendCommand(self,APDCAM10G_codes_v1.OP_WRITEPDI,userData,sendImmediately=False)
                if err != "" :
                    self.lock.release()
                    return err
                if (w != 0):
                    userData = w.to_bytes(2,'big',signed=False)
                    err = APDCAM10G_regCom.sendCommand(self,APDCAM10G_codes_v1.OP_WAIT,userData,sendImmediately=False)
                    if err != "" :
                        self.lock.release()
                        return err
            err = APDCAM10G_regCom.sendCommand(self,None,None,sendImmediately=True)
            if err != "" :
                time.sleep(0.001)
                continue
            if (noReadBack == True) :
                self.lock.release()
                return err
            
            time.sleep(0.001)
            # Reading back data for check
            err, d_read = APDCAM10G_regCom.readPDI(self,cardAddress,registerAddress,\
                                                   numberOfBytes,arrayData=arrayData,\
                                                   byteOrder=byteOrder)
            if (err != "") :
                err = "Error in writePDI: Error reading back data: "+err
                time.sleep(0.1)
                self.clearAnswerQueue()
                continue
            if (data != d_read) :
                err = "Error in writePDI: Data read back is different from written."                
                continue
            break  # We get here if write was done
        # end of cycle over repeats
        self.lock.release()
 #       print("End writePDI")
        if (err != "") :
            err = "Error (writePDI):"+err
        return err
   # end of writePDI
   
    def timerIdle(self):
        """ Returns error text
        """
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfc
        data = bytearray([0,mode])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        return err
        
    def timerArm(self):
        """ Returns error text
        """
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfc
        mode = mode | 0x02
        data = bytearray([0,mode])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        if (err != ""):
            return err
        mode = mode | 1
        data = bytearray([0,mode])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        return err
    
    def timerRun(self):      
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfd
        data = bytearray([0,mode])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        if (err != ""):
            return err
        mode = mode | 3
        data = bytearray([0,mode])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        return err

    def setTimerOutput(self) :
        data = bytes(\
                     [self.CAMTIMER.outputEnable | (self.CAMTIMER.outputPolarity << 4), \
                      self.CAMTIMER.outputIdleState | (self.CAMTIMER.outputArmedState << 4)]\
                      )
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTOUTPUT,data,sendImmediately=False)
        if (err != ""):
            return err
    
    def loadTimerSetup(self):
        """ Loads the actual setup to the camera
            returns error text
        """
        data = self.CAMTIMER.mode << 2
        if (self.CAMTIMER.extTriggerEnable):
            if (self.CAMTIMER.extTriggerPolarity == APDCAM_timer.RISING_EDGE):
                data = data | 0x10
            else:
                data = data | 0x20
        if (self.CAMTIMER.intTriggerEnable):
            data = data | 0x40
        data = bytes([0,data])
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=False)
        if (err != ""):
            return err
        data = bytes(\
                     [self.CAMTIMER.outputEnable | (self.CAMTIMER.outputPolarity << 4), \
                      self.CAMTIMER.outputIdleState | (self.CAMTIMER.outputArmedState << 4)]\
                      )
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTOUTPUT,data,sendImmediately=False)
        if (err != ""):
            return err
        data = self.CAMTIMER.clockDiv.to_bytes(2,byteorder='big',signed=False)
        err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCLKDIV,data,sendImmediately=False)    
        if (err != ""):
            return err
        for i in range(10):
            data = bytearray(13)
            data[0] = i+1
            if (self.CAMTIMER.timers[i].used) :
                if ((self.CAMTIMER.timers[i].delay > 2.**28) or (self.CAMTIMER.timers[i].delay < 0)):
                    return "CAMTIMER delay is out of range."
                self.CAMTIMER.timers[i].delay = round(self.CAMTIMER.timers[i].delay)
                if ((self.CAMTIMER.timers[i].pulseOn > 65535) or (self.CAMTIMER.timers[i].pulseOn < 0)):
                    return "CAMTIMER pulse on length is out of range ({:d}).".format(self.CAMTIMER.timers[i].pulseOn)
                self.CAMTIMER.timers[i].pulseOn = round(self.CAMTIMER.timers[i].pulseOn)
                if ((self.CAMTIMER.timers[i].pulseOff > 65535) or (self.CAMTIMER.timers[i].pulseOff < 0)):
                    return "CAMTIMER pulse off length is out of range ({:d}).".format(self.CAMTIMER.timers[i].pulseOff)
                self.CAMTIMER.timers[i].pulseOff = round(self.CAMTIMER.timers[i].pulseOff)
                if ((self.CAMTIMER.timers[i].numberOfPulses > 2.**28) or (self.CAMTIMER.timers[i].numberOfPulses < 0)):
                    return "CAMTIMER number of pulses is out of range."
                self.CAMTIMER.timers[i].numberOfPulses = round(self.CAMTIMER.timers[i].numberOfPulses)
                data[1:5] = self.CAMTIMER.timers[i].delay.to_bytes(4,byteorder='big',signed=False) 
                data[5:7] = self.CAMTIMER.timers[i].pulseOn.to_bytes(2,byteorder='big',signed=False)
                data[7:9] = self.CAMTIMER.timers[i].pulseOff.to_bytes(2,byteorder='big',signed=False)
                data[9:14] = self.CAMTIMER.timers[i].numberOfPulses.to_bytes(4,byteorder='big',signed=False)
                data[9] = (data[9] & 0x0f) | (self.CAMTIMER.timers[i].channelEnable << 4)
            err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTTIMER ,data,sendImmediately=False)   
            if (err != ""):
                return err
        err = self.sendCommand(None,None,sendImmediately=True)   
        return err

    def clearAllTimers(self):
        """ Clear everything
        """
        self.CAMTIMER = copy.deepcopy(APDCAM_timer())
        
    def clearOneTimer(self,timer):
        """ Clear one timer. 
            timer: 1...10
        """
        onetimer = APDCAM_onetimer()
        self.CAMTIMER.timers[timer-1] = copy.deepcopy(onetimer)
        
    def allocateTimer(self,timersettings):
        """ Will search for the first unused timer and load the settings to it
            timersettings is APDCAM_onetimer class
            Returns allocated timer number (1...10) or 0 if could not allocate.
        """
        found = 0
        for i in range(10):
            if (not self.CAMTIMER.timers[i].used) :
              self.CAMTIMER.timers[i] = copy.deepcopy(timersettings)
              self.CAMTIMER.timers[i].used = True
              found = i+1
              break
        return found
    
    def getInterface(self):
        """ Determine network interface name
            Works only on Linux
            Return error text
        """
        
        ip = self.getIP()
        net = ip.split('.')
        net = net[0]+'.'+net[1]+'.'+net[2]+'.'
        cmd = "ip -f inet address show | grep "+net
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
        if (len(d.stdout) == 0):
            return "Cannot find interface for APDCAM. Is the camera on?"
        txt = d.stdout
        txt_lines = txt.split(b'\n')
        txt = txt_lines[0].split()
        self.interface = txt[-1]
        return ""
        
    def setClock(self,source,adcdiv=33, adcmult=33, extdiv=20, extmult=20,autoExternal=False):
        """ Set external clock.
            source: APDCAM10G_regCom.CLK_INTERNAL or APDCAM10G_regCom.CLK_EXTERNAL
            extdiv: EXTRDCM divider
            extmult: EXTDCM multiplier
            adcdiv: ADC clock divider
            adcmult: ADC clock multiplier
            autoExternal: False or True
            
            Does not check clock quality, just sets. Use getAdcClock() to get status.
            
            Returns an error code. 
        """
        d = 0
        if (source == APDCAM10G_regCom.CLK_EXTERNAL):
            d |= 0x04
        if (autoExternal):    
            d |= 0x08
        err = self.sendCommand(self.codes_CC.OP_SETCLOCKCONTROL,bytes([d]),sendImmediately=True)
        if (err != ""):
            return err
        
        if (source == APDCAM10G_regCom.CLK_EXTERNAL):
            d = bytearray(2)
            d[0] = extmult
            d[1] = extdiv
            err = self.sendCommand(self.codes_CC.OP_PROGRAMEXTDCM,d,sendImmediately=True)
            if (err != ""):
                return err
        
        d = bytearray(5)
        d[0] = adcmult
        d[2] = adcdiv
        err = self.sendCommand(self.codes_CC.OP_PROGRAMBASICPLL,d,sendImmediately=True)
        if (err != ""):
            return err
        
        return ""
        
    def getAdcClock(self):
        """ Determines the ADC clock frequency. Handles external/internal clock.
            Returns err,f,mode[MHz]
            source: APDCAM10G_regCom.CLK_INTERNAL or APDCAM10G_regCom.CLK_EXTERNAL
        """
        err = self.readStatus(dataOnly=True)   
        if (err != ""):
            return err,None,None
        d = self.status.CC_variables[self.codes_CC.CC_REGISTER_PLLSTAT]
        if (d & 0x01 == 0):
            err = "Clock not locked."
            return err, None, None
        d = self.status.CC_settings[self.codes_CC.CC_REGISTER_CLOCK_CONTROL]
        if (d & 0x04 != 0):
            # External clock
            extdiv = self.status.CC_settings[self.codes_CC.CC_REGISTER_EXT_DCM_DIV]
            extmult = self.status.CC_settings[self.codes_CC.CC_REGISTER_EXT_DCM_MULT]                        
            d = self.status.CC_variables[self.codes_CC.CC_REGISTER_PLLSTAT]
            if (d & 0x0C != 0x0C):
                err = "External clock not valid."
                return err, None, None
            f = int.from_bytes(self.status.CC_variables[\
                                self.codes_CC.CC_REGISTER_EXTCLKFREQ:self.codes_CC.CC_REGISTER_EXTCLKFREQ+2],'big',signed=False)
            f_base = float(f)/1e3/extdiv*extmult
            source = APDCAM10G_regCom.CLK_EXTERNAL
        else:
            f_base = 20.
            source = APDCAM10G_regCom.CLK_INTERNAL
        adc_mult = int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_MULT])
        adc_div = int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_DIV_ADC])
        f = f_base*adc_mult/adc_div
        return "",f,source
            
    def syncADC(self):
        """ Synchronizes the ADC blocks in the ADC cards.
            Returns an error text. 
        """
            
        n_adc = len(self.status.ADC_address)
        reg = [self.codes_ADC.ADC_REG_CONTROL]*n_adc
        l = [1]*n_adc

        self.lock.acquire()
        while(1):
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break
            # print("Control regs (syncADC in): {:b},{:b}".format(data[0],data[1]))
    
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break
            for i in range(n_adc):
                data[i] |= 0x04 
            err = self.writePDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),copy.deepcopy(data),\
                                numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=False)
            if (err != ""):
                #print(err)
                break
            time.sleep(0.2)
            for i in range(n_adc):
                data[i] &= 0xFB
            err = self.writePDI(self.status.ADC_address,reg,data,numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=False)
            
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break
            #print("Control regs (syncADC out): {:b},{:b}".format(data[0],data[1]))
            break
        self.lock.release()
        return err

    def getDualSATA(self):
        """
        Reads the dual SATA state from the communications card.
        Does not check dual SATA setting in the ADCs.
        
        Return value
        ------------
        str
            error text or "" if no error
        bool
           True if dual SATA
           False if not dual SATA
        """
        
        if (self.commSocket is None):
            return "Not connected.", None
        err = self.readCCdata(dataType=self.codes_CC.CC_DATATYPE_SATACONTROL)
        if (err != ""):
            return err, None
        sata_state = self.status.CC_settings[self.codes_CC.CC_REGISTER_SATACONTROL]
        if (sata_state & 0x01 == 1):
            return "",True
        else:
            return "",False
               
    def setDualSATA(self, dual_SATA_state=True):
        """
            Sets the dual SATA state of the whole system, 10G card and ADCs
            
            Parameters
            ----------
            dual_SATA_state: bool
                True: set dual SATA
                False: clear dual SATA
            Return value
            ------------
            str:
                Returns an error text or "" of no error 
        """
        if (self.commSocket is None):
            return "Not connected."
        if (dual_SATA_state):
            d = bytearray([0x01])
        else:
            d = bytearray([0x00])
        err = self.sendCommand(self.codes_CC.OP_SETSATACONTROL,d,sendImmediately=True)
        if (err != ""):
           return err
        return self.setADCDualSATA(dual_SATA_state=dual_SATA_state)      
        
    def setADCDualSATA(self,dual_SATA_state=True):
        """
            Sets the dual SATA state in all ADCs.
            
            Parameters
            ----------
            dual_SATA_state: bool
                True: set dual SATA bits
                False: clear dual SATA bits
            Return value
            ------------
            str:
                Returns an error text or "" of no error 
        """
        self.lock.acquire()
        while (1):
            n_adc = len(self.status.ADC_address)
            reg = [self.codes_ADC.ADC_REG_CONTROL]*n_adc
            l = [1]*n_adc
            err,data = self.readPDI(self.status.ADC_address,reg,l,arrayData=[False]*n_adc)
            if (err != ""):
                break
            for i in range(n_adc):
                if (dual_SATA_state):
                    data[i] |= 0x03
                else:
                    data[i] &= 0xfd
            err = self.writePDI(self.status.ADC_address,reg,data,\
                                numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=False)
            if (err != ""):
                break
            
            # Don't need to read back, it is done in writePDI anyway
            # err,data = self.readPDI(self.status.ADC_address,reg,l,arrayData=[False]*n_adc)
            # if (err != ""):
            #     break
            #print("Control regs (setADCDualSATA): {:b},{:b}".format(data[0],data[1]))
            break
        self.lock.release()
        return err

    def sendADCIstruction(self,address,instruction):    
        """ Sends an instruction in to the ADC board. 
        address: ADC card address
        instruction: byte array of the instruction data
        """
        data = bytearray(len(instruction)+5)
        data[0] = address
        data[1:1+4] = bytes([0xff,0xff,0xff,0xff])
        data[5:5+len(instruction)] = instruction
        err = self.sendCommand(self.codes_CC.OP_WRITEPDI,data,sendImmediately=True)
        return err
 
    def initDAC(self,address):
        """ Sets the configuration of the DAC chips
        address: ADC card address
        """
        dac_instr = bytes([0x11,0x00,0x03,0x0C,0x34,0x00])
        return self.sendADCIstruction(address,dac_instr)
        
        
    def setOffsets(self,offsets):
        """ Sets all the offsets of the ADC channels
            offsets should be a list of offsets (integers) for the ADC channels
            returns error message or ""
        """
        n_adc = len(self.status.ADC_address)
        adcmap = DAC_ADC_channel_mapping()

        for i_adc in range(n_adc):
            self.initDAC(self.status.ADC_address[i_adc])
            data = bytearray(64)
            for i in range(32):
                dac_addr = adcmap[i]-1
                data[i*2:i*2+2] = offsets[dac_addr+32*i_adc].to_bytes(2,'little',signed=False)
            err = self.writePDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_DAC1,data,numberOfBytes=64,arrayData=True)
            if (err != ""):
                return "Error in setOffsets, ADC {:d}: {:s}".format(i_adc+1,err)
        return ""
    
    def getOffsets(self):
        """ Get all of the offset values on the channels.
            Returns an error message and list of offsets.
        """
        n_adc = len(self.status.ADC_address)
        adcmap = DAC_ADC_channel_mapping()
        data = []
        for i_adc in range(n_adc):
            err,offsets = self.readPDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_DAC1,numberOfBytes=64,arrayData=True)
            if (err != ""):
                return "Error in setOffsets, ADC {:d}: {:s}".format(i_adc+1,err),None
            offsets = offsets[0]
            for i in range(32):
                dac_addr = adcmap[i]-1
                data.append(int.from_bytes(offsets[dac_addr * 2:dac_addr * 2 + 2], 'little'))
        return "",data

    def getTestPattern(self):
        """ 
        Get all of the test pattern settings in the ADCs
            
        Parameters
        ----------
            None
            
        Return value
        ------------
        Returns
        -------
        string
            "" or error text.
        list
            List of test pattern values. The list has as many elements as ADC boards
            and each list element is a list of 4 values: the test pattern for the 4 blocks
        """
        n_adc = len(self.status.ADC_address)
        data = []
        for i_adc in range(n_adc):
            err,d = self.readPDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_AD1TESTMODE,numberOfBytes=4,arrayData=True)
            if (err != ""):
                return "Error in getTestPattern, ADC {:d}: {:s}".format(i_adc+1,err),None
            data.append(d[0])
        return "",data

    def setTestPattern(self,value):
        """ Set the test pattern of the ADCs.
        
        Parameters
        ----------
        value : list or int
            If int all ADCs will be set to this test pattern
            If list then each list element corresponds to one ADC block.
            If a list element is a single number then each 8-block in the ADC is set to this value.
            If a list element is a 4-element list the 8-channel blocks are set to these test patterns.
        """   
        n_adc = len(self.status.ADC_address)
        if (type(value) is list):
            if (len(value) != n_adc):
                return "Bad input in setTestPattern. Should be scalar or list with number of elements equal to number of ADCs."
            _value = value
        else:
            try:
                _value = [int(value)] * n_adc
            except ValueError:
                return "Bad input in setTestPattern."
        for i_adc in range(n_adc):  
            d = bytearray(4)
            if (type(_value[i_adc]) is list):
                if (len(_value[i_adc]) != 4):
                    return "Bad input in setTestPattern."
                for i in range(4):
                    d[i] = _value[i]
            else:
                for i in range(4):
                    d[i] = _value[i_adc]                
            err = self.writePDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_AD1TESTMODE,d,numberOfBytes=4,arrayData=True)
            if (err != ""):
                break
        return err  
    
    def setCallight(self,value):
        """ Set the calibration light.
        """    
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_CALLIGHT,value,numberOfBytes=2,arrayData=False)
        return err  

    def setAnalogPower(self,value):
        """ 
        Switch the analog power on/off.
            
        Parameters
        ----------
        value: int
            0: power off
            1: power on
            
        Return value
        ------------
        err : string
            "" or error text.
        
        """    
        err, d = self.readPDI(self.codes_PC.PC_CARD,self.codes_PC.PC_IRQ_POWER_PID_ENABLE,numberOfBytes=1,arrayData=False)
        if (err != ""):
            return err
        d = d[0]
        if (value == 0):
            d &= 0xfd
        elif (value == 1):
            d |= 0x02
        else:
            return "Invalid input value to setAnalogPower."
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_IRQ_POWER_PID_ENABLE,d,numberOfBytes=1,arrayData=False)
        return err  

    def getAnalogPower(self):
        """ 
        Return the status of the analog power (on/off).
            
        Parameters
        ----------
        none            
        
        Return value
        ------------
        err : string
            "" or error text.
        value: int
            0: power is off
            1: power is on
        """    
        err, d = self.readPDI(self.codes_PC.PC_CARD,self.codes_PC.PC_IRQ_POWER_PID_ENABLE,numberOfBytes=1,arrayData=False)
        if (err != ""):
            return err, 0
        if (d[0] & 0x02 == 0):
            return "", 0
        else:
            return "", 1

    def setShutter(self,value):
        """
        Set the shutter state.        

        Parameters
        ----------
        value : int
            0: Close
            1: Open

        Returns
        -------
        err : string
            "" or error text.
        """
        
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_SHSTATE,value,numberOfBytes=1,arrayData=False)
        return err  


    def getCallight(self):
        """ Get the current calibration  light setting.
        Returns error text and number
        """
        err, d = self.readPDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_CALLIGHT,numberOfBytes=2,arrayData=False)
        return err,d[0]
    
    def getHV(self,n): 
        """
        Get the HV value for one HV generator.

        Parameters
        ----------
        n : int
            The HV generator number (1...).

        Returns
        -------
        err: string
            
        value: float
            The HV in Volts

        """
        err = self.readStatus()
        if (err != ""):
            return err, None
        return err, self.status.HV_act[n - 1]
        
    def setHV(self,n,value):
        """ Set a detector voltage
        
        Parameters
        ----------
        n: int
            The HV generator number (1...)
        value: int or float
            The HV value in Volts.
        
        Returns
        ------------
        error text or ""
        """
        
        d = int(value/self.HV_conversion[n-1])

        err = self.writePDI(self.APDCAM_reg.codes_PC.PC_CARD,
                            self.APDCAM_reg.codes_PC.PC_REG_HV1SET+(n-1)*2,
                            d,
                            numberOfBytes=2,
                            arrayData=False
                            )
        return err
    
    def enableHV(self):
        """
        Enables the HV for the detectors.

        Returns
        -------
        err : string
            error text or ""
        """
        d = 0xAB
        err = self.writePDI(self.codes_PC.PC_CARD,
                            self.codes_PC.PC_REG_HVENABLE,
                            d,
                            numberOfBytes=1,
                            arrayData=False
                            )
        return err

    def disableHV(self):
        """
        Disables the HV for the detectors.

        Returns
        -------
        err : string
            error text or ""
        """
        d = 0
        err = self.writePDI(self.codes_PC.PC_CARD,
                            self.codes_PC.PC_REG_HVENABLE,
                            d,
                            numberOfBytes=1,
                            arrayData=False
                            )
        return err

    def HVOn(self,n):
        """
        Switches on one detector HV on.

        Parameters
        ----------
        n : int
            The HV generator number (1...)

        Returns
        -------
        error: string
               "" if no error, otherwise error message

        """

        err, d = self.readPDI(self.codes_PC.PC_CARD,
                              self.codes_PC.PC_REG_HVON,
                              1,
                              arrayData=False
                              )
        if (err != ""):
            return err
        d = d[0]
        d = d | 2**(n-1)
        err = self.writePDI(self.codes_PC.PC_CARD,
                            self.codes_PC.PC_REG_HVON,
                            d,
                            numberOfBytes=1,
                            arrayData=False
                            )
        return err

    def HVOff(self,n):
        """
        Switches on one detector HV off.

        Parameters
        ----------
        n : int
            The HV generator number (1...)

        Returns
        -------
        error: string
               "" if no error, otherwise error message

        """

        err, d = self.readPDI(self.codes_PC.PC_CARD,
                              self.codes_PC.PC_REG_HVON,
                              1,
                              arrayData=False
                              )
        if (err != ""):
            return err
        d = d[0]
        d = d & (2**(n-1) ^ 0xff)
        err = self.writePDI(self.codes_PC.PC_CARD,
                            self.codes_PC.PC_REG_HVON,
                            d,
                            numberOfBytes=1,
                            arrayData=False
                            )
        return err
    
    def setInternalTrigger(self,channel=None,enable=True,level=None,polarity=None):
        """
        Sets the internal trigger for one channel, but does not enable internal trigger globally.
        Use setTrigger to set up the global trigger scheme.

        Parameters
        ----------
        channel : int
            The ADC channel. (1...)
        level : int
            The level in 14 bit resolution. This is the scale of the ADC sigals. The final output signlas from the measurement 
            are 16384 - signal. Valid range: 0...16383
        polarity : int
            The polarity. Either self.codes_ADC.INT_TRIG_POSITIVE or self.codes_ADC.INT_TRIG_NEGATIVE
        enable: boolean, optional
            If True enables trigger on this channel. The default is True

        Returns
        -------
        err
            Error text or "".

        """
        
        if ((channel is None) or (level is None) or (polarity is None)):
            return "Parameters not set."
        adc_no = int((channel - 1) // 32)
        ch_num = int((channel - 1) % 32)
        if (enable):
            d = 2 ** 15  # Enable
        else:
            d = 0
        if (polarity == self.codes_ADC.INT_TRIG_POSITIVE):
            pass
        elif (polarity == self.codes_ADC.INT_TRIG_NEGATIVE):
            d += 2 ** 14
        else:
            return "Invalid trigger polarity"
        if ((level >= 2 ** 14) or (level < 0)):
            return "Invalid trigger level"
        d += level
        
        err = self.writePDI(self.status.ADC_address[adc_no],self.codes_ADC.ADC_REG_MAXVAL11 + ch_num * 2,int(d),numberOfBytes=2,arrayData=False)
        if (err != ""):
            return "Error setting internal trigger:"+err
        return ""

    def setInternalTriggerADC(self,enable=True):
        """
        Enable/Disable trigger output in all ADC blocks.

        Parameters
        ----------
        enable : boolean, optional
            True: Enable trigger. 
            False: Disable trigger.
                   The default is True.

        Returns
        -------
        err : string
            "" or error message.

        """
        n_adc = len(self.status.ADC_address)
        reg = [self.codes_ADC.ADC_REG_CONTROL] * n_adc           
        err,ret = self.readPDI(self.status.ADC_address,
                               reg,
                               numberOfBytes=[1]*n_adc,
                               arrayData=[False]*n_adc
                               )
        for i in range(len(ret)):
            if (enable):
                ret[i] |= 0x20
            else:
                ret[i] &= 0xff - 0x20
        err = self.writePDI(self.status.ADC_address,
                            reg,
                            ret,
                            numberOfBytes=[1]*n_adc,
                            arrayData=[False]*n_adc,
                            noReadBack=False
                            )
        return err
        
    
    def setTrigger(self,externalTriggerPolarity=None,internalTrigger=False,triggerDelay = 0):
        """
        Sets the trigger scheme in the camera.

        Parameters
        ----------
        externalTriggerPolarity: None: no external trigger
                                    0: Positive edge
                                    1: Negative edge
        internalTrigger: True enables internal trigger
        triggerDelay:  Trigger with this delay [microsec]

        Returns
        -------
        error: string
               "" if no error, otherwise error message

        """

        if (triggerDelay < 0):
            td = int(0)
        else:
            td = int(triggerDelay)
        d = 0x40
        if (externalTriggerPolarity is not None):
            if (externalTriggerPolarity == 0):
                d = d | 0x01
            else:
                d = d | 0x02
        if (internalTrigger):
            d = d | 0x04
        userData = bytes([d]) + td.to_bytes(4,'big',signed=False) 
        err = self.sendCommand(self.codes_CC.OP_SETTRIGGER,userData,sendImmediately=True)
        if (err != ""):
            return err
        return  self.setInternalTriggerADC(enable=internalTrigger)        
        
    def clearAllInternalTrigger(self):
        """
        Clears all internal trigger settings but does not disable internal trigger.

        Returns
        -------
        str
            DESCRIPTION.

        """
        d = bytearray(64)
                                          
        for adc in self.status.ADC_address:
           err = self.writePDI(adc,self.codes_ADC.ADC_REG_MAXVAL11,d,numberOfBytes=64,arrayData=True)
           if (err != ""):
               return "Error clearing internal trigger"
        return ""
           
    def measure(self,numberOfSamples=100000, channelMasks=[0xffffffff,0xffffffff, 0xffffffff, 0xffffffff], \
                sampleDiv=None, datapath="data", bits=None, waitForResult=True, externalTriggerPolarity=None,\
                internalTrigger=False, internalTriggerADC=None,  triggerDelay=0):
        """ This method measures by calling APDTest_10G. It will be replaced by another method in the
        APDCAM_data class as soon as Python measures fast.
        externalTriggerPolarity: None: no external trigger
                                    0: Positive edge
                                    1: Negative edge
        internalTrigger: True enables internal trigger, False disables.
                         If internalTriggerADC is None internal trigger enable in the ADCs
                         follows this setting.
        internalTriggerADC: None or boolean
                            None: Internal trigger Enable/Disable follows internalTrigger
                            True: Internal trigger in ADCs is enables
                            False: Internal trigger in ADCs disables
        triggerDelay:  Trigger with this delay [microsec]
        waitForResult: <=0 : Do not wait for APDTest_10G to stop
                        > 0 : Wait this much seconds
                        
        Returns, error, warning
                        
        """
        self.readStatus(dataOnly=True)
        
        chmask = copy.deepcopy(channelMasks)
        if (len(chmask) < 4):
            for i in range(4-len(chmask)):
                chmask = [chmask, 0]
                
        if (sampleDiv != None):
            sd = round(sampleDiv)
            userData = sd.to_bytes(2,'big',signed=False)
            err = self.sendCommand(self.codes_CC.OP_PROGRAMSAMPLEDIVIDER,userData,sendImmediately=True)
            if (err != ""):
                return err,""
            self.measurePara.sampleDiv = sampleDiv
        else:
            self.measurePara.sampleDiv =  int(self.status.CC_settings[self.codes_CC.CC_REGISTER_SAMPLEDIV])
            
        if (bits != None):
            if (round(bits) == 14):
                res = 0
            elif (round(bits) == 12):
                res = 1
            elif (round(bits) == 8):    
                res = 2
            else:
                return "Invalid resolution",""
            n_adc = len(self.status.ADC_address)
            reg = [self.codes_ADC.ADC_REG_RESOLUTION]*n_adc
            l = [res]*n_adc
            err = self.writePDI(self.status.ADC_address,reg,l,numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc)
            if (err != ""):
                return err,""
            self.measurePara.bits = bits
        else:
            n_adc = len(self.status.ADC_address)
            reg = [self.codes_ADC.ADC_REG_RESOLUTION]*n_adc
            err,data = self.readPDI(self.status.ADC_address,reg,[1]*n_adc,arrayData=[False]*n_adc)
            if (err != ""):
                return err,""
            if (n_adc != 1):
                for i in range(n_adc):
                    if (data[0] != data[i]):
                        return "ADC blocks have different resolution setting.",""
            if (data[0] == 0):
                self.measurePara.bits = 14
            elif (data[0] == 1):
                self.measurePara.bits = 12
            elif (data[0] == 2):
                self.measurePara.bits = 8
            else:
               return "Invalid bit resolution setting in ADCs." ,""
                
        err = self.setTrigger(externalTriggerPolarity=externalTriggerPolarity,
                              internalTrigger=internalTrigger,triggerDelay=triggerDelay
                              )
        if (err != ""):
            return err,""
        
        if (internalTriggerADC is not None):
            self.setInternalTriggerADC(enable=internalTriggerADC)
    
        err = self.syncADC()
        if (err != ""):
            return err,""
        
        cmdfile_name = "apd_python_meas.cmd"
        cmdfile = datapath+'/'+cmdfile_name
        try:
            f = open(cmdfile,"wt")
        except:
            return "Error opening file "+cmdfile,""
        
        ip = self.getIP()
        interface = self.interface.decode('ascii')
        chnum = 0
        for i in range(n_adc):
            chnum += bin(chmask[i]).count("1")
            
        numberOfSamples_plus = numberOfSamples + 10000    
        buflen = numberOfSamples_plus * chnum * 2
        min_buflen = 2e8
        if (buflen > min_buflen):
            buflen = round(min_buflen/float(buflen)*100)
        else:
            buflen = 100    
        
        
        try:
            f.write("Open "+ip+"\n")
            f.write("Stop\n")
            f.write("Stream-Interface "+interface+"\n")
            s = "Allocate "+str(round(numberOfSamples_plus))+" "+str(bits)+" " 
            for i in range(4):
                s = s+"0x{:X} ".format(chmask[i])
            s = s+"{:d}".format(buflen)
            f.write(s+"\n")
            f.write("Arm 0 "+str(round(numberOfSamples_plus))+" 0 1\n")
            f.write("Start\n")
            f.write("Wait 10000000\n")
            f.write("Save\n")
            # This clears the sample counter
            f.write("CCCONTROL 276 6 0 0 0 0 0 0\n")
            f.close()
        except :
 #           print("Error: "+se.args[1])
            return "Error writing command file " + cmdfile,""
            f.close()
    
        self.measurePara.numberOfSamples = numberOfSamples
        self.measurePara.channelMasks = copy.deepcopy(chmask)
        self.measurePara.externalTriggerPolarity = externalTriggerPolarity
        self.measurePara.internalTrigger = internalTrigger
        self.measurePara.triggerDelay = triggerDelay
        
        time.sleep(1)
        thisdir = os.path.dirname(os.path.realpath(__file__))
        apdtest_prog = 'APDTest_10G'
        apdtest = os.path.join(thisdir,'APDTest_10G','APDTest_10G')
        cmd = "killall -KILL "+apdtest_prog+" 2> /dev/null ; cd "+datapath+" ; rm Channel*.dat 2> /dev/null ; "+apdtest+" "+cmdfile_name+" >APDTest_10G.out 2>&1 &"
        d = subprocess.run([cmd],check=False,shell=True)
        sleeptime = 0.1
        maxcount = int(10/sleeptime)+1
        err = ""
        started = False
        for i in range(maxcount):
            try:
                f = open(datapath+"/"+"APDTest_10G.out","rt")
            except:
                time.sleep(sleeptime)
                continue
            all_txt = f.readlines()
            f.close()
            for il in range(len(all_txt)):
               if (all_txt[il].lower().find("error") >= 0):
                  err = "Error starting measurement: "+all_txt[il]
                  return err,""
               if (all_txt[il].lower().find("start succes") >= 0):
                  started = True
                  break
            if (started):
                break
            time.sleep(sleeptime)

        if (not started):
            return "APDCAM did not start",""
        
        if (waitForResult <=0):
            return "",""
        
        err,warning = self.waitForMeasurement(waitForResult)
        return err,warning
   
    def measurementStatus(self,datapath="data"):
        """ Check whether the APDTest_10G program is still running.
            Returns error,status,warning
            status is "Finished" or "Running"
        """
        
        err = ""
        warning = ""
        cmd =  "ps ax |grep APDTest_10G | grep -v grep"
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
        if (len(d.stdout) == 0):
            # APDTest_10G is not running
            run_stat = "Finished"
        else:
            run_stat = "Running"
        # Reading the output
        try:
            f = open(datapath+"/"+"APDTest_10G.out","rt")
        except:
            err = "Measurement did not start."
            return err,run_stat,warning
        
        all_txt = f.readlines()
        f.close()
        for il in range(len(all_txt)):
            if (all_txt[il].lower().find("error") >= 0):
                err = "Error during measurement: "+all_txt[il]
                return err,run_stat,warning
            if (all_txt[il].lower().find("warning") >= 0):
                warning = all_txt[il]
        return err,run_stat,warning

        
    def waitForMeasurement(self,timeout):
        """ Waits for the measurement end
            timeout is in second
            returns error,warning
        """
        sleeptime = 0.1
        maxcount = int(timeout/sleeptime)+1
        for i in range(maxcount):
            err,status,warning = self.measurementStatus()
            if (status == "Finished"):
                return err,warning
            time.sleep(sleeptime)
        return "Timeout",""
            
    def abortMeasurement(self):
        cmd = "killall APDTest_10G"
        d = subprocess.run([cmd],check=False,shell=True)

        
    def writeConfigFile(self,datapath="data"):
        """ Reads the configuration from the camera and
        writes an XML configuraition file.
        Call this routine only after a succesful measure() !!!
        """
        
        self.readStatus(dataOnly=True)
        fn = datapath+"/APDCAM_config.xml"
        m = apdcamXml(fn)
        m.createHead("APDCAM-10G")
       
        m.addElement(section="ADCSettings",element="ADCMult", \
                     value= int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_MULT]),\
                     value_type='int')
        m.addElement(section="ADCSettings",element="ADCDiv", \
                     value= int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_DIV_ADC]),\
                     value_type='int')
        m.addElement(section="ADCSettings",element="Samplediv", \
                     value= self.measurePara.sampleDiv,\
                     value_type='int')
        m.addElement(section="ADCSettings",element="SampleNumber", \
                     value= self.measurePara.numberOfSamples,\
                     value_type='long')
        for i in range(4):
            m.addElement(section="ADCSettings",element="ChannelMask"+str(i+1), \
                     value= "{:X}".format(self.measurePara.channelMasks[i]),\
                     value_type='long',\
                     comment="The channel mask for ADC block "+str(i+1)+"(hex). Each bit is one channel.")
        m.addElement(section="ADCSettings",element="Bits", \
                     value= self.measurePara.bits,\
                     value_type='long',\
                     comment="The bit resolution of the ADC")
        if (self.measurePara.externalTriggerPolarity == None):
            trig = -1
        else:
            trig = float(self.measurePara.triggerDelay)/1e6

        m.addElement(section="ADCSettings",element="Trigger", \
                     value= float(trig),\
                     unit = 's',\
                     value_type='float',
                     comment="Trigger: <0: manual,otherwise external or internal with this delay")
        if (self.measurePara.internalTrigger):
            inttrig = 1
        else:
            inttrig = 0
        m.addElement(section="ADCSettings",element="InernalTrigger",
             value= inttrig,
             unit = '',
             value_type = 'int',
             comment="Internal trigger: 0: Disabled, 1: Enabled"
             )
        try:
            m.writeFile()
        except: return "Error writing file "+fn
        
        return ""

    def writeStreamData(self):
        
        self.readCCdata(dataType=0)
        for i in range(1):
            d_octet = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i+2]
            octet = int.from_bytes(d_octet,'big',signed=False)
            d_ip = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i:APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i+4]
            d_port = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i+2]
            port = int.from_bytes(d_port,'big',signed=False)
            print("Stream {:d}...octet:{:d}... IP:{:d}.{:d}.{:d}.{:d}...port:{:d}".format(i+1,octet,\
                  int(d_ip[0]),int(d_ip[1]),int(d_ip[2]),int(d_ip[3]),port))
      
            data = bytearray(9)
            data[0] = 3
            data[1:3] = d_octet
            data[3:7] = bytes([239,123,13,100])
            p = 10003
            data[7:9] = p.to_bytes(2,'big')
            err = self.sendCommand(APDCAM10G_codes_v1.OP_SETMULTICASTUDPSTREAM,data,sendImmediately=True)
            print(err)
            
            data = bytearray(15)
            data[0] = 3
            data[1:3] = d_octet
            data[3:9] = bytes([0x90,0xe2,0xba,0xe3,0xa4,0x62])
            data[9:13] = bytes([239,123,13,100])
            p = 10003
            data[13:15] = p.to_bytes(2,'big')
            err = self.sendCommand(APDCAM10G_codes_v1.OP_SETUDPSTREAM,data,sendImmediately=True)
            print(err)
 
        self.readCCdata(dataType=0)                       
        for i in range(4):
            d_octet = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i+2]
            octet = int.from_bytes(d_octet,'big',signed=False)
            d_ip = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i:APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i+4]
            d_port = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i+2]
            port = int.from_bytes(d_port,'big',signed=False)
            print("Stream {:d}...octet:{:d}... IP:{:d}.{:d}.{:d}.{:d}...port:{:d}".format(i+1,octet,\
                  int(d_ip[0]),int(d_ip[1]),int(d_ip[2]),int(d_ip[3]),port))
   
    def resetStream3(self):
        # This is a workaround for a problem of the APDTest program. For a 64 channel APDCAM10G
        # APDTest sets up streams 1 and 2 for measurement. However, in a dual-SATA camera configuration
        # streams 1 and 3 are used. During testing this worked accidentally as the factory setting of stream 3
        # is identical to the setting of stream 2 by APDTest. If the setting of stream 3 is changed by whatever reason
        # it has to be set back to the factory values either by resetting the camera (physically pressing the button) or 
        # by running this function.
        
        # This contains the MAC address of a certain computer!!!!!!
        code = self.codes_CC
            
        d = bytearray(9)
        d[0] = 3
        octet = 1118
        port = 10003
        d[1:3] = octet.to_bytes(2,'big',signed=False)
        d[3:7] = bytearray([239,123,13,100])
        d[7:9] = port.to_bytes(2,'big',signed=False)
        err = self.sendCommand(code.OP_SETMULTICASTUDPSTREAM,d,sendImmediately=True)
        
        d = bytearray(15)
        d[0] = 3
        octet = 1118
        port = 10003
        d[1:3] = octet.to_bytes(2,'big',signed=False)
        d[3:9] =[0x90, 0xe2, 0xba, 0xe3, 0xa4, 0x62]
        d[9:13] = bytearray([239,123,13,100])
        d[13:15] = port.to_bytes(2,'big',signed=False)
        err = self.sendCommand(code.OP_SETUDPSTREAM,d,sendImmediately=True)
        
 # end of class APDCAM10G_regComm

class APDCAM10G_data:
    """ This class is for measuring APDCAM-10G data.
        Created and instance and keep and call the startReceiveAnswer() method
        before reading/writing registers, this starts the UDP packet read.
        When the instance is deleted the UDP read is stopped and registers
        cannot be read/written any more.
    """ 
    RECEIVE_PORTS = [10000, 10001, 10002, 10003] # these are the receiving ports
    MULTICAST_ADDRESS = "239.123.13.100"
    DEF_MTU = 9000
    IPV4_HEADER = 20
    UDP_HEADER = 8
    CC_STREAMHEADER = 22
    MULTICAST = False
                
    def __init__(self):
        """"
            INPUT:
                APDCAM: APDCAM10G_regCom classs for accessing camera registers
        """        
        self.APDCAM_IP = b"10.123.13.102"
        self.receiveSockets = [None, None, None, None]
        self.MTU = APDCAM10G_data.DEF_MTU
        maxAdcDataLength = self.MTU-\
                             (APDCAM10G_data.IPV4_HEADER+APDCAM10G_data.UDP_HEADER\
                              +APDCAM10G_data.CC_STREAMHEADER)
        self.octet = maxAdcDataLength//8
        self.streamTimeout = 10000 # ms
        
    def __del__(self):
        for i in range(4) :
            if self.receiveSockets[i] != None :
                self.receiveSockets[i].close()
            
    def setIP(self,IP):
        self.APDCAM_IP = IP
        
    def getIP(self):
        return self.APDCAM_IP
    
    def setOctet(self,MTU):
        self.MTU = MTU
        maxAdcDataLength = MTU-\
                            (APDCAM10G_data.IPV4_HEADER+APDCAM10G_data.UDP_HEADER\
                              +APDCAM10G_data.CC_STREAMHEADER)
        self.octet = maxAdcDataLength//8
        

    def stopReceive(self,APDCAM):
        """Stops streams and closes all the stream receive sockets
            INPUT:
                streamList: List 4 boolean values for enabling streams
            Returns "" or error message
        """

        # Delete sockets
        for i in range(4) :
            if (self.receiveSockets[i] != None):
               self.receiveSockets[i].close()
               self.receiveSockets[i] = None
               
        
    def startReceive(self,APDCAM,streamList):
        """Starts the stream receive
            INPUT:
                streamList: List 4 boolean values for enabling streams
            Returns "" or error message
        """
        import socket
        import struct
        import sys
        
        APDCAM10G_data.stopReceive(self,APDCAM)
        
        for i in range(4) :
            if (streamList[i] == True) :
                try:
                    self.receiveSockets[i] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                except socket.error as se:
                    return se.args[1]
                try:
                    self.receiveSockets[i].bind(('', APDCAM10G_data.RECEIVE_PORTS[i]))
                except socket.error as se :
                    return se.args[1]
                if APDCAM10G_data.MULTICAST :
                    d = socket.inet_aton(APDCAM10G_data.MULTICAST_ADDRESS)
                    mreq = struct.pack('4sL', d, socket.INADDR_ANY)
                    self.receiveSockets[i].setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                self.receiveSockets[i].setblocking(1)  # non blocking receive
                self.receiveSockets[i].settimeout(self.streamTimeout/1000.)
     
    def startStream(self,APDCAM,streamList) :
        import socket
        
        APDCAM10G_data.stopStream(self,APDCAM)
        
        strcontrol = bytearray([0])        
        for i in range(4) :
            if (streamList[i] == True) :
                strcontrol[0] = strcontrol[0] | 2**i
                print("Stream %d Octet: %d" % (i,self.octet))
                if (APDCAM10G_data.MULTICAST) :
                    UDP_data = bytearray(9)
                    UDP_data[0] = i+1
                    UDP_data[1] = self.octet // 256
                    UDP_data[2] = self.octet % 256
                    d = socket.inet_aton(APDCAM10G_data.MULTICAST_ADDRESS)
                    UDP_data[3] = d[0]
                    UDP_data[4] = d[1]
                    UDP_data[5] = d[2]
                    UDP_data[6] = d[3]
                    UDP_data[7] = APDCAM10G_data.RECEIVE_PORTS[i] // 256
                    UDP_data[8] = APDCAM10G_data.RECEIVE_PORTS[i] % 256
                    err = APDCAM.sendCommand(APDCAM10G_codes_v1.OP_SETMULTICASTUDPSTREAM,UDP_data,sendImmediately=True)
                else :    
                    UDP_data = bytearray(15)
                    UDP_data[0] = i+1
                    UDP_data[1] = self.octet // 256
                    UDP_data[2] = self.octet % 256
                    # mac = bytearray([0x90, 0xE2, 0xBA, 0xC3, 0x76, 0xA0]) # Helium
                    mac = bytearray([0x90, 0xE2, 0xBA, 0xE3, 0xA4, 0x62])  # W7-X
                    UDP_data[3] = mac[0]
                    UDP_data[4] = mac[1]
                    UDP_data[5] = mac[2]
                    UDP_data[6] = mac[3]
                    UDP_data[7] = mac[4]
                    UDP_data[8] = mac[5]
                    d = socket.inet_aton("10.123.13.202")
                    UDP_data[9] = d[0]
                    UDP_data[10] = d[1]
                    UDP_data[11] = d[2]
                    UDP_data[12] = d[3]
                    UDP_data[13] = APDCAM10G_data.RECEIVE_PORTS[i] // 256
                    UDP_data[14] = APDCAM10G_data.RECEIVE_PORTS[i] % 256
                    err = APDCAM.sendCommand(APDCAM10G_codes_v1.OP_SETUDPSTREAM,UDP_data,sendImmediately=True)
                
        # Start streams
        #print("TEST UDP!!!")
        #err = APDCAM.sendCommand(APDCAM10G_codes_v2.OP_SETUDPTESTCLOCKDIVIDER,bytes([1,0,0,0]),sendImmediately=True)
        #strcontrol[0] = strcontrol[0] | 0xF0
        err = APDCAM.sendCommand(APDCAM10G_codes_v1.OP_SETSTREAMCONTROL,strcontrol,sendImmediately=True)
        if (err != "") :
            return err
        return ""
    
    def stopStream(self,APDCAM):
        # Stop streams
        APDCAM.sendCommand(APDCAM10G_codes_v1.OP_SETSTREAMCONTROL,bytes([0]),sendImmediately=True)

    def getData(self,streamNo):
        """
        streamNo: 0...3
        """
        import socket
        
        if (self.receiveSockets[streamNo] == None):
            return "Stream is not open.", None
        try:
            data = self.receiveSockets[streamNo].recv(9000)
        except socket.timeout as st:
            return "Timeout receiving data", None
        except socket.error as se :
            return se.argv[1], None
        return "", data        
        
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
