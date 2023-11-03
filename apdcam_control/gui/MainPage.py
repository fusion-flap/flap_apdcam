import sys
import re
import time

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt

from .ApdcamUtils import *

class MainPage(QtWidgets.QWidget):
    def __init__(self,parent):
        super(MainPage,self).__init__(parent)

        self.gui = parent

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        addressGroupBox = QGridGroupBox("")
        layout.addWidget(addressGroupBox) #,Qt.AlignmentFlag.AlignLeft)
        addressGroupBox.addWidget(QtWidgets.QLabel("Address:"),0,0)
        self.addressEntry = QtWidgets.QLineEdit()
        self.addressEntry.setText("10.123.13.102")
        #self.addressEntry.setText("10.123.13.101")
        self.addressEntry.setToolTip("The IP address of the camera")
        addressGroupBox.addWidget(self.addressEntry,0,1)
        addressGroupBox.addWidget(QtWidgets.QLabel("Interface: "),1,0)
        self.interface = QtWidgets.QLineEdit()
        addressGroupBox.addWidget(self.interface,1,1)

        layout.addWidget(QtWidgets.QLabel("Camera type:"))
        self.cameraType = QtWidgets.QTextEdit()
        self.cameraType.setToolTip("Firmware and other hardware info, obtained from the camera when connecting to it")
        layout.addWidget(self.cameraType)

        l = QtWidgets.QHBoxLayout()
        layout.addLayout(l)

        self.connectCameraButton = QtWidgets.QPushButton("Connect camera")
        self.connectCameraButton.clicked.connect(self.cameraOn)
        self.connectCameraButton.setToolTip("Connect to the camera at the given IP address, and update the GUI control values from the actual camera settings, whereever possible")
        l.addWidget(self.connectCameraButton)

        self.disconnectCameraButton = QtWidgets.QPushButton("Disconnect camera")
        self.disconnectCameraButton.clicked.connect(self.cameraOff)
        self.disconnectCameraButton.setToolTip("Disconnect from the camera")
        l.addWidget(self.disconnectCameraButton)

        self.startGuiUpdateButton = QtWidgets.QPushButton("Start GUI update")
        self.startGuiUpdateButton.clicked.connect(self.gui.startGuiUpdate)
        l.addWidget(self.startGuiUpdateButton)

        self.stopGuiUpdateButton = QtWidgets.QPushButton("Stop GUI update")
        self.stopGuiUpdateButton.clicked.connect(self.gui.stopGuiUpdate)
        l.addWidget(self.stopGuiUpdateButton)

        self.cameraConnectedStatus = QtWidgets.QLabel("Camera status: camera disconnected");
        l.addWidget(self.cameraConnectedStatus)

        layout.addWidget(QtWidgets.QLabel("Connection messages"))

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)

    def cameraOff(self):
        self.gui.stopGuiUpdate()
        self.cameraConnectedStatus.setText("Camera status: disconnected")
        self.gui.status.connected = False
        self.gui.camera.close()  # APDCAM10G.controller should handle the case if camera is on or off when calling close()
        self.gui.show_message("Camera disconnected")

    def cameraOn(self):
        """
        Connects to APDCAM
        """

        #self.messages.setText("") # clear previous messages
        self.cameraType.setText("")

        # Check if the IP Address if of the right format: 4 integers separated by dot
        if not re.search("^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$",self.addressEntry.text()):
            self.messages.append("Bad IP address: '" + self.addressEntry.text() + "'")
            QtWidgets.QApplication.processEvents()
            return

        # Try 10 times
        for i in range(10) :
            # self.gui.camera.HV_conversion = [0.12,0.12,0.12,0.12]
            # there is already HV_conversion_in and HV_conversion_out
            self.messages.append("Trying to connect to " + self.addressEntry.text())
            QtWidgets.QApplication.processEvents()
            ret = self.gui.camera.connect(ip=self.addressEntry.text())
            if (ret == ""):
                time.sleep(1) 
                break
            self.gui.camera.close()
            time.sleep(1)  
        if ret != "" :
            self.messages.append(ret)
            self.gui.show_error("Failed to connect to camera at the address " + self.addressEntry.text())
            QtWidgets.QApplication.processEvents()
            self.cameraOff()
            self.gui.status.connected = False
            return
        self.cameraConnectedStatus.setText("Camera status: connected")
        self.gui.status.connected = True

        self.cameraType.append("CC card serial number: " + str(self.gui.camera.status.CC_serial))
        self.cameraType.append("CC card firmware:      " + self.gui.camera.status.CC_firmware.decode('utf-8'))
        
        self.cameraType.append("")
        self.cameraType.append("PC card serial no.:    " + str(self.gui.camera.status.PC_serial))
        self.cameraType.append("PC card firmware:      " + self.gui.camera.status.PC_FW_version)

        nAdcBoards = len(self.gui.camera.status.ADC_address) 
        self.gui.adcControl.clearAdcs()
        for i in range(nAdcBoards):
            self.cameraType.append("")
            self.cameraType.append("ADC " + str(i+1))
            self.cameraType.append("   Address:      " +  str(self.gui.camera.status.ADC_address[i]))
            self.cameraType.append("   FPGA Version: " +  self.gui.camera.status.ADC_FPGA_version[i])
            self.cameraType.append("   MC Version:   " +  self.gui.camera.status.ADC_MC_version[i])
            self.cameraType.append("   Serial no.:   " +  str(self.gui.camera.status.ADC_serial[i]))
            self.gui.adcControl.addAdc(i+1,self.gui.camera.status.ADC_address[i])

        self.gui.version_specific_setup()

        err = self.gui.camera.readStatus()
        if (err != "") :
            self.messages.append(err)
            self.gui.show_error(err)
            self.cameraOff()
            return

        self.gui.startGuiUpdate()
        self.gui.initSettingsOnConnect()
