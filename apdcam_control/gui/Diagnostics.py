import sys
import time

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")
Qt = QtCore.Qt

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox
# from PyQt6.QtCore import Qt
from .ApdcamUtils import *
from .GuiMode import *
from .UdpPacketInspector import *
from .RegisterInspector import RegisterInspector
from .ExpertSettings import *
from functools import partial

class Diagnostics(QtWidgets.QWidget):
    def __init__(self,parent):
        super(Diagnostics,self).__init__(parent)
        self.gui = parent
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QtWidgets.QTabWidget(self)
        layout.addWidget(self.tabs)

        self.udpPacketInspector = UdpPacketInspector(self)
        self.tabs.addTab(self.udpPacketInspector,"UDP Packet Inspector")

        self.registerInspector = RegisterInspector(self,self.gui)
        self.tabs.addTab(self.registerInspector,"Register inspector")

        self.expertSettings = ExpertSettings(self,self.gui)
        self.tabs.addTab(self.expertSettings,"Expert settings")

    def loadSettingsFromCamera(self):
        self.registerInspector.loadSettingsFromCamera()
