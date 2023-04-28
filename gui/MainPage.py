import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
from PyQt6.QtCore import Qt
from ApdcamUtils import *


class MainPage(QWidget):
    def __init__(self,parent):
        super(MainPage,self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        addressGroupBox = QGridGroupBox("")
        layout.addWidget(addressGroupBox,Qt.AlignmentFlag.AlignLeft)
        addressGroupBox.addWidget(QLabel("Address:"),0,0)
        self.addressEntry = QLineEdit()
        addressGroupBox.addWidget(self.addressEntry,0,1)
        addressGroupBox.addWidget(QLabel("Interface: "),1,0)
        self.interface = QLineEdit()
        addressGroupBox.addWidget(self.interface,1,1)

        self.cameraConnectedStatus = QLabel("Camera connected locally");
        layout.addWidget(self.cameraConnectedStatus)

        self.findCameraButton = QPushButton("Find camera")
        layout.addWidget(self.findCameraButton)

        self.messages = QTextEdit(self)
        layout.addWidget(self.messages)

        self.controlFactoryResetButton = QPushButton("Control factory reset")
        self.controlFactoryResetButton.factorySetting = True
        layout.addWidget(self.controlFactoryResetButton)

        l = QHBoxLayout()
        layout.addLayout(l)
        l.addWidget(QLabel("PC Error:"))
        self.pcError = QLineEdit()
        self.pcError.setEnabled(False)
        l.addWidget(self.pcError)
        
        
        
#        layout = QFormLayout()
#        self.setLayout(layout)
#        layout.addRow('First Name:', QLineEdit(self))
#        layout.addRow('Last Name:', QLineEdit(self))
#        layout.addRow('DOB:', QDateEdit(self))
        
