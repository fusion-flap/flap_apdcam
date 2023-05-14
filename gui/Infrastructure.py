import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from ApdcamUtils import *
from GuiMode import *

class Infrastructure(QtWidgets.QWidget):
    def __init__(self,parent):
        self.gui = parent
        super(Infrastructure,self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        l1 = QtWidgets.QVBoxLayout()
        layout.addLayout(l1)

        hv = QVGroupBox("HV settings")
        l1.addWidget(hv)
        self.readHvStatusButton = QtWidgets.QPushButton("Read HV Status")
        self.readHvStatusButton.clicked.connect(self.readHvStatus)
        hv.addWidget(self.readHvStatusButton)

        l = QtWidgets.QHBoxLayout()
        hv.addLayout(l)
        self.hvSet = [None]*4
        self.hvActual = [None]*4
        self.hvMax = [None]*4
        self.hvOn = [None]*4
        self.hvOff = [None]*4
        self.hvGroup = [None]*4
        for i in range(4):
            self.hvGroup[i] = QGridGroupBox()
            l.addWidget(self.hvGroup[i])
            self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" set"),0,0)
            self.hvSet[i] = QDoubleEdit()
            self.hvSet[i].setMaximumWidth(40)

            self.hvSet[i].returnPressed.connect(self.gui.call(lambda i=i: self.gui.camera.setHV(i+1,self.hvSet[i].value())))

            self.hvGroup[i].addWidget(self.hvSet[i],0,1)
            self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" act."),1,0)
            self.hvActual[i] = QtWidgets.QLineEdit()
            self.hvActual[i].setMaximumWidth(40)
            self.hvActual[i].setEnabled(False)
            self.hvGroup[i].addWidget(self.hvActual[i],1,1)
            self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" max."),2,0)
            self.hvMax[i] = QtWidgets.QLineEdit()
            self.hvMax[i].setMaximumWidth(40)
            self.hvGroup[i].addWidget(self.hvMax[i],2,1)
            ll = QtWidgets.QHBoxLayout()
            self.hvGroup[i].addLayout(ll,3,0,1,2)
            self.hvOn[i] = QtWidgets.QPushButton("ON" + str(i+1))
            self.hvOn[i].setStyleSheet("padding:4px;")
            self.hvOn[i].setToolTip("Switch HV generatlr #" + str(i+1) + " on")
            self.hvOn[i].clicked.connect(self.gui.call(lambda i=i: self.gui.camera.hvOnOff(i+1,True), \
                                                       name="self.gui.camera.hvOnOff(" + str(i+1) + ",True)", \
                                                       where=__file__))
            ll.addWidget(self.hvOn[i])
            self.hvOff[i] = QtWidgets.QPushButton("OFF" + str(i+1))
            self.hvOff[i].setStyleSheet("padding:4px;")
            self.hvOn[i].setToolTip("Switch HV generatlr #" + str(i+1) + " off")
            self.hvOff[i].clicked.connect(self.gui.call(lambda i=i: self.gui.camera.hvOnOff(i+1,False), \
                                                        name="self.gui.camera.hvOnOff(" + str(i+1) + ",False)", \
                                                        where=__file__))
            ll.addWidget(self.hvOff[i])
        l.addStretch(1)

        l = QtWidgets.QHBoxLayout()
        hv.addLayout(l)
        self.hvEnableButton = QtWidgets.QPushButton("HV Enable")
        self.hvEnableButton.setToolTip("Enable high voltage")
        self.hvEnableButton.clicked.connect(self.gui.call(lambda: self.gui.camera.enableHV(), name='self.gui.camera.enableHV()',where=__file__))
        l.addWidget(self.hvEnableButton)
        self.hvDisableButton = QtWidgets.QPushButton("HV Disable")
        self.hvDisableButton.setToolTip("Disable high voltage")
        self.hvDisableButton.clicked.connect(self.gui.call(lambda: self.gui.camera.enableHV(), name='self.gui.camera.disableHV()',where=__file__))
        l.addWidget(self.hvDisableButton)
        self.hvEnabledStatus = QtWidgets.QLabel("HV Disabled")
        l.addWidget(self.hvEnabledStatus)
        l.addStretch(1)

        shutter = QHGroupBox("Shutter control")
        l1.addWidget(shutter)
        self.shutterOpenButton = QtWidgets.QPushButton("Open")
        shutter.addWidget(self.shutterOpenButton)
        self.shutterCloseButton = QtWidgets.QPushButton("Close")
        shutter.addWidget(self.shutterCloseButton)
        self.shutterExternalControl = QtWidgets.QCheckBox()
        self.shutterExternalControl.setText("External control")
        shutter.addWidget(self.shutterExternalControl)
        shutter.addStretch(1)

        calib = QHGroupBox("Calibration light control")
        l1.addWidget(calib)
        calib.addWidget(QtWidgets.QLabel("Intensity:"))
        self.calibrationLightIntensity = QtWidgets.QSpinBox()
        self.calibrationLightIntensity.setMinimum(0)
        self.calibrationLightIntensity.setMaximum(4095)
        calib.addWidget(self.calibrationLightIntensity)
        calib.addStretch(1)

        l = QtWidgets.QHBoxLayout()
        l1.addLayout(l)
        l.addWidget(QtWidgets.QLabel("PC Error:"))
        self.pcError = QtWidgets.QLineEdit()
        self.pcError.setReadOnly(True)
        l.addWidget(self.pcError)

        self.controlFactoryResetButton = QtWidgets.QPushButton("Control factory reset")
        self.controlFactoryResetButton.guiMode = GuiMode.factory
        l1.addWidget(self.controlFactoryResetButton)
        

        g = QGridGroupBox("Temperatures")
        layout.addWidget(g)
        tmp = [["01","temp01"],
            ["02","temp02"],
            ["03","temp03"],
            ["04","temp04"],
            ["Detector 1","tempDetector1"],
            ["Analog panel 1","tempAnalog1"],
            ["Analog panel 2","tempAnalog2"],
            ["Detector 2","tempDetector2"],
            ["Analog panel 3","tempAnalog3"],
            ["Analog panel 4","tempAnalog4"],
            ["Baseplate","tempBasePlate"],
            ["12","temp12"],
            ["13","temp13"],
            ["PC card heatsink","tempPcCardHeatsink"],
            ["Power panel 1","tempPowerPanel1"],
            ["Power panel 2","tempPowerPanel2"]]

        for i in range(len(tmp)):
            g.addWidget(QtWidgets.QLabel(tmp[i][0]),i,0)
            t = QtWidgets.QLineEdit()
            setattr(self,tmp[i][1],t)
            t.setEnabled(False)
            g.addWidget(t,i,1)

        self.readTempsButton = QtWidgets.QPushButton("Read temps")
        g.addWidget(self.readTempsButton,len(tmp),0)

