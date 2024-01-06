import re

class APDCAM10G_register:
    def __init__(self, startByte, numberOfBytes, shortDescription, byteOrder='msb', signed=False, longDescription=''):
        """
        This class stores information about the address/length/byte-order/signed etc of (possibly multi-byte)
        registers of the CC card, PC card or ADC cards, together with short and long descriptions/explanations.

        Parameters
        ^^^^^^^^^^
        byteOrder  -- 'msb' or equivalently 'big', or 'lsb' or equivalently 'little'

        """
        self.startByte = startByte
        self.numberOfBytes = numberOfBytes
        self.shortDescription = shortDescription
        self.signed = signed
        self.longDescription = longDescription
        self.byteOrder = byteOrder.lower()
        if self.byteOrder == 'msb':
            self.byteOrder = 'big'
            self.byteOrderUncertain = False
        if self.byteOrder == 'msb?' or self.byteOrder == 'big?':
            self.byteOrder = 'big'
            self.byteOrderUncertain = True
        if self.byteOrder == 'lsb':
            self.byteOrder = 'little'
            self.byteOrderUncertain = False;
        if self.byteOrder == 'lsb?' or self.byteOrder == 'little?':
            self.byteOrder = 'little'
            self.byteOrderUncertain = True
    
    def __call__(self,data=None):
        """
        Return the value of this (possibly multi-byte) register as an integer

        Parameters
        ^^^^^^^^^^
        data  -- if None: the function returns the value of this register which has already been acquired
                 before from the camera and stored in this class instance (no reading from the camera now).
                 Does not check data validity (i.e. if it has been read at all from the camera).
                 Otherwise, 'data' must be a byte array holding the contenet of the entire register table,
                 in which the 'startByte', 'numberOfBytes' etc are interpreted
        """
        return int.from_bytes(self.bytes if data is None else data[self.startByte:self.startByte+self.numberOfBytes],signed=self.signed,byteorder=self.byteOrder)

    def store_value(self,registerBytes):
        """
        This function stores the bytes of this register in this class instance so that it is cached in memory and does not need
        to be queried from the camera at subsequent times

        Parameters:
        ^^^^^^^^^^^
        registerBytes - the bytes from the register table corresponding to this register
        """
        self.bytes = registerBytes

    def display_value(self,data):
        """
        This function must return a string representation of the value, for displaying
        """
        return "APDCAM10G_register.display_value must be overridden!"

class APDCAM10G_register_str(APDCAM10G_register):    
    def __init__(self, startByte, numberOfBytes, shortDescription, longDescription=''):
        super().__init__(startByte, numberOfBytes, shortDescription, longDescription=longDescription)

    def display_value(self,data=None):
        try:
            return (self.bytes if data is None else data[self.startByte:self.startByte+self.numberOfBytes]).decode('utf-8')
        except:
            return ">>> can not decode string <<<"

class APDCAM10G_register_int(APDCAM10G_register):
    def __init__(self, startByte, numberOfBytes, shortDescription, byteOrder='msb', signed=False, longDescription='', format='dec'):
        """
        Parameters
        ^^^^^^^^^^
        format  - string: 'dec' or 'hex'
        """
        super().__init__(startByte, numberOfBytes, shortDescription, byteOrder=byteOrder, signed=signed, longDescription=longDescription)
        self.format = format

    def display_value(self,data=None):
        v = self.__call__(data)
        return (hex(v) if self.format=='hex' else str(v))

class APDCAM10G_register_ip(APDCAM10G_register):
    def __init__(self, startByte, shortDescription, longDescription=''):
        super().__init__(startByte, 4, shortDescription, byteOrder='msb', signed=False, longDescription=longDescription)

    def display_value(self,data=None):
        result = ""
        for i in range(4):
            if i>0:
                result += "."
            result += str(int.from_bytes(self.bytes[i:i+1] if data is None else data[self.startByte+i:self.startByte+i+1]))
        return result
        
class APDCAM10G_register_mac(APDCAM10G_register):
    def __init__(self, startByte, shortDescription, longDescription=''):
        super().__init__(startByte, 6, shortDescription, byteOrder='msb', signed=False, longDescription=longDescription)

    def display_value(self,data=None):
        result = ""
        for i in range(6):
            if i>0:
                result += ":"
            result += hex(self.bytes[i] if data is None else data[self.startByte+i])[2:]
        return result

class APDCAM10G_register_bits(APDCAM10G_register):
    class Bits:
        def __init__(self, parent, symbol, firstBit, lastBit, description='',format='dec'):
            self.parent = parent
            self.symbol = symbol
            self.firstBit = firstBit
            self.lastBit = lastBit
            self.description = description
            self.nBits = lastBit-firstBit+1
            self.mask = 2**self.nBits-1   # mask when the bit(group) is already shifted to bit0
            self.format = format

        def __call__(self, data=None):
            """
            Returns the value of the bit (or group of bits) as an integer.

            Parameters:
            ^^^^^^^^^^^
            data - a byte array holding the entire register table of the given board. If None, the parent register (APDCAM10G_register object)
                   must have been set to store the corresponding bytes locally
            """
            int_value = int.from_bytes(self.parent.bytes if data is None else data[self.parent.startByte:self.parent.startByte+self.parent.numberOfBytes],\
                                       signed=False,byteorder=self.parent.byteOrder)
            return (int_value>>self.firstBit)&self.mask

        def display_value(self,data=None):
            v = self.__call__(data)
            return (hex(v) if format=='hex' else str(v))

        def set(self,value):
            # Get the integer value from the byte-array stored in the parent (i.e. the register value must have already been
            # queried from the camera and set in the parent object)
            int_value = int.from_bytes(self.parent.bytes,signed=False,byteorder=self.parent.byteOrder)
            # loop over all bits of this bit-group, and set the corresponding bit in the integer representation
            for b in range(self.lastBit-self.firstBit+1):
                if (value>>b)&1:
                    int_value |= 1<<(self.firstBit+b)
                else:
                    int_value &= ~(1<<(self.firstBit+b))
            # write back the value to the parent object
            self.parent.bytes = int_value.to_bytes(len(self.parent.bytes),byteorder=self.parent.byteOrder,signed=False)

    def __init__(self, startByte, numberOfBytes, shortDescription, bits, byteOrder='msb', longDescription=''):
        """
        Parameters
        ^^^^^^^^^^
        startByte        - starting byte address in the register table
        numberOfBytes    - self-explanatory...
        shortDescription - self-explanatory...
        bits             - a list of lists. Each list element must have 3 or 4 elements: [symbol, firstBit(least-significant), lastBit(most-significant, inclusive, optional), description(optional)]
        """
        super().__init__(startByte, numberOfBytes, shortDescription, byteOrder=byteOrder, signed=False, longDescription=longDescription)
        firstBits = []
        unsortedBits = []
        for b in bits:
            symbol = b[0]
            firstBit = b[1]
            lastBit = (b[2] if len(b)>2 else b[1])
            desc = (b[3] if len(b)>3 else '')
            # propagate down a lot of info to the bits, so that they can do the same conversion (minor code duplication)
            bb = self.Bits(self, symbol, firstBit, lastBit, desc)
            firstBits.append(firstBit)
            unsortedBits.append(bb)

            # make this decoder as a symbolic attribute within the register
            match = re.match(r'([a-zA-Z_]+)\[([0-9]+)\]',symbol)
            if match is not None:
                listname = match.group(1)
                index = int(match.group(2))
                if not hasattr(self,listname):
                    setattr(self,listname,[])
                list = getattr(self,listname)
                while len(list) < index+1:
                    list.append(None)
                list[index] = bb
            else:
                setattr(self,symbol,bb)

        # a sorted array containing the bits ordered by their bit position (and not by their symbols, as
        # it would be achievable by iterating through the attributes of this object)
        self.sortedBits = [x[1] for x in sorted(zip(firstBits,unsortedBits))]
        
    def display_value(self,data):
        return "Please use the display_value function of all sub-bits"

class APDCAM10G_register_table:
    def __init__(self):
        # add an attribute 'symbol' to each register 
        for regname in dir(self):
            if regname.startswith("_") or regname.upper()!=regname:
                continue
            a = getattr(self,regname)
            if type(a) is list:
                for i in range(len(a)):
                    setattr(a[i],'symbol',regname + "[" + str(i) + "]")
            else:
                setattr(a,'symbol',regname)

    def registerNames(self):
        """
        Returns a list of register names stored in this table, sorted by address
        """
        regnames = []
        addresses = []
        for regname in dir(self):
            # skip attributes starting with _ or not being fully uppercase
            if regname.startswith("_") or regname.upper() != regname:
                continue
            r = getattr(self,regname)

            if type(r) is list:
                for i in range(len(r)):
                    if not hasattr(r[i],'startByte') or not hasattr(r[i],'numberOfBytes'):
                        continue
                    regnames.append(regname + "[" + str(i) + "]")
                    addresses.append(r[i].startByte)
            else:
                if not hasattr(r,'startByte') or not hasattr(r,'numberOfBytes'):
                    continue

                regnames.append(regname)
                addresses.append(r.startByte)

        return [x[1] for x in sorted(zip(addresses,regnames))]

    def registers(self):
        """
        Returns a list of registers stored in this table, sorted by address
        """
        registerNames = self.registerNames()
        result = []
        for registerName in registerNames:
            result.append(getattr(self,registerName))
        return result

    def size(self):
        """
        Returns the size (in bytes) of the byte array required by this register table
        """
        result = 0
        for regname in dir(self):
            # skip attributes starting with _ or not being fully uppercase
            if regname.startswith("_") or regname.upper() != regname:
                continue
            register = getattr(self,regname)
            if not hasattr(register,'startByte') or not hasattr(register,'numberOfBytes'):
                continue
            startByte = getattr(register,'startByte')
            numberOfBytes = getattr(register,'numberOfBytes')
            if startByte+numberOfBytes > result:
                result = startByte+numberOfBytes
        return result

    def filter(self,filter):

        # Create an empty register table
        result = APDCAM10G_register_table()

        registerNames = self.registerNames()
        for registerName in registerNames:
            match = re.match(r'([a-zA-Z_]+)\[([0-9]+)\]',registerName)
            if match is not None:
                listname = match.group(1)
                index = int(match.group(2))
                lll = getattr(self,listname)
                register = lll[index]
            else:
                register = getattr(self,registerName)
            if filter(register) == True:
                setattr(result,registerName,register)
        return result

