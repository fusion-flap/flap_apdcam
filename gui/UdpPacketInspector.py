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

class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

def pseudo_test_pattern_fast(adc_bits=14):
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
    sample_len = len(bitseq)//adc_bits
    assert sample_len*adc_bits == len(bitseq)

    pseudo_samples = [0]*sample_len
    for isample in range(sample_len):
        for bit in range(adc_bits):
            if bitseq[len(bitseq)-(isample+1)*adc_bits+bit]:
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
        self.numberOfSamples.setValue(200)
        self.numberOfSamples.lineEdit().returnPressed.connect(self.get_data)
        commands.addWidget(self.numberOfSamples)
        self.getDataButton = QtWidgets.QPushButton("Get data")
        self.getDataButton.setToolTip("Read the specified number of samples from the camera and display an analysis result of the received packets")
        self.getDataButton.clicked.connect(self.get_data)
        commands.addWidget(self.getDataButton)
        commands.addStretch(1)

        self.summary_display = [None]*4
        self.packets_display = [None]*4
        self.packets_display_layout = [None]*4

        self.stream = [None]*4
        for i in range(4):
            self.summary_display[i] = QtWidgets.QTextEdit()
            self.summary_display[i].setFixedHeight(80)
            self.summary_display[i].setText("ADC " + str(i+1) + " summary")
            layout.addWidget(self.summary_display[i],1,i)
            self.packets_display[i] = QtWidgets.QScrollArea()
            self.packets_display[i].setWidgetResizable(True)
            
            #self.packetsDisplay[i] = QtWidgets.QTextEdit()
            #self.packetsDisplay[i].setText("Packet info listing")
            layout.addWidget(self.packets_display[i],2,i)
        self.init_packets_displays()


    def init_packets_displays(self):
        for i in range(4):
            w = self.packets_display[i].widget()
            if w is not None:
                w.deleteLater()
            w = QtWidgets.QWidget()
            self.packets_display_layout[i] = QtWidgets.QVBoxLayout()
            w.setLayout(self.packets_display_layout[i])
            self.packets_display[i].setWidget(w)

    def match_pattern(self,signals,pattern,samplediv):
        """
        Generate a peuseo random number pattern according to the standard, and try to match against the received
        data from the ADC

        Parameters:
        ^^^^^^^^^^^
        signals: a list of values corresponding to subsequent samples from a single channel
        pattern: the pseudo-random sequence, which is assumed to be periodic

        Returns:
        ^^^^^^^^
        True/False: indicating whether a full match was found
        matches   : a list of (eventually partial) matches. Each element of this list is a 2-element list, 
                    the first element being the start index of the signal sequence within the pattern sequence,
                    the 2nd element is the length of values matching
        
        """

        # A list of matches. Each element of this list is a 2-element list, the first element of which is
        # the starting position of the match within the pattern sequence, the 2nd element is the length of the match
        matches = []

        n = len(pattern)

        if signals is None:
            return False,[]

        # Find the locations where the first element of the signals is found
        for i in range(n):
            if signals[0] == pattern[i]:
                matches.append([i,1])  # So far we matched 1 value at index i

        # If the first signal was not found, we finish
        if len(matches) == 0:
            return False,matches

        print("Length of initial matches: " + str(len(matches)))

        full_match = False
        for i_signal in range(1,len(signals)):
            for match in matches:
                # match[1] is the number of matching characters. It must be equal to i_signal, otherwise
                # the match was broken already before, so we should not continue comparing
                if match[1] != i_signal:
                    continue

                # index within the pattern sequence, cyclized
                pattern_index = (match[0]+i_signal*samplediv)%n

                # If we match this element as well, increase the number of 
                if pattern[pattern_index] == signals[i_signal]:
                    match[1] += 1
                    # If this is the last signal value and we matched, we have a full match
                    if i_signal == len(signals)-1:
                        full_match = True
                else:
                    for j in range(n):
                        if signals[i_signal] == pattern[j]:
                            print("Not found where needed (" + str(pattern_index) + "), but elsewhere: " + str(j))

        return full_match,matches

    def find_in_pattern(self,signals,pattern):
        n = 1000000
        for i in range(len(signals)):
            if signals[i] is None:
                continue
            if(len(signals[i]) < n):
                n = len(signals[i])
        for s in range(n):
            line = f'{s:03d}'+ ": " 
            for i in range(len(signals)):
                if signals[i] is None:
                    continue
                try:
                    index = pattern.index(signals[i][s])
                    index = "[" + f'{index:03d}' + "]  "
                except:
                    index = "[---]  "
                line += f'{signals[i][s]:6d}' + " " + index
            print(line)

    def get_data(self):
        self.gui.stopGuiUpdate()
        time.sleep(1)

        self.gui.show_warning("WE SHOULD QUERY THE CAMERA TO GET THE RESOLUTIONS FOR EACH ADC BOARDS, AND GET THE TEST PATTERN CODE TO AUTOMATICALLY MAKE A TEST PATTERN MATCH WITH THE CORRECT RESOLUTION")

        for i in range(4):
            self.summary_display[i].setText("")

        n = self.numberOfSamples.value()
        error,warning,data_receiver = self.gui.camera.measure(numberOfSamples=n,dataReceiver="python",logger=self.gui)
        if error!="":
            self.gui.show_error(error)
        if warning!="":
            self.gui.show_warning(warning)
        if data_receiver is None:
            self.gui.show_error("No data_receiver object: " + error)

        #self.gui.show_message("Stream start time 1: " + str(data_receiver.stream_start_time_1))
        #self.gui.show_message("Stream start time 2: " + str(data_receiver.stream_start_time_2))

        packets = data_receiver.packets
        if packets is None:
            self.gui.show_error("Did not receive any data")
            return
        if not isinstance(packets,list):
            self.gui.show_error("Received packets is not a list")
            return

        self.init_packets_displays()
        
        for i_adc in range(len(packets)):
            if packets[i_adc] is None:
                continue

            first = True
            receivedPackets = 0
            for i_packet in range(len(packets[i_adc])):
                print("i_packet = " + str(i_packet))
                p = packets[i_adc][i_packet]
                if not first:
                    print("-------------------")
                    l = QHLine()
                    self.packets_display_layout[i_adc].addWidget(l)

                s = "#" + str(i_packet)
                if p.received():
                    s += "  Serial: " + str(p.serial())
                s += "   @" + str(p.time())
                if p.udp_test_mode():
                    s += " (UDP test mode!)"
                print(s)
                self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel(s))

                s = "Planned: " + str(p.plannedFirstSampleNumber) + "(" + str(p.plannedFirstSampleStartByte) + ") -- " + str(p.plannedLastSampleNumber) + "(" + str(p.plannedLastSampleStopByte) + ")"
                print(s)
                self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel(s))
                if p.received():
                    s = "Sample: " + str(p.firstSampleNumber()) + "(" + ("full" if p.firstSampleFull() else "partial") + ")"
                    print(s)
                    self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel(s))
                    receivedPackets += 1
                else:
                    print("MISSING")    
                    self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel("MISSING"))
                first = False
                
            self.packets_display_layout[i_adc].addStretch(1)

            self.summary_display[i_adc].append("Bytes/sample: " + str(data_receiver.bytes_per_sample[i_adc]))
            self.summary_display[i_adc].append("Expected: " + str(len(packets[i_adc])) + ". Received: " + str(receivedPackets))
            self.summary_display[i_adc].append("Number of data bytes in packet: " + str(data_receiver.octet) + "*8 = " + str(data_receiver.octet*8))

        self.gui.startGuiUpdate()

        pattern = pseudo_test_pattern_fast(14)

        # for i_adc in range(2):
        #     print("--------- ADC " + str(i_adc+1) + " ------------")
        #     for i_channel in range(32):
        #         print("CHANNEL: " + str(i_channel+1))
        #         signals = data_receiver.get_channel_data(i_adc+1,i_channel+1)
        #         full,matches = self.match_pattern(signals,pattern)
        #         print(full, matches)

        c11 = data_receiver.get_channel_data(1,1)
        c18 = data_receiver.get_channel_data(1,8)
        c19 = data_receiver.get_channel_data(1,9)
        c115 = data_receiver.get_channel_data(1,15)
        c21 = data_receiver.get_channel_data(2,1)
        c22 = data_receiver.get_channel_data(2,2)

        print("BITS: " + str(data_receiver.bits))

        print("----- pattern matching --------")
        self.gui.camera.readStatus()
        samplediv = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV:self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV+2]
        samplediv = int.from_bytes(samplediv,'big')

        print("Samplediv: " + str(samplediv))

        self.find_in_pattern([c11,c18,c19,c115,c21,c22],pattern)

        print(self.match_pattern(c11,pattern,samplediv))
        print(self.match_pattern(c18,pattern,samplediv))
        print(self.match_pattern(c19,pattern,samplediv))
        print(self.match_pattern(c115,pattern,samplediv))
        print(self.match_pattern(c21,pattern,samplediv))
        print(self.match_pattern(c22,pattern,samplediv))

        print("-------------------------------")
        
