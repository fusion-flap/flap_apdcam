import sys

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt

from .ApdcamUtils import *

class SimpleMeasurementControl(QtWidgets.QWidget):
    def __init__(self,parent):
        super(SimpleMeasurementControl,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel("Simple mode"))