class APDCAM10G_cc_settings_v1(APDCAM10G_register_table):
    """
    Settings of the CC card up to firmware version 1.03
    """

    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    def addressDisplay(self,a):
        if a<7-7+71-7:
            return str(a+7) + "-7"
        return str(a+7-71+7) + "-7+71-7"

    BOARD_VERSION  = s(7-7, 10, 'Board type')
    FIRMWARE_GROUP = s(17-7, 30-17+1, 'Firmware group')
    FIRMWARE_GROUP_VERSION = b(31-7,2,'Firmware group version',[['VL',0,7,'Version low'],['VH',8,15,'Version high']],byteOrder='msb')
    UPGRADEDATE            = b(33-7, 36-33+1,'Upgrade date',[['D',0,7,'Day'],['M',8,15,'Month'],['Y',16,31,'Year']],byteOrder='msb')
    MAN_FIRMWAREGROUP      = s(37-7,50-37+1,'Manufacturer firmware group')
    MAN_PROGRAMDATE        = b(51-7,54-51+1,'Manufacturer program date',[['D',0,7,'Day'],['M',8,15,'Month'],['Y',16,31,'Year']],byteOrder='msb')
    MAN_SERIAL             = i(55-7,58-55+1,'Manufacturer serial number',byteOrder='msb')
    MAN_TESTRESULT         = i(59-7,62-59+1,'Manufacturer test result',  byteOrder='msb')
    SETTINGS_VERSION       = i(7-7+71-7,1,'Settings version',byteOrder='msb?')
    DEV_NAME   = s(8-7+71-7,55-8+1,'Device name')
    DEV_TYPE   = i(56-7+71-7,2,'Device type',byteOrder='msb')
    DEV_SERIAL = i(58-7+71-7,4,'Device serial number',byteOrder='msb')
    COMPANY    = s(62-7+71-7,18,'Company name')
    HOST_NAME  = s(80-7+71-7,12,'Host name')
    CONFIG     = b(92-7+71-7,2,'Configuration',[['LOCK',0,0,'Device is locked']],'msb')
    USER_TEXT  = s(94-7+71-7,15,'User text')
    MANAGE_MAC = mac(135-7+71-7,'Management port static MAC address')
    MANAGE_IP  = ip(141-7+71-7,'Management port IPv4 address')
    MANAGE_IP_MASK  = ip(145-7+71-7,'Management port IPv4 network mask')
    MANAGE_MAC_MODE = i(149-7+71-7,1,'Management port MAC mode (0 - factorydefault, 1 - CW-Auto, 2 - static)')
    MANAGE_IP_MODE  = i(150-7+71-7,1,'Management port IP mode (1 - static, 2 - DHCP)')
    MANAGE_GW_MODE  = i(151-7+71-7,1,'Management port gateway mode (0 - None, 1 - static, 2 - DHCP)')
    MANAGE_GW_IP    = ip(152-7+71-7,'Management port gateway IPv4 address')
    MANAGE_ARP      = i(156-7+71-7,1,'Management port ARP (Advertisement Report Period) [s]')
    MANAGE_IGMP     = i(157-7+71-7,1,'Management port IGMP report period [s]')
    MANAGE_IP_TTL   = i(158-7+71-7,1,'Management port IPv4 Time To Live (TTL value in the IPv4 header)')
    MANAGE_MAC_DEFAULT = mac(159-7+71-7,'Management port factory default MAC address')
    STREAM_PORT_MAC    = mac(183-7+71-7,'Stream port static MAC address')
    STREAM_PORT_IP     = ip(189-7+71-7,'Stream port IPv4 address')
    STREAM_PORT_IP_MASK  = ip(193-7+71-7,'Stream port Ipv4 mask')
    STREAM_PORT_MAC_MODE = i(197-7+71-7,1,'Stream port MAC mode (0 - factory default, 1 - CW-auto, 2 - static)')
    STREAM_PORT_IP_MODE  = i(198-7+71-7,1,'Stream port IP mode (1 - static, 2 - DHCP)')
    STREAM_PORT_GW_MODE  = i(199-7+71-7,1,'Stream port gateway mode (0 - none, 1 - static, 2 - DHCP)')
    STREAM_PORT_GW_IP    = ip(200-7+71-7,'Stream port gateway IPv4 address')
    STREAM_PORT_ARP      = i(204-7+71-7,1,'Stream port ARP Advertisement Report Period (0=off) [s]')
    STREAM_PORT_IGMP     = i(205-7+71-7,1,'Stream port IGMP report period (0=off) [s]')
    STREAM_PORT_IP_TTL   = i(206-7+71-7,1,'Stream port IPv4 Time To Live (TTL value in the IPv4 header)')
    STREAM_PORT_MAC_DEFAULT = mac(207-7+71-7,'Stream port factory default MAC address')
    HTTP_PORT     = i(231-7+71-7,2,'HTTP Port','lsb')
    SMTP_PORT     = i(233-7+71-7,2,'SMTP server port','lsb')
    CLOCK_CONTROL = b(263-7+71-7,1,'Clock control (SETCLOCKCONTROL instruction)',[ ['AS',2,2,'AD clock source (0 - internal, 1 - external)'], \
                                                                                   ['AA',3,3,'External clock mode (0 - normal, 1 - auto)'], \
                                                                                   ['SS',4,4,'Sample source (0 - internal, 1 - external)'] ], byteOrder='msb' )
    CLOCK_ENABLE  = b(264-7+71-7,1,'Clock enable (SETCLOCKENABLE instruction)', [ ['CC',0,0,'Clock output of the CONTROL connector (0 - disable, 1 - enable)'], \
                                                                                  ['EC',1,1,'Clock output of the EIO connector (0 - disable, 1 - enable)'], \
                                                                                  ['CS',2,2,'Sample output of the CONTROL connector (0 - disable, 1 - enable)'], \
                                                                                  ['ES',3,3,'Sample output of the EIO connector (0 - disable, 1 - enable)'] ], byteOrder='msb' ) 
    BASE_PLL_MULT    = i(265-7+71-7,1,'Base PLL multiply value',byteOrder='msb')
    BASE_PLL_DIV0    = i(266-7+71-7,1,'Base PLL divide value 0',byteOrder='msb')
    BASE_PLL_DIV_ADC = i(267-7+71-7,1,'Base PLL divide value 1 (going to clock signal F1/ADC)',byteOrder='msb')
    BASE_PLL_DIV2    = i(268-7+71-7,1,'Base PLL divide value 2')
    BASE_PLL_DIV3    = i(269-7+71-7,1,'Base PLL divide value 3')
    EXT_DCM_MULT     = i(270-7+71-7,1,'External DCM multiply value')
    EXT_DCM_DIV      = i(271-7+71-7,1,'External DCM divide value')
    SAMPLEDIV        = i(272-7+71-7,2,'Sample divide value','msb')
    SPAREIO          = b(274-7+71-7,1,'Spare IO control',[ ['OUTVAL0',0,0,'Spare IO pin 0 output value'],\
                                                           ['OUTVAL1',1,1,'Spare IO pin 1 output value'],\
                                                           ['OUTVAL2',2,2,'Spare IO pin 2 output value'],\
                                                           ['OUTVAL3',3,3,'Spare IO pin 3 output value'] ], byteOrder='msb' )  # 4..7: direction in v2
    XFP         = b(275-7+71-7,1,'XFP',[ ['REFCLKENABLE',0,0,'XFP reference clock enable'] ] )
    SAMPLECOUNT = i(276-7+71-7,281-276+1,'Sample count','msb')
    TRIGSTATE   = b(282-7+71-7,1,'Trigger control (SETTRIGGER instruction)',[ ['ETR',0,0,'External trigger rising slope (0 - disabled, 1 - enabled)'], \
                                                                              ['ETF',1,1,'External trigger falling slope (0 - disabled, 1 - enabled)'], \
                                                                              ['IT', 2,2,'Internal trigger (0 - disabled, 1 - enabled)' ], \
                                                                              ['DT', 6,6,'Disable trigger event if streams are disabled'] ], byteOrder='msb' )
    TRIGDELAY       = i(283-7+71-7, 286-283+1,'Trigger delay',byteOrder='msb')
    SERIAL_PLL_MULT = i(287-7+71-7,1,'Serial PLL multiply value')
    SERIAL_PLL_DIV  = i(288-7+71-7,1,'Serial PLL divide value 0')
    SATACONTROL     = b(292-7+71-7,1,'SATA Control',[ ['DSM',0,0,'Dual SATA mode (0 - disabled, 1 - enabled)'] ] )
    STREAMCONTROL   = b(299-7+71-7,1,'Stream control (SETSTREAMCONTROL instruction)',[ ['EN1',0,0,'Stream 1 disabled (0) or enabled (1)'], \
                                                                                       ['EN2',1,1,'Stream 2 disabled (0) or enabled (1)'], \
                                                                                       ['EN3',2,2,'Stream 3 disabled (0) or enabled (1)'], \
                                                                                       ['EN4',3,3,'Stream 4 disabled (0) or enabled (1)'], \
                                                                                       ['TM1',4,4,'Test mode of stream 1 disabled (0) or enabled (1)'], \
                                                                                       ['TM2',5,5,'Test mode of stream 2 disabled (0) or enabled (1)'], \
                                                                                       ['TM3',6,6,'Test mode of stream 3 disabled (0) or enabled (1)'], \
                                                                                       ['TM4',7,7,'Test mode of stream 4 disabled (0) or enabled (1)'] ] )
    UDPTESTCLOCK_DIV = i(300-7+71-7,303-300+1,'UDP test clock divider value','msb')

    UDPOCTET = [APDCAM10G_register_int(311-7+71-7+j*16,2,'Stream '+str(j)+' octet','msb') for j in range(4)]
    UDPMAC   = [APDCAM10G_register_mac(313-7+71-7+j*16,'Stream '+str(j)+' MAC address') for j in range(4)]
    IP       = [APDCAM10G_register_ip (319-7+71-7+j*16,'Stream '+str(j)+' IPv4 address') for j in range(4)]
    UDPPORT  = [APDCAM10G_register_int(323-7+71-7+j*16,2,'Stream '+str(j)+' UDP port','msb') for j in range(4)]

    CAMTIMERDELAY   = [APDCAM10G_register_int(375+j*(4+2+2+4)-7+71-7,4,'CT timer '+str(j)+' delay','msb') for j in range(10)]
    CAMTIMERON      = [APDCAM10G_register_int(379+j*(4+2+2+4)-7+71-7,2,'CT timer '+str(j)+' on','msb') for j in range(10)]
    CAMTIMEROFF     = [APDCAM10G_register_int(381+j*(4+2+2+4)-7+71-7,2,'CT timer '+str(j)+' off','msb') for j in range(10)]
    CAMTIMERNPULSES = [APDCAM10G_register_int(383+j*(4+2+2+4)-7+71-7,4,'CT timer '+str(j)+' number of pulses','msb') for j in range(10)]

    CAMCONTROL  = i(495-7+71-7,2,'CAM timer control','msb')
    CAMCLKDIV   = i(497-7+71-7,2,'CAM timer clock divide value','msb')
    CAMOUTPUT   = i(499-7+71-7,2,'CAM timer output','msb')


