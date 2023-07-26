import sys
import re
import time

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt

from ApdcamUtils import *

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
        self.addressEntry.setText("10.123.13.101")
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

        # aaa = QtWidgets.QPushButton("Start GUI Update")
        # aaa.clicked.connect(lambda: self.gui.startGuiUpdate())
        # l.addWidget(aaa)

        self.disconnectCameraButton = QtWidgets.QPushButton("Disconnect camera")
        self.disconnectCameraButton.clicked.connect(self.cameraOff)
        self.disconnectCameraButton.setToolTip("Disconnect from the camera")
        l.addWidget(self.disconnectCameraButton)

        self.cameraConnectedStatus = QtWidgets.QLabel("Camera status: camera disconnected");
        l.addWidget(self.cameraConnectedStatus)

        layout.addWidget(QtWidgets.QLabel("Connection messages"))

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)

    def cameraOff(self):
        self.cameraConnectedStatus.setText("Camera status: disconnected")
        self.gui.status.connected = False
        self.gui.camera.close()  # APDCAM10G_control should handle the case if camera is on or off when calling close()
        self.gui.showMessage("Camera disconnected")
        self.gui.stopGuiUpdate()

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
            self.gui.showError("Failed to connect to camera at the address " + self.addressEntry.text())
            QtWidgets.QApplication.processEvents()
            self.cameraOff()
            self.gui.status.connected = False
            return
        self.cameraConnectedStatus.setText("Camera status: connected")
        self.gui.status.connected = True
        #self.cameraType.setText(" Firmware: {:s}".format(self.GUI_status.APDCAM_reg.status.firmware.decode('utf-8')))
        self.cameraType.append("Firmware: {:s}".format(self.gui.camera.status.firmware.decode('utf-8')))
        
        nAdcBoards = len(self.gui.camera.status.ADC_address) 
        self.gui.adcControl.clearAdcs()
        self.cameraType.append("")
        for i in range(nAdcBoards):
            self.cameraType.append("ADC " + str(i+1))
            self.cameraType.append("   Address:      " +  str(self.gui.camera.status.ADC_address[i]))
            self.cameraType.append("   FPGA Version: " +  self.gui.camera.status.ADC_FPGA_version[i])
            self.cameraType.append("   MC Version:   " +  self.gui.camera.status.ADC_MC_version[i])
            self.gui.adcControl.addAdc(i+1,self.gui.camera.status.ADC_address[i])

        self.cameraType.append("")
        self.cameraType.append("PC Firmware Version: " + self.gui.camera.status.PC_FW_version)

        err = self.gui.camera.readStatus()
        if (err != "") :
            self.messages.append(err)
            self.gui.showError(err)
            self.cameraOff()
            return

        for i in range(4):
            self.gui.infrastructure.hvSet[i].setValue(self.gui.camera.status.HV_set[i])

        for adcBoardNo in range(nAdcBoards):
            err,offsets = self.gui.camera.getOffsets(adcBoardNo+1)
            if (err != ""):
                self.gui.showError("Error reading offsets for board {:i}: {:s}".format(adcBoardNo+1,err))
            else:
                for channel in range(32):
                    self.gui.adcControl.adc[adcBoardNo].dac[channel].setValue(offsets[channel])

        err,d = self.gui.camera.getCallight()
        if (err != ""):
            self.gui.showError("Error reading calibration light: {:s}".format(err))
        else:
            self.gui.showMessage("Updated calibration light intensity value in the GUI from the camera")
            self.gui.infrastructure.calibrationLightIntensity.setValue(d)

        self.gui.startGuiUpdate()

