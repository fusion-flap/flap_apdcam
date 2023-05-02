import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
# from PyQt6.QtCore import Qt
from ApdcamUtils import *


class CameraControl(QtWidgets.QWidget):
    def __init__(self,parent):
        super(CameraControl,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        l = QtWidgets.QHBoxLayout()
        layout.addLayout(l)
        self.cameraOnButton = QtWidgets.QPushButton("APDCAM On")
        l.addWidget(self.cameraOnButton)
        self.cameraOffButton = QtWidgets.QPushButton("APDCAM Off")
        l.addWidget(self.cameraOffButton)
        self.cameraConnectedStatus = QtWidgets.QLabel("Camera not connected")
        l.addWidget(self.cameraConnectedStatus)