class APDCAM10G_cc_settings_v2(APDCAM10G_register_table):
    """
    Settings of the CC card up to firmware version 1.05
    """

    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    def addressDisplay(self,a):
        if a<7-7+71-7:
            return str(a+7) + "-7"
        return str(a+7-71+7) + "-7+71-7"

    BOARD_VERSION  = s(7-7, 10, 'Board type')
    FIRMWARE_GROUP = s(17-7, 30-17+1, 'Firmware group')
    FIRMWARE_GROUP_VERSION = b(31-7,2,'Firmware group version',[['VL',0,7,'Version low'],['VH',8,15,'Version high']],byteOrder='msb')
    UPGRADEDATE            = b(33-7, 36-33+1,'Upgrade date',[['D',0,7,'Day'],['M',8,15,'Month'],['Y',16,31,'Year']],byteOrder='msb')
    MAN_FIRMWAREGROUP      = s(37-7,50-37+1,'Manufacturer firmware group')
    MAN_PROGRAMDATE        = b(51-7,54-51+1,'Manufacturer program date',[['D',0,7,'Day'],['M',8,15,'Month'],['Y',16,31,'Year']],byteOrder='msb')
    MAN_SERIAL             = i(55-7,58-55+1,'Manufacturer serial number',byteOrder='msb')
    MAN_TESTRESULT         = i(59-7,62-59+1,'Manufacturer test result',  byteOrder='msb')
    SETTINGS_VERSION       = i(7-7+71-7,1,'Settings version',byteOrder='msb?')
    DEV_NAME   = s(8-7+71-7,55-8+1,'Device name')
    DEV_TYPE   = i(56-7+71-7,2,'Device type',byteOrder='msb')
    DEV_SERIAL = i(58-7+71-7,4,'Device serial number',byteOrder='msb')
    COMPANY    = s(62-7+71-7,18,'Company name')
    HOST_NAME  = s(80-7+71-7,12,'Host name')
    CONFIG     = b(92-7+71-7,2,'Configuration',[['LOCK',0,0,'Device is locked']],'msb')
    USER_TEXT  = s(94-7+71-7,15,'User text')
    MANAGE_MAC = mac(135-7+71-7,'Management port static MAC address')
    MANAGE_IP  = ip(141-7+71-7,'Management port IPv4 address')
    MANAGE_IP_MASK  = ip(145-7+71-7,'Management port IPv4 network mask')
    MANAGE_MAC_MODE = i(149-7+71-7,1,'Management port MAC mode (0 - factorydefault, 1 - CW-Auto, 2 - static)')
    MANAGE_IP_MODE  = i(150-7+71-7,1,'Management port IP mode (1 - static, 2 - DHCP)')
    MANAGE_GW_MODE  = i(151-7+71-7,1,'Management port gateway mode (0 - None, 1 - static, 2 - DHCP)')
    MANAGE_GW_IP    = ip(152-7+71-7,'Management port gateway IPv4 address')
    MANAGE_ARP      = i(156-7+71-7,1,'Management port ARP (Advertisement Report Period) [s]')
    MANAGE_IGMP     = i(157-7+71-7,1,'Management port IGMP report period [s]')
    MANAGE_IP_TTL   = i(158-7+71-7,1,'Management port IPv4 Time To Live (TTL value in the IPv4 header)')
    MANAGE_MAC_DEFAULT = mac(159-7+71-7,'Management port factory default MAC address')
    STREAM_PORT_MAC    = mac(183-7+71-7,'Stream port static MAC address')
    STREAM_PORT_IP     = ip(189-7+71-7,'Stream port IPv4 address')
    STREAM_PORT_IP_MASK  = ip(193-7+71-7,'Stream port Ipv4 mask')
    STREAM_PORT_MAC_MODE = i(197-7+71-7,1,'Stream port MAC mode (0 - factory default, 1 - CW-auto, 2 - static)')
    STREAM_PORT_IP_MODE  = i(198-7+71-7,1,'Stream port IP mode (1 - static, 2 - DHCP)')
    STREAM_PORT_GW_MODE  = i(199-7+71-7,1,'Stream port gateway mode (0 - none, 1 - static, 2 - DHCP)')
    STREAM_PORT_GW_IP    = ip(200-7+71-7,'Stream port gateway IPv4 address')
    STREAM_PORT_ARP      = i(204-7+71-7,1,'Stream port ARP Advertisement Report Period (0=off) [s]')
    STREAM_PORT_IGMP     = i(205-7+71-7,1,'Stream port IGMP report period (0=off) [s]')
    STREAM_PORT_IP_TTL   = i(206-7+71-7,1,'Stream port IPv4 Time To Live (TTL value in the IPv4 header)')
    STREAM_PORT_MAC_DEFAULT = mac(207-7+71-7,'Stream port factory default MAC address')
    HTTP_PORT     = i(231-7+71-7,2,'HTTP Port','lsb')
    SMTP_PORT     = i(233-7+71-7,2,'SMTP server port','lsb')
    CLOCK_CONTROL = b(263-7+71-7,1,'Clock control (SETCLOCKCONTROL instruction)',[ ['AS',2,2,'AD clock source (0 - internal, 1 - external)'], \
                                                                                   ['AA',3,3,'External clock mode (0 - normal, 1 - auto)'], \
                                                                                   ['SS',4,4,'Sample source (0 - internal, 1 - external)'] ], byteOrder='msb' )
    CLOCK_ENABLE  = b(264-7+71-7,1,'Clock enable (SETCLOCKENABLE instruction)', [ ['CC',0,0,'Clock output of the CONTROL connector (0 - disable, 1 - enable)'], \
                                                                                  ['EC',1,1,'Clock output of the EIO connector (0 - disable, 1 - enable)'], \
                                                                                  ['CS',2,2,'Sample output of the CONTROL connector (0 - disable, 1 - enable)'], \
                                                                                  ['ES',3,3,'Sample output of the EIO connector (0 - disable, 1 - enable)'] ], byteOrder='msb' ) 
    BASE_PLL_MULT    = i(265-7+71-7,1,'Base PLL multiply value',byteOrder='msb')
    BASE_PLL_DIV0    = i(266-7+71-7,1,'Base PLL divide value 0',byteOrder='msb')
    BASE_PLL_DIV_ADC = i(267-7+71-7,1,'Base PLL divide value 1 (going to clock signal F1/ADC)',byteOrder='msb')
    BASE_PLL_DIV2    = i(268-7+71-7,1,'Base PLL divide value 2')
    BASE_PLL_DIV3    = i(269-7+71-7,1,'Base PLL divide value 3')
    EXT_DCM_MULT     = i(270-7+71-7,1,'External DCM multiply value')
    EXT_DCM_DIV      = i(271-7+71-7,1,'External DCM divide value')
    SAMPLEDIV        = i(272-7+71-7,2,'Sample divide value','msb')
    SPAREIO          = b(274-7+71-7,1,'Spare IO control',[ ['OUTVAL0',0,0,'Spare IO pin 0 output value'],\
                                                           ['OUTVAL1',1,1,'Spare IO pin 1 output value'],\
                                                           ['OUTVAL2',2,2,'Spare IO pin 2 output value'],\
                                                           ['OUTVAL3',3,3,'Spare IO pin 3 output value'],\
                                                           ['DIR0',4,4,'Direction (0-input, 1-output)'],\
                                                           ['DIR1',5,5,'Direction (0-input, 1-output)'],\
                                                           ['DIR2',6,6,'Direction (0-input, 1-output)'],\
                                                           ['DIR3',7,7,'Direction (0-input, 1-output)'] ], byteOrder='msb' )  # 4..7: direction in v2
    XFP         = b(275-7+71-7,1,'XFP',[ ['REFCLKENABLE',0,0,'XFP reference clock enable'] ] )
    SAMPLECOUNT = i(276-7+71-7,281-276+1,'Sample count','msb')
    EIO_ADC_CLK_DIV = i(282-7+71-7,1,'EIO ADC clock divider value')
    TRIGDELAY       = i(283-7+71-7, 286-283+1,'Trigger delay',byteOrder='msb')
    SERIAL_PLL_MULT = i(287-7+71-7,1,'Serial PLL multiply value')
    SERIAL_PLL_DIV  = i(288-7+71-7,1,'Serial PLL divide value 0')
    SATACONTROL     = b(292-7+71-7,1,'SATA Control',[ ['DSM',0,0,'Dual SATA mode (0 - disabled, 1 - enabled)'] ] )
    G1TRIGCONTROL   = b(293-7+71-7,1,'G1 trigger control (SETG1TRIGGERMODULE instruction)', [ ['ETR',0,0,'External trigger rising slope (0=disabled, 1=enabled)'], \
                                                                                              ['ETF',1,1,'External trigger falling slope (0=disabled, 1=enabled)'], \
                                                                                              ['IT', 2,2,'IT','Internal trigger (0=disabled, 1=enabled)'], \
                                                                                              ['CTR',3,3,'CAM timer 0 rising slope trigger (0=disabled, 1=enabled)'], \
                                                                                              ['CTF',4,4,'CAM timer 0 rising slope trigger (0=disabled, 1=enabled)'], \
                                                                                              ['SWT',5,5,'Generate software trigger'],\
                                                                                              ['SWC',6,6,'Clear the output by software'],\
                                                                                              ['CTS',7,7,'Clear trigger status'] ] )
    G2GATECONTROL = b(294-7+71-7,1,'G2 gate control (SETG2GATEMODULE instruction)', [ ['EGP' ,0,0,'External gate polarity (0=normal, 1=inverted)'], \
                                                                                      ['ETE' ,1,1,'External gate (0=disabled, 1=enabled)'], \
                                                                                      ['IGP' ,2,2,'Internal gate polarity (0=normal, 1=inverted)'], \
                                                                                      ['IGE' ,3,3,'Internal gate (0=disabled, 1=enabled)'], \
                                                                                      ['CTGP',4,4,'CAM timer 0 gate polarity (0=normal, 1=inverted)'], \
                                                                                      ['CTGE',5,5,'CAM timer 0 gate (0=diabled, 1=enabled)'],\
                                                                                      ['SWG' ,7,7,'SWG','Software gate (0=cleared, 1=set - THIS IS WRITTEN VICE VERSA IN THE DOC!)'] ] )

    STREAMCONTROL   = b(299-7+71-7,1,'Stream control (SETSTREAMCONTROL instruction)',[ ['EN1',0,0,'Stream 1 disabled (0) or enabled (1)'], \
                                                                                       ['EN2',1,1,'Stream 2 disabled (0) or enabled (1)'], \
                                                                                       ['EN3',2,2,'Stream 3 disabled (0) or enabled (1)'], \
                                                                                       ['EN4',3,3,'Stream 4 disabled (0) or enabled (1)'], \
                                                                                       ['TM1',4,4,'Test mode of stream 1 disabled (0) or enabled (1)'], \
                                                                                       ['TM2',5,5,'Test mode of stream 2 disabled (0) or enabled (1)'], \
                                                                                       ['TM3',6,6,'Test mode of stream 3 disabled (0) or enabled (1)'], \
                                                                                       ['TM4',7,7,'Test mode of stream 4 disabled (0) or enabled (1)'] ] )
    UDPTESTCLOCK_DIV = i(300-7+71-7,303-300+1,'UDP test clock divider value','msb')

    UDPOCTET = [APDCAM10G_register_int(311-7+71-7+j*16,2,'Stream '+str(j)+' octet','msb') for j in range(4)]
    UDPMAC   = [APDCAM10G_register_mac(313-7+71-7+j*16,'Stream '+str(j)+' MAC address') for j in range(4)]
    IP       = [APDCAM10G_register_ip (319-7+71-7+j*16,'Stream '+str(j)+' IPv4 address') for j in range(4)]
    UDPPORT  = [APDCAM10G_register_int(323-7+71-7+j*16,2,'Stream '+str(j)+' UDP port','msb') for j in range(4)]

    CAMTIMERDELAY   = [APDCAM10G_register_int(375+j*16-7+71-7,4,'CT timer '+str(j)+' delay','msb') for j in range(10)]
    CAMTIMERON      = [APDCAM10G_register_int(379+j*16-7+71-7,4,'CT timer '+str(j+1)+' on','msb') for j in range(10)]
    CAMTIMEROFF     = [APDCAM10G_register_int(383+j*16-7+71-7,4,'CT timer '+str(j+1)+' off','msb') for j in range(10)]
    CAMTIMERNPULSES = [APDCAM10G_register_int(387+j*16-7+71-7,4,'CT timer '+str(j+1)+' number of pulses','msb') for j in range(10)]

    CAMCONTROL  = i(495-7+71-7,2,'CAM timer control','msb')
    CAMCLKDIV   = i(497-7+71-7,2,'CAM timer clock divide value','msb')
    CAMOUTPUT   = i(499-7+71-7,2,'CAM timer output','msb')

    
