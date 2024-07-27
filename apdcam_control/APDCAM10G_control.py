# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 19:34:00 2018

APDCAM-10G register access functions

@authors: Sandor Zoletnik, Centre for Energy Research  
          zoletnik.sandor@ek-cer.hu
          Daniel Barna, Wigner Resesarch Centre for Physics
          daniel.barna@fusioninstruments.com
"""


"""
TODO:
- add a function for SETCLOCKENABLE
- data parser for v1.05 (new CC header format!)

"""

import traceback
import re
import threading
import time
import copy
import subprocess
import xml.etree.ElementTree as ET
import socket
import os
import numpy as np
from datetime import date
#import struct
import sys
import platform

# Sorry, probably worst practice, could not get it working without explicitely
# specifying the directory for the APDCAM10G_registers script
dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir)
from APDCAM10G_registers import *

def showtrace():
    for line in traceback.format_stack():
        print(line.strip())
    

def DAC2ADC_channel_mapping():
    """
    Returns an array, which maps the ADC channel numbers (1...32) to the 32 DAC channel numbers (-1).
    Note that both ADC and DAC channel numbers are 1-based, therefore in order to obtain the
    ADC channel number for a DAC channel:
    ch_adc = DAC_ADC_channel_mapping()[ch_dac-1]
    """
    return [30, 32, 31, 1, 2, 3 ,14 ,4 , 16, 13, 21, 19, 17, 20, 15, 18, 22, 24, 23, 9, 10, 11, 12, 6, 8, 5, 29, 25, 27, 28, 7, 26]

def ADC2DAC_channel_mapping():
    """
    Returns an array, which maps the DAC channel numbers (1...32) to the 32 ADC channel numbers (-1)
    That is, ch_dac = ADC_DAC_channel_mapping()[ch_adc-1], where both channel numbers are 1-based
    """
    data1 = DAC2ADC_channel_mapping()
    data2 = [0]*32
    for i in range(32):
        data2[data1[i]-1] = i+1
    return data2

class APDCAM10G_codes_v1:
    """
    Instruction codes and other defines for V1 of the 10G communication card
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
    OP_PROGRAMBASICPLL=0x0100  # The internal ADC clock's associated PLL 
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

    # DIT (Device Identification Table) - acquired from the camera starting from byte #7
    # The documentation lists by byte number, hence a -7 offset for the DIT registers
    CC_REGISTER_BOARDTYPE = 7-7
    CC_DATATYPE_BOARDTYPE = 0
    CC_REGISTER_FIRMWARE = 17-7
    CC_DATATYPE_FIRMWARE = 0
    CC_REGISTER_FIRMWAREGROUPVERSION = 31-7
    CC_DATATYPE_FIRMWAREGROUPVERSION = 0
    CC_REGISTER_UPGRADEDATE = 33-7
    CC_DATATYPE_UPGRADEDATE = 0
    CC_REGISTER_MAN_FIRMWAREGROUP = 37-7
    CC_DATATYPE_MAN_FIRMWAREGROUP = 0
    CC_REGISTER_MAN_PROGRAMDATE = 51-7
    CC_DATATYPE_MAN_PROGRAMDATE = 0
    CC_REGISTER_MAN_SERIAL = 55-7
    CC_DATATYPE_MAN_SERIAL = 0
    CC_REGISTER_MAN_TESTRESULT = 59-7
    CC_DATATYPE_MAN_TESTRESULT = 0
    # SETTINGS - the documentation lists from byte #7, + we need to skip the 71-7 bytes of the DIT
    # hence the offset -7+71-7
    CC_REGISTER_DEV_NAME = 8-7+71-7
    CC_DATATYPE_DEV_NAME = 0
    CC_REGISTER_DEV_SERIAL = 58-7+71-7
    CC_DATATYPE_DEV_SERIAL = 0
    CC_REGISTER_CLOCK_CONTROL = 263-7+71-7
    CC_DATATYPE_CLOCK_CONTROL = 0
    CC_REGISTER_CLOCK_ENABLE = 264-7+71-7
    CC_DATATYPE_CLOCK_ENABLE = 0
    CC_REGISTER_BASE_PLL_MULT = 265-7+71-7
    CC_DATATYPE_BASE_PLL_MULT = 0
    CC_REGISTER_BASE_PLL_DIV_ADC = 267-7+71-7  # This goes to clock signal F1 (to ADC)
    CC_DATATYPE_BASE_PLL_DIV_ADC = 0
    CC_REGISTER_EXT_DCM_MULT = 270-7+71-7
    CC_DATATYPE_EXT_DCM_MULT = 0
    CC_REGISTER_EXT_DCM_DIV = 271-7+71-7
    CC_DATATYPE_EXT_DCM_DIV = 0
    CC_REGISTER_SAMPLEDIV = 272-7+71-7
    CC_DATATYPE_SAMPLEDIV = 0
    CC_REGISTER_SAMPLECOUNT = 276-7+71-7
    CC_DATATYPE_SAMPLECOUNT = 0
    CC_REGISTER_TRIGSTATE = 282-7+71-7
    CC_DATATYPE_TRIGSTATE = 0
    CC_REGISTER_TRIGDELAY = 283-7+71-7
    CC_DATATYPE_TRIGDELAY = 0    
    CC_REGISTER_SERIAL_PLL_MULT = 287-7+71-7
    CC_DATATYPE_SERIAL_PLL_MULT = 0
    CC_REGISTER_SERIAL_PLL_DIV = 288-7+71-7
    CC_DATATYPE_SERIAL_PLL_DIV = 0
    CC_REGISTER_SATACONTROL = 292-7+71-7
    CC_DATATYPE_SATACONTROL = 0
    CC_REGISTER_UDPOCTET1 = 311-7+71-7
    CC_DATATYPE_UDPOCTET1 = 0
    CC_REGISTER_UDPMAC1 = 313-7+71-7
    CC_DATATYPE_UDPMAC1 = 0
    CC_REGISTER_IP1 = 320-7+71-7  # shouldn't this be 319-7+71-7? BS_10GBCCCard_v104_IM_noflashwrite.pdf page 69
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

    CC_REGISTER_18VXC = 283-7
    CC_DATATYPE_18VXC = 1
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
    """
    Instruction codes and other defines for V2 (Firmware 105 and up) of the 10G communication card
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

    # These addresses are valid for DIT+Settings block 
    # The address is calculated from the Settings table as <byte address>-7+71
    # DATATYPE inndicates which block the variable is in (0: settings, 1: variables)

    # DIT (Device Identification Table) - acquired from the camera starting from byte #7
    # The documentation lists by byte number, hence a -7 offset for the DIT registers
    CC_REGISTER_BOARDTYPE = 7-7
    CC_DATATYPE_BOARDTYPE = 0
    CC_REGISTER_FIRMWARE = 17-7
    CC_DATATYPE_FIRMWARE = 0
    CC_REGISTER_FIRMWAREGROUPVERSION = 31-7
    CC_DATATYPE_FIRMWAREGROUPVERSION = 0
    CC_REGISTER_UPGRADEDATE = 33-7
    CC_DATATYPE_UPGRADEDATE = 0
    CC_REGISTER_MAN_FIRMWAREGROUP = 37-7
    CC_DATATYPE_MAN_FIRMWAREGROUP = 0
    CC_REGISTER_MAN_PROGRAMDATE = 51-7
    CC_DATATYPE_MAN_PROGRAMDATE = 0
    CC_REGISTER_MAN_SERIAL = 55-7
    CC_DATATYPE_MAN_SERIAL = 0
    CC_REGISTER_MAN_TESTRESULT = 59-7
    CC_DATATYPE_MAN_TESTRESULT = 0
    # SETTINGS - the documentation lists from byte #7, + we need to skip the 71-7 bytes of the DIT
    # hence the offset -7+71-7
    CC_REGISTER_DEV_NAME = 8-7+71-7
    CC_DATATYPE_DEV_NAME = 0
    CC_REGISTER_DEV_SERIAL = 58-7+71-7
    CC_DATATYPE_DEV_SERIAL = 0
    CC_REGISTER_CLOCK_CONTROL = 263-7+71-7
    CC_DATATYPE_CLOCK_CONTROL = 0
    CC_REGISTER_CLOCK_ENABLE = 264-7+71-7
    CC_DATATYPE_CLOCK_ENABLE = 0
    CC_REGISTER_BASE_PLL_MULT = 265-7+71-7
    CC_DATATYPE_BASE_PLL_MULT = 0
    CC_REGISTER_BASE_PLL_DIV_ADC = 267-7+71-7  # This goes to clock signal F1 (to ADC)
    CC_DATATYPE_BASE_PLL_DIV_ADC = 0
    CC_REGISTER_EXT_DCM_MULT = 270-7+71-7
    CC_DATATYPE_EXT_DCM_MULT = 0
    CC_REGISTER_EXT_DCM_DIV = 271-7+71-7
    CC_DATATYPE_EXT_DCM_DIV = 0
    CC_REGISTER_SAMPLEDIV = 272-7+71-7
    CC_DATATYPE_SAMPLEDIV = 0
    CC_REGISTER_SAMPLECOUNT = 276-7+71-7
    CC_DATATYPE_SAMPLECOUNT = 0
# New in Firmware 1.05
    CC_REGISTER_EIO_ADC_DIV = 282-7+71-7
    CC_DATATYPE_EIO_ADC_DIV = 0
# Firmware before 1.05
#    CC_REGISTER_TRIGSTATE = 282-7+71-7
#    CC_DATATYPE_TRIGSTATE = 0
    CC_REGISTER_TRIGDELAY = 283-7+71-7
    CC_DATATYPE_TRIGDELAY = 0    
    CC_REGISTER_SERIAL_PLL_MULT = 287-7+71-7
    CC_DATATYPE_SERIAL_PLL_MULT = 0
    CC_REGISTER_SERIAL_PLL_DIV = 288-7+71-7
    CC_DATATYPE_SERIAL_PLL_DIV = 0
    CC_REGISTER_SATACONTROL = 292-7+71-7
    CC_DATATYPE_SATACONTROL = 0
# new in Firmware 1.05
    CC_REGISTER_G1TRIGCONTROL = 293-7+71-7
    CC_DATATYPE_G1TRIGCONTROL = 0
    CC_REGISTER_G2GATECONTROL = 294-7+71-7
    CC_DATATYPE_G2GATECONTROL = 0

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

    CC_REGISTER_18VXC = 283-7
    CC_DATATYPE_18VXC = 1
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
    
    
    
    
class APDCAM10G_ADCcodes_v1 :  
    """
    Register addresses and other defines for the 10G ADC board V1
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
    """
    Register addresses and other defines for the APDCAM control board
    """
    PC_CARD = 2
    PC_REG_BOARD_SERIAL = 0x0100
    PC_REG_FW_VERSION = 0x0002
    PC_REG_HV1SET = 0x56
    PC_REG_HV2SET = 0x58
    PC_REG_HV3SET = 0x5A
    PC_REG_HV4SET = 0x5C
    PC_REG_HV1MON = 0x04
    PC_REG_HV2MON = 0x06
    PC_REG_HV3MON = 0x08 # Added by D. Barna
    PC_REG_HV4MON = 0x0A # Added by D. Barna
    PC_REG_HV1MAX = 0x102
    PC_REG_HV2MAX = 0x104
    PC_REG_HV3MAX = 0x106
    PC_REG_HV4MAX = 0x108
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
    """
    Settings of one timer in CAMTIMER
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
    """
    This contains the APDCAM CAMTIMER settings and methods.
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
        self.externalTriggerPos=None
        self.externalTriggerNeg=None
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
    """
    This class stores data read from APDCAM10G
    """
    def __init__(self):
        self.CC_firmware = ""
        self.CC_serial = ""
        # List of ADC addresses
        self.ADC_address = [] 
        self.ADC_serial = []
        self.ADC_FPGA_version = []
        self.ADC_MC_version = []
        self.ADC_registers = []
        self.PC_serial = None
        self.PC_FW_version = None
        self.PC_registers = []
        self.HV_set = [0,0,0,0]
        self.HV_act = [0,0,0,0]
        self.temps = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]      
        self.ref_temp = 0.0
        self.extclock_valid = False
        self.extclock_freq = 0.0  # kHz
        self.CC_settings = None
        self.CC_variables = None

class Terminal:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def showMessage(self,s):
        print(s)
    def showWarning(self,s):
        print(self.WARNING + s + self.ENDC)
    def showError(self,s):
        print(self.FAIL + s + self.ENDC)
        
