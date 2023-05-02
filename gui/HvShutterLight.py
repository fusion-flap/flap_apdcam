import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from ApdcamUtils import *


class HvShutterLight(QtWidgets.QWidget):
    def __init__(self,parent):
        super(HvShutterLight,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        hv = QVGroupBox("HV settings")
        layout.addWidget(hv)
        self.readHvStatus = QtWidgets.QPushButton("Read HV Status")
        hv.addWidget(self.readHvStatus)

        l = QtWidgets.QHBoxLayout()
        hv.addLayout(l)
        self.hvSet = [None]*4
        self.hvActual = [None]*4
        self.hvMax = [None]*4
        self.hvOn = [None]*4
        self.hvOff = [None]*4
        for i in range(4):
            g = QGridGroupBox()
            l.addWidget(g)
            g.addWidget(QtWidgets.QLabel("HV"+str(i+1)+" set"),0,0)
            self.hvSet[i] = QtWidgets.QLineEdit()
            self.hvSet[i].setMaximumWidth(40)
            self.hvSet[i].setEnabled(False)
            g.addWidget(self.hvSet[i],0,1)
            g.addWidget(QtWidgets.QLabel("HV"+str(i+1)+" act."),1,0)
            self.hvActual[i] = QtWidgets.QLineEdit()
            self.hvActual[i].setMaximumWidth(40)
            self.hvActual[i].setEnabled(False)
            g.addWidget(self.hvActual[i],1,1)
            g.addWidget(QtWidgets.QLabel("HV"+str(i+1)+" max."),2,0)
            self.hvMax[i] = QtWidgets.QLineEdit()
            self.hvMax[i].setMaximumWidth(40)
            g.addWidget(self.hvMax[i],2,1)
            ll = QtWidgets.QHBoxLayout()
            g.addLayout(ll,3,0,1,2)
            self.hvOn[i] = QtWidgets.QPushButton("ON" + str(i+1))
            self.hvOn[i].setStyleSheet("padding:4px;")
            ll.addWidget(self.hvOn[i])
            self.hvOff[i] = QtWidgets.QPushButton("OFF" + str(i+1))
            self.hvOff[i].setStyleSheet("padding:4px;")
            ll.addWidget(self.hvOff[i])
        l.addStretch(1)

        l = QtWidgets.QHBoxLayout()
        hv.addLayout(l)
        self.hvEnableButton = QtWidgets.QPushButton("HV Enable")
        l.addWidget(self.hvEnableButton)
        self.hvDisableButton = QtWidgets.QPushButton("HV Disable")
        l.addWidget(self.hvDisableButton)
        self.hvEnabledStatus = QtWidgets.QLabel("HV Disabled")
        l.addWidget(self.hvEnabledStatus)
        l.addStretch(1)

        shutter = QHGroupBox("Shutter control")
        layout.addWidget(shutter)
        self.shutterOpenButton = QtWidgets.QPushButton("Open")
        shutter.addWidget(self.shutterOpenButton)
        self.shutterCloseButton = QtWidgets.QPushButton("Close")
        shutter.addWidget(self.shutterCloseButton)
        self.shutterExternalControl = QtWidgets.QCheckBox()
        self.shutterExternalControl.setText("External control")
        shutter.addWidget(self.shutterExternalControl)
        shutter.addStretch(1)

        calib = QHGroupBox("Calibration light control")
        layout.addWidget(calib)
        calib.addWidget(QtWidgets.QLabel("Intensity:"))
        self.calibrationLightIntensity = QtWidgets.QSpinBox()
        self.calibrationLightIntensity.setMinimum(0)
        self.calibrationLightIntensity.setMaximum(4095)
        calib.addWidget(self.calibrationLightIntensity)
        calib.addStretch(1)

        layout.addStretch(1)
