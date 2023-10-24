import sys
import re
import time

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

from ApdcamUtils import *
sys.path.append('/home/barna/fusion-instruments/apdcam/sw/flap_apdcam/apdcam_control')
import APDCAM10G

def pseudoTestPatternFast(adc_bits=14):
    # we represent each bit by an integer (0/1)
    # Even though this pseudo-random sequence has a period of 511, we start with 1022
    # because we want to have an integer number of times the number of ADC bits. ADC bits is 8, 12 or 14
    # so we will need an even number of bits, for sure
    bits = 1022
    bitseq = bytearray(bits)
    bitseq[0:8] = [1,1,1,1,1,0,1,1]  # first 8 bits
    for i in range(bits-8):
        c = (bitseq[4]+bitseq[8])%2
        bitseq[1:bits] = bitseq[0:bits-1]  # shift the array forward by 1 index
        bitseq[0] = c

    # Now replicate the bit-sequence as many times as needed to fit an integer times the number
    # of ADC bits
    bitseq1 = bitseq
    for i in range(14):
        if len(bitseq)%adc_bits == 0:
            break
        bitseq = bitseq + bitseq1

    # the number of generated samples (adc_bits bits transformed into integers)    
    sample_len = len(bitseq)/adc_bits

    pseudo_samples = [0]*sample_len
    for isample in range(1,sample_len+1):
        for bit in range(adc_bits):
            if bitseq[len(bitseq)-isample*adc_bits+bit]:
                pseudo_samples[isample] |= 1<<bit;
        
    return pseudo_samples

        
class UdpPacketInspector(QtWidgets.QWidget):
    def __init__(self,parent):
        super(UdpPacketInspector,self).__init__(parent)

        #self.parent = parent
        self.gui = parent.gui

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        commands = QtWidgets.QHBoxLayout()
        layout.addLayout(commands,0,0,1,4)
        commands.addWidget(QtWidgets.QLabel("Number of samples: "))
        self.numberOfSamples = QtWidgets.QSpinBox()
        self.numberOfSamples.setFixedWidth(300)
        self.numberOfSamples.setMaximum(100000)
        self.numberOfSamples.setValue(1000)
        commands.addWidget(self.numberOfSamples)
        self.getDataButton = QtWidgets.QPushButton("Get data")
        self.getDataButton.setToolTip("Read the specified number of samples from the camera and display an analysis result of the received packets")
        self.getDataButton.clicked.connect(self.getData)
        commands.addWidget(self.getDataButton)
        commands.addStretch(1)

        self.summaryDisplay = [None]*4
        self.packetsDisplay = [None]*4

        self.stream = [None]*4
        for i in range(4):
            self.summaryDisplay[i] = QtWidgets.QTextEdit()
            self.summaryDisplay[i].setFixedHeight(80)
            self.summaryDisplay[i].setText("ADC " + str(i+1) + " summary")
            layout.addWidget(self.summaryDisplay[i],1,i)
            self.packetsDisplay[i] = QtWidgets.QTextEdit()
            self.packetsDisplay[i].setText("Packet info listing")
            layout.addWidget(self.packetsDisplay[i],2,i)

    def matchPseudo(self,packets):
        """
        Generate a peuseo random number pattern according to the standard, and try to match against the received
        data from the ADC

        Parameters:
        ^^^^^^^^^^^
        packets: list of UDP packets from a given ADC board
        """

        

    def getData(self):
        self.gui.stopGuiUpdate()
        time.sleep(1)

        for i in range(4):
            self.packetsDisplay[i].setText("")
            self.summaryDisplay[i].setText("")

        n = self.numberOfSamples.value()
        error,warning,data_receiver = self.gui.camera.measure(numberOfSamples=n,dataReceiver="python",logger=self.gui)
        if error!="":
            self.gui.show_error(error)
        if warning!="":
            self.gui.show_warning(warning)

        #self.gui.show_message("Stream start time 1: " + str(data_receiver.stream_start_time_1))
        #self.gui.show_message("Stream start time 2: " + str(data_receiver.stream_start_time_2))

        packets = data_receiver.packets
        if packets is None:
            self.gui.show_error("Did not receive any data")
            return
        if not isinstance(packets,list):
            self.gui.show_error("Received packets is not a list")
            return

        for i_adc in range(len(packets)):
            if packets[i_adc] is None:
                continue

            first = True
            receivedPackets = 0
            #self.packetsDisplay[i_adc].setText("")
            for i_packet in range(len(packets[i_adc])):
                print("i_packet = " + str(i_packet))
                p = packets[i_adc][i_packet]
                if not first:
                    print("-------------------")
                    self.packetsDisplay[i_adc].append("--------------------------")
                print("#" + str(i_packet) + " @" + str(p.time()))
                self.packetsDisplay[i_adc].append("#" + str(i_packet) + " @" + str(p.time()))
                print("Planned: " + str(p.plannedFirstSampleNumber) + "(" + str(p.plannedFirstSampleStartByte) + ") -- " + str(p.plannedLastSampleNumber) + "(" + str(p.plannedLastSampleStopByte) + ")")
                self.packetsDisplay[i_adc].append("Planned: " + str(p.plannedFirstSampleNumber) + "(" + str(p.plannedFirstSampleStartByte) + ") -- " + str(p.plannedLastSampleNumber) + "(" + str(p.plannedLastSampleStopByte) + ")")
                if p.received():
                    print("Sample: " + str(p.firstSampleNumber()) + "(" + ("full" if p.firstSampleFull() else "partial") + ")")
                    self.packetsDisplay[i_adc].append("Sample: " + str(p.firstSampleNumber()) + "(" + ("full" if p.firstSampleFull() else "partial") + ")")
                    receivedPackets += 1
                else:
                    print("MISSING")    
                    self.packetsDisplay[i_adc].append("MISSING")    
                first = False
                
            self.summaryDisplay[i_adc].append("Bytes/sample: " + str(data_receiver.bytes_per_sample[i_adc]))
            self.summaryDisplay[i_adc].append("Expected: " + str(len(packets[i_adc])) + ". Received: " + str(receivedPackets))
            self.summaryDisplay[i_adc].append("Number of data bytes in packet: " + str(data_receiver.octet) + "*8 = " + str(data_receiver.octet*8))

        self.gui.startGuiUpdate()

        c1 = data_receiver.get_channel_signals(1,1)
        c2 = data_receiver.get_channel_signals(2,1)
        n = 1000
        if c1 is not None:
            print("Length of c1: " + str(len(c1)))
            if len(c1)<n:
                n = len(c1)
        if c2 is not None: 
            print("Length of c2: " + str(len(c2)))
            if len(c2)<n:
                n = len(c2)

        for i in range(n):
            print("  >> " + (str(c1[i]) if c1 is not None else "") + " " + (str(c2[i]) if c2 is not None else ""))
