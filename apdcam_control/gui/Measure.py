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
from functools import partial

class Measure(QtWidgets.QWidget):
    def __init__(self,parent):
        super(Measure,self).__init__(parent)
        self.gui = parent
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        h = QtWidgets.QHBoxLayout()
        layout.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Sample number: "))
        self.sampleNumber = QtWidgets.QSpinBox()
        self.sampleNumber.settingsName = "Sample number"
        self.sampleNumber.setMinimum(1)
        self.sampleNumber.setMaximum(1000000)
        self.sampleNumber.setValue(10)
        self.sampleNumber.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.sampleNumber.lineEdit().returnPressed.connect(lambda: self.gui.camera.setSampleNumber(self.sampleNumber.value()))
        self.sampleNumber.setToolTip("Set the number of samples to acquire")
        h.addWidget(self.sampleNumber)

        h.addStretch(1)

        h.addWidget(QtWidgets.QLabel("Timeout [s]: "))
        self.timeout = QtWidgets.QSpinBox()
        self.timeout.settingsName = "Timeout"
        self.timeout.setMinimum(0)
        self.timeout.setValue(100)
        self.timeout.setToolTip("Specify the timeout of the data acquisition. It will terminate after this time is passed")
        h.addWidget(self.timeout)
        h.addStretch(10)

        h = QtWidgets.QHBoxLayout()
        layout.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Data directory: "))
        self.dataDirectory = QtWidgets.QLineEdit()
        self.dataDirectory.settingsName = "Data directory"
        self.dataDirectory.setToolTip("Directory for storing the recorded data from the camera")
        self.dataDirectory.setText("/home/apdcam/tmp")
#        self.dataDirectory.setText("/home/barna/tmp/apdcam")
        h.addWidget(self.dataDirectory)
        self.dataDirectoryDialogButton = QtWidgets.QPushButton("PICK")
        h.addWidget(self.dataDirectoryDialogButton)
        self.dataDirectoryDialogButton.clicked.connect(lambda: self.dataDirectory.setText(str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))))

        self.measureButton = QtWidgets.QPushButton("Start measurement")
        self.measureButton.clicked.connect(self.measure)
        self.measureButton.setToolTip("Start the measurement")
        layout.addWidget(self.measureButton)

        self.messages = QtWidgets.QTextEdit(self)
        layout.addWidget(self.messages)

        layout.addStretch(1)

    def show_message(self,msg):
        self.messages.append(msg)

    def measure(self):
        if not self.gui.status.connected:
            self.gui.show_error("Camera is not connected")
            return
        self.gui.stopGuiUpdate()
        self.gui.show_warning("After the measurement is completed, please re-start the GUI update manually by clicking on the corresponding button in the 'Main' tab")
        time.sleep(1)
        self.gui.saveSettings(ask=False)
        self.gui.camera.measure(numberOfSamples=self.sampleNumber.value(),datapath=self.dataDirectory.text(),timeout=self.timeout.value()*1000)