class APDCAM10G_control:
    """
    This class is for reading/writing APDCAM-10G registers and sending commands
    Create an instance and call the connect() method
    before reading/writing registers, this starts the UDP packet read.
    When the instance is deleted the UDP read is stopped and registers
    cannot be read/written any more.
    For receiving measurement data create an APDCAM10G.data instance.
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
        self.version = None;  # code for firmware type 0: before 105, 1: from 105
#        self.HV_conversion_out = [0.12, 0.12, 0.12, 0.12] # V/digit   # Removed by D. Barna
#        self.HV_conversion_in  = [0.12, 0.12, 0.12, 0.12] # V/digit   # Removed by D. Barna
        self.HV_conversion  = [0.12, 0.12, 0.12, 0.12] # V/digit       # Added by D. Barna
        self.lock = threading.RLock()
        self.repeatNumber=5 # Number of times a read/write operation is repeated before an error is indicated
        self.CAMTIMER = APDCAM_timer()
        self.interface = None
        self.log = lambda msg: print(msg)
        self.errorHandler = None

    def setErrorHandler(self,func):
        self.errorHandler = func
        
    def connect(self,ip="10.123.13.102"):
        """
        Connect to the camera and start the answer reading socket
        Returns an error message or the empty string
        """
        if (type(ip) is str):
            _ip = bytearray(ip,encoding='ASCII')
        elif(type(ip) is bytes):
            _ip = ip
        else:
            raise ValueError("Invalid IP address for camera. Should be string or bytearray.")
        self.APDCAM_IP = ip

        err = self.startReceiveAnswer()  # Changed by D. Barna

        if (err != "") :
            self.close()
            return "Error connecting to camera: "+err
        err = self.readStatus(dataOnly=True) # Changed by D. Barna
        if (err != ""):
            self.close()
            return "Error connecting to camera: "+err

        #Extracting camera information
        d = self.status.CC_settings 

        # Note that here we use the hard-coded APDCAM10G_codes_v1.CC_REGISTER_MAN_SERIAL symbol because this function is called
        # to read the CC board settings, that is, also when reading the camera firmware version, i.e. before the
        # firmware is known and self.codes_CC is set to the correct object based on camera firmware version.
        # So we must rely on CC_REGISTER_MAN_SERIAL not changing between firmware versions
        # The same holds at some other places within this function
        self.status.CC_serial = int.from_bytes(d[APDCAM10G_codes_v1.CC_REGISTER_MAN_SERIAL:APDCAM10G_codes_v1.CC_REGISTER_MAN_SERIAL+4],byteorder='little',signed=False)
        #self.status.CC_serial = int.from_bytes(d[self.codes_CC.CC_REGISTER_MAN_SERIAL:self.codes_CC.CC_REGISTER_MAN_SERIAL+4],byteorder='little',signed=False)
        self.status.CC_firmware = d[APDCAM10G_codes_v1.CC_REGISTER_FIRMWARE:APDCAM10G_codes_v1.CC_REGISTER_FIRMWARE+14]
        #self.status.CC_firmware = d[self.codes_CC.CC_REGISTER_FIRMWARE:self.codes_CC.CC_REGISTER_FIRMWARE+14]
        self.log("Manufacturer serial number: " + str(self.status.CC_serial))
        self.log("Firmware: " + str(self.status.CC_firmware))
        if (self.status.CC_firmware[0:11] != b"BSF12-0001-"):
            err = "Unknown camera firmware."
            self.close()
            return err
        self.version = int(self.status.CC_firmware[11:14])

        if (self.version < 105) :
            self.codes_CC  = APDCAM10G_codes_v1()
            self.codes_ADC = APDCAM10G_ADCcodes_v1()
            self.codes_PC  = APDCAM_PCcodes_v1()
            self.builtinAdcFreqDivider = 1
            # New framework
            self.ADC_registers = APDCAM10G_adc_registers_v1()
            self.CC_settings   = APDCAM10G_cc_settings_v1()
            self.CC_variables  = APDCAM10G_cc_variables_v1()
            self.PC_registers  = APDCAM10G_pc_registers_v1()
            # store a class *type* which interprets the C&C header in the UDP packets
            self.udpPacketHeader = APDCAM10G_packet_header_v1
        else:
            self.codes_CC  = APDCAM10G_codes_v2()
            self.codes_ADC = APDCAM10G_ADCcodes_v1()
            self.codes_PC  = APDCAM_PCcodes_v1()
            self.builtinAdcFreqDivider = 2
            # New framework
            self.ADC_registers = APDCAM10G_adc_registers_v2()
            self.CC_settings   = APDCAM10G_cc_settings_v2()
            self.CC_variables  = APDCAM10G_cc_variables_v2()
            self.PC_registers  = APDCAM10G_pc_registers_v2()
            # store a class *type* which interprets the C&C header in the UDP packets
            self.udpPacketHeader = APDCAM10G_packet_header_v2

        # Check the available ADC boards
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
                self.log("Found ADC board at address: " + str(check_address_list[i]))
                self.status.ADC_address.append(check_address_list[i])
                self.status.ADC_serial.append(int.from_bytes(d[3:5],byteorder='little',signed=False))
                self.status.ADC_FPGA_version.append(str(int.from_bytes([d[5]],'little',signed=False))+\
                                        "."+str(int.from_bytes([d[6]],'little',signed=False)))
                self.status.ADC_MC_version.append(str(int.from_bytes([d[1]],'little',signed=False))+\
                                        "."+str(int.from_bytes([d[2]],'little',signed=False)))
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
        if (err != ""):
            return err
        ret, ds = self.getDualSata()
        if (ret != ""):
            return ret
        self.dualSATA = ds

        if self.version >= 105:
            self.setAdcStreamMode('all','off')

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
        """
        Starts the receiver socket

        Returns
        ^^^^^^^
        Error message or empty string
        """
        
        # Return is socket already allocated
        if self.commSocket != None:
            return ""
        try:
            self.commSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as se:
            self.commSocket = None
            return se.args[1]
        try:
            self.commSocket.bind((b'0.0.0.0', self.commPort))
        except socket.error as se :
            self.commSocket = None
            return se.args[1]
        self.commSocket.setblocking(1) 
        self.commSocket.settimeout(self.answerTimeout/1000.)  

        return ""
    
    def getAnswer(self):
        
        """
        Get an answer sent by APDCAM-10G in one UDP packet

        Returns 
        ^^^^^^^
        err
            Error string or ""
        data
            bytes of data
        """
        if (self.commSocket == None):
            return "APDCAM is not connected.",None
        try:
            data = self.commSocket.recv(self.MAX_UDP_DATA)
        except socket.timeout:
            return "",None
        except socket.error as se:
            return se.args[1],None
        return "", data
    
    
    def sendCommand(self,opCode,userData,sendImmediately=True,waitAfter=0.01):
        """
        Will create DDToIP command and add to existing UDP command package
        Will immadiately send UDP if SendImmadiately is not False
        If opCode is None then will add no data just send if sendImmediately is set True
        
        Parameters
        ^^^^^^^^^^
        opCode: int or bytes 
            The operation code OP_... (see class APDCAM10G_codes_...)
        userData: bytearray
            The user data for the operation. Set None of no data.
        sendImmediately: bool
            If True send immediately
        WaitAfter: float
            Time to wait after sending the command [s]. The default is 0.01s.
        
        Return values
        ^^^^^^^^^^^^^^
        str
            "" If no error
            "Too much data": Too much data, cannot fit into present UDP packet
            "No data to send"
            Other error text relating to network
        """
        import socket

        #if opCode != None:
        #    print("sendCommand: " + hex(opCode) + ", " + str(len(userData)) + ", " + str([hex(userData[i]) for i in range(len(userData))]))
        #else:
        #    print("sendCommand: None")

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
                UDP_command_block += bytes(2) # Shouldn't it be initialized to zero? Or is it automatically done?
            self.UDP_data += UDP_command_block
        if sendImmediately == False :
            self.lock.release()
            return ""
        if self.UDP_data == None :  # this will never occur... (!)
            self.lock.release()
            return "No data to send"        
        try:
            ndat = self.commSocket.sendto(self.UDP_data, (self.APDCAM_IP, self.APDCAM_PORT))
        except socket.error as se:
            self.lock.release()
            return se.args[1]
        if (ndat != len(self.UDP_data)) :
            self.UDP_data = None
            self.lock.release()
            return "Could not send all data."
        self.UDP_data = None
        if (waitAfter is not None):
            time.sleep(waitAfter)
        self.lock.release()
        return ""
 
    def readCCdata(self,dataType=0):
        """
        Reads the Settings or the Variables data block from the 10G (CC) card. 
        Stores the result in self.status.CC_settings or self.status.CC_variables.

        Parameters
        ^^^^^^^^^^
        dataType:
            0: Settings
            1: Variables
                  
        Returns
        ^^^^^^^
        Error message or empty string
        """
        
        if (dataType == 0) :
            dataCode = 2 # DIT & Settings
        else :
            dataCode = 3 #Variables
        userData =bytes([0,dataCode])
        self.lock.acquire()
        for rep in range(self.repeatNumber) :
            # Note that here we use the hard-coded APDCAM10G_codes_v1.OP_SENDACK symbol because this function is called
            # to read the CC board settings, that is, also when reading the camera firmware version, i.e. before the
            # firmware is known and self.codes_CC is set to the correct object based on camera firmware version.
            # So we must rely on OP_SENDACK not changing between firmware versions
            # The same holds at some other places within this function
            err = self.sendCommand(APDCAM10G_codes_v1.OP_SENDACK,userData,sendImmediately=True)
            #err = self.sendCommand(self.codes_CC.OP_SENDACK,userData,sendImmediately=True)
            if (err != ""):
                time.sleep(0.001)
                print("repeat readCCdata/1 {:d}".format(rep))
                continue
            err1, d = self.getAnswer()
            if (err != "" or d == None):
                time.sleep(0.1)
                self.clearAnswerQueue()
                #print("Error radCCdata/2:"+err)
                #print("repeat readCCdata/2 {:d}".format(rep))
                continue
            d = d[22:len(d)]
            resp_command = int.from_bytes(d[0:2],'big',signed=False)
            if (resp_command != APDCAM10G_codes_v1.AN_ACK) :
            #if (resp_command != self.codes_CC.AN_ACK) :
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

    def setEioAdcClockDivider(self,value):
        """
        Set the divider value for the ADC clock output at the EIO connector

        Parameters:
        ^^^^^^^^^^^
        value - even integer between 2-254. If it is not even, it is rounded down

        Returns:
        ^^^^^^^^
        error - error message, or empty string

        """
        if not hasattr(self.codes_CC,"OP_SETEIOCLKDIV"):
            return "This camera version can not set the ADC clock output divider"

        if value > 255:
            value = 255
        if value < 1:
            value = 1
        if value%2 != 0 and value != 1:
            value -= 1
        data = bytes([value])
        return self.sendCommand(self.codes_CC.OP_SETEIOCLKDIV,data,sendImmediately=True)

        
    def readAdcRegisters(self):
        """
        Read the entire register table of all ADC boards into self.status.ADC_registers
        self.status.ADC_registers will be a list with the same number of elements as there are ADC boards,
        and each list element is a bytearray mirroring the content of the registers of the given
        ADC board
        Returns an error message or the empty string if no error occurred. 
        """
        self.status.ADC_registers = [None]*len(self.status.ADC_address)
        for i in range(len(self.status.ADC_address)):
            err,regs = self.readPDI(self.status.ADC_address[i], 0, 0x0100+256, arrayData=True)
            if err != "":
                return err
            self.status.ADC_registers[i] = regs[0]
        return ""

    def readPcRegisters(self):
        """
        Read the entire register table of all PC board into self.status.PC_registers
        Returns an error message or the empty string if no error occurred. 
        """
        err,regs = self.readPDI(self.codes_PC.PC_CARD, 0, 264, arrayData=True)
        if err != "":
            return err
        self.status.PC_registers = regs[0]
        return ""

    
    def readStatus(self,dataOnly=False,HV_repeat=1):
        """
        Reads the status of APDCAM (Settings and Variables tables of the 10G communication card,
        some Control card (PC) data, and the register table of teh ADC cards.
        These data are stored in the 'status' property, which is an APDCAM10G_status class.

        Parameters
        ^^^^^^^^^^
        HV_repeat: integer
            If larger than 1, the HV monitors will be read this many times for averaging
        
        Returns
        ^^^^^^^
        Error message or empty string
        """

        self.lock.acquire()

        # Read DIT and Settings from the 10G card
        err = self.readCCdata(dataType=0)
        if (err != ""):
            self.lock.release()
            return err
        
         # Read variables data from the 10G card
        err = self.readCCdata(dataType=1)
        if (err != ""):
            self.lock.release()
            return err

        if dataOnly:
            self.lock.release()
            return ""


        # Make some post-processing of the CC card's variables, calculate derived values directly into self.status
        # such as temperatures, frequencies, pll lock status, etc. 
        self.status.extclock_valid = self.status.CC_variables[self.codes_CC.CC_REGISTER_PLLSTAT] & 2**3 != 0
        freq = self.status.CC_variables[self.codes_CC.CC_REGISTER_EXTCLKFREQ:self.codes_CC.CC_REGISTER_EXTCLKFREQ+2]       
        self.status.extclock_freq = int.from_bytes(freq,'big',signed=False)
        self.status.CCTemp = int(self.status.CC_variables[self.codes_CC.CC_REGISTER_BOARDTEMP])

        # Reading some dedicated data from the control card to get high voltage values, temperatures. 
        c = self.codes_PC.PC_CARD
        cards = [c,c,c,c]
        regs = [self.codes_PC.PC_REG_HV1SET,\
                self.codes_PC.PC_REG_HV1MON,\
                self.codes_PC.PC_REG_TEMP_SENSOR_1,\
                self.codes_PC.PC_REG_DETECTOR_TEMP_SET]
                
        err, data = self.readPDI(cards,regs,[8,8,32,2],arrayData=[True,True,True,False])
        if err != "" :
            self.lock.release()
            return err

        d = data[0]
        for i in range(4):
            self.status.HV_set[i] = (d[0+i*2]+d[1+i*2]*256)*self.HV_conversion[i]  # here there was a multiplication by 255. Corrected to 256 by D. Barna
            #print("HV set: " + str(self.status.HV_set[i]))

        d = data[2]
        for i in range(16):
            self.status.temps[i] = (d[0+i*2]+d[1+i*2]*256)*0.1   # here there was a multiplication by 255. Corrected to 256 by D. Barna
        self.status.ref_temp = data[3]*0.1

        d = data[1]
        for i in range(4):
            self.status.HV_act[i]  = (d[0+i*2]+d[1+i*2]*256)*self.HV_conversion[i]   # here there was a multiplication by 255. Corrected to 256 by D. Barna. It seems it is LSB (???)
            #print("HV act: " + str(self.status.HV_act[i]))
        if (HV_repeat > 1):
            for i in range(HV_repeat-1):  
                err, data = self.readPDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_HV1MON,8,arrayData=True)
                if err != "" :
                    self.lock.release()
                    return err
                d = data[0]
                for j in range(4):
                    self.status.HV_act[j]  += (d[0+j*2]+d[1+j*2]*256)*self.HV_conversion[j]  # here there was a multiplication by 255. Corrected to 256 by D. Barna
            for j in range(4):
                self.status.HV_act[j] /= HV_repeat        

        # Now copy the entire register array of all ADC boards into self.status.ADC_registers
        self.readAdcRegisters()

        # Now copy the entire Power and Control unit register table into self.status.PC_registers
        self.readPcRegisters()

        self.lock.release()
        return ""
       
    def clearAnswerQueue(self):
        """
        Reads answers from the camera until a timeout occurs.
        This is used for clearing the answers if an error happened

        Returns
        ^^^^^^^
        Error message or empty string
        """
        while 1 :
            err, d = self.getAnswer()
            if (err != ""):
                return err
            if (d == None):
                return ""
    
    def FactoryReset(self,reset_bool):
        """
        Do factory reset for all components of the camera.

        Parameters
        ^^^^^^^^^^
        reset_bool : bool
            Does reset only if this is True.

        Returns
        ^^^^^^^
        Error message or empty string

        """
        if (self.commSocket is None):
            return "Not connected."
        if (not (reset_bool)):
            return

        # Read the SATA state as it will be changed by the factory reset in V1
        err,dual_SATA_state = self.getDualSata()
        if (err != ""):
            return err

        # Reset the ADCs
        err = self.setAdcRegister('all',self.ADC_registers.RESET_FACTORY,0xcd,noReadBack=True)
        if err != "":
            return err
        time.sleep(2)
        err = self.setAdcRegister('all',self.ADC_registers.RESET_FACTORY,0,   noReadBack=True)
        if err != "":
            return err
        
        # n_adc = len(self.status.ADC_address)
        # for adc_addr in self.status.ADC_address:
        #     reg = self.codes_ADC.ADC_REG_RESET
        #     data = 0xcd
        #     err = self.writePDI(adc_addr,
        #                         reg,
        #                         data,
        #                         numberOfBytes=1,
        #                         arrayData=False,
        #                         noReadBack=True
        #                         )
        #     if (err != ""):
        #         return err
        #     time.sleep(2)
        #     data = 0
        #     err = self.writePDI(adc_addr,
        #                         reg,
        #                         data,
        #                         numberOfBytes=1,
        #                         arrayData=False,
        #                         noReadBack=True
        #                         )
        #     if (err != ""):
        #         return err
        #     time.sleep(1)

        #Reset the control card
        err = self.setPcRegister(self.PC_registers.RESET_FACTORY,0xcd,noReadBack=True)
        # err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_RESET,0xcd,\
        #                     numberOfBytes=1,arrayData=False,noReadBack=True)
        if (err != ""):
            return err

        time.sleep(2)
        err = self.setPcRegister(self.PC_registers.RESET_FACTORY,0,noReadBack=True)
        # err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_RESET,0,\
        #                     numberOfBytes=1,arrayData=False,noReadBack=True)
        if (err != ""):
            return err

        err = self.sendCommand(self.codes_CC.OP_RESET,bytearray([0,0x07,0xd0]),sendImmediately=True)
        if (err != ""):
           return err
        time.sleep(5)
        err = self.setDualSata(dual_SATA_state=dual_SATA_state)
        if (err != ""):
            err = "Could not set dual SATA setting to original state after reset. Camera was not on default address?"
        return ""


    def readPDI(self,cardAddress=None,registerAddress=None,numberOfBytes=None,arrayData=None,byteOrder=None,waitTime=None):       
        """
        Reads data through the Parallel Data Interface (PDI). Can do multiple reads in succession.
        Waits a given time after each read. Returns data in a list, each element is the result 
        of one read operation. Returns data either as array of bytes or integer, as defined by the
        arrayData and byteOrder input.

        Parameters
        ^^^^^^^^^^
        cardAddress:
                    Card address(es) (a single number, or a list of addresses for multiple reads)
        registerAddress:
                    Register start address(es) (a single number, of a list of addresses for multiple reads)
                    Its length must be equal to that of cardAddress
        numberOfBytes:
                    Read length (list length should be equal to cardAddress length)
        arrayData :
                    For each read operation sets whether the data should be returned as one 
                    integer or byte array. False: return integer, True: return byte array.
                    Default is that all reads are integer.
        byteOrder:
                    defines the byte order for converting to integer. 
                    List with 'MSB' or 'LSB' elements. LSB means LSB first.  Default is LSB.         
        waitTime:
                    Wait time between register read commands in ms. Will insert a wait command
                    between the read commands and also after the last one. If 0 no wait commands will be generated.

        Returns
        ^^^^^^^
        error (string):
                    Error message, or empty string in case of no error
        data:
                    List of results. Each element is either an integer (if the corresponding element of
                    the arrayData argument was False) or a byte array (if the corresponding element of
                    the arrayDAta argument was True)
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
                #err = self.sendCommand(APDCAM10G_codes_v1.OP_READPDI,userData,sendImmediately=False)
                err = self.sendCommand(self.codes_CC.OP_READPDI,userData,sendImmediately=False)
                if err != "" :
                    self.lock.release()
                    return err,None
                if (w != 0) :
                    userData = w.to_bytes(2,'big',signed=False)
                    #err = self.sendCommand(APDCAM10G_codes_v1.OP_WAIT,userData,sendImmediately=False)
                    err = self.sendCommand(self.codes_CC.OP_WAIT,userData,sendImmediately=False)
                    if err != "" :
                        self.lock.release()
                        return err,None 
            err = self.sendCommand(None,None,sendImmediately=True)
            if err != "" :
                time.sleep(0.001)
                continue
            data = []
            for i in range(n_read):
                err, d = self.getAnswer()
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
                        if (byteOrder[i] == "MSB" or byteOrder[i].lower() == 'big') :
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
        """
        Writes data through the Parallel Data Interface (PDI). Can do multiple writes in succession.
        Waits a given time after each write. Accepts data either as array of bytes or integer, as defined by the
        arrayData and byteOrder input.
    
        Parameters
        ^^^^^^^^^^
        cardAddress: Card addresses (list, one or more address) 
        registerAddress: Register start address list (list length should be equal to cardAddress length)
        data
            Data to write. If it is a list should be the same length as cardAddress.
            Each element is either an integer or bytearray.
        numberOfBytes
            Write length for each write operation. (List length should be equal to cardAddress length)
            If all writes are arrayData then this is optional.
        arrayData
            For each write operation sets whether the data should be inteprepted as one 
            integer or byte array. False: integer, True: byte array.
            Default is that all data are integer. If arrayData == False
            then the integer is converted to a byte array of numberOfBytes 
        byteOrder
            defines the byte order for converting from integer to register data. 
            List with 'MSB' or 'LSB' elements. LSB means LSB first.  Default is LSB.          
        waitTime
            Wait time between register write commands in ms. Will insert a wait command
            between the read commands and also after the last one. If 0 no wait commands will be generated.
        noReadBack
            if False, it will read back the written data and compare to the input   

        Returns
        ^^^^^^^
        Error message or empty string
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
                    
                #err = self.sendCommand(APDCAM10G_codes_v1.OP_WRITEPDI,userData,sendImmediately=False)
                err = self.sendCommand(self.codes_CC.OP_WRITEPDI,userData,sendImmediately=False)
                if err != "" :
                    self.lock.release()
                    return err
                if (w != 0):
                    userData = w.to_bytes(2,'big',signed=False)
                    #err = self.sendCommand(APDCAM10G_codes_v1.OP_WAIT,userData,sendImmediately=False)
                    err = self.sendCommand(self.codes_CC.OP_WAIT,userData,sendImmediately=False)
                    if err != "" :
                        self.lock.release()
                        return err
            err = self.sendCommand(None,None,sendImmediately=True)
            if err != "" :
                time.sleep(0.001)
                continue
            if (noReadBack == True) :
                self.lock.release()
                return err
            
            time.sleep(0.001)
            # Reading back data for check
            err, d_read = self.readPDI(cardAddress,registerAddress,\
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
        #mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode  = self.status.CC_settings[self.codes_CC.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfc
        data = bytearray([0,mode])
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=True)
        return err
        
    def timerArm(self):
        """ Returns error text
        """
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        #mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode  = self.status.CC_settings[self.codes_CC.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfc
        mode = mode | 0x02
        data = bytearray([0,mode])
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=True)
        if (err != ""):
            return err
        mode = mode | 1
        data = bytearray([0,mode])
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=True)
        return err
    
    def timerRun(self):      
        err = self.readCCdata(dataType=0)
        if (err != ""):
            return err
        #mode  = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_CAMCONTROL+1]
        mode  = self.status.CC_settings[self.codes_CC.CC_REGISTER_CAMCONTROL+1]
        mode = mode & 0xfd
        data = bytearray([0,mode])
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=True)
        if (err != ""):
            return err
        mode = mode | 3
        data = bytearray([0,mode])
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=True)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=True)
        return err

    def setTimerOutput(self) :
        data = bytes(\
                     [self.CAMTIMER.outputEnable | (self.CAMTIMER.outputPolarity << 4), \
                      self.CAMTIMER.outputIdleState | (self.CAMTIMER.outputArmedState << 4)]\
                      )
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTOUTPUT,data,sendImmediately=False)
        err = self.sendCommand(self.codes_CC.OP_SETCTOUTPUT,data,sendImmediately=False)
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
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCONTROL,data,sendImmediately=False)
        err = self.sendCommand(self.codes_CC.OP_SETCTCONTROL,data,sendImmediately=False)
        if (err != ""):
            return err
        data = bytes(\
                     [self.CAMTIMER.outputEnable | (self.CAMTIMER.outputPolarity << 4), \
                      self.CAMTIMER.outputIdleState | (self.CAMTIMER.outputArmedState << 4)]\
                      )
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTOUTPUT,data,sendImmediately=False)
        err = self.sendCommand(self.codes_CC.OP_SETCTOUTPUT,data,sendImmediately=False)
        if (err != ""):
            return err
        data = self.CAMTIMER.clockDiv.to_bytes(2,byteorder='big',signed=False)
        #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTCLKDIV,data,sendImmediately=False)    
        err = self.sendCommand(self.codes_CC.OP_SETCTCLKDIV,data,sendImmediately=False)    
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
            #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETCTTIMER ,data,sendImmediately=False)   
            err = self.sendCommand(self.codes_CC.OP_SETCTTIMER ,data,sendImmediately=False)   
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
        """
        Determine network interface name
        Works only on Linux
        Stores ther result in self.interface
        
        Returns
        ^^^^^^^
        str
            "" or error txt

        """

        # Added by S. Zoletnik (2024. January 19)
        if (platform.platform().lower()[:len('windows')] == 'windows'):
            print("Windows system detected. Cannot determine interface. Measuement does not work with APDTest.")
            self.interface =  ""
            return ""        
        
        ip = self.getIP()
        net = ip.split('.')
        net = net[0]+'.'+net[1]+'.'+net[2]+'.'
        cmd = "ip -f inet address show | grep "+net
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)  
        if (len(d.stdout) != 0):    
            txt = d.stdout
            txt_lines_0 = txt.split(b'\n')
            txt_lines = []
            for l in txt_lines_0:
                if (len(l) != 0):
                    txt_lines.append(l)
            if (len(txt_lines) > 1):
                return("Multiple interfaces with {:s} netaddress?".format(net))
            txt = txt_lines[0].split()
            self.interface = txt[-1]
        else:
            cmd = "ifconfig"
            d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
            if (len(d.stdout) == 0):    
                return "Cannot find interface for APDCAM. Is the camera on?"
            txt_lines = d.stdout.split(b'\n')
            for i,lb in enumerate(txt_lines):
                l = str(lb,encoding='ascii')
                if (l.find(net) > 0):
                    if (i == 0):
                        return "Cannot find interface for APDCAM. Bad answer from ifconfig."
                    txt = str(txt_lines[i-1],encoding='ascii').split()
                    if (txt[0][-1] != ":"):
                        return "Cannot find interface for APDCAM. Bad answer from ifconfig."
                    self.interface = bytes(txt[0][:-1],encoding='ascii')
                    return("")
            else:
                return "Cannot find interface for APDCAM. Is the camera on?"
        return ""

        
    def setClock(self,source, adcmult=33, adcdiv=33, extmult=20, extdiv=20, autoExternal=False, externalSample=False):
        """
        Set ADC digitization clock source and multiplier/divider values

        Parameters
        ^^^^^^^^^^
        source: int
            controller.CLK_INTERNAL or controller.CLK_EXTERNAL
        extmult: int (2..33)
            Multiplier for the external clock signal
        extdiv: int (1..32)
            Divider for the external clock signal
        adcmult: int (20..50)
            Multiplier for the internal ADC clock frequency
        adcdiv: int (8..100)
            Divider for the internal ADC clock frequency
        autoExternal: bool
            Only effective if source specifies to use external clock.
            False - normal external clock mode, always external clock is used
            True - the external clock is used if quality is good and the PLL can lock, but will fall back to internal
            if the PLL can not lock
        externalSample: bool
            If True, use the external source for sampling
            
            Does not check clock quality, just sets. Use getAdcClock() to get status.

        Returns
        ^^^^^^^
        Error message or empty string
        """

        d = 0
        if source == self.CLK_EXTERNAL:
            #d |= 0x04
            d |= 1<<2
        if autoExternal:    
            #d |= 0x08
            d |= 1<<3
        if externalSample:
            d |= 1<<4
        err = self.sendCommand(self.codes_CC.OP_SETCLOCKCONTROL,bytes([d]),sendImmediately=True)
        if (err != ""):
            return err
        
        if (source == self.CLK_EXTERNAL):
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
        """
        Determines the ADC clock frequency. Handles external/internal clock.
        Returns err,f,mode[MHz]
        source: controller.CLK_INTERNAL or controller.CLK_EXTERNAL
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
            source = self.CLK_EXTERNAL
        else:
            f_base = 20.
            source = self.CLK_INTERNAL
        adc_mult = int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_MULT])
        adc_div = int(self.status.CC_settings[self.codes_CC.CC_REGISTER_BASE_PLL_DIV_ADC])
        f = f_base*adc_mult/adc_div
        return "",f,source
            
    def syncADC(self):
        """
        Synchronizes the ADC blocks in the ADC cards.

        Returns
        ^^^^^^^
        Error message or empty string
        """
            
        n_adc = len(self.status.ADC_address)
        reg = [self.codes_ADC.ADC_REG_CONTROL]*n_adc
        l = [1]*n_adc

        self.lock.acquire()

        # What is this while loop serving for??? There is no 'continue' statement, and at the end of the loop, there is a 'break' statement, so it
        # only runs once
        # Ok, it's a kind of 'goto' construct
        while(1): 
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break
            # print("Control regs (syncADC in): {:b},{:b}".format(data[0],data[1]))

            # We read another time? Why?
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break

            # This block (down to # ---- finish) was added by D. Barna
            for i in range(n_adc):
                data[i] &= 0xFB 
            err = self.writePDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),copy.deepcopy(data),\
                                numberOfBytes=[1]*n_adc,arrayData=[False]*n_adc,noReadBack=False)
            if (err != ""):
                #print(err)
                break

            time.sleep(0.2)

            # ---- finish


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

            # Make a final read attempt to check error (but value is not checked)
            err,data = self.readPDI(copy.deepcopy(self.status.ADC_address),copy.deepcopy(reg),l,arrayData=[False]*n_adc)
            if (err != ""):
                #print(err)
                break
            #print("Control regs (syncADC out): {:b},{:b}".format(data[0],data[1]))
            break
        self.lock.release()
        return err


    def setSampleNumber(self,sampleNumber=0):

        # Firmware version before 1.05
        if hasattr(self.codes_CC,"OP_SETSAMPLECOUNT"):
            if (self.commSocket is None):
                return "Not connected.", None
            d = sampleNumber.to_bytes(6,'big')
