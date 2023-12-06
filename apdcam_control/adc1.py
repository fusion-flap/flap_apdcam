class APDCAM10G_adc_registers_v1(APDCAM10G_register_table):
    # typedefs/shorthands
    b = APDCAM10G_register_bits
    r = APDCAM10G_register
    r2i  = APDCAM10G_register2int
    r2b  = APDCAM10G_register2bits
    r2s  = APDCAM10G_register2str
    BOARDVER    = r(0x0000, 1, 'Board version number')
    VERSION     = r(0x0001, 2, 'Microcontroller program version','msb?')
    SERIAL      = r(0x0003, 2, 'Board serial number','msb?')
    XCVERSION   = r(0x0005, 2, 'FPGA program vesion','msb?')
    STATUS1     = r(0x0008, 1, 'STATUS1 register', interpreter=r2b([b(0,0,"BPLLOCK","Base PLL locked")]))
    STATUS2     = r(0x0009, 1, 'STATUS2 register', interpreter=r2b([b(0,0,"ITS","Internal trigger status")]))
    TEMPERATURE = r(0x000A, 1, 'Board temperature')
    CONTROL     = r(0x000B, 1, "CONTROL register", interpreter=r2b([b(0,0,"SATAonoff","SATA channels on/off"),\
                                                                    b(1,1,"DSM","Dual SATA mode"), \
                                                                    b(2,2,"SS","SATA Sync"), \
                                                                    b(3,3,"TM","Test mode on"), \
                                                                    b(4,4,"FIL","Filter on"),  \
                                                                    b(5,5,"ITE","Internal trigger enabled"), \
                                                                    b(6,6,"RBO","Reverse bit order in the stream (1=LSbit first)")]))
    DSLVCLKMUL  = r(0x000C, 1, 'SATA clock multiplier relative to 20 MHz internal clock')
    DSLVCLKDIV  = r(0x000D, 1, 'SATA clock divider relative to 20 MHz internal clock')
    DVDD33      = r(0x000E, 2, 'DVDD 3.3V voltage in mV','lsb')
    DVDD25      = r(0x0010, 2, 'DVDD 2.5V voltage in mV','lsb')
    AVDD33      = r(0x0012, 2, 'AVDD 3.3V voltage in mV','lsb')
    AVDD18      = r(0x0014, 2, 'AVDD 1.8V voltage in mV','lsb')
    CHENABLE1   = r(0x0016, 1, 'Channels 1-8 enabled (1)/disabled (0)',interpreter=r2b([\
                   b(0,0,'CH8','Channel 8 enabled'), \
                   b(1,1,'CH7','Channel 7 enabled'), \
                   b(2,2,'CH6','Channel 6 enabled'), \
                   b(3,3,'CH5','Channel 5 enabled'), \
                   b(4,4,'CH4','Channel 4 enabled'), \
                   b(5,5,'CH3','Channel 3 enabled'), \
                   b(6,6,'CH2','Channel 2 enabled'), \
                   b(7,7,'CH1','Channel 1 enabled')]))
    CHENABLE2   = r(0x0017, 1, 'Channels 9-16 enabled (1)/disabled (0)',interpreter=r2b([\
                   b(0,0,'CH16','Channel 16 enabled'), \
                   b(1,1,'CH15','Channel 15 enabled'), \
                   b(2,2,'CH14','Channel 14 enabled'), \
                   b(3,3,'CH13','Channel 13 enabled'), \
                   b(4,4,'CH12','Channel 12 enabled'), \
                   b(5,5,'CH11','Channel 11 enabled'), \
                   b(6,6,'CH10','Channel 10 enabled'), \
                   b(7,7,'CH9','Channel 9 enabled')]))
    CHENABLE3   = r(0x0018, 1, 'Channels 17-24 enabled (1)/disabled (0)',interpreter=r2b([\
                   b(0,0,'CH24','Channel 24 enabled'), \
                   b(1,1,'CH23','Channel 23 enabled'), \
                   b(2,2,'CH22','Channel 22 enabled'), \
                   b(3,3,'CH21','Channel 21 enabled'), \
                   b(4,4,'CH20','Channel 20 enabled'), \
                   b(5,5,'CH19','Channel 19 enabled'), \
                   b(6,6,'CH18','Channel 18 enabled'), \
                   b(7,7,'CH17','Channel 17 enabled')]))
    CHENABLE4   = r(0x0019, 1, 'Channels 25-32 enabled (1)/disabled (0)',interpreter=r2b([\
                   b(0,0,'CH32','Channel 32 enabled'), \
                   b(1,1,'CH31','Channel 31 enabled'), \
                   b(2,2,'CH30','Channel 30 enabled'), \
                   b(3,3,'CH29','Channel 29 enabled'), \
                   b(4,4,'CH28','Channel 28 enabled'), \
                   b(5,5,'CH27','Channel 27 enabled'), \
                   b(6,6,'CH26','Channel 26 enabled'), \
                   b(7,7,'CH25','Channel 25 enabled')]))
    RINGBUFSIZE = r(0x001A, 2, 'Ring buffer size', interpreter=r2b([b(0,9,'RBSIZE','Ring buffer size. If 0, ring buffer is disabled')],'msb?'))
    RESOLUTION = r(0x001C, 1, 'Resolution (number of bits per sample)')
    BPSCH1     = r(0x001D, 1, 'Bytes per sample of 8-channel block 1')
    BPSCH2     = r(0x001E, 1, 'Bytes per sample of 8-channel block 2')
    BPSCH3     = r(0x001F, 1, 'Bytes per sample of 8-channel block 3')
    BPSCH4     = r(0x0020, 1, 'Bytes per sample of 8-channel block 4')
    ERRORCODE  = r(0x0024, 1, 'The code of the last error. 0 = no error')
    RESETFACTORY = r(0x0025, 1, 'Writing 0xCD here causes factory reset')
    AD1TEST     = r(0x0028, 1, 'ADC chip1 test mode selector. 0 = normal mode',r2b([b(0,3,'TESTMODE','Test mode. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...')]))
    AD2TEST     = r(0x0029, 1, 'ADC chip2 test mode selector. 0 = normal mode',r2b([b(0,3,'TESTMODE','Test mode. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...')]))
    AD3TEST     = r(0x002A, 1, 'ADC chip3 test mode selector. 0 = normal mode',r2b([b(0,3,'TESTMODE','Test mode. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...')]))
    AD4TEST     = r(0x002B, 1, 'ADC chip4 test mode selector. 0 = normal mode',r2b([b(0,3,'TESTMODE','Test mode. 0=normal,1=b100000000000(8192),2=b11111111111111(16383),3=0,4=1010...(10922),0101...(5461),5=longpseudo,6=shortpseudo,7=1111...,0000...')]))
    ANALOGOUT  = r(0x0030,  2*32, 'Analog outputs for offset control', interpreter=r2b([b(0,12,'OFFSET','Offset')],byteOrder='msb?',bytePeriod=2))
    TRIGLEVEL  = r(0x0070,  2*32, 'Internal trigger control for the 32 channels', \
                   interpreter=r2b([b(0,13,'TRIGLEV','Trigger level'),b(14,14,'MAX/MIN','Max / min trigger'),b(15,15,'ENABLED','Trigger enabled')],byteOrder='msb?',bytePeriod=2))
    OVDLEVEL   = r(0xC0, 2, 'Overload level', r2b([b(0,13,'LEVEL',''),b(14,14,'OVDPOLARITY','Overload polarity'),b(15,15,'ENABLE','Overload enable')],'msb?'))
    OVDSTATUS  = r(0xC2, 1, 'Overload status', r2b([b(0,0,'OVDEV','Overload event')]))
    OVDTIME    = r(0xC3, 2, 'Overload time [10 us units]', 'msb?')
    COEFF_01 = r(0x00D0,2,'Filter coefficient 1','lsb?')
    COEFF_02 = r(0x00D2,2,'Filter coefficient 2','lsb?')
    COEFF_03 = r(0x00D4,2,'Filter coefficient 3','lsb?')
    COEFF_04 = r(0x00D6,2,'Filter coefficient 4','lsb?')
    COEFF_05 = r(0x00D8,2,'Filter coefficient 5','lsb?')
    COEFF_06 = r(0x00DA,2,'Filter coefficient 6','lsb?')
    COEFF_07 = r(0x00DC,2,'Filter coefficient 7','lsb?')
    COEFF_08_FILTERDIV = r(0x00DE,2,'Filter divide factor (0..11)','lsb?')
    #FACTCALTABLE = r(0x0100, 256, 'Factory calibration data space')
