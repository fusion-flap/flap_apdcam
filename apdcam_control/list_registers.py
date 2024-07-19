# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 15:59:20 2024

@author: Zoletnik
"""

import flap_apdcam.apdcam_control as ap

def list_registers(file='dump.txt',card='CC'):
    """
    List the register contents for a card in APDCAM.

    Parameters
    ----------
    file : string,optional
        Name of a text file containing the dump of register content. The default is 'dump.txt'.
    card : sting, optional
        The card:'CC', 'ADC8', 'ADC9', 'ADC10', ADC11', 'Control'. The default is 'CC'.

    Returns
    -------
    None.

    """
    
    with open(file, "rt") as f:
        lines = f.readlines()
        if (card[:3] == 'ADC'):
            address = int(card[3:])
            search_text = 'READ result, Address: {:1d}, subaddress: 0, data:'.format(address)
        elif (card == 'Control'):
            search_text = 'READ result, Address: 2, subaddress: 0, data:'
        elif (card == 'CC'):
            search_text = 'C&C REGISTER VALUES:'
        else:
            raise ValueError("Unknown card. Valid: 'CC', 'ADC8', 'ADC9', 'ADC10', ADC11', 'Control'")
        for i in range(len(lines)):
            if (lines[i][:len(search_text)] == search_text):
                break
        else:
            raise ValueError("Invalid file, cannot find start of data.")
            
        if (card[:3] == 'ADC'):
            regs = []
            l = lines[i][len(search_text):]
            while True:
                data = l.split()
                for d in data:
                    try:
                        regs.append(int(d))
                    except ValueError:
                        break
                if (i < len(lines) - 1):
                    i += 1
                    l = lines[i]
                else:
                    break
            codes = ap.APDCAM10G_ADCcodes_v1()
            print("Card registers:")
            print("MC version {:d}.{:d}".format(regs[codes.ADC_REG_MC_VERSION],regs[codes.ADC_REG_MC_VERSION + 1]))
            print("FPGA version {:d}.{:d}".format(regs[codes.ADC_REG_FPGA_VERSION],regs[codes.ADC_REG_FPGA_VERSION + 1]))
            print("Serial No: {:d}".format(regs[3] + 256 * regs[4]))
            print("DVDD33 {:f} V".format((regs[codes.ADC_REG_DVDD33] + 256 * regs[codes.ADC_REG_DVDD33 + 1]) / 1000))
            print("DVDD25 {:f} V".format((regs[codes.ADC_REG_DVDD25] + 256 * regs[codes.ADC_REG_DVDD25 + 1]) / 1000))
            print("AVDD33 {:f} V".format((regs[codes.ADC_REG_AVDD33] + 256 * regs[codes.ADC_REG_AVDD33 + 1]) / 1000))
            print("AVDD18 {:f} V".format((regs[codes.ADC_REG_AVDD18] + 256 * regs[codes.ADC_REG_AVDD18 + 1]) / 1000))
            print("Board temperature: {:d} C".format(regs[codes.ADC_REG_TEMP]))
            print("Control:")
            print("  SATA on/off: {:1d}".format(regs[codes.ADC_REG_CONTROL] % 2))
            print("  DUAL SATA mode: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 2) % 2))
            print("  SATA sync: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 4) % 2))
            print("  Test mode: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 8) % 2))
            print("  Filter on/off: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 16) % 2))
            print("  Max trigger EN: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 32) % 2))
            print("  Reverse bitorder: {:1d}".format((regs[codes.ADC_REG_CONTROL] // 64) % 2))
            print("Status:")
            print("  Basic PLL locked: {:1d}".format(regs[codes.ADC_REG_STATUS1] % 2))
            print("  Max trigger: {:1d}".format(regs[codes.ADC_REG_STATUS2] % 2))
            print("  Overload: {:1d}".format((regs[codes.ADC_REG_STATUS2] // 2) % 2))
            print("  SATA1 data out LED: {:1d}".format((regs[codes.ADC_REG_STATUS2] // 4) % 2))
            print("  SATA2 data out LED: {:1d}".format((regs[codes.ADC_REG_STATUS2] // 8) % 2))
            chen = ""
            for ib in range(4):
                chen += "{:08b} ".format(regs[codes.ADC_REG_CHENABLE1 + ib])
            print("Ch. Enable: {:s}".format(chen))
            if (regs[codes.ADC_REG_RESOLUTION] == 0):
                res = "14"
            elif (regs[codes.ADC_REG_RESOLUTION] == 1):
                res = "12"
            elif (regs[codes.ADC_REG_RESOLUTION] == 2):
                res = "8"
            else:
                res = "Invalid"
            print("Ring buffer size: {:d}".format((regs[codes.ADC_REG_RINGBUFSIZE ] + 256 * regs[codes.ADC_REG_RINGBUFSIZE  + 1])))
            for ib in range(4):
                print("BPSCH{:1d}: {:d}".format(ib + 1,regs[codes.ADC_REG_BPSCH1 + ib]))
            print("SATAWORDS: {:d}".format(regs[0x21]))
            print("ERRORCODE: {:d}".format(regs[codes.ADC_REG_ERRORCODE]))
            print("RESETFACTORY: {:02x}".format(regs[codes.ADC_REG_RESET]))
            t = ""
            for ib in range(4):
                t += "{:d} ".format(regs[codes.ADC_REG_AD1TESTMODE + ib])
            print("ADC test modes: " + t)
            
        elif (card[:3] == 'CC'):
             acktype = int(lines[i + 1][len("  Acktype:"):])
             start_address = int(lines[i + 2][len("  Start address: :"):])
             l = lines[i + 3][len("  Values:"):]
             regs = []
             while True:
                 data = l.split()
                 for d in data:
                     try:
                         regs.append(int(d))
                     except ValueError:
                         break
                 if (i < len(lines) - 1):
                     i += 1
                     l = lines[i]
                 else:
                     break
             
             codes = ap.APDCAM10G_codes_v1()
             if (acktype == 3):
                 add = ""
                 for ib in range(4):
                     add += "{:d}".format(regs[13 - 7 + 7 - start_address + ib])
                     if (ib != 3):
                         add += "."
                 print("Management port IPv4 address: "+add)
                 print("Board temperature: {:d} C".format(regs[codes.CC_REGISTER_BOARDTEMP + 7 - start_address]))
                 print("VDD33 {:4.2f} V".format((regs[codes.CC_REGISTER_33V + 7 - start_address] + 256 * regs[codes.CC_REGISTER_33V + 7 - start_address + 1]) / 1000))
                 print("VDD25 {:4.2f} V".format((regs[codes.CC_REGISTER_25V + 7 - start_address] + 256 * regs[codes.CC_REGISTER_25V + 7 - start_address + 1]) / 1000))
                 print("VDD18 {:4.2f} V".format((regs[codes.CC_REGISTER_12VXC + 7 - start_address] + 256 * regs[codes.CC_REGISTER_12VXC + 7 - start_address + 1]) / 1000)) 
                 print("VDD12 {:4.2f} V".format((regs[codes.CC_REGISTER_12VST + 7 - start_address] + 256 * regs[codes.CC_REGISTER_12VST + 7 - start_address + 1]) / 1000)) 
                 for ib in range(3):
                     counter = 0
                     mult = 1
                     for ic in range(6):
                         counter += regs[305 - 7 + 7 - start_address + ic + ib * 6] * mult
                         mult *= 256 
                     print("Stream #{:1d} sample counter: {:d}".format(ib + 1, counter))
                 print("DSLV lock status: {:04b}".format(regs[198 - 7 + 7 - start_address]))
            
                  
            

#list_registers(file='APDTest_adc8_res.txt',card='ADC8')  
#print("-----------------------------") 
#list_registers(file='APDTest_adc9_res.txt',card='ADC9')       
#list_registers(file='APDTest_cc_res.txt',card='CC')          
        