#            d=bytearray(6)
#            for i in range(6):
#                d[5 - i] = (sampleNumber // 2 ** (i * 8)) % 256
            err = self.sendCommand(self.codes_CC.OP_SETSAMPLECOUNT,d,sendImmediately=True)
            return err

        # Firmware version 1.05 and higher
        if hasattr(self.codes_CC,"OP_SETG1TRIGGERMODULE"):
            # assume that readCCdata was called recently! implement a flag later!
            data = bytearray(11)
            data[0] = self.status.CC_settings[self.codes_CC.CC_REGISTER_G1TRIGCONTROL]
            data[1:5] = self.status.CC_settings[self.codes_CC.CC_REGISTER_TRIGDELAY:self.codes_CC.CC_REGISTER_TRIGDELAY+4]
            data[6:12] = sampleNumber.to_bytes(6,'big')
            err = self.sendCommand(self.codes_CC.OP_SETG1TRIGGERMODULE,data,sendImmediately=True)
            return err

        return "This should never happen in APDCAM10G.setSampleNumber"

    def setSerialPll(self,mult,div):
        """
        Set the serial PLL multiplier/divider

        Parameters
        ^^^^^^^^^^
        mult: int (range???) - multiplier
        div:  int (range???) - divider

        Returns
        ^^^^^^^
        Error message or empty string

        """

        d=bytearray(2)
        d[0] = mult
        d[1] = div
        return self.sendCommand(self.codes_CC.OP_PROGRAMSERIALPLL,d,sendImmediately=True)
        

    def getDualSata(self):
        """
        Reads the dual SATA state from the communications card.
        Does not check dual SATA setting in the ADCs.
        
        Returns
        ^^^^^^^
        error
            Error text or "" if no error
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
               
    def setDualSata(self, dual_SATA_state=True):
        """
        Sets the dual SATA state of the whole system, 10G card and ADCs
            
        Parameters
        ^^^^^^^^^^
        dual_SATA_state: bool
            True: set dual SATA
            False: clear dual SATA
        Returns
        ^^^^^^^
        Error message or empty string   
        """
        if (self.commSocket is None):
            return "Not connected."

        err = self.sendCommand(self.codes_CC.OP_SETSATACONTROL,bytes([0x1 if dual_SATA_state else 0x0]),sendImmediately=True)
        if (err != ""):
           return err
        return self.setAdcDualSata('all',dual_SATA_state)

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

    def setAdcStreamMode(self,adcBoardNo,mode):
        """
        Sets the stream mode of the given ADC.

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int(1..4) or the string 'all'
            The ADC board number (1..4) or 'all' if the stream mode of all ADC board is to be set
        mode: string or integer
            Possible string values: 'Off', 'Continuous', 'Gated', 'Triggered' (case insensitive)
            Possible integer values: 0b00, 0b01,         0b10,    0b11

        Returns
        ^^^^^^^
        error message, or empty string

        """

        print("Set ADC stream mode for " + str(adcBoardNo) + ": " + mode)

        if self.version < 105:
            return "ADC stream mode can only be set for version >=1.05"

        if mode == 0b00 or mode.lower() == 'off':
            return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.STREAMMODE,0)
        if mode == 0b01 or mode.lower() == 'continuous':
            return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.STREAMMODE,0b01)
        if mode == 0b10 or mode.lower() == 'gated':
            return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.STREAMMODE,0b10)
        if mode == 0b11 or mode.lower() == 'triggered':
            return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.STREAMMODE,0b11)

        return "Bad mode: " + str(mode)


    def setAdcResolution(self,adcBoardNo,bits):
        """
        Set the data resolution

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int(1..4) or string the string 'all'
            The ADC board number (1..4) or 'all' if the resolution of all ADC boards is to be set
        bits: 8, 12 or 14
            The number of bits (resolution)

        Returns
        ^^^^^^^
        Error message or empty string
        """

        if bits != 14 and bits != 12 and bits != 8:
            return "ADC resolution must be 14, 12 or 8 bits"

        value = 0
        if bits == 12:
            value = 1
        if bits == 8:
            value = 2
        return self.setAdcRegister(adcBoardNo,self.ADC_registers.RESOLUTION,value)

    def getAdcResolution(self,adcBoardNo):
        """
        Get the resolution of the ADC board(s)

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int(1..4) or the string 'all'

        Returns
        ^^^^^^^
        err
            Error message, or empty string

        value[s]
            The single numerical value (8, 12 or 14) if adcBoardNo is a number, or the list of values if adcBoardNo=='all'
        
        """

        err,reg =  self.getAdcRegister(adcBoardNo,self.ADC_registers.RESOLUTION)
        if err != "":
            return err,None

        # if asked for a single board only, the retured value is a single value. listify it.
        if type(adcBoardNo) is int:
            reg = [reg]

        # in-place replace the returned values (1,2,3) by the number of bits of the resolution

        for i in range(len(reg)):
            # Mask the lowest 2 bits (the higher ones are 'reserved' and I don't know if they are set to zero or not)
            reg[i] = [14,12,8,0][reg[i]()&3]  # added an extra dummy to the end to avoid problems if the register value is 3 (which should not be the case...)
            # If adcBoardNo was a single integer, then de-listify the result, return a single integer 

        if type(adcBoardNo) is int:
            return "",reg[0]
        return "",reg
        
    def setRingBufferSize(self,adcBoardNo,size):
        """
        Sets the ring buffer size

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4)
            The ADC board number
        size: int
            The buffer size. Ring buffer is disabled if zero

        Returns
        ^^^^^^^
        Error message or empty string
        """

        print("Setting ring buffer size of adc: " + str(adcBoardNo) + " --> " + str(size))

        if hasattr(self.ADC_registers,'RINGBUFSIZE'):
            return self.setAdcRegister(adcBoardNo,self.ADC_registers.RINGBUFSIZE,size)
        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.RBSIZE,size)

    def getRingBufferSize(self,adcBoardNo):
        """
        Get the ring buffer size

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or the string 'all'
            The ADC board number

        Returns
        ^^^^^^^
        error
            Error message, or empty string
        buffersize
            If adcBoardNo is a single integer, return the size of the ring buffer of this ADC board.
            If adcBoardNo is 'all', return the sizes of the ring buffers of all ADC boards in a list
        """

        if hasattr(self.ADC_registers,"RINGBUFSIZE"): # v104 and before
            err,reg = self.getAdcRegister(adcBoardNo,self.ADC_registers.RINGBUFSIZE)
            if type(adcBoardNo) == int:
                return err,reg()
            return err,[r() for r in reg]
        else:  #v105 and after (hopefully)
            return self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.STREAMCONTROL.RBSIZE)
    
    def initDAC(self,address):
        """ Sets the configuration of the DAC chips
        address: ADC card address
        """
        dac_instr = bytes([0x11,0x00,0x03,0x0C,0x34,0x00])
        return self.sendADCIstruction(address,dac_instr)

        
    def setOffsets(self,adcBoardNo,user_offsets):
        """
        Sets all the offsets of the ADC channels

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..)
            The ADC board number, in the range 1..4, should correspond to a physically existing board

        offsets
            List of offsets (integers) for the ADC channels

        Returns
        ^^^^^^^
        Returns error message or empty string if no error
        """

        err,adcAddresses = self.adcAddresses(adcBoardNo)
        if err != "":
            return err

        adcmap = ADC2DAC_channel_mapping()
        #adcmap = DAC_ADC_channel_mapping()

        for adcAddress in adcAddresses:
            self.initDAC(adcAddress)
            register_data = bytearray(64)
            for i_adc in range(32):
                dac_addr = adcmap[i_adc]-1
                register_data[2*dac_addr:2*dac_addr+2] = user_offsets[i_adc].to_bytes(2,'little',signed=False)
                #register_data[i*2:i*2+2] = user_offsets[dac_addr].to_bytes(2,'little',signed=False)
            err = self.writePDI(adcAddress,self.codes_ADC.ADC_REG_DAC1,register_data,numberOfBytes=64,arrayData=True)
            if (err != ""):
                return "Error in setOffsets, ADC {:d}: {:s}".format(adcBoardNo,err)
            time.sleep(0.1)

        return ""

    def setOffset(self,adcBoardNo,channel,offset):
        """
        Sets all the offsets of the ADC channels

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..)
            The ADC board number, in the range 1..4, should correspond to a physically existing board

        channel: int (1..32)
            Channel number

        offsets
            List of offsets (integers) for the ADC channels

        Returns
        ^^^^^^^
        Returns error message or empty string if no error
        """
        
        n_adc = len(self.status.ADC_address)
        if adcBoardNo > n_adc or adcBoardNo < 1:
            return "Bad ADC board number: " + str(adcBoardNo)

        if channel<1 or 32<channel:
            return "Bad channel number; " + str(channel)

        adcmap = ADC2DAC_channel_mapping()
        self.initDAC(self.status.ADC_address[adcBoardNo-1])
        dac_addr = adcmap[channel-1]-1
        err = self.writePDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_DAC1+2*dac_addr,offset,numberOfBytes=2,arrayData=False)
        if (err != ""):
            return "Error in setOffset, ADC {:d}: {:s}".format(adcBoardNo,err)
        time.sleep(0.1)

        return ""

    
    def getOffsets(self,adcBoardNo):
        """
        Get all of the offset values on the channels.

        Parameters
        ^^^^^^^^^^
        adcBoardNo (int or 'all')
            ADC board number, in the range (1..4). Must correspond to a physically existing board,
            or the string 'all'
        
        Returns
        ^^^^^^^
        error:string
            Error string, or an empty string if no problem
        offsets
            If adcBoardNo is an integer, a list of 32 offset values.
            If adcBoardNo=='all', a list with as many elements as there are adc boards, each list element is a list of 32 offsets

        """

        err,adcAddresses = self.adcAddresses(adcBoardNo)
        if err!="":
            return err;

        adcmap = ADC2DAC_channel_mapping()
        offsets = []

        for adcAddress in adcAddresses:
            err,register_data = self.readPDI(adcAddress,self.codes_ADC.ADC_REG_DAC1,numberOfBytes=64,arrayData=True)
            if err!="":
                return err;
            register_data = register_data[0]
            adc_board_offsets = [0]*32
            for i_adc in range(32):
                dac_addr = adcmap[i_adc]-1
                adc_board_offsets[i_adc] = int.from_bytes(register_data[2*dac_addr:2*dac_addr+2],'little')
            if type(adcBoardNo) == int:
                return "",adc_board_offsets
            offsets.append(adc_board_offsets)
        return "",offsets

    # Original code by S. Zoletnik
    #
    # def setOffsets(self,offsets):
    #     """ Sets all the offsets of the ADC channels
    #         offsets should be a list of offsets (integers) for the ADC channels
    #         returns error message or ""
    #     """
    #     n_adc = len(self.status.ADC_address)
    #     adcmap = DAC_ADC_channel_mapping()
    #     # Here, 'offsets' is the user-defined values, and 'data' is the data written to the registers
    #     for i_adc in range(n_adc):
    #         self.initDAC(self.status.ADC_address[i_adc])
    #         data = bytearray(64)
    #         for i in range(32):
    #             dac_addr = adcmap[i]-1
    #             data[i*2:i*2+2] = offsets[dac_addr+32*i_adc].to_bytes(2,'little',signed=False)
    #         err = self.writePDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_DAC1,data,numberOfBytes=64,arrayData=True)
    #         if (err != ""):
    #             return "Error in setOffsets, ADC {:d}: {:s}".format(i_adc+1,err)
    #         time.sleep(0.1)
    #     return ""
    
    # def getOffsets(self):
    #     """ Get all of the offset values on the channels.
    #         Returns an error message and list of offsets.
    #     """
    #     n_adc = len(self.status.ADC_address)
    #     adcmap = DAC_ADC_channel_mapping()
    #     # Below, 'offsets' is the data in the registers, and 'data' is what is returned to the user
    #     data = []
    #     for i_adc in range(n_adc):
    #         err,offsets = self.readPDI(self.status.ADC_address[i_adc],self.codes_ADC.ADC_REG_DAC1,numberOfBytes=64,arrayData=True)
    #         if (err != ""):
    #             return "Error in setOffsets, ADC {:d}: {:s}".format(i_adc+1,err),None
    #         offsets = offsets[0]
    #         for i in range(32):
    #             dac_addr = adcmap[i]-1
    #             data.append(int.from_bytes(offsets[dac_addr * 2:dac_addr * 2 + 2], 'little'))
    #         time.sleep(0.1)
    #     return "",data

    
    def getTestPattern(self,adcBoardNo):
        """ 
        Get all of the test pattern settings in the ADCs
            
        Parameters
        ^^^^^^^^^^
        adcBoardNo
            The number of the ADC board (1..4), or the string 'all' to set the pattern for all ADCs
            
        Returns
        ^^^^^^^
        error
            "" or error text.
        values
            List of test pattern values.
            if 'adcBoardNo' is 'all', then the list contains as many elements as the number of ADC boards, and all list element
            is a list of 4 numbers corresponding to the 4 chips of the ADC board
            if 'adcBoardNo' is a single number, the list contains 4 numbers, each corresponding to the 4 blocks of the given ADC
        """
        if adcBoardNo == 'all':
            adcBoardNos = list(range(1,1+len(self.status.ADC_address)))
        else:
            adcBoardNos = [adcBoardNo]

        result = []
        for adc in adcBoardNos:
            # Since ADC_registers.TESTMODE is an array, here we get an array of registers in return, the 4 values
            err,regs = self.getAdcRegister(adc,self.ADC_registers.TESTMODE)
            if err != "":
                return err,None
            # evaluate and store all 4 values
            result.append([r() for r in regs])
            time.sleep(0.1)
        if type(adcBoardNo) is int:
            return "",result[0]
        return "",result

    def setTestPattern(self,adcBoardNo='all',value=0):
        """ Set the test pattern of the ADCs.
        
        Parameters
        ^^^^^^^^^^
        adcBoardNo
            The number of the ADC (1..4), or the string 'all' to set the pattern for all ADCs
        value : list or int/string
            If adcBoardNo is 'all', then
              If single integer, all block of all ADCs will be set to this test pattern
              If list then each list element corresponds to one ADC block.
              If a list element is a single number then each 8-block in the ADC is set to this value.
              If a list element is a 4-element list the 8-channel blocks are set to these test patterns.
            If adcBoardNo is a number, then
              If a single number, all ADC blocks of the board will be set to this number
              If a list with 4 elements, the 8-channel blocks are set to these values
            The values can be given as strings as well, in which case they are safely converted to integers,
            returning an error if the conversion fails

        Returns
        ^^^^^^^
        Error message

        """   

        err,adcAddresses = self.adcAddresses(adcBoardNo)
        if err!="":
            return err

        n_adc = len(adcAddresses)

        # First transform the values into a list with n_adc elements, each list member being a list of 4 numbers
        if adcBoardNo == 'all':

            # if setting is for all ADC boards, and value is a list, just check if it has the same number of elements, as the number of ADC boards
            if type(value) is list:
                if (len(value) != n_adc):
                    return "Bad input in setTestPattern. Should be scalar or list with number of elements equal to number of ADCs."
            # otherwise if value is a single number, then make it a lis
            else:
                value = [value] * n_adc

            # Now, 'value' is a list with number of elements = number of ADC boards. Make sure each element of this list
            # is a list of 4 elements
            for i_adc in range(n_adc):
                if type(value[i_adc]) is list:
                    if len(value[i_adc]) != 4:
                        return "Bad input in setTestPattern"
                else:
                    value[i_adc] = [value[i_adc]]*4
        else:
            # if the setting is for a single ADC board, and 'value' is a list, it must be containing 4 elements, corresponding to the 4 blocks. 
            if type(value) is list:
                # make sure first that it contains 4 elements
                if len(value) != 4:
                    return "Bad input in setTestPattern. Should be scalar or list with 4 numbers"
                # Then create a 1-element list of
                value = [value]
            # otherwise, if a single number, make a list of 1 element being a 4-element list
            else:
                value = [[value]*4]

        for i_adc in range(n_adc):  
            d = bytearray(4)
            for i in range(4):
                try:
                    d[i] = int(value[i_adc][i])
                except ValueError:
                    return "Can not convert to integer: " + str(value[i_adc][i])
            err = self.writePDI(adcAddresses[i_adc],self.codes_ADC.ADC_REG_AD1TESTMODE,d,numberOfBytes=4,arrayData=True)
            if (err != ""):
                return err
            time.sleep(0.1)
        return ""
    
    def setCallight(self,value):
        """
        Set the calibration light.

        Parameters
        ^^^^^^^^^^
        value: int
            Light intensity. 0 is complete dark, maximum is 4095

        """    
        if value > 4095:
            value = 4095
        if value < 0:
            value = 0
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

    def adcAddresses(self,adcBoardNo):
        """
        Get the addresses of the given ADC boards

        Parameters
        ^^^^^^^^^^
        adcBoardNo
            If a single number (starting from 1, up to the number of actual cards in the camera, max 4),
            return the address of that ADC board as a list of length 1
            If a list of numbers, return their addresses
            If 'all', return the addresses of all actually present ADC boards

        Returns
        ^^^^^^^
        err
            Error message or empty string
        addresses
            A list of addresses (with a length of 1 if adcBoardNo is a single number)
        """

        if adcBoardNo == 'all':
            adcBoardNo = list(range(1,1+len(self.status.ADC_address)))

        if type(adcBoardNo) is not list:
            adcBoardNo = [adcBoardNo]

        addresses = []
        for adc in adcBoardNo:
            if adc<1 or len(self.status.ADC_address)<adc:
                return "Bad ADC board number: " + str(adc),[]
            addresses.append(self.status.ADC_address[adc-1])
        return "",addresses

    def getAdcOrPcRegister(self, boardAddress, register):
        """
        Return the value of a single or multiple (potentially multi-byte) register(s)
        of an ADC or the PC board.

        Parameters
        ^^^^^^^^^^
        boardAddress  - address of the board to read the register(s) from

        register      - APDCAM10G_register object

        Returns
        ^^^^^^^
        error   - error message or the empty string

        values  - If 'register' is a list of APDCAM10G_register objects, a list of the same
                  type of objects is returned, which contain the register values, i.e.
                  which can be evaluated by the () operator

                  If 'register' is a single APDCAM10G_register object, a single object
                  of the same type is returned, containing the register value

                  If 'register' is an integer, 

        """
        # a list of registers: make a single read from the first to the last byte of the
        # byte range spanned by all list elements (even if this range is not continuous...)
        if type(register) is list and isinstance(register[0],APDCAM10G_register):
            startByte = min([r.startByte for r in register])
            endByte   = max([r.startByte+r.numberOfBytes for r in register])
            err,d = self.readPDI(boardAddress,startByte,numberOfBytes=endByte-startByte,arrayData=True)
            if err != "":
                return err,None
            result = []
            for r in register:
                rcopy = copy.deepcopy(r)
                rcopy.store_value(d[0][r.startByte-startByte:r.startByte+r.numberOfBytes-startByte])
                result.append(rcopy)
            return "",result

        # a single register
        elif isinstance(register,APDCAM10G_register):
            err,d = self.readPDI(boardAddress,register.startByte,numberOfBytes=register.numberOfBytes,arrayData=True)
            if err != "":
                return err,None
            r = copy.deepcopy(register)
            r.store_value(d[0])
            return "",r

        # a register address
        else:
            print("getAdcOrPcRegister must be called with an APDCAM10G_register object. Use readPDI for lower-level operation.")
            showtrace()
            sys.exit(1)
        time.sleep(0.005)

    def setAdcOrPcRegister(self,boardAddress,register,value=None,noReadBack=False):
        """
        Sets the (potentially multi-byte) register of a given card

        Parameters
        ^^^^^^^^^^
        boardAddress   - address of the board

        register       - An APDCAM10G_register object containing register address, length, byteorder, etc

        value          - value to be set. If None (default), the values stored in 'register' are written
                         into the register of the camera
        """

        registerAddress = register.startByte
        numberOfBytes = register.numberOfBytes
        byteOrder = ''
        if register.byteOrder.upper() == 'MSB' or register.byteOrder.upper() == 'BIG':
            byteOrder = 'MSB'
        if register.byteOrder.upper() == 'LSB' or register.byteOrder.upper() == 'LITTLE':
            byteOrder = 'LSB'
        if value is not None:
            return self.writePDI(boardAddress,registerAddress,value,numberOfBytes=numberOfBytes,byteOrder=byteOrder,arrayData=False,noReadBack=noReadBack)
        else:
            return self.writePDI(boardAddress,registerAddress,register.bytes,numberOfBytes=numberOfBytes,byteOrder=byteOrder,arrayData=True,noReadBack=noReadBack)

    def getAdcRegister(self,adcBoardNo,register):
        """
        Get the value of a register of a single or multiple ADC board(s)

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int(1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        register:
            an APDCAM10G_register object which stores info about the register
            (start address, num. of bytes, how to interpret), or a list of such objects

        Returns
        ^^^^^^^
        err
            Error message or empty string
        value[s]
            if adcBoardNo is a single integer (i.e. one ADC board is queried), a single (or a list of) APDCAM10G_register
            objects (see the documentation of getAdcOrPcRegister), depending on whether register is a single or a list of
            APDCAM10G_register objects
            If adcBoardNo=='all', a list of the above types (each element corresponding to one ADC board)
        """

        err,adcAddresses = self.adcAddresses(adcBoardNo)
        result = []
        for adcAddress in adcAddresses:
            err,tmp = self.getAdcOrPcRegister(adcAddress,register)
            if err!="":
                return err,None
            result.append(tmp)

        if type(adcBoardNo) is int:
            return "",result[0]
        return "",result
        
    def setAdcRegister(self,adcBoardNo,register,value=None,noReadBack=False):
        """
        Set a given register to a given value

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int(1..4) or the string 'all'
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        register:
            An APDCAM10G_register object which stores both the address and the number of bytes. 
        value:
            Value to be written to the register. If it is None (default), the value stored
            in 'register' is used

        Returns
        ^^^^^^^
        Error message or empty string

        """

        err,adcAddresses = self.adcAddresses(adcBoardNo)
        if len(adcAddresses) > 1:
            self.lock.acquire()

        for adcAddress in adcAddresses:
            err = self.setAdcOrPcRegister(adcAddress,register,value=value,noReadBack=noReadBack)
            if err!="":
                if len(adcAddresses) > 0:
                    self.lock.release()
                return err

        if len(adcAddresses) > 1:
            self.lock.release()

        return ""

    def setPcRegister(self,register,value=None,noReadBack=False):
        """
        Set a given register of the Power and Control unit to a given value

        Parameters
        ^^^^^^^^^^
        register:
            Address of the register
        value:
            Value to be written to the register

        Returns
        ^^^^^^^
        Error message or empty string

        """
        
        return self.setAdcOrPcRegister(self.codes_PC.PC_CARD,register,value=value,noReadBack=noReadBack)

    def getPcRegister(self,register):
        """
        Get the value of a register of the PC board

        Parameters
        ^^^^^^^^^^
        register:
            An APDCAM10G_register object

        Returns
        ^^^^^^^
        err
            Error message or empty string
        value
            An APDCAM10G_register object containing the value of the register
        """

        return self.getAdcOrPcRegister(self.codes_PC.PC_CARD,register)
        
    
    def setAdcRegisterBit(self,adcBoardNo,register_bit,value):
        """
        Set a single bit (or a group of bits) in the given register of the ADC. To do so, it first reads the value of the register,
        changes the given bit to the desired value, and then writes it back to the register

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or the string 'all'
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        register_bit:
            An APDCAM10G_register_bits.Bits object which stores info about register address, and the sub-bits
        value:
            The value to be stored in the given number of bits. It is treated bit-by-bit, i.e. specifying
            a value of '2' for a single-bit target, the result will be a zero  bit!

        Returns
        ^^^^^^^
        Error (or empty) string

        """

        # copy to avoid modification of the original
        bit = copy.deepcopy(register_bit)
        register = bit.parent

        if adcBoardNo == 'all':
            adcBoardNos = list(range(1,1+len(self.status.ADC_address)))
        else:
            adcBoardNos = [adcBoardNo]
        
        if len(adcBoardNos) > 1:
            self.lock.acquire()

        for adc in adcBoardNos:
            err,r = self.getAdcRegister(adc,register)
            if err != "":
                if len(adcBoardNos) > 1:
                    self.lock.release()
                return err

            # copy the value back to the original register variable
            register.store_value(r.bytes)

            # modify the bits
            bit.set(value)

            # write the value stored in 'register' back to the camera
            err = self.setAdcRegister(adc,register)

            if err != "":
                if len(adcBoardNos) > 1:
                    self.lock.release()
                return err

        if len(adcBoardNos) > 1:
            self.lock.release()

        return ""

    def getAdcRegisterBit(self,adcBoardNo, register_bit):
        """
        Get a single ibt (ora group of bits) in the given register of the ADC.

        Parameters:
        ^^^^^^^^^^^
        adcBoardNo: int (1..4) or the string 'all'
            The ADC board number ofo 'all' to indicated that it should be made for all ADCs
        register_bit:
            An APDCAM10G_register_bits.Bits object which stores info about register address, and sub-bits

        Returns:
        ^^^^^^^^
        error: error message or empty string

        value:
            If 'adcBoardNo' is an integer, the value stored in the given sub-bits.
            If 'adcBoardNo' is 'all', a list of these values for all ADC boards

        """

        # copy to avoid modification of the original
        bit = copy.deepcopy(register_bit)
        register = bit.parent

        if adcBoardNo == 'all':
            adcBoardNos = list(range(1,1+len(self.status.ADC_address)))
        else:
            adcBoardNos = [adcBoardNo]

        result = []
        for adc in adcBoardNos:
            err, reg = self.getAdcRegister(adc,register)
            if err != "":
                return err,None
            # copy the obtained data into the parent of the function argument, for interpretation
            register.store_value(reg.bytes)

            # now obtain the value stored in the given sub-bits (bit() uses the data stored in its parent)
            result.append(bit())

            time.sleep(0.005)

        if type(adcBoardNo) is int:
            return "",result[0]
        return "",result

    def setPcRegisterBit(self,register_bit,value,noReadBack=False):
        """
        Set a single bit (or a group of bits) in the given register of the ADC. To do so, it first reads the value of the register,
        changes the given bit to the desired value, and then writes it back to the register

        Parameters
        ^^^^^^^^^^
        register_bit:
            An APDCAM10G_register_bits.Bits object which stores info about register address, and the sub-bits
        value:
            The value to be stored in the given number of bits. It is treated bit-by-bit, i.e. specifying
            a value of '2' for a single-bit target, the result will be a zero  bit!

        Returns
        ^^^^^^^
        Error (or empty) string

        """

        # copy to avoid modification of the original
        bit = copy.deepcopy(register_bit)
        register = bit.parent

        err,r = self.getPcRegister(register)
        if err != "":
            return err

        # copy the value back to the original register variable
        register.store_value(r.bytes)

        # modify the bits
        bit.set(value)

        # write the value stored in 'register' back to the camera
        err = self.setPcRegister(register,noReadBack=noReadBack)

        if err != "":
            return err
        return ""

    def setSataOn(self,adcBoardNo,state):
        """
        Switches the SATA channels on/off for the given ADC board

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch the SATA channel on if True, off if False

        Returns
        ^^^^^^^
        Error message or empty string
        
        """
        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.SATAONOFF,1 if state else 0)

    def getSataOn(self,adcBoardNo):
        """
        Returns
        ^^^^^^^
        error   - error message or empty string
        on      - boolean indicating whether SataOn bit is set
        """
        return  self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.SATAONOFF)

    def setAdcDualSata(self,adcBoardNo,state):
        """
        Switches the Dual SATA mode on/off for the given ADC board, or all boards

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch the dual SATA mode on if True, off if False

        Returns
        ^^^^^^^
        Error message or empty string
        
        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.DSM,1 if state else 0)

    def setSataSync(self,adcBoardNo,state):
        """
        Switches the SATA sync mode on/off for the given ADC board

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch the SATA sync mode on if True, off if False

        Returns
        ^^^^^^^
        Error message or empty string
        
        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.SS,2,state)

    def getSataSync(self,adcBoardNo):
        """
        Returns
        ^^^^^^^
        error    - error message or empty string
        bit      - True/False indicating whether the SataSync bit is set
        """
        return  self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.SS)

    def setTestPatternMode(self,adcBoardNo,state):
        """
        Switches the Test mode on/off for the given ADC board

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch the Test mode on if True, off if False

        Returns
        ^^^^^^^
        Error message or empty string
        
        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.TM,1 if state else 0)
    
    def getTestPatternMode(self,adcBoardNo):
        """
        Returns
        ^^^^^^^
        error   - error message or empty string
        bit     - True/False indicating whether the Test Pattern Mode bit is set
        """
        return self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.TM)

    def setFilterOn(self,adcBoardNo,state):
        """
        Switches the filter on or off for the given board

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch the filter on if True, off if False

        Returns
        ^^^^^^^
        Error message or empty string
        
        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.FIL,1 if state else 0)

    def setReverseBitord(self,adcBoardNo,state):
        """
        Switches reverse bit order on/off

        Parameters
        ^^^^^^^^^^
        adcBoardNo: int (1..4) or string
            The ADC board number (1..4) or 'all' to indicate that it should be made for all ADCs
        state:bool
            Switch reverse bit order if true. 

        Returns
        ^^^^^^^
        Error message or empty string
        
        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.RBO,1 if state else 0)

    def getReverseBitord(self,adcBoardNo):
        return self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.RBO)

    def setFilterCoeffs(self,adcBoardNo,values):
        """
        Sets the FIR/IIR filter coefficients

        Parameters
        ^^^^^^^^^^
        adcBoardNo : int (1..4)
            ADC Board number
        values: array[8]
            Filter coefficient values

        Returns
        ^^^^^^^
        Error message or empty string
        """

        if adcBoardNo < 1 or len(self.status.ADC_address) < adcBoardNo:
            return "Bad ADC board number: " + str(adcBoardNo)

        if len(values) != 8:
            return "The number of values must be 8!"

        err = ""
        # This code segment attempted to write the 8 values in one go. It did not work, only the first COEFF_01 was written
        # data = bytearray(16)
        # print("///>>>")
        # for i in range(8):
        #     print(values[i])
        #     data[i*2:i*2+2] = values[i].to_bytes(2,'little',signed=False)

        # err = self.writePDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_COEFF_01,data,numberOfBytes=16,arrayData=True)

        # Loop over all coeffs, and write them one-by-one to the camera. Upon writing the last one, the values are
        # written from the camera registers to the FPGA
        for i in range(8):
            err = self.writePDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_COEFF_01+2*i,values[i],numberOfBytes=2,arrayData=False)
            if err != "":
                return err
            time.sleep(0.01) # for safety, too quick writes may fail... I don't know (D. Barna)
        
        return err

    def getFilterCoeffs(self,adcBoardNo):
        """
        Gets the FIR/IIR filter coefficients

        Parameters
        ^^^^^^^^^^
        adcBoardNo : int (1..4)
            ADC Board number

        Returns
        ^^^^^^^
        error:str
            Error message, or empty string
        coeffs:array
            The 8 coefficients (0-4: FIR, 5: IIR, 6: dummy, 7: filter div)
        """

        if adcBoardNo < 1 or len(self.status.ADC_address) < adcBoardNo:
            return "Bad ADC board number: " + str(adcBoardNo)

        # Here, in contrast to writing, a block-read (i.e. 2x8 bytes) works. 
        err,rawData = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_COEFF_01,16,arrayData=True)
        if err != "":
            return err,None

        rawData = rawData[0]
        data = [65535]*8
        for i in range(8):
            data[i] = int.from_bytes(rawData[2*i:2*i+2],'little')
        return "",data

    def setSampleDivider(self,sampleDiv):
        """
        Set the sample divider value (to reduce the number of samples sent by the communication card,
        compared to the ADC clock frequench), see Fig. 6 of 'APDCAM-10G Users Guide'

        Parameters
        ^^^^^^^^^^
        sampleDiv: int (what range?)
            The divider value. For an ADC clock frequency of 20 MHz and sampleDiv=10, for example,
            the sampling is at 2 MHz.

        Returns
        ^^^^^^^
        Error message or empty string

        """

        sd = round(sampleDiv)
        userData = sd.to_bytes(2,'big',signed=False)
        return self.sendCommand(self.codes_CC.OP_PROGRAMSAMPLEDIVIDER,userData,sendImmediately=True)
    
    def shutterOpen(self,value):
        """
        Set the shutter state. This function does not check whether shutter mode is manual (i.e. if
        the user can use this function to control the shutter)!

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

    def shutterMode(self,value):
        """
        Set the shutter mode.

        Parameters
        ----------
        value : int
            0: Manual, open/close is done by shutterOpen
            1: External

        Returns
        -------
        err : string
            "" or error text.
        """
        
        err = self.writePDI(self.codes_PC.PC_CARD,self.codes_PC.PC_REG_SHMODE,value,numberOfBytes=1,arrayData=False)
        return err  

    
    def setAdcChannelEnable(self,channel,state):
        """
        Enable/Disable a given ADC channel

        Parameters
        ^^^^^^^^^^
        channel: int
            Channel number (1..128)
        state: bool
            True: enable, False: disable

        Returns
        ^^^^^^^
        Error message in string, empty string if no error
        """

        adc_no       = ((channel-1)//32)  # 0..3
        channel_no   = ((channel-1)% 32)  # 0..31
        chip_no      = channel_no//8      # 0..3
        return self.setAdcRegisterBit(adc_no+1,self.ADC_registers.CHENABLE[chip_no].CH[channel_no%8],1 if state else 0)

    def getCallight(self):
        """ Get the current calibration  light setting.
        Returns error text and number
        """
        err, d = self.getPcRegister(self.PC_registers.CALLIGHT)
        return err,d()
    
    def getHV(self,n): 
        """
        Get the HV value for one HV generator.

        Parameters
        ----------
        n : int   -- The HV generator number (1...).

        Returns
        -------
        err: string
        value: float  --  The HV in Volts

        """
        err = self.readStatus()
        if (err != ""):
            return err, None
        return err, self.status.HV_act[n - 1]

    def setHV(self,n,value):
        """
        Set a detector high voltage
        
        Parameters
        ^^^^^^^^^^
        n: int
            The HV generator number (1...)
        value: int or float
            The HV value in Volts.
        
        Returns
        ^^^^^^^
        Error message or empty string
        """

        d = int(value/self.HV_conversion[n-1])  # This line was here before D. Barna replaced HV_conversion_in and HV_conversion_out by HV_conversion

        return self.setPcRegisterBit(self.PC_registers.HVSET[n-1].HV,d)

    def getHV(self,n):
        if n<1 or 4<n:
            return ("Bad HV generator number",0)
        err,hv = self.getPcRegister(self.PC_registers.HVMON[n-1])
        return err,hv.HV()*self.HV_conversion[n-1]

    def setHVMax(self,n,value):
        """
        Set the maximum for a detector high voltage
        
        Parameters
        ----------
        n: int  -- The HV generator number (1..4)
        value: int or float  --  The HV value in Volts.
        
        Returns
        ------------
        error text or ""
        """
        
        d = int(value/self.HV_conversion[n-1])  
        return self.setPcRegister(self.PC_registers.HVMAX[n-1].MAX,d)

    
    def hvEnable(self,state):
        """
        Enables/Disables the HV for the detectors.

        Parameters
        ^^^^^^^^^^
        state: bool
            If True, enables all HV generators. Otherwise it disables

        Returns
        ^^^^^^^
        err : string
            error text or ""
        """
        if state:
            d = 0xAB
        else:
            d = 0
        err = self.writePDI(self.codes_PC.PC_CARD,
                            self.codes_PC.PC_REG_HVENABLE,
                            d,
                            numberOfBytes=1,
                            arrayData=False
                            )
        return err


    def hvOnOff(self,n,on):
        """
        Switches on detector HV on or off

        Parameters
        ^^^^^^^^^^
        n : int
            The HV generator number (1...)

        on: bool
            If true, switches the given generator on. If false, switches off

        Returns
        ^^^^^^^
        error: string
            Error message, or empty string if no error
        """

        # First check if global "HV Enable" is on. If not, writing PC_REG_HVON will fail
        err, hvEnabled = self.getPcRegister(self.PC_registers.HVENABLE)

        return self.setPcRegisterBit(self.PC_registers.HVON.HV[n-1],1 if on else 0,noReadBack=(hvEnabled()!=0xAB))

    def setInternalTrigger(self,channel=None,enable=True,level=None,polarity=None):
        """
        Sets the internal trigger for one channel, but does not enable internal trigger globally.
        Use setTrigger to set up the global trigger scheme.

        Parameters
        ^^^^^^^^^^
        channel : int
            The ADC channel. (1..128 [or the maximum physically existing channels])
        level : int
            The level in 14 bit resolution. This is the scale of the ADC sigals. The final output signlas from the measurement 
            are 16384 - signal. Valid range: 0...16383
        polarity : int
            The polarity. Either self.codes_ADC.INT_TRIG_POSITIVE or self.codes_ADC.INT_TRIG_NEGATIVE
        enable: boolean, optional
            If True enables trigger on this channel. The default is True

        Returns
        ^^^^^^^
        Error message or empty string

        """

        if ((channel is None) or (level is None) or (polarity is None)):
            return "Parameters not set."
        adc_no = int((channel - 1) // 32) # 0..3
        ch_num = int((channel - 1) % 32)
        d=0
        if (enable):
            #d = 2 ** 15  # Enable
            d = 1<<15
        if (polarity == self.codes_ADC.INT_TRIG_POSITIVE):
            pass
        elif (polarity == self.codes_ADC.INT_TRIG_NEGATIVE):
            #d += 2 ** 14
            d |= 1<<14
        else:
            return "Invalid trigger polarity"
        if ((level >= 2 ** 14) or (level < 0)):
            return "Invalid trigger level"
        d += level
        
        err = self.writePDI(self.status.ADC_address[adc_no],self.codes_ADC.ADC_REG_MAXVAL11 + ch_num * 2,d,numberOfBytes=2,arrayData=False,byteOrder='MSB')
        if (err != ""):
            return "Error setting internal trigger:"+err
        return ""

    def setInternalTriggerAdc(self, adcBoardNo, enable):
        """
        Enable/Disable trigger output in one or all ADC blocks.

        Parameters
        ^^^^^^^^^^
        adcBoard: int(1..4) or the string 'all'
            The ADC board number
        enable : boolean, optional
            True: Enable trigger. 
            False: Disable trigger.
                   The default is True.

        Returns
        ^^^^^^^
        Error message or empty string

        """

        return self.setAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.ITE,1 if enable else 0)

    def getInternalTriggerAdc(self,adcBoardNo):
        return self.getAdcRegisterBit(adcBoardNo,self.ADC_registers.CONTROL.ITE)
    
    def setGate(self, externalGateEnabled=False, externalGateInverted=False, internalGateEnabled=False, internalGateInverted=False, camTimer0Enabled=False, camTimer0Inverted=False, swGate=False):
        """
        Set the G1 trigger module parameters. 
        """

        if not hasattr(self.codes_CC,"OP_SETG2GATEMODULE"):
            return "APDCAM10G.set_gate can not be used for this firmware"

        print("Setting gate")

        data = 0
        if externalGateEnabled:
            data |= 1<<1
        if externalGateInverted:
            data |= 1<<0
        if internalGateEnabled:
            data |= 1<<3
        if internalGateInverted:
            data |= 1<<2
        if camTimer0Enabled:
            data |= 1<<5
        if camTimer0Inverted:
            data |= 1<<4
        if swGate:
            data |= 1<<7

        print(bin(data))

        return self.sendCommand(self.codes_CC.OP_SETG2GATEMODULE,bytearray([data]),sendImmediately=True)

    def setTrigger(self, externalTriggerPos=False, externalTriggerNeg=False, internalTrigger=False, camTimer0Pos=None, camTimer0Neg=None, softwareTrigger=None, clearOutput=None, clearTriggerStatus=None, triggerDelay = 0, disableWhileStreamsOff = None, numberOfSamples = None):
        """
        Sets the trigger scheme in the camera. New implementation by D. Barna

        Parameters
        ^^^^^^^^^^
        externalTriggerPos (bool)
            Enable triggering on the rising edge of the external signal

        externalTriggerNeg (bool)
            Enable triggering on the falling edge of the external signal
        
        internalTrigger: boolean
            If True, internal triggering (trigger signal coming from any of the ADC boards) is enabled

        camTimer0Pos: boolean
            If True, enable triggering on the rising edge of the camera timer0 module signal
            (only available in firmware v1.05 or above, it is ignored otherwise with an error message)

        camTimer0Neg: boolean
            If True, enable triggering on the falling edge of the camera timer0 module signal
            (only available in firmware v1.05 or above, it is ignored otherwise with an error message)
        
        softwareTrigger: boolean
            Generate a software trigger
            (only available in firmware v1.05 or above, it is ignored otherwise with an error message)

        clearOutput: boolean
            Clear the output of the gate module (?)
            (only available in firmware v1.05 or above, it is ignored otherwise with an error message)

        clearTriggerStatus: boolean

        triggerDelay:       Trigger with this delay [microsec]

        disableWhileStreamsOff: ???

        numberOfSamples: int
            The number of samples to be recorded. Only effective if the ADCs are in 'gated' mode, and
            a trigger event occurs (either by some hardware input, or by software, now, if the softwareTrigger
            flag is set to true.

        Returns
        ^^^^^^^
        Error message or empty string
        """

        if softwareTrigger and (externalTriggerPos or externalTriggerNeg or internalTrigger or camTimer0Pos or camTimer0Neg):
            return "Either a software trigger, or the combination of hardware triggers can be specified, but not both"

        if clearTriggerStatus and (softwareTrigger or externalTriggerPos or externalTriggerNeg or internalTrigger or camTimer0Pos or camTimer0Neg):
            return "clearTriggerStatus can not be specified with any other triggers"

        if clearOutput and (softwareTrigger or externalTriggerPos or externalTriggerNeg or internalTrigger or camTimer0Pos or camTimer0Neg):
            return "clearOutput can not be specified with any other triggers"

        error = ""

        if (triggerDelay < 0):
            triggerDelay = int(0)
        else:
            triggerDelay = int(triggerDelay)

        # The control byte (#5) of the command
        control=0

        if hasattr(self.codes_CC,"OP_SETTRIGGER"):
            if disableWhileStreamsOff:
                control |= 1<<6 # disable trigger events while streams are off
        else:
            if disableWhileStreamsOff is not None:
                error += "With this firmware, one can not use disableWhileStreamsOff in APDCAM10G.set_trigger. Ignonring."

        # external trigger
        if externalTriggerPos:
            control |= 1<<0
        if externalTriggerNeg:
            control |= 1<<1

        # enable accepting internal triggers coming from any of the ADC boards
        if internalTrigger:
            control |= 1<<2

        if hasattr(self.codes_CC,"OP_SETG1TRIGGERMODULE"):
            if camTimer0Pos:
                control |= 1<<3
            if camTimer0Neg:
                control |= 1<<4
            if softwareTrigger:
                control |= 1<<5
            if clearOutput:
                control |= 1<<6
            if clearTriggerStatus:
                control |= 1<<7
        else:
            if camTimer0Pos is not None:
                error += ("\n" if error != "" else "") + "camTimer0Pos can not be set for this firmware. Ignoring"
            if camTimer0Neg is not None:
                error += ("\n" if error != "" else "") + "camTimer0Neg can not be set for this firmware. Ignoring"
            if softwareTrigger is not None:
                error += ("\n" if error != "" else "") + "softwareTrigger can not be set for this firmware. Ignoring"
            if clearOutput is not None:
                error += ("\n" if error != "" else "") + "clearOutput can not be set for this firmware. Ignoring"
            if clearTriggerStatus is not None:
                error += ("\n" if error != "" else "") + "clearTriggerStatus can not be set for this firmware. Ignoring"
                
        # enable outputting the internal trigger on all ADC boards as well (still not on the channel-level!)
        err = self.setInternalTriggerAdc(adcBoardNo='all',enable=internalTrigger)
        if err != "":
            error += ("\n" if error != "" else "") + err

        user_data = bytes([control]) + triggerDelay.to_bytes(4,'big',signed=False) 
        if hasattr(self.codes_CC,"OP_SETTRIGGER"):
            err = self.sendCommand(self.codes_CC.OP_SETTRIGGER,user_data,sendImmediately=True)

        # For FW version >=1.05 we need to append the number of samples to the data bytes of this command
        elif hasattr(self.codes_CC,"OP_SETG1TRIGGERMODULE"):
            # If the user provided number of samples as a function argument, use this
            if numberOfSamples is not None:
                user_data += numberOfSamples.to_bytes(6,'big',signed=False)
            # otherwise use the value stored in the corresponding camera register
            else:
                #user_data += self.status.CC_settings[self.codes_CC.CC_REGISTER_SAMPLECOUNT:self.codes_CC.CC_REGISTER_SAMPLECOUNT+6]
                user_data += self.CC_settings.SAMPLECOUNT(self.status.CC_settings).to_bytes(6,'big',signed=False)
            print("SETG1TRIGGERMODULE user data: ")
            for i in range(len(user_data)):
                print(hex(user_data[i]))
            err = self.sendCommand(self.codes_CC.OP_SETG1TRIGGERMODULE,user_data,sendImmediately=True)
            print("command is sent")

        if (err != ""):
            error += ("\n" if error != "" else "") + err

        return error

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

    def startContinuousData(self):
        print("======================= start continuous data stream for 100 samples ======================")
        # Enable all streams
        data = bytes([15])
        self.sendCommand(self.codes_CC.OP_SETSTREAMCONTROL,data,sendImmediately=True)

        self.setAdcStreamMode('all','off')
        time.sleep(1)
        self.setAdcStreamMode('all','gated')

        #             SWT     Delay    
        data = bytes([0x20,   0,0,0,0,   0,0,0,0,0,0x64])
        self.sendCommand(self.codes_CC.OP_SETG1TRIGGERMODULE,data,sendImmeidately=True)

    # def measure(self,numberOfSamples=100000, channelMasks=[0xffffffff,0xffffffff, 0xffffffff, 0xffffffff], \
    #             sampleDiv=10, datapath="data", bits=14, waitForResult=0, externalTriggerPolarity=None,\
    #             internalTrigger=False, internalTriggerADC=None,  triggerDelay=0, data_receiver='APDTest'):
    def measure(self,
                streamMode=None, \
                numberOfSamples=None, \
                generateSwTriggerWithDelay=None,
                channelMasks=None, \
                sampleDiv=None, \
                datapath="data",
                bits=None, \
                waitForResult=0, \
                externalTriggerPos=None, \
                externalTriggerNeg=None, \
                internalTrigger=None, \
                internalTriggerADC=None,  \
                triggerDelay=0, \
                dataReceiver='APDTest',
                timeout=10000000,
                logger=Terminal(),
                onProgress=None
                ):
        """
        Start measurement in APDCAM.
        
        Parameters
        ^^^^^^^^^^
        streamMode : string
            Stream mode, obligatory for firmware 1.05, must not be given for earlier firmware versions
            'Continuous', 'Gated' or 'Triggered' (case insensitive)
        numberOfSamples : int, optional
            The number of samples to measure in one ADC channel. The default is 100000.
        generateSwTriggerWithDelay : int
            If not the default None, after setting up the camera (ADC stream modes, streams started, etc),
            generate a software trigger with this delay (in microsecs)
            It is useful if you want to start the measurement immediately, without waiting for any
            internal or external trigger event. Note that trigger conditions (such as external trigger enabled, etc)
            set earlier are not changed, so if these occur during the wait period, they can trigger
            the data sampling/transmission earlier than specified by this argument. If you want precise control,
            disable all triggers before.
        channelMasks : list of integers, length must be the same as number of ADC boards, optional
            Channel masks to enable ADC channel. Each bit enables one channel. 
            If omitted, the status is obtained from the registers CHENABLEx (x=1..4)
            Each element of this list corresponds to one ADC board
            MSB in each number is channel 1, LSB in each number is channel 32
            The most significant byte in the number corresponds to CHENABLE1, the
            least significant byte in th enumber corresponds to CHENABLE4 (I hope it is correct like this)
        sampleDiv : int, optional
            The sample clock divider.
            The default is 10. For the default ADC clock setting this means 2 MHz sampling.
        datapath : string, optional
            The path where data is stored. The default is "data".
        bits : int, optional
            The number of bits in sampling. The default is 14.
        waitForResult : int, optional
             <=0 : Do not wait for APDTest_10G to stop
                   Measurement status can be checked with measurementStatus or 
                   waited for with waiMeasurement.
             > 0 : Wait this much seconds
        externalTriggerPos: None | bool
            If None, use the existing settings from the camera, do not change.
            Otherwise, it indicates whether triggering on the rising edge of the external trigger signal is enabled
        externalTriggerNeg: None | bool
            If None, use the existing settings from the camera, do not change.
            Otherwise, it indicates whether triggering on the falling edge of the external trigger signal is enabled
        internalTrigger: boolean
            True enables internal trigger, False disables.
            If internalTriggerADC is None internal trigger enable in all ADCs
            follows this setting.
        internalTriggerADC: None or boolean
            None: Internal trigger Enable/Disable follows internalTrigger
            True: Internal trigger in all ADCs is enabled
            False: Internal trigger in all ADCs is disabled
        triggerDelay: int or float  
            Trigger with this delay [microsec]
        dataReceiver: str
            The data receiver method:
                'APDTest': The scriptable APDTest_10G C++ program which is part of the module. This should be compiled
                           and will be called to collect data into files.
                'Python': Python code inside this method. (Might still call some external C program.)
        timeout: int (10000000)
            Timeout in milliseconds for the external data acquisition program APDtest
        logger: object
            An object that must have  showMessage(string), showWarning(string) and showError(string) functions to show eventual messages

        onProgress: a function that will be periodically executed during data acquisition. It can inform the calling thread about the progress.
            It must have two arguments: a floating point value (which will have a value between 0..1 indicating the progress), and a string,
            which gives a textual information about the progress or anything that is happening.
            It must return a boolean. If it returns True, data acquisition continues. False will cause data acquisition to be stopped.

        Returns
        ^^^^^^^
        str
            "" or error message
        str
            Warning. "" if no warning.
        datareceiver
            An APDCAM10G.data object (if the argument dataReceiver=="python") which contains the data
        

        """

        logger.showMessage("[MEASUREMENT] Starts")

        # Argument consistency checks
        if self.version >= 105:
            if streamMode is None:
                return "Stream mode must be specified for firmware version >=1.05"
        else:
            if streamMode is not None:
                return "Stream mode must not be given for firmware version <1.05"

#        if streamMode is not None and streamMode.lower() != 'gated' and numberOfSamples is not None:
#            return "Number of samples can only be specified if stream mode is 'gated'"

        self.readStatus()

        chmask = None

        n_adc = len(self.status.ADC_address)

        # If no channel mask was given by the user, read the CHENABLEx (x=1..4) registers from the camera
        # and set the mask from these values
        if channelMasks is None:
            chmask = [0]*4
            for adc in range(n_adc):
                tmp = bytearray(4)
                for i in range(4):
                    err,r = self.getAdcRegister(adc+1,self.ADC_registers.CHENABLE[i])
                    if err != "":
                        error = "Error reading the channel enabled status from the camera: " + err 
                        logger.showError(error)
                        return error,"",None
                    tmp[i] = r()
                chmask[adc] = int.from_bytes(tmp,'big')
        else:
            chmask = copy.deepcopy(channelMasks)
            if (len(chmask) < n_adc):
                for i in range(n_adc-len(chmask)):
                    chmask.append(0)
                    #chmask = [chmask, 0]
                    #this (old code) is probably wrong, we want to append zeros??? this will create nested lists
        self.measurePara.channelMasks = copy.deepcopy(chmask)

        if (sampleDiv != None):
            self.setSampleDivider(sampleDiv)
            self.measurePara.sampleDiv = sampleDiv
        else:
            self.measurePara.sampleDiv =  int(self.status.CC_settings[self.codes_CC.CC_REGISTER_SAMPLEDIV])

        if (bits != None):
            err = self.setAdcResolution('all',bits)
            if err!='':
                logger.showError(err)
                return err,"",None
            self.measurePara.bits = bits
        else:
            err,resolutions = self.getAdcResolution('all')
            for i in range(len(resolutions)-1):
                if resolutions[0] != resolutions[i+1]:
                    error = "ADC blocks have different resolution setting." 
                    logger.showError(error)
                    return error,"",None
            if resolutions[0] != 8 and resolutions[0] != 12 and resolutions[0] != 14:
                error = "Invalid bit resolution setting in ADCs." 
                logger.showError(error)
                return error,"",None 
            bits = resolutions[0]
            self.measurePara.bits = resolutions[0]

        trigstate = None
        if hasattr(self.CC_settings,"TRIGSTATE"):
            trigstate = self.CC_settings.TRIGSTATE
        elif hasattr(self.CC_settings,"G1TRIGCONTROL"):
            trigstate = self.CC_settings.G1TRIGCONTROL

        # IF TRIGGERS ARE NOT SPECIFIED, DO WE NEED TO READ THE TRIGGER SETTINGS FROM THE CAMERA AND WRITE IT BACK???
        
        # Trigger settings
        if externalTriggerPos is None: # default value, i.e. parameter not specified, then take it from the camera
            #externalTriggerPos = bool(self.status.CC_settings[self.codes_CC.CC_REGISTER_TRIGSTATE] & (1<<0))
            externalTriggerPos = trigstate.ETR(self.status.CC_settings)

        if externalTriggerNeg is None: 
            externalTriggerNeg = trigstate.ETF(self.status.CC_settings)

        if internalTrigger is None: # default value, i.e. parameter not specified, then take it from the camera
            internalTrigger = trigstate.IT(self.status.CC_settings)

        if triggerDelay is None: # default value, i.e. parameter not specified, then take it from the camera
            #triggerDelay = int.from_bytes(self.status.CC_settings[self.codes_CC.CC_REGISTER_TRIGDELAY:self.codes_CC.CC_REGISTER_TRIGDELAY+4],'big')
            triggerDelay = self.CC_settings.TRIGDELAY(self.status.CC_settings)

        if hasattr(self.codes_CC,"OP_SETTRIGGER"):
            err = self.setTrigger(externalTriggerPos=externalTriggerPos,
                                  externalTriggerNeg=externalTriggerNeg,
                                  internalTrigger=internalTrigger,
                                  triggerDelay=triggerDelay)
        elif hasattr(self.codes_CC,"OP_SETG1TRIGGERMODULE"):
            #print("FIXME! self.setTrigger in measure() must be updated for this firmware")
            err = self.setTrigger(externalTriggerPos=externalTriggerPos,
                                  externalTriggerNeg=externalTriggerNeg,
                                  internalTrigger=internalTrigger,
                                  camTimer0Pos=False,
                                  camTimer0Neg=False,
                                  triggerDelay=triggerDelay)

        self.measurePara.externalTriggerPos = externalTriggerPos
        self.measurePara.externalTriggerNeg = externalTriggerNeg
        self.measurePara.internalTrigger = internalTrigger
        self.measurePara.triggerDelay = triggerDelay

        if numberOfSamples is None:
            numberOfSamples = int.from_bytes(self.status.CC_settings[self.codes_CC.CC_REGISTER_SAMPLECOUNT:self.codes_CC.CC_REGISTER_SAMPLECOUNT+6],byteorder='big')

        self.measurePara.numberOfSamples = numberOfSamples
        
        if (err != ""):
            logger.showError(err)
            return err,"",None
        
        if (internalTriggerADC is not None):
            self.setInternalTriggerADC(adcBoard='all', enable=internalTriggerADC)
    
        err = self.syncADC()
        if (err != ""):
            logger.showError(err)
            return err,"",None

        if (dataReceiver.lower() == 'apdtest'):

            if streamMode is not None:
                print("Can not launch apdtest for the new hardware yet")
                return "Can not launch apdtest for the new hardware yet"

            if (self.interface == ""):
                error = "Cannot measure, as network interface could not be found." 
                logger.show_error(error)
                return error,"",None 
            
            cmdfile_name = "apd_python_meas.cmd"
            cmdfile = datapath+'/'+cmdfile_name
            logger.showMessage("[MEASUREMENT] Command file: " + cmdfile)
            try:
                f = open(cmdfile,"wt")
            except:
                error = "Error opening file "+cmdfile
                logger.showError(error)
                return error,"",None 
            
            ip = self.getIP()
            interface = self.interface.decode('ascii')

            # Calculate the number of active channels
            chnum = 0
            for i in range(len(self.status.ADC_address)):
                chnum += bin(chmask[i]).count("1")

            # add some safety margin to the buffer
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
                f.write("Wait " + str(timeout) + "\n")
                f.write("Save\n")
                # This clears the sample counter
                f.write("CCCONTROL 276 6 0 0 0 0 0 0\n")
                f.close()
            except :
                error = "Error writing command file " + cmdfile
                logger.showError(error)
                return error,"",None 
                f.close()
            
            time.sleep(1)
            thisdir = os.path.dirname(os.path.realpath(__file__))
            apdtest_prog = 'APDTest_10G'
            apdtest = os.path.join(thisdir,'../apdcam_control/APDTest_10G','APDTest_10G')
            cmd = "killall -KILL "+apdtest_prog+" 2> /dev/null ; cd "+datapath+" ; rm APDTest_10G.out Channel*.dat 2> /dev/null ; "+apdtest+" "+cmdfile_name+" >APDTest_10G.out 2>&1 &"
            logger.showMessage("[MEASUREMENT] Executing: " + cmd)

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
                      logger.showError(err)
                      return err,"",None
                   if (all_txt[il].lower().find("start succes") >= 0):
                      started = True
                      break
                if (started):
                    break
                time.sleep(sleeptime)
    
            if (not started):
                err = "APDCAM did not start"
                logger.showError(err)
                return err,"",None
        else:
            # Native Python measurement
            data_receiver = APDCAM10G_data(self,logger)

            ret = data_receiver.get_net_parameters()
            if (ret != ""):
                logger.showError(ret)
                return ret,"",data_receiver

            ret = data_receiver.allocate(channel_masks=chmask,sample_number=numberOfSamples,bits=bits)
            if (ret != ""):
                logger.showError(ret)
                return ret,"",data_receiver

            ret = data_receiver.start_receive()
            if (ret != ""):
                logger.showError(ret)
                return ret,"",data_receiver

            ret = data_receiver.start_stream(streamMode)
            if (ret != ""):
                logger.showError(ret)
                return ret,"",data_receiver

            if generateSwTriggerWithDelay is not None:
                print("Setting trigger with delay: " + str(generateSwTriggerWithDelay))
                self.setTrigger(softwareTrigger=True,triggerDelay=generateSwTriggerWithDelay,numberOfSamples=numberOfSamples)

            err, warn = data_receiver.get_data(onProgress)
            logger.showMessage("[MEASUREMENT] Stop streams")

            data_receiver.stop_stream()
            logger.showMessage("[MEASUREMENT] Stop receive")
            data_receiver.stop_receive()
            if err != "":
                logger.showError(err)
            if warn != "":
                logger.showWarning(warn)
            logger.showMessage("[MEASUREMENT] Finished")
            return err,warn,data_receiver
            
        if (waitForResult <=0):
            return "","",None
        
        err,warning = self.waitForMeasurement(waitForResult)
        logger.showMessage("[MEASUREMENT] Finished")
        return err,warning,None
   
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
        
        self.readStatus()
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

        if not self.measurePara.externalTriggerPos and not self.measurePara.externalTriggerNeg:
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
            #d_octet = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i+2]
            d_octet = self.status.CC_settings[self.codes_CC.CC_REGISTER_UDPOCTET1+16*i:self.codes_CC.CC_REGISTER_UDPOCTET1+16*i+2]
            octet = int.from_bytes(d_octet,'big',signed=False)
            #d_ip = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i:APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i+4]
            d_ip = self.status.CC_settings[self.codes_CC.CC_REGISTER_IP1+16*i:self.codes_CC.CC_REGISTER_IP1+16*i+4]
            #d_port = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i+2]
            d_port = self.status.CC_settings[self.codes_CC.CC_REGISTER_UDPPORT1+16*i:self.codes_CC.CC_REGISTER_UDPPORT1+16*i+2]
            port = int.from_bytes(d_port,'big',signed=False)
            print("Stream {:d}...octet:{:d}... IP:{:d}.{:d}.{:d}.{:d}...port:{:d}".format(i+1,octet,\
                  int(d_ip[0]),int(d_ip[1]),int(d_ip[2]),int(d_ip[3]),port))
      
            data = bytearray(9)
            data[0] = 3
            data[1:3] = d_octet
            data[3:7] = bytes([239,123,13,100])
            p = 10003
            data[7:9] = p.to_bytes(2,'big')
            #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETMULTICASTUDPSTREAM,data,sendImmediately=True)
            err = self.sendCommand(self.codes_CC.OP_SETMULTICASTUDPSTREAM,data,sendImmediately=True)
            print(err)
            
            data = bytearray(15)
            data[0] = 3
            data[1:3] = d_octet
            data[3:9] = bytes([0x90,0xe2,0xba,0xe3,0xa4,0x62])
            data[9:13] = bytes([239,123,13,100])
            p = 10003
            data[13:15] = p.to_bytes(2,'big')
            #err = self.sendCommand(APDCAM10G_codes_v1.OP_SETUDPSTREAM,data,sendImmediately=True)
            err = self.sendCommand(self.codes_CC.OP_SETUDPSTREAM,data,sendImmediately=True)
            print(err)
 
        self.readCCdata(dataType=0)                       
        for i in range(4):
            #d_octet = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPOCTET1+16*i+2]
            d_octet = self.status.CC_settings[self.codes_CC.CC_REGISTER_UDPOCTET1+16*i:self.codes_CC.CC_REGISTER_UDPOCTET1+16*i+2]
            octet = int.from_bytes(d_octet,'big',signed=False)
            #d_ip = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i:APDCAM10G_codes_v1.CC_REGISTER_IP1+16*i+4]
            d_ip = self.status.CC_settings[self.codes_CC.CC_REGISTER_IP1+16*i:self.codes_CC.CC_REGISTER_IP1+16*i+4]
            #d_port = self.status.CC_settings[APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i:APDCAM10G_codes_v1.CC_REGISTER_UDPPORT1+16*i+2]
            d_port = self.status.CC_settings[self.codes_CC.CC_REGISTER_UDPPORT1+16*i:self.codes_CC.CC_REGISTER_UDPPORT1+16*i+2]
            port = int.from_bytes(d_port,'big',signed=False)
            print("Stream {:d}...octet:{:d}... IP:{:d}.{:d}.{:d}.{:d}...port:{:d}".format(i+1,octet,\
                  int(d_ip[0]),int(d_ip[1]),int(d_ip[2]),int(d_ip[3]),port))

    def getAdcPllLocked(self,adcBoardNo):
        """
        Get the PLL locked status (true/false)
        """
        (err,pllLocked) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_STATUS1,1,arrayData=False)
        return (err,bool(pllLocked[0] & 1))


    def getAdcPowerVoltages(self,adcBoardNo):
        """
        Get the power voltages

        Returns
        ^^^^^^^
        (error,dvdd33,dvdd25,avdd33,avdd18)

        """
        errors = ""

        (err,dvdd33) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_DVDD33,2,arrayData=False)
        if err != "":
            errors += err + ";"
        (err,dvdd25) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_DVDD25,2,arrayData=False)
        if err != "":
            errors += err + ";"
        (err,avdd33) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_AVDD33,2,arrayData=False)
        if err != "":
            errors += err + ";"
        (err,avdd18) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_AVDD18,2,arrayData=False)
        if err != "":
            errors += err + ";"
        #return (errors,dvdd33,dvdd25,avdd33,avdd18)
        return (errors,dvdd33[0],dvdd25[0],avdd33[0],avdd18[0])  # Changed by D. Barna

    def getAdcTemperature(self,adcBoardNo):
        err,r = self.getAdcRegister(adcBoardNo,self.ADC_registers.TEMPERATURE)
        return err,r()
        
    def getAdcOverload(self,adcBoardNo):
        """
        Return True/False if any of the channels went to overload. It clears the latched bit
        corresponding to this event
        
        """
        # Read the status
        (error,status) = self.readPDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_OVDSTATUS,1,arrayData=False)

        # Clear the status byte (the latched bit 0, which is indicating the overload stsatus)
        self.writePDI(self.status.ADC_address[adcBoardNo-1],self.codes_ADC.ADC_REG_OVDSTATUS,0,1)

        #return True/False
        return (error,bool(status[0] & 1))

    def loadfup(self,filename,reconnect,logger=None,progress=None):
        """
        Load a firmware upgrade (fup) to the camera.

        Parameters:
        ^^^^^^^^^^^
        filename  - the firmware upgrade filename
        reconnect - (bool) if true, connection to the camera is closed and reopened
        logger    - a function (taking a string argument) to log/display messages. 
        progress  - a function (taking a floating point argument between 0..1) which is called during the upgrade
                    to indicate progress
        """

        log = lambda m: logger(m) if (logger!=None) else 0

        if filename=='':
            log("No firmware file is chosen")
            return "No firmware file is chosen"
        filesize = os.path.getsize(filename)
        log("Opening '" + filename + "'")
        try:
            file = open(filename,'rb') # open in binary mode
        except:
            log("File '" + filename + "' could not be opened")
            return "File '" + filename + "' could not be opened"
        n = 1024
        addr = 0
        data = file.read(n)
        log("Uploading firmware to the camera")
        while data:
            cmdData = addr.to_bytes(length=4,byteorder='big') + data
            # add a 'loadfup' instruction to the instruction queue, but do not send it yet
            err1 = self.sendCommand(self.codes_CC.OP_LOADFUP,cmdData,sendImmediately=False)
            # add a 'sendack' instruction with a code (0x801) to request FUP checksum. It is invalid yet, so we only wait for the
            # answer before we continue with the next chunk of the file, but ignore the received data
            err2 = self.sendCommand(self.codes_CC.OP_SENDACK,0x801.to_bytes(length=2,byteorder='big'),sendImmediately=True)
            if err1!="" or err2!="":
                log("Failed to load firmware to camera")
                return "Failed to load firmware to the camera"
            err3,d = self.getAnswer()
            if err3!="" or d==None:
                log("Did not receive answer from camera, failed to load firmware")
                return "Did not receive answer from camera, failed to load firmware"
            d = d[22:len(d)] # skip CC header
            response = int.from_bytes(d[0:2],'big',signed=False)
            if response != self.codes_CC.AN_ACK:
                log("Unexpected response from camera, failed to load firmware")
                return "Unexpected response from camera, failed to load firmware"
            addr += len(data) # advance the address (data location) within the file
            data = file.read(n)
            if progress!=None:
                progress(addr/filesize)

        log("Firmware uploaded.")
    
        today = date.today()
        data = today.year.to_bytes(length=2,byteorder='big') + today.month.to_bytes(length=1) + today.day.to_bytes(length=1)
        err = self.sendCommand(self.codes_CC.OP_STARTFUP,data,sendImmediately=True)
        if err!="":
            log("Error: " + err + ". Firmware not upgraded.")
            return "Error: " + err + ". Firmware not upgraded."
        time.sleep(1)
        err, d = self.getAnswer()
        if err!="":
            log("Error getting answer from the camera. Firmware not upgraded.")
            return "Error getting answer from the camera. Firmware not upgraded."
        d = d[22:len(d)]
        response = int.from_bytes(d[0:2],'big',signed=False)
        if response != self.codes_CC.AN_ACK:
            log("Did not receive the expected answer from the camera. Firmware not upgraded.")
            return "Did not receive the expected answer from the camera. Firmware not upgraded."
        type = int.from_bytes(d[4:6],'big',signed=False)
        if type != 0x801:
            log("Answer type is not FUPCHECKSUM. Firmware not upgraded.")
            return "Answer type is not FUPCHECKSUM. Firmware not upgraded."
        chksum = int.from_bytes(d[6:10],'big',signed=False)
        if chksum!=0:
            log("Incorrect checksum. Firmware not upgraded.")
            return "Incorrect checksum. Firmware not upgraded."
        log("Checksum is ok. Upgrade is in progress. Please wait")
        time.sleep(15)

        ok = False
        for i in range(30):
            time.sleep(3)
            log("Querying camera...")
            err = self.sendCommand(self.codes_CC.OP_SENDACK,0x801.to_bytes(length=2,byteorder='big'),sendImmediately=True)
            if err!="":
                log("Failed to send query to camera")
                return "Failed to send query to camera"
            # Do not check content, only wait for an answer
            time.sleep(1)
            err,d = self.getAnswer()
            if err=="" and d!=None:
                ok = True
                break
        if not ok:
            log("Did not receive a response from the camera, firmware upgrade most probably failed")
            return "Did not receive a response from the camera, firmware upgrade most probably failed"
        else:
            log("Firmware upgrade completed, you can now restart the camera or the GUI")

        if reconnect:
            log("Closing connection to the camera")
            self.close()
            time.sleep(0.5)
            log("Reopening connection to the camera")
            self.connect(self.APDCAM_IP)
        return ""

    