class APDCAM10G_cc_variables_v1(APDCAM10G_register_table):
    """
    Variables of the CC card up to firmware version 1.04
    """

    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    def addressDisplay(self,a):
        return str(a+7) + "-7"

    MANAGE_MAC      = mac(7-7, 'Management port MAC address')
    MANAGE_IP       = ip(13-7, 'Management port IPv4 address')
    MANAGE_IP_MASK  = ip(17-7,'Management port IPv4 network mask')
    MANAGE_LINK_ON  = i(21-7,1,'Management port link on')
    MANAGE_GW_STATE = i(22-7,1,'Management port gateway state (0=none, 1=ok, 2=searching mac, 3=searching IP with DHCP)')
    MANAGE_IP_STATE = i(23-7,1,'Management port IP state (1=ok, 3=searching IP with DHCP)')
    MANAGE_DHCP_STATE = i(24-7,1,'Management port DHCP state (0=idle, 1=request, 2=discover)')
    MANAGE_GW_MAC   = mac(25-7,'Management port gateway MAC address')
    MANAGE_GW_IP    = ip(31-7,'Management port gateway IPv4 address')
    MANAGE_DHCP_MAC = mac(35-7,'Management port DHCP server MAC address')
    MANAGE_DHCP_SERVER_IP = ip(41-7,'Management port DHCP server IPv4 address')
    MANAGE_IGMP_MAC = mac(45-7,'Management port IGMP switch MAC address')
    MANAGE_IGMP_IP  = ip(51-7,'Management port IGMP switch IPv4 address')
    MANAGE_DHCP_LT  = i(55-7,4,'Management port DHCP lease time','lsb')
    MANAGE_ETHRX = i(59-7,4,'Management port ethernet RX frames','lsb')
    MANAGE_ETHTX = i(63-7,4,'Management port ethernet TX frames','lsb')
    STREAM_PORT_MAC = mac(71-7,'Stream port MAC address')
    STREAM_PORT_IP  = ip(77-7,'Stream port IPv4 address')
    STREAM_PORT_IP_MASK = ip(81-7,'Stream port IPv4 network mask')
    STREAM_PORT_LINK_ON = i(85-7,1,'Stream port link on')
    STREAM_PORT_GW_STATE = i(86-7,1,'Stream port gateway state (0=none, 1=ok, 2=searching MAC, 3=searching IP with DHCP)')
    STREAM_PORT_IP_STATE = i(87-7,1,'Stream port IP state (1=ok, 3=searching IP with DHCP)')
    STREAM_PORT_DHCP_STATE = i(88-7,1,'Stream port DHCP state (0=idle, 1=request, 2=discover)')
    STREAM_PORT_GW_MAC = mac(89-7,'Stream port gateway MAC address')
    STREAM_PORT_GW_IP = ip(95-7,'Stream port gateway IPv4 address')
    STREAM_PORT_DHCP_MAC = mac(99-7,'Stream port DHCP server MAC address')
    STREAM_PORT_DHCP_IP  = ip(105-7,'Stream port DHCP server IPv4 address')
    STREAM_PORT_IGMP_MAC = mac(109-7,'Stream port IGMP switch MAC address')
    STREAM_PORT_IGMP_IP  = ip(115-7,'Stream port IGMP switch IPv4 address')
    STREAM_PORT_DHCP_LT = i(119-7,4,'Stream port DHCP lease time','lsb')
    STREAM_PORT_ETHRX = i(123-7,4,'Stream port ethernet RX frames','lsb')
    STREAM_PORT_ETHTX = i(127-7,4,'Stream port ethernet TX frames','lsb')
    MANAGE_ETHBUF = i(135-7,1,'Management port ethernet buffers used')
    MANAGE_ETHBUFMAX = i(136-7,1,'Management port ethernet buffers used max.')
    MANAGE_ETHDROP = i(139-7,4,'Management port ethernet dropped frames','lsb')
    MANAGE_TCPRX   = i(143-7,4,'Management port TCP RX packets','lsb')
    MANAGE_TCPTX   = i(147-7,4,'Management port TCP TX packets','lsb')
    MANAGE_TCPESTCONN  = i(151-7,4,'Management port TCP established connections','lsb')
    MANAGE_TCPREJCONN  = i(155-7,4,'Management port TCP rejected connections','lsb')
    MANAGE_TCPCLOCONN  = i(159-7,4,'Management port TCP closed connections','lsb')
    MANAGE_TCPACTCONN  = i(163-7,4,'Management port TCP active connections','lsb')
    MANAGE_TCPKATO     = i(167-7,4,'Management port TCP keep alive timeout','lsb')
    MANAGE_TCPRETTO    = i(171-7,4,'Management port TCP retransmit timeout','lsb')
    MANAGE_TCPRETRANS  = i(175-7,4,'Management port TCP retransmissions','lsb')
    SYSTEMUPTIME = i(183-7,4,'System up time [ms]','lsb')
    HWERROR = b(187-7,2,'Hardware error',[ ['SDRAM', 0,0,'SDRAM error'], \
                                           ['EEPROM',1,1,'EEPROM error'], \
                                           ['FPGA',  2,2,'FPGA error'], \
                                           ['FLASH',3,3,'Internal flash error'], \
                                           ['FLASH1',4,4,'Flash 1 error (web server flash)'], \
                                           ['FLASH2',5,5,'Flash 2 error (storage flash)'] ],'lsb')
    IICERROR = b(189-7,2,'IIC error', [ ['NOACK',0,0,'No ACK received'],\
                                        ['ADDOVG',1,1,'ADDOVF','Address overflow'],\
                                        ['POLL',2,2,'Polling error'] ],'lsb')
    FPGAVH = i(192-7,1,'FPGA program version high')
    FPGAVL = i(193-7,1,'FPGA program version low')
    FPGA_STATUS = b(194-7,1,'FPGA status',[ ['BPLLLCK',0,0,'Basic PLL locked'],\
                                            ['SPLLLCK',1,1,'Serial PLL locked'],\
                                            ['EPLLLCK',2,2,'External DCM locked'],\
                                            ['EXTCLKVAL',3,3,'External clock valid'],\
                                            ['CAMTIM',4,5,'CAM timer state (0=idle, 1=armed, 1=running)'],\
                                            ['STRADC',6,6,'Streaming ADC board data'],\
                                            ['OVLD',7,7,'Overload'] ] )
    STREAM_PORT_ETHSTAT = b(195-7,1,'Stream port ethernet status', [ ['XDCMLCK',0,0,'XGMII RX DCM locked'],\
                                                                     ['XLNK',1,1,'XGMII link'],\
                                                                     ['TXFULL',2,2,'Reserved for internal use (TX buffer is full)'] ] )
    EXTCLKFREQ = i(196-7,2,'External clock frequench [kHz]','msb')
    DSLVLCK = i(198-7,1,'DSLV lock status')
    STREAM_PORT_RXERRCNT = i(199-7,2,'Stream port RX error counter','msb')
    STREAM_PORT_RXOVFCNT = i(201-7,2,'Stream port RX overflow counter','msb')
    STREAM_PORT_RXPKTCNT = i(203-7,2,'Stream port RX packetk counter','msb')
    TRIGSTATE = i(205-7,1,'Trigger status')
    STATUS = b(215-7,4,'Status',[ ['WEBBSY',0,0,'Web flash is busy (1) or free (0)'],\
                                  ['STBSY',1,1,'Storage flash is busy (1) or free (0)'] ], byteOrder='lsb')
    FUPCHKSUM = i(271-7,4,'FUP checksum','msb?')
    FUPPROGR = i(275-7,1,'FUP in process')
    BOARDTEMP = i(276-7,1,'Board temperature [C]')
    VDD33 = i(279-7, 2, 'VDD 3.3V voltage [mV] (main power supply)',byteOrder='lsb')
    VDD25 = i(281-7, 2, 'VDD 2.5V voltage [mV]',byteOrder='lsb')
    VDD18 = i(283-7, 2, 'VDD 1.8V XC voltage [mV] (Xilinx FPGA)',byteOrder='lsb')
    VDD12 = i(285-7, 2, 'VDD 1.2V ST voltage [mV] (core voltage of Stellaris Microcontroll.)',byteOrder='lsb')
    SCBVER = i(287-7,2,'SCB controller version',byteOrder='msb?') 
    MARVELLBC = i(289-7,2,'Marvell boot counter (for internal use)',byteOrder='msb')
    MARVELL30x8127 = i(289-7,2,'Marvell register 3.0x8127 (for internal use)',byteOrder='msb')
    DEBUGSTATE = i(299-7,2,'Debug state (for internal use)',byteOrder='msb')
    MAXBOARDTEMP = i(302-7,1,'Maximum board temperature')
    MAXVDD33 = i(303-7,2,'Maximum VDD 3.3V','lsb?')
    SAMPLECOUNT = [APDCAM10G_register_int(305-7+j*6,6,'Actual value ofo the stream #' + str(j) + ' sample counter','msb?') for j in range(4)]

