import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
from PyQt6.QtCore import Qt
from ApdcamUtils import *

class Adc(QVGroupBox):
    def __init__(self,parent,number):
        super(Adc,self).__init__(parent)
        self.number = number
        self.mean = [None]*32
        self.hf = [None]*32
        self.lf = [None]*32
        self.dac = [None]*32
        l = QGridLayout()
        self.addLayout(l)
        label = QLabel("<b>ADC"+str(number)+"</b>")
        label.setStyleSheet("background-color: rgba(0,0,0,0.1); padding:4px;")
        l.addWidget(label,0,0)
        l.addWidget(QLabel("Mean"),1,0)
        l.addWidget(QLabel("HF"),2,0)
        l.addWidget(QLabel("LF"),3,0)
        l.addWidget(QLabel("DAC"),4,0)
        
        for i in range(32):
            l.addWidget(QLabel(str(i+1)),0,i+1)
            self.mean[i] = QLineEdit()
            self.mean[i].setEnabled(False)
            self.mean[i].setMaximumWidth(30)
            l.addWidget(self.mean[i],1,i+1)
            self.hf[i] = QLineEdit()
            self.hf[i].setEnabled(False)
            self.hf[i].setMaximumWidth(30)
            l.addWidget(self.hf[i],2,i+1)
            self.lf[i] = QLineEdit()
            self.lf[i].setEnabled(False)
            self.lf[i].setMaximumWidth(30)
            l.addWidget(self.lf[i],3,i+1)
            self.dac[i] = QLineEdit()
            self.dac[i].setMaximumWidth(30)
            l.addWidget(self.dac[i],4,i+1)
        l.setColumnStretch(l.columnCount(),1)

        l = QHBoxLayout()
        self.addLayout(l)
        self.measureDataButton = QPushButton("Measure data")
        l.addWidget(self.measureDataButton)
        self.getDacValuesButton = QPushButton("Get DAC values")
        l.addWidget(self.getDacValuesButton)
        self.setDacOutputButton = QPushButton("Set DAC output")
        l.addWidget(self.setDacOutputButton)
        l.addWidget(QLabel("Set all 32 DAC values to:"))
        self.allDacValuesEntry = QSpinBox()
        self.allDacValuesEntry.setMinimum(0)
        self.allDacValuesEntry.setMaximum(10)
        l.addWidget(self.allDacValuesEntry)
        l.addStretch(1)

class OffsetNoise(QWidget):
    def __init__(self,parent):
        super(OffsetNoise,self).__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.adc = []
        self.addAdc()

        b = QPushButton("Add ADC (Debugging...)")
        b.clicked.connect(self.addAdc)
        self.layout.addWidget(b)

        l = QHBoxLayout()
        self.layout.addLayout(l)
        self.measureAllDataButton = QPushButton("Measure all data")
        l.addWidget(self.measureAllDataButton)
        self.getAllDacValuesButton = QPushButton("Get all DAC values")
        l.addWidget(self.getAllDacValuesButton)
        self.setAllDacOutputsButton = QPushButton("Set all DAC outputs")
        l.addWidget(self.setAllDacOutputsButton)
        l.addWidget(QLabel("Set all DAC values to:"))
        self.allDacValuesEntry = QSpinBox()
        self.allDacValuesEntry.setMinimum(0)
        self.allDacValuesEntry.setMaximum(10)
        l.addWidget(self.allDacValuesEntry)
        l.addStretch(1)

        self.layout.addStretch(1)

    def addAdc(self):
        adc = Adc(self,len(self.adc)+1)
        self.adc.append(adc)
        self.layout.insertWidget(len(self.adc)-1,adc)