# end of class controller

class APDCAM10G_packet_header_v1:
    def setData(self,d):
        self.data = d

    def serial(self):
        """
        Returns the serial number from the CC packet header
        """
        return int.from_bytes(self.data[0:4],'big') # I assume big endian, not sure

    def packetNumber(self):
        """
        Returns the packet number (packet counter) from the C&C header
        """
        return int.from_bytes(self.data[8:14],'big')

    def streamNumber(self):
        """
        Returns the stream number: a value in the range 0..3
        This is contained in the S1 bytes
        """
        S1 = int.from_bytes(self.data[4:6],'big')
        return (S1>>14)&3 

    def udpTestMode(self):
        """
        Returns the 'UDP test mode' flag from the CC header (contained in the S1 bytes)
        """

        if self.data is None:
            return None
        S1 = int.from_bytes(self.data[4:6],'big')
        return (((S1>>1)&1) > 0)

    def firstSampleFull(self):
        """
        Returns the sample start condition. If True, the first data byte in the packet is the first data byte of a sample,
        i.e. the packet boundary coincides with a sample data boundary. Otherwise a sample was split between two
        packets, and this packet is the continuation of a previous sample
        """
        S1 = int.from_bytes(self.data[4:6],'big')
        return S1&1

    def sampleCounter(self):
        """
        Returns the sample number of the first sample in the packet. It seems to have some offset,
        I am not sure it has a meaning. It seems to be removed in v1.05
        """
        return int.from_bytes(self.data[16:22],'big')



