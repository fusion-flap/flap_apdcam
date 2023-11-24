import sys
import re
import time

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

from .ApdcamUtils import *
sys.path.append('/home/barna/fusion-instruments/apdcam/sw/flap_apdcam/apdcam_control')
import APDCAM10G_control

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
        self.numberOfSamples.setToolTip("Set the number of samples to be read from the camera")
        self.numberOfSamples.lineEdit().returnPressed.connect(self.get_data)
        commands.addWidget(self.numberOfSamples)
        self.useTestPattern = QtWidgets.QCheckBox("Use test pattern")
        self.useTestPattern.setToolTip("Set the camera (only temporarily) to send the short pseudo-random sequence, then reset the test pattern flag to the original value")
        self.useTestPattern.setChecked(True)
        commands.addWidget(self.useTestPattern)

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

        return full_match,matches

    def find_in_pattern(self,channel_data,pattern):
        # Each element of this list is a 2-element list, of which the first element is the index in the pseudo-random sequence,
        # the second element is a string containing info about the match. 
        result = []
        for i in range(len(channel_data)):
            # If no channel data has been found in the pattern sequence so far, store a "[dataindex:patternindex]" string
            # as a feedback for the user, where dataindex is the index of the data series (if this is non-zero, the user
            # will recognize that earlier data values were not matched), and patternindex is the index within the pseudo-random
            # sequence where the match was found
            if len(result) == 0:
                try:
                    index = pattern.index(channel_data[i])
                    result.append([index, "[" + str(i) + ":" + str(index) + "]"])
                except:
                    return result
            # otherwise if there was a previous match already, we report relative index offsets w.r.t. the last match.
            # Ideally these increments should be equal to SAMPLEDIV
            else:
                # relative index w.r.t. to the last match position
                this_element_found = False
                for j in range(1,len(pattern)):
                    index = (result[len(result)-1][0]+j) % len(pattern)
                    if pattern[index] == channel_data[i]:
                        result.append([index,"+" + str(j)])
                        this_element_found = True
                        break
                if not this_element_found:
                    result.append([result[len(result)-1][0],"[-]"])
        return result

    def get_data(self):
        self.gui.stopGuiUpdate()
        time.sleep(1)

        self.gui.show_warning("WE SHOULD QUERY THE CAMERA TO GET THE RESOLUTIONS FOR EACH ADC BOARDS, AND GET THE TEST PATTERN CODE TO AUTOMATICALLY MAKE A TEST PATTERN MATCH WITH THE CORRECT RESOLUTION")

        useTestPattern = self.useTestPattern.isChecked()
        origTestPatterns = []
        if useTestPattern:
            error,origTestPatterns = self.gui.camera.getTestPattern('all')
            print("---------------")
            print(origTestPatterns)
            self.gui.camera.setTestPattern('all',6)

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
            print("No data_receiver obejct: " + error)

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
                    s += "  Serial: " + str(p.header.serial())
                s += "   @" + str(p.time())
                if p.header.udpTestMode():
                    s += " (UDP test mode!)"
                print(s)
                self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel(s))

                s = "Planned: " + str(p.plannedFirstSampleNumber) + "(" + str(p.plannedFirstSampleStartByte) + ") -- " + str(p.plannedLastSampleNumber) + "(" + str(p.plannedLastSampleStopByte) + ")"
                print(s)
                self.packets_display_layout[i_adc].addWidget(QtWidgets.QLabel(s))
                if p.received():
                    s = "Sample: " + str(p.header.sampleCounter()) + "(" + ("full" if p.header.firstSampleFull() else "partial") + ")"
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

        if useTestPattern:
            self.gui.camera.readStatus()
            samplediv = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV:self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV+2]
            samplediv = int.from_bytes(samplediv,'big')

            for i_adc in range(len(self.gui.camera.status.ADC_address)):
                bits = int(self.gui.adcControl.adc[i_adc].bits.currentText())
                pattern = pseudo_test_pattern_fast(bits)
                error_display = None
                all_channels_ok = True
                for i_channel in range(32):
                    if not self.gui.adcControl.adc[i_adc].channelOn[i_channel].isChecked():
                        continue
                    channel_data = data_receiver.get_channel_data(i_adc+1,i_channel+1)
                    ok,matches = self.match_pattern(channel_data,pattern,samplediv)
                    
                    if not ok:
                        all_channels_ok = False
                        if error_display is None:
                            error_display = QtWidgets.QTextEdit()
                            self.packets_display_layout[i_adc].addWidget(error_display)
                        details = self.find_in_pattern(channel_data,pattern)
                        error_display.append("--------- channel " + str(i_channel+1) + " -------------")
                        s = ""
                        for a in details:
                            if s != "":
                                s += " "
                            s += a[1]
                        error_display.append(s)

                if not all_channels_ok:
                    self.summary_display[i_adc].append("<font color='red'>Pattern match failed for some channels</font>")
                else:
                    self.summary_display[i_adc].append("<font color='green'>Pattern match OK for all channels</font>")
            self.gui.camera.setTestPattern('all',origTestPatterns)



        
