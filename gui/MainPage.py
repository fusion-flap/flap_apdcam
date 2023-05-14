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

    def cameraOn(self):
        """
        Connects to APDCAM
        """
        self.messages.setText("") # clear previous messages

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
        self.cameraType.setText(" Firmware: {:s}".format(self.GUI_status.APDCAM_reg.status.firmware.decode('utf-8')))
        
        nAdcBoards = len(self.gui.camera.status.ADC_address) 
        txt = ""
        for i in range(nAdcBoards):
            txt = txt + str(self.gui.camera.status.ADC_address[i])+" "
        self.messages.append(" No of ADCs: {:d}, Addresses: {:s}".format(nAdcBoards,txt))
        #self.gui.offsetNoise.setAdcBoards(nAdcBoards)
        self.gui.adcControl.setAdcs(nAdcBoards)
        #self.gui.infrastructure.setHvGroups(nAdcBoards)

        err = self.gui.camera.readStatus()
        if (err != "") :
            self.messages.append(err)
            self.gui.showError(err)
            self.cameraOff()
            return

        # self.GUI_status.APDCAM_status = self.GUI_status.APDCAM_reg.status
        # self.var_HV1_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[0]))
        # self.var_HV2_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[1]))
        # self.var_HV3_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[2]))
        # self.var_HV4_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[3]))
        for i in range(4):
            self.gui.infrastructure.hvSet[i].setText("{:5.1f}".format(self.gui.camera.status.HV_set[0]))

        # self.var_detTemp_set.set("---")
        # self.var_detTemp_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.ref_temp))
        # if (self.var_clocksource.get() == 'External'): 
        #     err = self.GUI_status.APDCAM_reg.setClock(APDCAM10G_regCom.CLK_EXTERNAL,extmult=4,extdiv=2,autoExternal=True)
        # else:
        #     err = self.GUI_status.APDCAM_reg.setClock(APDCAM10G_regCom.CLK_INTERNAL)

        err,d = self.gui.camera.getOffsets()
        if (err != ""):
            self.gui.showError("Error reading offsets: {:s}".format(err))
        else:
            # Assuming all offsets are the same, using the first one
            gui.showMessage("Updated ADC offsets in the tab 'Offset/noise'")
            for adc in range(len(gui.offsetNoise.adc)):
                for channel in range(32):
                    gui.offsetNoise.adc[adc].dac[channel].setText(str(d[0]))

        err,d = self.gui.camera.getCallight()
        if (err != ""):
            self.gui.showError("Error reading calibration light: {:s}".format(err))
        else:
            gui.showMessage("Updated calibration light intensity value in the GUI from the camera")
            self.gui.infrastructure.calibrationLightIntensity.setValue(d)

            

        # self.GUI_status.GUI_top.APDCAM_settings_widg.update()
