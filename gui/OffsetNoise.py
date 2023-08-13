import sys

import importlib
from QtVersion import *
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from ApdcamUtils import *

# Egesz offset/noise ful eltunhet, menjen aDC.be

class AdcBoard(QVGroupBox):
    def __init__(self,parent,number):
        super(AdcBoard,self).__init__(parent)
        self.number = number
        self.mean = [None]*32
        self.hf = [None]*32
        self.lf = [None]*32
        self.dac = [None]*32
        l = QtWidgets.QGridLayout()
        self.addLayout(l)
        label = QtWidgets.QLabel("<b>ADC"+str(number)+"</b>")
        label.setStyleSheet("background-color: rgba(0,0,0,0.1); padding:4px;")
        l.addWidget(label,0,0)
#        l.addWidget(QtWidgets.QLabel("Mean"),1,0)
#        l.addWidget(QtWidgets.QLabel("HF"),2,0)
#        l.addWidget(QtWidgets.QLabel("LF"),3,0)
        l.addWidget(QtWidgets.QLabel("DAC"),4,0)
        
        for i in range(32):
            l.addWidget(QtWidgets.QLabel(str(i+1)),0,i+1,AlignCenter)
            # csak DAC kell
            self.mean[i] = QtWidgets.QLineEdit()
            self.mean[i].setEnabled(False)
            self.mean[i].setMaximumWidth(30)
            l.addWidget(self.mean[i],1,i+1,AlignCenter)
            self.hf[i] = QtWidgets.QLineEdit()
            self.hf[i].setEnabled(False)
            self.hf[i].setMaximumWidth(30)
            l.addWidget(self.hf[i],2,i+1,AlignCenter)
            self.lf[i] = QtWidgets.QLineEdit()
            self.lf[i].setEnabled(False)
            self.lf[i].setMaximumWidth(30)
            l.addWidget(self.lf[i],3,i+1,AlignCenter)
            self.dac[i] = QtWidgets.QSpinBox()
            self.dac[i].setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
#            self.dac[i] = QIntEdit(0,65535)
            self.dac[i].setMinimum(0)
            self.dac[i].setMaximum(65535)
            self.dac[i].setMaximumWidth(54)
            l.addWidget(self.dac[i],4,i+1,AlignCenter)
        l.setSpacing(0)
        l.setColumnStretch(l.columnCount(),1)

        l = QtWidgets.QHBoxLayout()
        self.addLayout(l)
#        self.measureDataButton = QtWidgets.QPushButton("Measure data")
#        l.addWidget(self.measureDataButton)
        self.getDacValuesButton = QtWidgets.QPushButton("Get DAC values")
        l.addWidget(self.getDacValuesButton)
        self.setDacOutputButton = QtWidgets.QPushButton("Set DAC output")
        l.addWidget(self.setDacOutputButton)
        l.addWidget(QtWidgets.QLabel("Set all 32 DAC values to:"))
        self.allDacValuesEntry = QtWidgets.QSpinBox()
        self.allDacValuesEntry.setMinimum(0)
        self.allDacValuesEntry.setMaximum(65535)
        l.addWidget(self.allDacValuesEntry)
        l.addStretch(1)

class OffsetNoise(QtWidgets.QWidget):
    def __init__(self,parent):
        super(OffsetNoise,self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.adcBoards = []
        self.setAdcBoards(3)

        l = QtWidgets.QHBoxLayout()
        self.layout.addLayout(l)
        self.measureAllDataButton = QtWidgets.QPushButton("Measure all data")
        l.addWidget(self.measureAllDataButton)
        self.getAllDacValuesButton = QtWidgets.QPushButton("Get all DAC values")
        l.addWidget(self.getAllDacValuesButton)
        self.setAllDacOutputsButton = QtWidgets.QPushButton("Set all DAC outputs")
        l.addWidget(self.setAllDacOutputsButton)
        l.addWidget(QtWidgets.QLabel("Set all DAC values to:"))
        self.allDacValuesEntry = QtWidgets.QSpinBox()
        self.allDacValuesEntry.setMinimum(0)
        self.allDacValuesEntry.setMaximum(65535)
        l.addWidget(self.allDacValuesEntry)
        l.addStretch(1)

        self.layout.addStretch(1)

    def addAdcBoard(self):
        adc = AdcBoard(self,len(self.adcBoards)+1)
        self.adcBoards.append(adc)
        self.layout.insertWidget(len(self.adcBoards)-1,adc)

    def setAdcBoards(self,n):
        """
        Set the specified number of ADC boards
        """
        
        for i in range(len(self.adcBoards)):
            self.adcBoards[i].setParent(None)

        self.adcBoards = [None]*n
        for i in range(n):
            self.adcBoards[i] = AdcBoard(self,i+1)
            self.layout.insertWidget(i,self.adcBoards[i])
