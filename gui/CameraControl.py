import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
from PyQt6.QtCore import Qt
from ApdcamUtils import *


class CameraControl(QWidget):
    def __init__(self,parent):
        super(CameraControl,self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        l = QHBoxLayout()
        layout.addLayout(l)
        self.cameraOnButton = QPushButton("APDCAM On")
        l.addWidget(self.cameraOnButton)
        self.cameraOffButton = QPushButton("APDCAM Off")
        l.addWidget(self.cameraOffButton)
        self.cameraConnectedStatus = QLabel("Camera not connected")
        l.addWidget(self.cameraConnectedStatus)
