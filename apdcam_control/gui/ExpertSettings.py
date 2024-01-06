import sys
import os
from functools import partial
import re

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from .ApdcamUtils import *
from .GuiMode import *
from ..APDCAM10G_control import *


class ExpertSettings(QtWidgets.QWidget):

    def __init__(self,parent,gui):
        self.gui = gui
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        factoryResetButton = QtWidgets.QPushButton("Factory reset")
        layout.addWidget(factoryResetButton)
        factoryResetButton.clicked.connect(lambda: self.gui.camera.FactoryReset(True))
