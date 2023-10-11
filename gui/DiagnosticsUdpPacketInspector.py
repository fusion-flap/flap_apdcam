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

class DiagnosticsUdpPacketInspector(QtWidgets.QWidget):
    def __init__(self,parent):
        super(DiagnosticsUdpPacketInspector,self).__init__(parent)

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

        self.summary = [None]*4
        self.stream = [None]*4
        self.streamWidget = [None]*4
        self.streamWidgetLayout = [None]*4
        for i in range(4):
            self.summary[i] = QtWidgets.QLabel("Stream " + str(i+1))
            layout.addWidget(self.summary[i],1,i)
            self.stream[i] = QtWidgets.QScrollArea()
            #self.stream[i].setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            layout.addWidget(self.stream[i],2,i)

    def getData(self):
        self.gui.stopGuiUpdate()
        time.sleep(1)
        n = self.numberOfSamples.value()
        error,warning,data_receiver = self.gui.camera.measure(numberOfSamples=n,dataReceiver="python",logger=self.gui)
        if error!="":
            self.gui.showError(error)
        if warning!="":
            self.gui.showWarning(warning)

        packets = data_receiver.getPackets()
        if packets is None:
            self.gui.showError("Did not receive any data")
            return
        if not isinstance(packets,list):
            self.gui.showError("Received packets is not a list")
            return

        for i in range(4):
            if self.streamWidget[i] is not None:
                self.streamWidget[i].deleteLater()
            self.streamWidget[i] = QtWidgets.QWidget()
            self.streamWidgetLayout[i] = QtWidgets.QVBoxLayout()
            self.streamWidget[i].setLayout(self.streamWidgetLayout[i])
            l = self.streamWidgetLayout[i]

            stream_packets = packets[i]
            if stream_packets is None:
                self.gui.showError("Packets is None for stream " + str(i+1))
                continue

            first = True
            receivedPackets = 0
            for p in stream_packets:
                if not first:
                    l.addWidget(QHLine())
                label = None
                if p is None:
                    label = QtWidgets.QLabel("Missing")
                else:
                    txt = str(p.packetNumber()) + "@" + str(p.time()) + " Sample: " + str(p.firstSampleNumber()) + "(" + ("full" if p.firstSampleFull() else "partial") + ") - ??? (tbd)"
                    label = QtWidgets.QLabel(txt)
                    receivedPackets += 1
                #label.setAutoFillBackground(False)
                label.setStyleSheet("background-color: rgba(255,255,255,1);")
                l.addWidget(label)
                first = False

            self.summary[i].setText("Expected: " + str(len(stream_packets)) + ". Received: " + str(receivedPackets))

            self.streamWidget[i].setStyleSheet("background-color: rgba(255,255,255,0);")
            self.stream[i].setWidget(self.streamWidget[i])
        self.gui.startGuiUpdate()