class APDCAM10G_packet_header_v2:
    def setData(self,d):
        self.data = d

    def serial(self):
        """
        Returns the serial number from the CC packet header
        """
        return int.from_bytes(self.data[0:4],'big') # I assume big endian, not sure

    def packetNumber(self):
        """
        Returns the packet number (packet counter) from the C&C header
        """
        return int.from_bytes(self.data[8:14],'big')

    def streamNumber(self):
        """
        Returns the stream number: a value in the range 0..3
        This is contained in the S1 bytes
        """
        S1 = int.from_bytes(self.data[4:6],'big')
        return (S1>>14)&3 

    def udpTestMode(self):
        """
        Returns the 'UDP test mode' flag from the CC header (contained in the S1 bytes)
        """

        if self.data is None:
            return None
        S1 = int.from_bytes(self.data[4:6],'big')
        return (((S1>>1)&1) > 0)

    def firstSampleFull(self):
        """
        Returns the sample start condition. If True, the first data byte in the packet is the first data byte of a sample,
        i.e. the packet boundary coincides with a sample data boundary. Otherwise a sample was split between two
        packets, and this packet is the continuation of a previous sample
        """
        S2 = int.from_bytes(self.data[16:18],'big')
        return (S2>>13)&1  # I am not sure, must check!

    def burstCounter(self):
        return int.from_bytes(self.data[6:8],'big')

    def dataBytes(self):
        return int.from_bytes(self.data[18:20],'big')

    def triggerLocation(self):
        """
        If there was (a) triggered sample(s) in the packet, it returns the start byte's offset of the
        first triggered sample *in the data bytes*, i.e. excluding the CC header.
        If there are no triggered samples, it returns None
        """
        tl = int.from_bytes(self.data[20:22],'big')
        if tl==0:
            return None
        return tl-22 # subtract the length of the CC header

    def triggerStatus(self):
        R = int.from_bytes(self.data[14:16],'big')
        return (R>>8)&255

    def adcStreamMode(self):
        S2 = int.from_bytes(self.data[16:18],'big')
        return (S2>>14)&3

    def triggerEdgeType(self):
        """
        Returns a flag indicating whether the trigger edge was rising (0) or falling (1)
        """
        S2 = int.from_bytes(self.data[16:18],'big')
        return (S2>>12)&1

    def dualSataMode(self):
        """
        Returns a flag indicating dual SATA mode
        """
        S2 = int.from_bytes(self.data[16:18],'big')
        return (S2>>11)&1
    
    def burstStart(self):
        """
        Returns a flag indicating whether a burst is started
        """
        S2 = int.from_bytes(self.data[16:18],'big')
        return (S2>>10)&1

    

