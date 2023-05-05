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
        self.addressEntry.setToolTip("The IP address of the camera")
        addressGroupBox.addWidget(self.addressEntry,0,1)
        addressGroupBox.addWidget(QtWidgets.QLabel("Interface: "),1,0)
        self.interface = QtWidgets.QLineEdit()
        addressGroupBox.addWidget(self.interface,1,1)

        l = QtWidgets.QHBoxLayout()
        layout.addLayout(l)
        l.addWidget(QtWidgets.QLabel("Camera type:"))
        self.cameraType = QtWidgets.QLineEdit()
        l.addWidget(self.cameraType)

        l = QtWidgets.QHBoxLayout()
        layout.addLayout(l)
        self.cameraConnectedStatus = QtWidgets.QLabel("Camera connected locally");
        l.addWidget(self.cameraConnectedStatus)
        self.connectCameraButton = QtWidgets.QPushButton("Connect camera")
        self.connectCameraButton.clicked.connect(self.cameraOn)
        l.addWidget(self.connectCameraButton)
        self.disconnectCameraButton = QtWidgets.QPushButton("Disconnect camera")
        l.addWidget(self.disconnectCameraButton)

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)

    def cameraOff(self):
        self.cameraConnectedStatus.setText("Camera disconnected")
        self.gui.camera.close()  # APDCAM10G_control should handle the case if camera is on or off when calling close()
        self.gui.showMessage("Camera disconnected")

    def cameraOn(self):
        """
        Connects to APDCAM
        """
        self.messages.setText("") # clear previous messages

        if not re.search("^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$",self.addressEntry.text()):
            self.messages.append("Bad IP address: '" + self.addressEntry.text() + "'")
            QtWidgets.QApplication.processEvents()
            return

        for i in range(10) :
            self.gui.camera.HV_conversion = [0.12,0.12,0.12,0.12]
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
            return
        self.cameraConnectedStatus.setText("Camera connected")
        self.cameraType.setText(" Firmware: {:s}".format(self.GUI_status.APDCAM_reg.status.firmware.decode('utf-8')))
        
        n = len(self.gui.camera.status.ADC_address) 
        txt = ""
        for i in range(n):
            txt = txt + str(self.gui.camera.status.ADC_address[i])+" "
        self.messages.append(" No of ADCs: {:d}, Addresses: {:s}".format(n,txt))
        self.GUI_status.APDCAM_connected = True
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
        # err,d = self.GUI_status.APDCAM_reg.getOffsets()
        # if (err != ""):
        #     self.GUI_status.GUI.add_message("Error reading offsets: {:s}".format(err))
        # else:
        #     # Assuming all offsets are the same, using the first one
        #     self.var_offset.set(str(d[0]))

        err,d = self.gui.camera.getCallight()
        if (err != ""):
            self.gui.showError("Error reading calibration light: {:s}".format(err))
        else:
            self.gui.infrastructure.calibrationLightIntensity.setValue(d)

            

        # self.GUI_status.GUI_top.APDCAM_settings_widg.update()
