import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
from PyQt6.QtCore import Qt
from ApdcamUtils import *


class HvShutterLight(QWidget):
    def __init__(self,parent):
        super(HvShutterLight,self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        hv = QVGroupBox("HV settings")
        layout.addWidget(hv)
        self.readHvStatus = QPushButton("Read HV Status")
        hv.addWidget(self.readHvStatus,Qt.AlignmentFlag.AlignLeft)

        l = QHBoxLayout()
        hv.addLayout(l)
        self.hvSet = [None]*4
        self.hvActual = [None]*4
        self.hvMax = [None]*4
        self.hvOn = [None]*4
        self.hvOff = [None]*4
        for i in range(4):
            g = QGridGroupBox()
            l.addWidget(g)
            g.addWidget(QLabel("HV"+str(i+1)+" set"),0,0)
            self.hvSet[i] = QLineEdit()
            self.hvSet[i].setMaximumWidth(40)
            self.hvSet[i].setEnabled(False)
            g.addWidget(self.hvSet[i],0,1)
            g.addWidget(QLabel("HV"+str(i+1)+" act."),1,0)
            self.hvActual[i] = QLineEdit()
            self.hvActual[i].setMaximumWidth(40)
            self.hvActual[i].setEnabled(False)
            g.addWidget(self.hvActual[i],1,1)
            g.addWidget(QLabel("HV"+str(i+1)+" max."),2,0)
            self.hvMax[i] = QLineEdit()
            self.hvMax[i].setMaximumWidth(40)
            g.addWidget(self.hvMax[i],2,1)
            ll = QHBoxLayout()
            g.addLayout(ll,3,0,1,2)
            self.hvOn[i] = QPushButton("ON" + str(i+1))
            self.hvOn[i].setStyleSheet("padding:4px;")
            ll.addWidget(self.hvOn[i])
            self.hvOff[i] = QPushButton("OFF" + str(i+1))
            self.hvOff[i].setStyleSheet("padding:4px;")
            ll.addWidget(self.hvOff[i])
        l.addStretch(1)

        l = QHBoxLayout()
        hv.addLayout(l)
        self.hvEnableButton = QPushButton("HV Enable")
        l.addWidget(self.hvEnableButton)
        self.hvDisableButton = QPushButton("HV Disable")
        l.addWidget(self.hvDisableButton)
        self.hvEnabledStatus = QLabel("HV Disabled")
        l.addWidget(self.hvEnabledStatus)
        l.addStretch(1)

        shutter = QHGroupBox("Shutter control")
        layout.addWidget(shutter)
        self.shutterOpenButton = QPushButton("Open")
        shutter.addWidget(self.shutterOpenButton)
        self.shutterCloseButton = QPushButton("Close")
        shutter.addWidget(self.shutterCloseButton)
        self.shutterExternalControl = QCheckBox()
        self.shutterExternalControl.setText("External control")
        shutter.addWidget(self.shutterExternalControl)
        shutter.addStretch(1)

        calib = QHGroupBox("Calibration light control")
        layout.addWidget(calib)
        calib.addWidget(QLabel("Intensity:"))
        self.calibrationLightIntensity = QSpinBox()
        self.calibrationLightIntensity.setMinimum(0)
        self.calibrationLightIntensity.setMaximum(4095)
        calib.addWidget(self.calibrationLightIntensity)
        calib.addStretch(1)

        layout.addStretch(1)
