import sys
import os
import time

import importlib
from .QtVersion import QtVersion
from .ApdcamUtils import *
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt

from .ApdcamUtils import *

class Factory(QtWidgets.QWidget):
    def __init__(self,parent):
        self.gui = parent
        super(Factory,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        fw = QtWidgets.QGroupBox("Firmware upgrade")
        layout.addWidget(fw)
        fwLayout = QtWidgets.QHBoxLayout()
        fw.setLayout(fwLayout)

        fwCC = QtWidgets.QGroupBox("C&C Card")
        fwLayout.addWidget(fwCC)
        fwCCLayout = QtWidgets.QGridLayout()
        fwCC.setLayout(fwCCLayout)

        fwCCLayout.addWidget(QtWidgets.QLabel("Current firmware version:"),0,0)
        self.fwCCCurrentVersion = QtWidgets.QLabel()
        fwCCLayout.addWidget(self.fwCCCurrentVersion,0,1)

        l = QtWidgets.QHBoxLayout()
        fwCCLayout.addLayout(l,1,0,1,2)
        self.fwCCFilename = QtWidgets.QLineEdit()
        self.fwCCFilename.setText('/user-data/barna/fusion-instruments/apdcam/fw/BSF12-0001-105_0702.fup')
        l.addWidget(self.fwCCFilename)

        b = QtWidgets.QPushButton("Choose file")
        l.addWidget(b)
        self.fwCCDirectory = "."
        b.clicked.connect(self.setCCFirmwareFile)

        fwCCLayout.addWidget(QtWidgets.QLabel("Chosen file's version:"),2,0)
        self.fwCCFileVersion = QtWidgets.QLabel()
        fwCCLayout.addWidget(self.fwCCFileVersion,2,1)
        self.fwCCFileVersion.setWordWrap(True)

        self.uploadCCFirmwareButton = QtWidgets.QPushButton("Upload firmware")
        fwCCLayout.addWidget(self.uploadCCFirmwareButton,3,0,1,2)
        self.uploadCCFirmwareButton.clicked.connect(self.uploadCCFirmware)

        self.uploadCCFirmwareProgressbar = QtWidgets.QProgressBar()
        fwCCLayout.addWidget(self.uploadCCFirmwareProgressbar,4,0,1,2)

        self.uploadCCFirmwareMessages = QtWidgets.QTextEdit()
        fwCCLayout.addWidget(self.uploadCCFirmwareMessages,5,0,1,2)

        layout.addStretch(1)
        

    def setCCFirmwareFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(None,'C&C card firmware file',self.fwCCDirectory,'Firmware files (*.fup)')
        filename = filename[0]
        if filename == '':
            return
        self.fwCCDirectory = os.path.dirname(filename)
        self.fwCCFilename.setText(filename)

    def uploadCCFirmware(self):
        #self.uploadCCFirmwareMessages.clear()
        self.gui.stopGuiUpdate(wait=True)
        # try:
        #     self.uploadCCFirmwareButton.clicked.disconnect()
        # except:
        #     pass
        #self.uploadCCFirmwareButton.setText("Uploading...")
        #self.uploadCCFirmwareButton.setStyleSheet("background-color:rgb(255,200,200);")

        filename = self.fwCCFilename.text()
        print(filename)
        self.gui.camera.loadfup(filename,reconnect=False,\
                                logger  = lambda m  : [print(m)], \
                                progress= lambda val: print("Status: " + str(val*100) + "%" ) )
        
        self.gui.main.cameraOff()
        time.sleep(0.5)
        self.gui.main.cameraOn()
        print("Camera restarted")
        #self.uploadCCFirmwareButton.clicked.connect(self.uploadCCFirmware)
        #self.uploadCCFirmwareButton.setStyleSheet("")