class APDCAM10G_cc_variables_v2(APDCAM10G_register_table):
    """
    Variables of the CC card up to firmware version 1.04
    """

    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    def addressDisplay(self,a):
        return str(a+7) + "-7"

    MANAGE_MAC      = mac(7-7,  'Management port MAC address')
    MANAGE_IP       = ip(13-7, 'Management port IPv4 address')
    MANAGE_IP_MASK  = ip(17-7,'Management port IPv4 network mask')
    MANAGE_LINK_ON  = i(21-7,1,'Management port link on')
    MANAGE_GW_STATE = i(22-7,1,'Management port gateway state (0=none, 1=ok, 2=searching mac, 3=searching IP with DHCP)')
    MANAGE_IP_STATE = i(23-7,1,'Management port IP state (1=ok, 3=searching IP with DHCP)')
    MANAGE_DHCP_STATE = i(24-7,1,'Management port DHCP state (0=idle, 1=request, 2=discover)')
    MANAGE_GW_MAC   = mac(25-7,'Management port gateway MAC address')
    MANAGE_GW_IP    = ip(31-7,'Management port gateway IPv4 address')
    MANAGE_DHCP_MAC = mac(35-7,'Management port DHCP server MAC address')
    MANAGE_DHCP_SERVER_IP = ip(41-7,'Management port DHCP server IPv4 address')
    MANAGE_IGMP_MAC = mac(45-7,'Management port IGMP switch MAC address')
    MANAGE_IGMP_IP  = ip(51-7,'Management port IGMP switch IPv4 address')
    MANAGE_DHCP_LT  = i(55-7,4,'Management port DHCP lease time','lsb')
    MANAGE_ETHRX = i(59-7,4,'Management port ethernet RX frames','lsb')
    MANAGE_ETHTX = i(63-7,4,'Management port ethernet TX frames','lsb')
    STREAM_PORT_MAC = mac(71-7,'Stream port MAC address')
    STREAM_PORT_IP  = ip(77-7,'Stream port IPv4 address')
    STREAM_PORT_IP_MASK = ip(81-7,'Stream port IPv4 network mask')
    STREAM_PORT_LINK_ON = i(85-7,1,'Stream port link on')
    STREAM_PORT_GW_STATE = i(86-7,1,'Stream port gateway state (0=none, 1=ok, 2=searching MAC, 3=searching IP with DHCP)')
    STREAM_PORT_IP_STATE = i(87-7,1,'Stream port IP state (1=ok, 3=searching IP with DHCP)')
    STREAM_PORT_DHCP_STATE = i(88-7,1,'Stream port DHCP state (0=idle, 1=request, 2=discover)')
    STREAM_PORT_GW_MAC = mac(89-7,'Stream port gateway MAC address')
    STREAM_PORT_GW_IP = ip(95-7,'Stream port gateway IPv4 address')
    STREAM_PORT_DHCP_MAC = mac(99-7,'Stream port DHCP server MAC address')
    STREAM_PORT_DHCP_IP  = ip(105-7,'Stream port DHCP server IPv4 address')
    STREAM_PORT_IGMP_MAC = mac(109-7,'Stream port IGMP switch MAC address')
    STREAM_PORT_IGMP_IP  = ip(115-7,'Stream port IGMP switch IPv4 address')
    STREAM_PORT_DHCP_LT = i(119-7,4,'Stream port DHCP lease time','lsb')
    STREAM_PORT_ETHRX = i(123-7,4,'Stream port ethernet RX frames','lsb')
    STREAM_PORT_ETHTX = i(127-7,4,'Stream port ethernet TX frames','lsb')
    MANAGE_ETHBUF = i(135-7,1,'Management port ethernet buffers used')
    MANAGE_ETHBUFMAX = i(136-7,1,'Management port ethernet buffers used max.')
    MANAGE_ETHDROP = i(139-7,4,'Management port ethernet dropped frames','lsb')
    MANAGE_TCPRX   = i(143-7,4,'Management port TCP RX packets','lsb')
    MANAGE_TCPTX   = i(147-7,4,'Management port TCP TX packets','lsb')
    MANAGE_TCPESTCONN  = i(151-7,4,'Management port TCP established connections','lsb')
    MANAGE_TCPREJCONN  = i(155-7,4,'Management port TCP rejected connections','lsb')
    MANAGE_TCPCLOCONN  = i(159-7,4,'Management port TCP closed connections','lsb')
    MANAGE_TCPACTCONN  = i(163-7,4,'Management port TCP active connections','lsb')
    MANAGE_TCPKATO     = i(167-7,4,'Management port TCP keep alive timeout','lsb')
    MANAGE_TCPRETTO    = i(171-7,4,'Management port TCP retransmit timeout','lsb')
    MANAGE_TCPRETRANS  = i(175-7,4,'Management port TCP retransmissions','lsb')
    SYSTEMUPTIME = i(183-7,4,'System up time [ms]','lsb')
    HWERROR = b(187-7,2,'Hardware error',[ ['SDRAM', 0,0,'SDRAM error'], \
                                           ['EEPROM',1,1,'EEPROM error'], \
                                           ['FPGA',  2,2,'FPGA error'], \
                                           ['FLASH',3,3,'Internal flash error'], \
                                           ['FLASH1',4,4,'Flash 1 error (web server flash)'], \
                                           ['FLASH2',5,5,'Flash 2 error (storage flash)'] ],'lsb')
    IICERROR = b(189-7,2,'IIC error', [ ['NOACK',0,0,'No ACK received'],\
                                        ['ADDOVG',1,1,'ADDOVF','Address overflow'],\
                                        ['POLL',2,2,'Polling error'] ],'lsb')
    FPGAVH = i(192-7,1,'FPGA program version high')
    FPGAVL = i(193-7,1,'FPGA program version low')
    FPGA_STATUS = b(194-7,1,'FPGA status',[ ['BPLLLCK',0,0,'Basic PLL locked'],\
                                            ['SPLLLCK',1,1,'Serial PLL locked'],\
                                            ['EPLLLCK',2,2,'External DCM locked'],\
                                            ['EXTCLKVAL',3,3,'External clock valid'],\
                                            ['CAMTIM',4,5,'CAM timer state (0=idle, 1=armed, 1=running)'],\
                                            ['STRADC',6,6,'Streaming ADC board data'],\
                                            ['OVLD',7,7,'Overload'] ] )
    STREAM_PORT_ETHSTAT = b(195-7,1,'Stream port ethernet status', [ ['XDCMLCK',0,0,'XGMII RX DCM locked'],\
                                                                     ['XLNK',1,1,'XGMII link'],\
                                                                     ['TXFULL',2,2,'Reserved for internal use (TX buffer is full)'] ] )
    EXTCLKFREQ = i(196-7,2,'External clock frequench [kHz]','msb')
    DSLVLCK = i(198-7,1,'DSLV lock status')
    STREAM_PORT_RXERRCNT = i(199-7,2,'Stream port RX error counter','msb')
    STREAM_PORT_RXOVFCNT = i(201-7,2,'Stream port RX overflow counter','msb')
    STREAM_PORT_RXPKTCNT = i(203-7,2,'Stream port RX packetk counter','msb')
    TRIGSTATE = b(205-7,1,'Trigger status',[ ['ETR',0,0,'External trigger rising slope'],\
                                             ['ETF',1,1,'External trigger falling slope'],\
                                             ['IT', 2,2,'Internal trigger'],\
                                             ['CTR',3,3,'CAM timer 0 rising slope'],\
                                             ['CTF',4,4,'CAM timer 0 falling slope'],\
                                             ['SWT',5,5,'Software trigger'],\
                                             ['G1',6,6,'Output of the G1 trigger module'],\
                                             ['G2',7,7,'Output of the G2 gate'] ] )
    SPAREIOIN = b(206-7,1,'Spare IO input',[ ['INVAL0',0,0,'Spare IO pin 0 input value'],\
                                             ['INVAL1',1,1,'Spare IO pin 1 input value'],\
                                             ['INVAL2',2,2,'Spare IO pin 2 input value'],\
                                             ['INVAL3',3,3,'Spare IO pin 3 input value'] ] )
    STATUS = b(215-7,4,'Status',[ ['WEBBSY',0,0,'Web flash is busy (1) or free (0)'],\
                                  ['STBSY',1,1,'Storage flash is busy (1) or free (0)'] ], byteOrder='lsb')
    FUPCHKSUM = i(271-7,4,'FUP checksum','msb?')
    FUPPROGR = i(275-7,1,'FUP in process')
    BOARDTEMP = i(276-7,1,'Board temperature [C]')
    VDD33 = i(279-7, 2, 'VDD 3.3V voltage [mV] (main power supply)',byteOrder='lsb')
    VDD25 = i(281-7, 2, 'VDD 2.5V voltage [mV]',byteOrder='lsb')
    VDD18 = i(283-7, 2, 'VDD 1.8V XC voltage [mV] (Xilinx FPGA)',byteOrder='lsb')
    VDD12 = i(285-7, 2, 'VDD 1.2V ST voltage [mV] (core voltage of Stellaris Microcontroll.)',byteOrder='lsb')
    SCBVER = i(287-7,2,'SCB controller version',byteOrder='msb?') 
    MARVELLBC = i(289-7,2,'Marvell boot counter (for internal use)',byteOrder='msb')
    MARVELL30x8127 = i(289-7,2,'Marvell register 3.0x8127 (for internal use)',byteOrder='msb')
    DEBUGSTATE = i(299-7,2,'Debug state (for internal use)',byteOrder='msb')
    MAXBOARDTEMP = i(302-7,1,'Maximum board temperature')
    MAXVDD33 = i(303-7,2,'Maximum VDD 3.3V','lsb?')
    SAMPLECOUNT = [APDCAM10G_register_int(305-7+j*6,6,'Actual value of the stream #' + str(j) + ' sample counter','msb?') for j in range(4)]
    