class APDCAM10G_packet:
    """
    A utility class to convert the bytes of the C&C header (22 bytes) to
    variables

    Parameters
    ^^^^^^^^^^
    h - bytearray(22), the 22 bytes of the C&C header in the UDP packets
    
    error - string, error message
    
    """

    def __init__(self,header,data=None,error=""):
        """
        Parameters:
        ^^^^^^^^^^^
        header - an interpreter class instance to decode the information in the C&C header of the UDP packet.
                 Either an APDCAM10G_packet_header_v1 or APDCAM10G_packet_header_v2 object
        data   - The byte array (including the C&C header) of the UDP packet
        """
        self.time_ = "--" 
        self.header = header
        # Set the 'data' variable of the header as well so that we do not need to give it as an argument
        # when evaluating info from the C&C header
        self.header.setData(data)
        self.data = None
        if data is not None:
            self.setData(data,error)

    def received(self):
        """
        Returns True if the packet has been received, False otherwise
        """
        return self.data is not None

    def setData(self,data,error=""):
        """
        Set the packet content (including the 22-byte CC board header and the subsequent ADC data
        """

        # keep time when the class was initialized (approx. the time when the packet was received)
        self.time_ = time.time()
        self.error_ = error
        self.data = data
        self.header.setData(data)

    def getAdcData(self):
        return self.data[22:]

    def error(self):
        return self.error_

    def time(self):
        return self.time_



