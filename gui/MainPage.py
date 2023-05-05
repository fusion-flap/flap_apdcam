import sys

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
        l.addWidget(self.connectCameraButton)
        self.disconnectCameraButton = QtWidgets.QPushButton("Disconnect camera")
        l.addWidget(self.disconnectCameraButton)

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)


        