class APDCAM10G_pc_registers_v1(APDCAM10G_register_table):
    """
    This class is a representation of the PC card's registers
    """

    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac
    
    def addressDisplay(self,a):
        return hex(self.startByte)
    
    BOARD_VERSION = i(0x0000, 1, 'Board version code')
    FW_VERSION    = i(0X0002, 2, 'Firmware version code (x100)','lsb')

    # for searching: HV1MON, HV2MON, HV3MON, HV4MON
    HVMON = [APDCAM10G_register_bits(0x04+j*2, 2, 'Monitor output of HV generator ' + str(j) + ' (/0.12)', [['HV',0,11,'Monitor of HV' + str(j) + ' voltage']], byteOrder='lsb') for j in range(4)]

    TEMP_SENSOR_1 = b(0x0C, 2, 'Temperature sensor 1 reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_2 = b(0x0E, 2, 'Temperature sensor 2 reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_3 = b(0x10, 2, 'Temperature sensor 3 reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_4 = b(0x12, 2, 'Temperature sensor 4 reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_5 = b(0x14, 2, 'Temperature sensor (detector 1) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_6 = b(0x16, 2, 'Temperature sensor (analog amplifier 1) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_7 = b(0x18, 2, 'Temperature sensor (analog amplifier 2) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_8 = b(0x1A, 2, 'Temperature sensor (detector 2) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_9 = b(0x1C, 2, 'Temperature sensor (analog amplifier 3) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_10 = b(0x1E, 2, 'Temperature sensor (analog amplifier 4) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_11 = b(0x20, 2, 'Temperature sensor (baseplate) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_12 = b(0x22, 2, 'Temperature sensor 12 reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_13 = b(0x24, 2, 'Temperature sensor (diode) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_14 = b(0x26, 2, 'Temperature sensor (Peltier heat sink) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_15 = b(0x28, 2, 'Temperature sensor (power panel) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    TEMP_SENSOR_16 = b(0x2A, 2, 'Temperature sensor (power panel heat sink) reading (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    PELT_CTRL   = i(0x2C, 2, 'Actual Peltier controller output voltage(current?) [-4000..4000]. Negative means heating',byteOrder='lsb?',signed=True)
    PELT_MANUAL = i(0x4E, 2, 'Manual Peltier controller output voltage(current?) [-4000..4000] enabled by bit#3 of ANALOG_POWER. Negative means heating',byteOrder='lsb?',signed=True) # for FW >= 1.43
    P_GAIN = i(0x50, 2, 'Peltier controller P gain value (x100)',byteOrder='lsb?')
    I_GAIN = i(0x52, 2, 'Peltier controller I gain value (x100)',byteOrder='lsb?')
    D_GAIN = i(0x54, 2, 'Peltier controller D gain value (x100)',byteOrder='lsb?')
    HVSET = [APDCAM10G_register_bits(0x56+j*2, 2, 'Set value of high voltage generator ' + str(j), [['HV',0,11,'']], byteOrder='lsb') for j in range(4)]
    HVON = b(0x5E, 1, 'High voltages on/off',[ ['HV['+str(j)+']',j,j,'HV'+str(j)+' is on'] for j in range(4) ])
    HVENABLE = i(0x60, 1, 'HV enabled (a value of 171 enables globally, otherwise disabled)')
    IRQ_ENABLE_HV = b(0x62, 1, 'Generate interrupt if HVMON differs from HVSET by more than HV_IRQ_LEVEL', [ ['HV'+str(j+1),j,j,'Generate interrupt if HV'+str(j+1)+' has wrong value'] for j in range(4) ])
    IRQ_POWER_PID_ENABLE = b(0x64, 1, 'Enable temperature alarm interrupt, analog +/-5V supplies, PID control',[ ['TEMPALRM',0,0,'Enable interrupt on temperature alarm'], \
                                                                                                                 ['ANALOG5V',1,1,'Enable analog +/-5V supplies'], \
                                                                                                                 ['PIDDISABLE',2,2,'Disable PID control'] ] )
    HV_IRQ_LEVEL = b(0x66,2,'Maximum difference allowed between the set and monitor voltages before interrupt is generated [mV?]',[ ['LEVEL',0,11,'The threshold difference value'] ],byteOrder='lsb?')
    
    HV_FAILURE = b(0x68, 1, 'Latched bits for HV failure (must be cleared explicitely)',[ ['HV'+str(j+1)+'FAIL',j,j,'HV'+str(j+1)+' has failed'] for j in range(4) ])

    DETECTOR_TEMP_SET = b(0x6A, 2, 'Reference temperature to which the detector temperature is controlled (x10)', [ ['TEMP',0,11,'The reference temperature value'] ],byteOrder='lsb?')
    FAN1_SPEED = i(0x6C, 1, 'Speed of fan 1 if fan is in manual mode')
    FAN2_SPEED = i(0x6E, 1, 'Speed of fan 2 if fan is in manual mode')
    FAN3_SPEED = i(0x70, 1, 'Speed of fan 3 if fan is in manual mode')
    FAN1_TEMP_SET = b(0x72, 2, 'Required temperature for fan1 control (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    FAN1_TEMP_DIFF = b(0x74, 2, 'Temp. diff. to start the fan (both + and -) (x10)', [ ['TDIFF',0,11,''] ],'lsb?')
    FAN2_TEMP_LIMIT = b(0x76, 2, 'Fan2 will switch in gradually when temp. reaches this value (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    FAN3_TEMP_LIMIT = b(0x78, 2, 'Fan3 will switch in gradually when temp. reaches this value (x10)', [ ['TEMP',0,11,''] ],'lsb?')
    CALLIGHT = b(0x7A, 2, 'Calibration LED current. Zero value ensures complete darkneww',[ ['CURRENT',0,11,''] ],'lsb?')
    CALUPDATE = i(0x7C, 2, 'LED update period [us]. 0 disables periodic LED update','lsb?')
    IRQ_STATUS = b(0x7E, 1, 'Status of various interrupt requests. Can be cleared by writing 0.', [ ['HV',0,0,'Interrupt due to HV'],\
                                                                                                    ['TEMP',1,1,'Tempertaure alarm'],\
                                                                                                    ['CALLIGHT',2,2,'Calibration update (failure?)'] ] )
    SHMODE  = i(0x80, 1, 'Shutter operation mode. (0 - manual [by writing to SHSTATE], 1 - external [by shutter control input])')
    SHSTATE = i(0x82, 1, 'Shutter state (0 - closed, 1 - open)')
    RESET_FACTORY = i(0x84, 1, 'Writing hex 0xCD here causes factory reset')
    ERRORCODE = i(0x86, 1, 'Code of the last error',longDescription='0x41-HV1SET>HV1MAX, 0x42-HV2SET>HV1MAX, 0x43-HV3SET>HV3MAX, 0x44-HV4SET>HV4MAX, 0x50-write attempt of read-only or non-existent register, 0xF6-shutter sense is opened/closed in same time, 0x7C-Peltier controller has no valid weight values or temp sensor error')
    FACTORY_WRITE = i(0x88,2,'Writing a hex 0x?? value enables writing FACTORY_CAL_TABLE','lsb?')
    FIRMWARE_UPGR_ERROR_CODE = i(0x8E, 1, 'Error code for checking the integrity of uploaded firmware (0x11=OK, 0x12=checksum error)',format='hex')
    START_FIRMWARE_UPGR = i(0x90, 1, 'Writing 0x28 triggers checking uploaded FW, 0xC4 triggers checking and installing FW')
    #FIRMWARE_NEXT_CHAR = i(0x92,1,'Actual firmware data byte')
    #FIRMWARE_NEXT_LINE = s(0x94,0xFF-0x94+1,'Will be the new communication method to write complete HEX line for faster FW upgrade')
    BOARD_SERIAL = i(0x100, 2, 'Board unique serial number','lsb?')

    # for searching: HV1MAX, HV2MAX, HV3MAX, HV4MAX
    HVMAX = [APDCAM10G_register_bits(0x102+j*2, 2, 'Maximum allowed value for HV' + str(j), [['MAX',0,11,'']], byteOrder='lsb') for j in range(4)]

    TEMP_CTRL_WEIGHTS = [APDCAM10G_register_int(0x10A+j*2,2,'Control weight for the temperature sensor for detector temperature control','lsb?') for j in range(16)]
    FAN1_CTRL_WEIGHTS = [APDCAM10G_register_int(0x12A+j*2,2,'Control weight for the control of fan1. If all are zero, fan is manually controlled by setting speed','lsb?') for j in range(16)]
    FAN2_CTRL_WEIGHTS = [APDCAM10G_register_int(0x14A+j*2,2,'Control weight for the control of fan2. If all are zero, fan is manually controlled by setting speed','lsb?') for j in range(16)]
    FAN3_CTRL_WEIGHTS = [APDCAM10G_register_int(0x16A+j*2,2,'Control weight for the control of fan3. If all are zero, fan is manually controlled by setting speed','lsb?') for j in range(16)]

    
class APDCAM10G_pc_registers_v2(APDCAM10G_pc_registers_v1):
    """
    CURRENTLY THIS IS A 1-TO-1O COPY OF V1, I DO NOT KNOW IF ANYTHING ON THE PC HAS CHANGED
    """
    pass
    
class APDCAM10G_adc_registers_v1(APDCAM10G_register_table):
    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    BOARDVER    = i(0x0000, 1, 'Board version number')
    VERSION     = i(0x0001, 2, 'Microcontroller program version',byteOrder='msb?')
    SERIAL      = i(0x0003, 2, 'Board serial number',byteOrder='msb?')
    XCVERSION   = i(0x0005, 2, 'FPGA (Xilinx) program vesion',byteOrder='msb?')
    STATUS1     = b(0x0008, 1, 'STATUS1 register', [ ['BPLLOCK',0,0,"Base PLL locked"] ] )
    STATUS2     = b(0x0009, 1, 'STATUS2 register', [ ['ITS',0,0,'Internal trigger status'], \
                                                     ['OVD',1,1,'Overload'], \
                                                     ['LED1',2,2,'SATA1 data out LED'], \
                                                     ['LED2',3,3,'SATA2 data out LED']
                                                    ] )
    TEMPERATURE = i(0x000A, 1, 'Board temperature')
    CONTROL     = b(0x000B, 1, "CONTROL register", [ ['SATAONOFF',0,0,"SATA channels on/off"],\
                                                     ['DSM',1,1,"Dual SATA mode"], \
                                                     ['SS',2,2,"SATA Sync"], \
                                                     ['TM',3,3,"Test mode on"], \
                                                     ['FIL',4,4,"Filter on"],  \
                                                     ['ITE',5,5,"Internal trigger enabled"], \
                                                     ['RBO',6,6,"Reverse bit order in the stream (1=LSbit first)"] ] )
    DSLVCLKMUL  = i(0x000C, 1, 'SATA clock multiplier relative to 20 MHz internal clock')
    DSLVCLKDIV  = i(0x000D, 1, 'SATA clock divider relative to 20 MHz internal clock')
    DVDD33      = i(0x000E, 2, 'DVDD 3.3V voltage in mV',byteOrder='lsb')
    DVDD25      = i(0x0010, 2, 'DVDD 2.5V voltage in mV',byteOrder='lsb')
    AVDD33      = i(0x0012, 2, 'AVDD 3.3V voltage in mV',byteOrder='lsb')
    AVDD18      = i(0x0014, 2, 'AVDD 1.8V voltage in mV',byteOrder='lsb')

    # for searching: CHENABLE0, CHENABLE1, CHENABLE2, CHENABLE3, CHENABLE[0], CHENABLE[1], CHENABLE[2], CHENABLE[3] (0-based !!!)
    CHENABLE    = [b(0x0016, 1, 'Channels 1-8 enabled (1)/disabled (0)' , [ ['CH['+str(7-j)+']',j,j,'Channel '+str(8-j) +' enabled'] for j in range(8) ]), \
                   b(0x0017, 1, 'Channels 9-16 enabled (1)/disabled (0)', [ ['CH['+str(7-j)+']',j,j,'Channel '+str(16-j)+' enabled'] for j in range(8) ]), \
                   b(0x0018, 1, 'Channels 17-24 enabled (1)/disabled (0)',[ ['CH['+str(7-j)+']',j,j,'Channel '+str(24-j)+' enabled'] for j in range(8) ]), \
                   b(0x0019, 1, 'Channels 25-32 enabled (1)/disabled (0)',[ ['CH['+str(7-j)+']',j,j,'Channel '+str(32-j)+' enabled'] for j in range(8) ])]
    
    RINGBUFSIZE = b(0x001A, 2, 'Ring buffer size', [ ['RBSIZE',0,9,'Ring buffer size. If 0, ring buffer is disabled'] ],byteOrder='msb?')
    RESOLUTION = i(0x001C, 1, 'Resolution (number of bits per sample: 0-->14, 1-->12, 2-->8)')
    BPSCH      = [ APDCAM10G_register_int(0x001D+j, 1, 'Bytes per sample of 8-channel block ' + str(j)) for j in range(4)]
    ERRORCODE  = i(0x0024, 1, 'The code of the last error. 0 = no error')
    RESET_FACTORY = i(0x0025, 1, 'Writing 0xCD here causes factory reset')

    # for searching: AD1TEST, AD2TEST, AD3TEST, AD4TEST (0-based !!!)
    TESTMODE   = [APDCAM10G_register_int(0x0028+j, 1, 'ADC chip'+str(j)+' test mode selector. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...') for j in range(4)]

    # for searching: ANALOGOUT1, ANALOGOUT2, ANALOGOUT3, etc
    # for searching: TRIGLEVEL1, TRIGLEVEL2, etc
    ANALOGOUT = [ APDCAM10G_register_bits(0x0030+j*2, 2, 'Analog output for offset control', [ ['OFFSET', 0, 12, ''] ], byteOrder='msb?') for j in range(32) ]
    TRIGLEVEL = [ APDCAM10G_register_bits(0x0070+j*2, 2, 'Internal trigger control for the 32 channels', [ ['TRIGLEV',0,13,'Trigger level'],\
                                                                                                           ['MAXMIN',14,14,'Max / min trigger'],\
                                                                                                           ['ENABLED',15,15,'Trigger enabled'] ], byteOrder='msb?') for j in range(32) ]

    OVDLEVEL   = b(0xC0, 2, 'Overload level', [ ['LEVEL',0,13,''],['OVDPOLARITY',14,14,'Overload polarity'],['ENABLE',15,15,'Overload enable'] ],'msb?')
    OVDSTATUS  = b(0xC2, 1, 'Overload status', [ ['OVDEV',0,0,'Overload event'] ])
    OVDTIME    = i(0xC3, 2, 'Overload time [10 us units]', 'msb?')
    COEFF_01 = i(0x00D0,2,'Filter coefficient 1','lsb?')
    COEFF_02 = i(0x00D2,2,'Filter coefficient 2','lsb?')
    COEFF_03 = i(0x00D4,2,'Filter coefficient 3','lsb?')
    COEFF_04 = i(0x00D6,2,'Filter coefficient 4','lsb?')
    COEFF_05 = i(0x00D8,2,'Filter coefficient 5','lsb?')
    COEFF_06 = i(0x00DA,2,'Filter coefficient 6','lsb?')
    COEFF_07 = i(0x00DC,2,'Filter coefficient 7','lsb?')
    COEFF_08_FILTERDIV = i(0x00DE,2,'Filter divide factor (0..11)','lsb?')

class APDCAM10G_adc_registers_v2(APDCAM10G_register_table):
    # typedefs/shorthands
    b = APDCAM10G_register_bits
    i = APDCAM10G_register_int
    s = APDCAM10G_register_str
    ip = APDCAM10G_register_ip
    mac = APDCAM10G_register_mac

    BOARDVER    = i(0x0000, 1, 'Board version number')
    VERSION     = i(0x0001, 2, 'Microcontroller program version','msb?')
    SERIAL      = i(0x0003, 2, 'Board serial number','msb?')
    XCVERSION   = i(0x0005, 2, 'FPGA (Xilinx) program vesion','msb?')
    STATUS1     = b(0x0008, 1, 'STATUS1 register', [ ['BPLLOCK',0,0,'Base PLL locked'] ] )
    STATUS2     = b(0x0009, 1, 'STATUS2 register', [ ['ITS',0,0,'Internal trigger status'], \
                                                     ['OVD',1,1,'Overload'], \
                                                     ['LED1',2,2,'SATA1 data out LED'], \
                                                     ['LED2',3,3,'SATA2 data out LED']
                                                    ] )
    TEMPERATURE = i(0x000A, 1, 'Board temperature')
    CONTROL     = b(0x000B, 1, "CONTROL register", [ ['SATAONOFF',0,0,"SATA channels on/off"],\
                                                     ['DSM',1,1,"Dual SATA mode"], \
                                                     ['SS',2,2,"SATA Sync"], \
                                                     ['TM',3,3,"Test mode on"], \
                                                     ['FIL',4,4,"Filter on"],  \
                                                     ['ITE',5,5,"Internal trigger enabled"], \
                                                     ['RBO',6,6,"Reverse bit order in the stream (1=LSbit first)"] ] )

    DSLVCLKMUL  = i(0x000C, 1, 'SATA clock multiplier relative to 20 MHz internal clock')
    DSLVCLKDIV  = i(0x000D, 1, 'SATA clock divider relative to 20 MHz internal clock')
    DVDD33      = i(0x000E, 2, 'DVDD 3.3V voltage in mV',byteOrder='lsb')
    DVDD25      = i(0x0010, 2, 'DVDD 2.5V voltage in mV',byteOrder='lsb')
    AVDD33      = i(0x0012, 2, 'AVDD 3.3V voltage in mV',byteOrder='lsb')
    AVDD18      = i(0x0014, 2, 'AVDD 1.8V voltage in mV',byteOrder='lsb')

    # for searching: CHENABLE0, CHENABLE1, CHENABLE2, CHENABLE3, CHENABLE[0], CHENABLE[1], CHENABLE[2], CHENABLE[3]  (0-based !!!)
    CHENABLE    = [b(0x0016, 1, 'Channels 1-8 enabled (1)/disabled (0)' , [ ['CH['+str(7-j)+']',j,j,'Channel '+str(8-j) +' enabled'] for j in range(8) ]), \
                   b(0x0017, 1, 'Channels 9-16 enabled (1)/disabled (0)', [ ['CH['+str(7-j)+']',j,j,'Channel '+str(16-j)+' enabled'] for j in range(8) ]), \
                   b(0x0018, 1, 'Channels 17-24 enabled (1)/disabled (0)',[ ['CH['+str(7-j)+']',j,j,'Channel '+str(24-j)+' enabled'] for j in range(8) ]), \
                   b(0x0019, 1, 'Channels 25-32 enabled (1)/disabled (0)',[ ['CH['+str(7-j)+']',j,j,'Channel '+str(32-j)+' enabled'] for j in range(8) ])]

#    RINGBUFSIZE = b(0x001A, 2, 'Ring buffer size', [ ['RBSIZE',0,9,'Ring buffer size. If 0, ring buffer is disabled'] ],byteOrder='msb?')
    STREAMCONTROL = b(0x1A, 2, 'Ring buffer size / SATA test mode / Stream mode', [ ['RBSIZE',0,9,'Ring buffer size. If 0, ring buffer is disabled'],\
                                                                                    ['SATATEST',13,13,'SATA test mode'],\
                                                                                    ['STREAMMODE',14,15,'0 = Off/sync mode; 1 = continuous mode; 2 = gate mode; 3 = trigger mode'] ],byteOrder='msb?')
    RESOLUTION = i(0x001C, 1, 'Resolution (number of bits per sample: 0-->14, 1-->12, 2-->8)')
    BPSCH      = [ APDCAM10G_register_int(0x001D+j, 1, 'Bytes per sample of 8-channel block ' + str(j)) for j in range(4)]
    ERRORCODE  = i(0x0024, 1, 'The code of the last error. 0 = no error')
    RESET_FACTORY = i(0x0025, 1, 'Writing 0xCD here causes factory reset')

    # for searching: AD1TEST, AD2TEST, AD3TEST, AD4TEST (0-based !!!)
    TESTMODE   = [APDCAM10G_register_int(0x0028+j, 1, 'ADC chip'+str(j)+' test mode selector. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...') for j in range(4)]
    # for j in range(4):

    DACCONTROL = b(0x2E,1,'DAC mixed channel mode',[ ['MIXED',0,0,'ADC and DAC channel numbering is mixed'] ] )

    # for searching: ANALOGOUT1, ANALOGOUT2, ANALOGOUT3, etc
    # for searching: TRIGLEVEL1, TRIGLEVEL2, etc
    ANALOGOUT = [ APDCAM10G_register_bits(0x0030+j*2, 2, 'Analog output for offset control', [ ['OFFSET', 0, 12, ''] ], byteOrder='msb?') for j in range(32) ]
    TRIGLEVEL = [ APDCAM10G_register_bits(0x0070+j*2, 2, 'Internal trigger control for the 32 channels', [ ['TRIGLEV',0,13,'Trigger level'],\
                                                                                                           ['MAXMIN',14,14,'Max / min trigger'],\
                                                                                                           ['ENABLED',15,15,'Trigger enabled'] ], byteOrder='msb?') for j in range(32) ]
    OVDLEVEL   = b(0xC0, 2, 'Overload level', [ ['LEVEL',0,13,''],['OVDPOLARITY',14,14,'Overload polarity'],['ENABLE',15,15,'Overload enable'] ],'msb?')
    OVDSTATUS  = b(0xC2, 1, 'Overload status', [ ['OVDEV',0,0,'Overload event'] ])
    OVDTIME    = i(0xC3, 2, 'Overload time [10 us units]', 'msb?')
    COEFF_01 = i(0x00D0,2,'Filter coefficient 1','lsb?')
    COEFF_02 = i(0x00D2,2,'Filter coefficient 2','lsb?')
    COEFF_03 = i(0x00D4,2,'Filter coefficient 3','lsb?')
    COEFF_04 = i(0x00D6,2,'Filter coefficient 4','lsb?')
    COEFF_05 = i(0x00D8,2,'Filter coefficient 5','lsb?')
    COEFF_06 = i(0x00DA,2,'Filter coefficient 6','lsb?')
    COEFF_07 = i(0x00DC,2,'Filter coefficient 7','lsb?')
    COEFF_08_FILTERDIV = i(0x00DE,2,'Filter divide factor (0..11)','lsb?')
    #FACTCALTABLE = r(0x0100, 256, 'Factory calibration data space')
        