class APDCAM10G_data:
    """ 
    This class is for measuring APDCAM-10G data.
    Created and instance and keep and call the startReceiveAnswer() method
    before reading/writing registers, this starts the UDP packet read.
    When the instance is deleted the UDP read is stopped and registers
    cannot be read/written any more.
    """ 
    RECEIVE_PORTS = [10000, 10001, 10002, 10003] # these are the receiving ports
    IPV4_HEADER = 20
    UDP_HEADER = 8
    CC_STREAMHEADER = 22
                
    def __init__(self,APDCAM,logger=Terminal()):
        """
        Constructor for an APDCAM10G.data object. 

        Parameters
        ^^^^^^^^^^
        APDCAM : controller
            The communication class for the camera. 
            It does not need to be connected at the time of construction of the
            APDCAM10G.data class.

        """
        self.logger = logger
        if (type(APDCAM) is not APDCAM10G_control):
            raise TypeError("An APDCAM10G_control class is expected as input to APDCAM10G.data")
        self.APDCAM = APDCAM
        self.receiveSockets = [None]*4
        self.MTU = None
        self.hostMac = None
        self.hostIP = None
        self.streamTimeout = 10000 # ms
        
    def __del__(self):
        """
        Destructor for class. CLoses all receive sockets.

        Returns
        -------
        None.

        """
        for i in range(4) :
            if self.receiveSockets[i] != None :
                self.receiveSockets[i].close()
            
    def allocate(self,channel_masks=[0xffffffff,0xffffffff,0xffffffff,0xffffffff],sample_number=100000,bits=14):
        self.logger.showMessage("Bits: " + str(bits))
        if (self.MTU is None):
            raise ValueError("Network parameters should be determined before calling allocate.")
        self.sample_number = sample_number
        self.channel_masks = [[[0]*8]*4]*4  # self.channel_masks[i_adc=0..3][i_chip=0..3][i_channel=0..7]
        self.bits = bits
        self.bytes_per_sample     = [0]        *len(self.APDCAM.status.ADC_address)
        self.chip_bits_per_sample  = [[0,0,0,0]]*len(self.APDCAM.status.ADC_address)
        self.chip_bytes_per_sample = [[0,0,0,0]]*len(self.APDCAM.status.ADC_address)
        self.packets = [None] * len(self.APDCAM.status.ADC_address)      # we collect packets associated with ADCs
        for i_adc in range(len(self.APDCAM.status.ADC_address)):
            print("ALLOCATING MEMORY FOR ADC " + str(i_adc+1))
            self.logger.showMessage("ADC BOARD: " + str(i_adc+1))
            for i_chip in range(4):
                for i_channel in range(8):
                    self.channel_masks[i_adc][i_chip][i_channel] = (channel_masks[i_adc]>>(i_chip*8+(7-i_channel))) & 1
                #chip_chmask = (channel_masks[i_adc] >> i_chip * 8) % 256
                #self.logger.showMessage("   Chip " + str(i_chip) + " mask: " + str(chip_chmask))

                self.chip_bits_per_sample[i_adc][i_chip] = bits*sum(self.channel_masks[i_adc][i_chip])

                self.logger.showMessage("   Chip bits per sample: " + str(self.chip_bits_per_sample[i_adc][i_chip]))
                # Each chip's data is rounded up to full bytes
                self.chip_bytes_per_sample[i_adc][i_chip] = self.chip_bits_per_sample[i_adc][i_chip] // 8
                if ((self.chip_bits_per_sample[i_adc][i_chip] % 8) != 0):
                    self.chip_bytes_per_sample[i_adc][i_chip] += 1

                # accumulate the number of bytes of this chip to the total
                self.bytes_per_sample[i_adc] += self.chip_bytes_per_sample[i_adc][i_chip]

            # An ADC board's data is rounded up to integer multiples of 32 bits

            if ((self.bytes_per_sample[i_adc] * 8) % 32 != 0):
                # Attention, attention! Here in the original code there was a simple division by 8:
                # self.bytes_per_sample[i_adc] = ((self.bytes_per_sample[i_adc] * 8) // 32 + 1) * 32 / 8
                # this unfortunately produces a floating point number, even if the number to be divided
                # is an integer multiple of 8. Must use integer division !!!
                self.bytes_per_sample[i_adc] = ((self.bytes_per_sample[i_adc] * 8) // 32 + 1) * 32 // 8

            #Calculate the number of packets
            packets_per_adc = (self.bytes_per_sample[i_adc] * self.sample_number) // (self.octet * 8) 
            if (self.bytes_per_sample[i_adc] * self.sample_number) % (self.octet * 8) != 0:
                packets_per_adc += 1

            # pre-allocate the number of packets for each ADC board. We do not store the number of packets per adc
            # for each ADC board in a separate variable, the length of the pre-allocated packet list, len(self.packets[i_adc])
            # can be used for that
            print("  Packets per adc: " + str(packets_per_adc))
            self.packets[i_adc] = [None]*packets_per_adc
            firstSampleNumber = 0
            firstSampleStartByte = 0
            for i_packet in range(packets_per_adc):
                print("    Allocating a packet...")
                self.packets[i_adc][i_packet] = APDCAM10G_packet(header=self.APDCAM.udpPacketHeader())
            
                self.packets[i_adc][i_packet].plannedFirstSampleNumber = firstSampleNumber
                self.packets[i_adc][i_packet].plannedFirstSampleStartByte = firstSampleStartByte

                # number of the bytes of the first (potentially fractional) sample
                firstSampleBytes = self.bytes_per_sample[i_adc] - firstSampleStartByte

                # Number of bytes available for further samples
                remainingBytes = self.octet*8 - firstSampleBytes

                # Number of full samples fitting into the remaining bytes
                nFullSamples = remainingBytes//self.bytes_per_sample[i_adc]

                # assume a full last sample fitting into the packet
                self.packets[i_adc][i_packet].plannedLastSampleNumber = firstSampleNumber + nFullSamples
                self.packets[i_adc][i_packet].plannedLastSampleStopByte = self.bytes_per_sample[i_adc]
                firstSampleNumber = self.packets[i_adc][i_packet].plannedLastSampleNumber + 1
                firstSampleStartByte = 0

                # If not, update
                if remainingBytes%self.bytes_per_sample[i_adc] != 0:
                    self.packets[i_adc][i_packet].plannedLastSampleNumber += 1
                    self.packets[i_adc][i_packet].plannedLastSampleStopByte = remainingBytes - nFullSamples*self.bytes_per_sample[i_adc]  # also the number of bytes of the last sample
                    firstSampleNumber = self.packets[i_adc][i_packet].plannedLastSampleNumber
                    firstSampleStartByte =  self.packets[i_adc][i_packet].plannedLastSampleStopByte
                print("    DONE")

        self.APDCAM.setSampleNumber(sampleNumber=sample_number)
        
# 		map_locked = MAP_LOCKED;

#             d *addr = mmap(NULL, m_BufferSize, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE | map_locked /*| MAP_HUGETLB*/, -1, 0);

#             (addr == MAP_FAILED)

        
        return ""
        
    def get_net_parameters(self):
        """
        Determine parameters of the network and host. The network name is assumed to be
        known in self.APDCAM.interface. See self.APDCAM.getInterface(). Puts the results into
        self.MTU, self.hostMac, self.hostIP. 

        Returns
        -------
        str:
            "" or error code.

        """
     
        
        def getParaFromLine(line,parameter):
            """
            Get the value of a parameter from the text line. It is
            expected that the paramter value follows the parameter name sperated
            by whitespace.

            Parameters
            ----------
            line : str
                The text line.
            parameter : str
                The parameter name.

            Returns
            -------
            para_val : str
                The parameter value.

            """
            para_val = None
            line_lower = line.lower()
            ind = line_lower.find(parameter.lower())
            if (ind >= 0):
                l_split = line_lower.split()
                para_ind = -1
                for i,t in enumerate(l_split):
                    if (t == parameter):
                        para_ind = i + 1
                        break
                if ((para_ind <= len(l_split) - 1) and (para_ind > 0)):
                    para_val = l_split[para_ind]
            return para_val
   
        if (self.APDCAM.interface is None):
            ret = self.APDCAM.getInterface()
            if (ret != ""):
                return ret
        mtu = None
        mac = None
        IP = None
        cmd = "ip link show " + self.APDCAM.interface.decode('ascii')
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE) 
        d.stdout = ""
        if (len(d.stdout) != 0):
            txt = d.stdout
            txt_lines = txt.split(b'\n')
            for l in txt_lines:
                mtu = getParaFromLine(l.decode('ascii'),'mtu')
                if (mtu is not None):
                    break
            for l in txt_lines:
                mac = getParaFromLine(l.decode('ascii'),'link/ether')
                if (mac is not None):
                    break
            if (mtu is not None):
                self.MTU = int(mtu)
            if (mac is not None):
                mac_split = mac.split(':')
                self.hostMac = [int(num,base=16) for num in mac_split]
        cmd = "ip -o address show " + self.APDCAM.interface.decode('ascii')
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
        d.stdout = ""
        if (len(d.stdout) != 0):
            txt = d.stdout
            txt_lines = txt.split(b'\n')
            for l in txt_lines:
                IP = getParaFromLine(l.decode('ascii'),'inet')
                if (IP is not None):
                    self.hostIP = IP.split('/')[0]
                    break
        if ((mtu is None) or (mac is None) or (IP is None)):
            cmd = "ifconfig " + self.APDCAM.interface.decode('ascii')
            d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
            if (len(d.stdout) != 0):
                txt = d.stdout
                txt_lines = txt.split(b'\n')
                for l in txt_lines:
                    if (mtu is None):
                        mtu = getParaFromLine(l.decode('ascii'),'mtu')
                        if (mtu is not None):
                            self.MTU = int(mtu)
                    if (IP is None):
                        IP = getParaFromLine(l.decode('ascii'),'inet')
                        if (IP is not None):
                            self.hostIP = IP
                    if (mac is None):
                        mac = getParaFromLine(l.decode('ascii'),'ether')
                        if (mac is not None):
                            mac_split = mac.split(':')
                            self.hostMac = [int(num,base=16) for num in mac_split]
                    if ((mac is not None) and (IP is not None) and (mtu is not None)):
                        break
        if ((mac is None) or (IP is None) or (mtu is None)):
            return "Cannot determine all host network parameters, neither with ip, nor with ifconfig."
        self.logger.showMessage("[MEASUREMENT] MAC: " + str(self.hostMac))
        self.logger.showMessage("[MEASUREMENT] MTU: " + str(self.MTU))
        self.logger.showMessage("[MEASUREMENT] IP : " + str(self.hostIP))

        self.set_octet()
        return ""    
       
    def set_octet(self):
        """
        Calculates the octet setting for camera data communication and saves it in 
        self.octet.

        Parameters
        ----------
        MTU : int
            The network interface MTU.

        Returns
        -------
        str:
            "" or rrror code.

        """
        if (self.MTU is None):
            ret = self.get_net_parameters()
            if (ret != ""):
                return ret
        max_adc_data_length = self.MTU-\
                            (self.IPV4_HEADER+self.UDP_HEADER+self.CC_STREAMHEADER)
        self.octet = max_adc_data_length//8
        if (self.octet < 1):
            return "too small MTU, cannot transfer data."
        return ""
        
    def stop_receive(self):
        """
        Stops data receive on the sockets and closes the sockets.

        Returns
        -------
        None.

        """
        
        # Delete sockets
        for i in range(4) :
            if (self.receiveSockets[i] != None):
               self.receiveSockets[i].close()
               self.receiveSockets[i] = None
               
        
    def start_receive(self):
        """
        Creates the data receive sockets and start to receive data on them.
        Sets up addresses and other parameters in the camera.
        Does not start the data streams in the camera.

        Parameters
        ----------
        None
        
        Returns
        -------
        str:
            "" or error message.
        """
        
        # Create a clear situation with all sockets closed
        self.stop_receive()
        
        # True means the stream will be active
        self.streamActive = [False]*4         # True/False indicating whether the given stream is active
        self.streamAdc  = [0]*4               # The ADC number this stream is associated with
        self.streamLastPacketNumber = [-1]*4  # Latest received packet number in the given stream
        self.streamErrors = [""]*4

        if self.APDCAM.dualSATA:
            if len(self.APDCAM.status.ADC_address)>2:
                return "Dual SATA is set but more than 2 ADC boards are present"
            for i in range(len(self.APDCAM.status.ADC_address)):
                self.streamActive[i*2] = True   
                self.streamAdc   [i*2] = i
        else:
            for i in range(len(self.APDCAM.status.ADC_address)):
                self.streamActive[i] = True   
                self.streamAdc   [i] = i

        for i in range(4) :
            if (self.streamActive[i] == True) :
                try:
                    print("Opening socket " + str(i))
                    self.receiveSockets[i] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                except socket.error as se:
                    print("Failed to open socket")
                    return se.args[1]

                try:
                    print("Binding socket " + str(i) + " to port " + str(self.RECEIVE_PORTS[i]))
                    self.receiveSockets[i].bind(('', self.RECEIVE_PORTS[i]))
                    print("Success")
                except socket.error as se :
                    print("Failed")
                    return str(se.args[1])
                
                self.receiveSockets[i].setblocking(False) # Non-blocking mode
                self.receiveSockets[i].settimeout(2)
                UDP_data = bytearray(15)
                UDP_data[0] = i+1
                UDP_data[1] = self.octet // 256
                UDP_data[2] = self.octet % 256
                # The address where to send data
                UDP_data[3] = self.hostMac[0]
                UDP_data[4] = self.hostMac[1]
                UDP_data[5] = self.hostMac[2]
                UDP_data[6] = self.hostMac[3]
                UDP_data[7] = self.hostMac[4]
                UDP_data[8] = self.hostMac[5]
                d = socket.inet_aton(self.hostIP)
                UDP_data[9] = d[0]
                UDP_data[10] = d[1]
                UDP_data[11] = d[2]
                UDP_data[12] = d[3]
                UDP_data[13] = self.RECEIVE_PORTS[i] // 256
                UDP_data[14] = self.RECEIVE_PORTS[i] % 256
                err = self.APDCAM.sendCommand(self.APDCAM.codes_CC.OP_SETUDPSTREAM,UDP_data,sendImmediately=True)
                if (err != ""):
                    return err
        return ""
     
    def start_stream(self, streamMode=None):
        """
        Starts the data streams in APDCAM.

        Parameters
        ----------
        streamMode : string
            'Continuous', 'Gated' or 'Triggered' (case-insensitive)
        
        Returns
        -------
        str:
            "" or error message.

        """

        print("--> start_stream")

        # if streamMode is given (version >=1.05) then first set all ADCs to OFF mode, so that the streams
        # are first enabled, waiting for the BURST_START issued by the ADC cards when they are set to any of the transmitting modes
