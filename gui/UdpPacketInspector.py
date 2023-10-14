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
from APDCAM10G_control import *


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class UdpPacketInspector(QtWidgets.QWidget):
    def __init__(self,parent):
        super(UdpPacketInspector,self).__init__(parent)

        self.parent = parent
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

    def getData(self):
        self.gui.stopGuiUpdate()
        time.sleep(1)

        for i in range(4):
            self.packetsDisplay[i].setText("")
            self.summaryDisplay[i].setText("")

        n = self.numberOfSamples.value()
        error,warning,data_receiver = self.gui.camera.measure(numberOfSamples=n,dataReceiver="python",logger=self.gui)
        if error!="":
            self.gui.showError(error)
        if warning!="":
            self.gui.showWarning(warning)

        #self.gui.showMessage("Stream start time 1: " + str(data_receiver.stream_start_time_1))
        #self.gui.showMessage("Stream start time 2: " + str(data_receiver.stream_start_time_2))

        packets = data_receiver.getPackets()
        if packets is None:
            self.gui.showError("Did not receive any data")
            return
        if not isinstance(packets,list):
            self.gui.showError("Received packets is not a list")
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