#        self.readWeightsButton = QtWidgets.QPushButton("Read weights")
#        g.addWidget(self.readWeightsButton,len(tmp),1)
        g.setRowStretch(g.rowCount(),1)

        # g = QGridGroupBox("Fan 1")
        # layout.addWidget(g)
        # self.fan1Mode = QtWidgets.QComboBox()
        # self.fan1Mode.addItem("Auto")
        # self.fan1Mode.addItem("Manual")
        # g.addWidget(self.fan1Mode,0,0,1,2)
        # g.addWidget(QtWidgets.QLabel("Speed"),1,0)
        # self.fan1Speed = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Speed,1,1)
        # g.addWidget(QtWidgets.QLabel("Diff"),2,0)
        # self.fan1Diff = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Diff,2,1)
        # g.addWidget(QtWidgets.QLabel("Ref"),3,0)
        # self.fan1Ref = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Ref,3,1)
        # g.addWidget(QtWidgets.QLabel("Ctrl"),4,0)
        # self.fan1Ctrl = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Ctrl,4,1)
        
        g.setRowStretch(g.rowCount(),1)

        layout.addStretch(1)

    def readHvStatus(self):
        self.gui.showError("Infrastructure.readHvStatus not implemented yet")

    def setHvGroups(self,n):
        """
        Set the number of HV groups, i.e.the number of ADC Boards.
        Instead of dynamically adding/removing them, the GUI creates the maximally possible 4 groups,
        and disables those which are not in the hardware
        """
        for i in range(4):
            if i >= n:
                self.hvGroup[i].setEnabled(False)
            else:
                self.hvGroup[i].setEnabled(True)