#        if streamMode is not None:
#            print("Setting ADC stream modes to OFF")
#            self.APDCAM.setAdcStreamMode('all','off')

        self.stop_stream()
        
        strcontrol = bytearray([0])       
        for i in range(4) :
            if (self.streamActive[i]) :
                # this line was strcontrol[0] |= 2<<i which is clearly a bug. How did it work at all before? Did it? when was this bug introduced?
                strcontrol[0] |= 1<<i
        self.stream_start_time_1 = time.time()

        print("strcontrol = " + str(bin(strcontrol[0])))

        err = self.APDCAM.sendCommand(self.APDCAM.codes_CC.OP_SETSTREAMCONTROL,strcontrol,sendImmediately=True,waitAfter=None)
        self.stream_start_time_2 = time.time()
        if err != "":
            return err

        # now, if streamMode is given (i.e. FW>=1.05, where ADC boards have different stream modes), then set them
        if streamMode is not None:
            err = self.APDCAM.setAdcStreamMode('all',streamMode)
        if err != "":
            return err

        return ""
    
    def stop_stream(self):
        """
        Stop streams
    
        Returns
        -------
        str:
            "" or error message.
        str:
            "" or warning

        """

        print("--> stop_stream")

        # for firmware version >=1.05 the ADC stream mode needs to be set to 'Off' as well
        if self.APDCAM.version >= 105:
            print("Setting all ADC stream modes to OFF")
            self.APDCAM.setAdcStreamMode('all','off')

        # disable all streams
        return self.APDCAM.sendCommand(self.APDCAM.codes_CC.OP_SETSTREAMCONTROL,bytes([0]),sendImmediately=True)

    def get_data(self,onProgress=None):
        """
        Get UDP data from a stream.

        Parameters
        ----------
        streamNo : int
            The stream number (0...3).

        onProgress : see the documentation of APDCAM10G_control.measure

        Returns
        -------
        str:
            "" or error message.

        """

        print("--> get data")

        packet_size = self.CC_STREAMHEADER + self.octet * 8
        streamRunning = self.streamActive
        # Loop until we get the expected number of packets, or the streams fail, or another thread sets the stopMeasurement flag
        while ((streamRunning[0] or streamRunning[1] or streamRunning[2] or streamRunning[3]) ):

            # if onProgress was specified, call it. It can inform the calling thread about the progress, it can process
            # Qt events (if this backend is used in a Qt environment), and it will return a true/false flag
            # indicating whether data acquisition should be continued
            print("STREAM read loop")
            if onProgress is not None:
                if not onProgress(0,"no message yet"):
                    break

            for i_stream in range(4):
                # skip those streams which are not sending data, or which have completed or failed
                if not self.streamActive[i_stream] or not streamRunning[i_stream]:
                    continue;

                print("       Checking stream: " + str(i_stream))

                try:
                    print("      now calling recv")
                    error = ""
                    print(self.receiveSockets[i_stream].gettimeout())
                    data = self.receiveSockets[i_stream].recv(packet_size)
                    print("      received socket with length: " + str(len(data)))
                    if (len(data) == 0):
                        continue
                    if (len(data) != packet_size):
                        self.streamErrors[i_stream] += "Data size is not equal to packet size.\n"

                    # This is the same in both V1.03 and V1.05, but it would be more elegant to decode it by the
                    # data header class implemented for the specific firmware version
                    packetNumber = int.from_bytes(data[8:14],'big')

                    print("      packet number: " + str(packetNumber))

                    # Check for monotonic increase of packet number obtained from the CC header. If non-monotonic, print
                    # error message and stop reading from this stream
                    if packetNumber <= self.streamLastPacketNumber[i_stream]:
                        self.streamErrors[i_stream] += "Non-monotonic packet number in stream " + str(i_stream) + "\n"
                        streamRunning[i_stream] = False
                        continue

                    # remember that we store the packets for each ADC and not for the streams. So get the ADC number
                    # corresponding to this stream. Python copies by reference
                    packets = self.packets[self.streamAdc[i_stream]]

                    # Check if a too high packet number arrived in the CC header. This would over-index the packets array,
                    # and is considered a fatal error, so stop the stream
                    if packetNumber >= len(packets):
                        self.streamErrors[i_stream] += "A packet with out-of-range number " + str(packetNumber) + " is received\n"
                        self.streamRunning[i_stream] = False
                        continue

                    # We have anyway preallocated the expected number of packet headers, so
                    # store every packet header at the right index, corresponding to the packet number
                    # If a packet is lost, the corresponding entry in the list 'self.packets' will remain None
                    packets[packetNumber].setData(data,error)
                    self.streamLastPacketNumber[i_stream] = packetNumber

                    # If we reached the expected (=pre-allocated) number of packets, stop the stream
                    if packetNumber == len(packets)-1:
                        streamRunning[i_stream] = False

                # and finally if we fail to read from the stream, mark it as stopped
                except socket.error as se :
                    print("Socket error occurred while retrieving data from stream %i: %s" % (i_stream,se))
                    #return "Socket error occurred while retrieving data from stream " + str(i_stream) + ": " se, "", None
                    streamRunning[i_stream] = False

        for i_stream in range(4):
            if (self.streamActive[i_stream]):
                with open("UDPtimes_ADC{:d}.dat".format(self.streamAdc[i_stream]),"wt") as f:
                    f.writelines("{:f}-{:f}\n".format(self.stream_start_time_1,self.stream_start_time_2))
                    for p in self.packets[self.streamAdc[i_stream]]:
                        if p is None:
                            continue
                        f.writelines("{:d}...{:f}...{:d}\n".format(i_stream+1,p.time(),p.packetNumber()))
        return "",""     

    def get_channel_data(self,adc_board,channel):
        """
        Skip the trailing missing packages and those which start with a non-full sample. Start interpreting
        the channel signal from the first received packages which contains a full starting sample.

        Parameters:
        ^^^^^^^^^^^
        adc_board - integer (1..4)
            The ADC board number
        channel - integer (1..32)
            The channel number within the ADC board

        """

        if adc_board<1 or channel<1:
            print("Bad adc_board or channel value")
            return None

        adc_board -= 1
        channel -= 1

        # Deduce the chip number (0..3 inclusive) from the channel number
        chip = channel//8

        if (adc_board<0 or len(self.APDCAM.status.ADC_address)<=adc_board):
            return None

        # skip non-received packets at the beginning and also those which do not start at a full sample. The CC packet header unfortunately
        # does not contain info about which byte a non-full sample is starting at so we need to skip these.
        i_packet = 0
        while i_packet<len(self.packets[adc_board]) and ( not self.packets[adc_board][i_packet].received() or not self.packets[adc_board][i_packet].header.firstSampleFull() ):
            i_packet = i_packet+1

        if i_packet >= len(self.packets[adc_board]):
            return None

        # now, self.packets[adc_board][i_packet] starts at a full sample. Start casting the series of bytes into channel signals

        # The values of a given channel (uninterrupted sequence)
        channel_signals = []
        
        adc_data = self.packets[adc_board][i_packet].getAdcData()

        i_data = 0   # index within the ADC data

        # now loop over the (continuously) received packets. Stop at an unreceived packet, because then
        # we loose track.
        while True:
            sample_data = None
            # if an entire sample does not fit into this packet
            if i_data+self.bytes_per_sample[adc_board] > len(adc_data):
                # if there is no next packet, or it was not received, break. We check before getting the sample data, because
                # we do not want to handle a partial sample (even if it contained the given channel we are looking for)
                if  i_packet+1>=len(self.packets[adc_board]) or not self.packets[adc_board][i_packet+1].received() :
                    break
                # If we are here, there is a next package which was received. Take frirst all remaining bytes from this packet
                sample_data = adc_data[i_data:]
                # Switch to the next packet
                i_packet += 1
                adc_data = self.packets[adc_board][i_packet].get_adc_data()  # Shouldn't it be getAdcData ?
                # Calculate the number of bytes missing from previous packet for this sample. 'n' is used for better clarity:
                n = self.bytes_per_sample[adc_board]-len(sample_data)  
                # append this many bytes to the sample data
                sample_data += adc_data[0:n]
                # and set the index within the ADC data to past the processed bytes
                i_data = n
            else:
                sample_data = adc_data[i_data:i_data+self.bytes_per_sample[adc_board]]
                i_data += self.bytes_per_sample[adc_board]

                # if we reached the end of the packet, go to the next one
                if i_data >= len(adc_data):
                    i_packet += 1
                    # if there is no next one, or it was not received, break. Note that sample_data has already been set so we
                    # will take this into account
                    if i_packet >= len(self.packets[adc_board]) or not self.packets[adc_board][i_packet].received():
                        break
                    # and reset the ADC data index to the beginning
                    i_data = 0

            # an index to the starting byte of the given chip
            chip_start = 0

            # increment the chip start index by all previous chip bytes
            for c in range(chip):
                chip_start += self.chip_bytes_per_sample[adc_board][c]

            chip_data = sample_data[chip_start:chip_start+self.chip_bytes_per_sample[adc_board][chip]]

            def get_bit(data, num):
                base = int(num // 8)
                shift = int(num % 8)
                return (data[base] >> (7-shift)) & 0x1

            channel_of_chip = channel%8
            # The starting bit index of the given channel. Check how many preceding channels are enabled. 
            channel_start = sum(self.channel_masks[adc_board][chip][0:channel_of_chip])*self.bits

            value = 0
            for bit in range(self.bits):
                if get_bit(chip_data,channel_start+bit):
                    value |= (1<<(self.bits-1-bit))

            channel_signals.append(value)

        return channel_signals

    
