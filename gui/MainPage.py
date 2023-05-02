import sys
import importlib

from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
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
        addressGroupBox.addWidget(self.addressEntry,0,1)
        addressGroupBox.addWidget(QtWidgets.QLabel("Interface: "),1,0)
        self.interface = QtWidgets.QLineEdit()
        addressGroupBox.addWidget(self.interface,1,1)

        self.cameraConnectedStatus = QtWidgets.QLabel("Camera connected locally");
        layout.addWidget(self.cameraConnectedStatus)

        self.findCameraButton = QtWidgets.QPushButton("Find camera")
        layout.addWidget(self.findCameraButton)

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)

        self.controlFactoryResetButton = QtWidgets.QPushButton("Control factory reset")
        self.controlFactoryResetButton.factorySetting = True
        layout.addWidget(self.controlFactoryResetButton)

        l = QtWidgets.QHBoxLayout()
        layout.addLayout(l)
        l.addWidget(QtWidgets.QLabel("PC Error:"))
        self.pcError = QtWidgets.QLineEdit()
        self.pcError.setReadOnly(True)
        l.addWidget(self.pcError)
        
