import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox, QScrollArea
# from PyQt6.QtCore import Qt,QLocale
# from PyQt6.QtGui import QDoubleValidator
from ApdcamUtils import *

class Adc(QtWidgets.QWidget):
    def name(self):
        return "ADC " + str(self.number)

    def __init__(self,parent,number):
        super(Adc,self).__init__(parent)
        self.number = number

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        l = QtWidgets.QGridLayout()
        layout.addLayout(l)
        l.addWidget(QtWidgets.QLabel("DVDD:"),1,0)
        self.dvdd = QtWidgets.QLineEdit()
        self.dvdd.setEnabled(False)
        l.addWidget(self.dvdd,1,1)
        
        l.addWidget(QtWidgets.QLabel("AVDD:"),2,0)
        self.avdd = QtWidgets.QLineEdit()
        self.avdd.setEnabled(False)
        l.addWidget(self.avdd,2,1)

        l.addWidget(QtWidgets.QLabel("1.8 V:"),3,0)
        self.v18 = QtWidgets.QLineEdit()
        self.v18.setEnabled(False)
        l.addWidget(self.v18,3,1)

        l.addWidget(QtWidgets.QLabel("2.5 V:"),4,0)
        self.v25 = QtWidgets.QLineEdit()
        self.v25.setEnabled(False)
        l.addWidget(self.v25,4,1)

        l.addWidget(QtWidgets.QLabel("Temp:"),5,0)
        self.temperature = QtWidgets.QLineEdit()
        self.temperature.setEnabled(False)
        l.addWidget(self.temperature,5,1)

        l.setRowStretch(l.rowCount(),1)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)
        g = QVGroupBox(self)
        l.addWidget(g)
        self.pllLocked = QtWidgets.QCheckBox("PLL Locked")
        self.pllLocked.setEnabled(False)
        g.addWidget(self.pllLocked)
        self.internalTriggerDisplay = QtWidgets.QCheckBox("Internal trigger")
        self.internalTriggerDisplay.setEnabled(False)
        g.addWidget(self.internalTriggerDisplay)
        self.overload = QtWidgets.QCheckBox("Overload")
        self.overload.setEnabled(False)
        g.addWidget(self.overload)
        self.led1 = QtWidgets.QCheckBox("LED 1")
        self.led1.setEnabled(False)
        g.addWidget(self.led1)
        self.led2 = QtWidgets.QCheckBox("LED 2")
        self.led2.setEnabled(False)
        g.addWidget(self.led2)
        self.allChannelsOnButton = QtWidgets.QPushButton("All channels on")
        l.addWidget(self.allChannelsOnButton)
        self.allChannelsOffButton = QtWidgets.QPushButton("All channels off")
        l.addWidget(self.allChannelsOffButton)
        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Error:"))
        self.error = QtWidgets.QLineEdit()
        self.error.setReadOnly(True)
        h.addWidget(self.error)
        l.addStretch(1)

        self.whatIsThis = [None]*32
        l = QtWidgets.QGridLayout()
        l.setContentsMargins(10,0,0,0)
        l.setSpacing(15)
        layout.addLayout(l)
        l.setVerticalSpacing(10)
        for col in range(4):
            l.setColumnMinimumWidth(col,1)
            for row in range(8):
                l.setRowMinimumHeight(row,1)
                self.whatIsThis[col*row] = QtWidgets.QCheckBox(str(col*8+row+1))
                self.whatIsThis[col*row].setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                self.whatIsThis[col*row].setContentsMargins(0,0,0,0)
                l.addWidget(self.whatIsThis[col*row],row,col)
        l.setRowStretch(l.rowCount(),1)

        g = QVGroupBox(self)
        layout.addWidget(g)
        self.sataOn = QtWidgets.QCheckBox()
        self.sataOn.setText("SATA On")
        self.sataOn.factorySetting = True
        g.addWidget(self.sataOn)
        self.dualSata = QtWidgets.QCheckBox()
        self.dualSata.setText("Dual SATA")
        self.dualSata.factorySetting = True
        g.addWidget(self.dualSata)
        self.sataSync = QtWidgets.QCheckBox()
        self.sataSync.setText("SATA Sync")
        g.addWidget(self.sataSync)
        self.test = QtWidgets.QCheckBox()
        self.test.setText("Test")
        g.addWidget(self.test)
        self.filter = QtWidgets.QCheckBox()
        self.filter.setText("Filter")
        g.addWidget(self.filter)
        self.internalTrigger = QtWidgets.QCheckBox("Internal trigger")
        g.addWidget(self.internalTrigger)
        self.reverseBitOrder = QtWidgets.QCheckBox("Rev. bitord.")
        self.reverseBitOrder.factorySetting = True
        g.addWidget(self.reverseBitOrder)
        g.addStretch(1)

        g = QGridGroupBox(self)
        layout.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Bits:"),0,0)
        self.bits = QtWidgets.QLineEdit()
        g.addWidget(self.bits,0,1)
        g.addWidget(QtWidgets.QLabel("Ring buffer:"),1,0)
        self.ringBuffer = QtWidgets.QLineEdit()
        g.addWidget(self.ringBuffer,1,1)
        g.addWidget(QtWidgets.QLabel("SATA CLK Mult:"),2,0)
        self.sataClkMult = QtWidgets.QSpinBox()
        g.addWidget(self.sataClkMult,2,1)
        g.addWidget(QtWidgets.QLabel("SATA CLK Div:"),3,0)
        self.sataClkDiv = QtWidgets.QSpinBox()
        g.addWidget(self.sataClkDiv,3,1)
        g.addWidget(QtWidgets.QLabel("Test pattern:"),4,0)
        self.testPattern = QtWidgets.QLineEdit()
        g.addWidget(self.testPattern,4,1)
        g.setRowStretch(g.rowCount(),1)

        g = QGridGroupBox(self)
        g.setTitle("FIR filter")
        layout.addWidget(g)
        self.firCoeff = [0,0,0,0,0]
        for i in range(5):
            g.addWidget(QtWidgets.QLabel("Coeff" + str(i+1)),i,0)
            self.firCoeff[i] = QtWidgets.QSpinBox()
            self.firCoeff[i].setMinimum(0)
            self.firCoeff[i].setMaximum(65535)
            g.addWidget(self.firCoeff[i],i,1)
        g.setRowStretch(g.rowCount(),1)

        b = QtWidgets.QVBoxLayout()
        layout.addLayout(b)
        g = QGridGroupBox("Int. Filter")
        b.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Coeff:"),0,0)
        self.internalFilterCoeff = QtWidgets.QSpinBox()
        self.internalFilterCoeff.setMinimum(0)
        self.internalFilterCoeff.setMaximum(4095)
        g.addWidget(self.internalFilterCoeff,0,1)
        self.internalFilterDiv = QtWidgets.QSpinBox()
        self.internalFilterDiv.setMinimum(0)
        self.internalFilterDiv.setMaximum(14)
        g.addWidget(QtWidgets.QLabel("Filter div.:"),1,0)
        g.addWidget(self.internalFilterDiv,1,1)
        b.addStretch(1)
        l = QtWidgets.QGridLayout()
        b.addLayout(l)
        l.addWidget(QtWidgets.QLabel("FIR Freq. [MHz]:"),0,0)
        self.firFrequency = QDoubleEdit()
        l.addWidget(self.firFrequency,0,1)
        l.addWidget(QtWidgets.QLabel("Rec. Freq. [MHz]:"),1,0)
        self.recFrequency = QDoubleEdit()
        l.addWidget(self.recFrequency,1,1)
        l.addWidget(QtWidgets.QLabel("Filter gain:"),2,0)
        self.filterGain = QtWidgets.QSpinBox()
        self.filterGain.setMinimum(0)
        l.addWidget(self.filterGain,2,1)
        b.addStretch(1)

        v = QtWidgets.QVBoxLayout()
        layout.addLayout(v)

        g = QGridGroupBox("Overload")
        v.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Overl. level:"),0,0)
        self.overloadLevel = QDoubleEdit()
        g.addWidget(self.overloadLevel,0,1)
        g.addWidget(QtWidgets.QLabel("Overl. time [\u03bcs]:"),1,0)
        self.overloadTime = QDoubleEdit()
        g.addWidget(self.overloadTime,1,1)
        self.overloadEnabled = QtWidgets.QCheckBox()
        self.overloadEnabled.setText("Overload en.")
        g.addWidget(self.overloadEnabled,2,0,1,2)
        self.ovrPlus = QtWidgets.QCheckBox("Ovr +")
        g.addWidget(self.ovrPlus,3,0,1,2)
        self.overload = QtWidgets.QCheckBox("OVERLOAD")
        g.addWidget(self.overload,4,0,1,2)

        g = QGridGroupBox("Trigger")
        v.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Trig. level (all)"),0,0)
        self.triggerLevelAll = QDoubleEdit()
        g.addWidget(self.triggerLevelAll,0,1)
        self.triggerEnabled = QtWidgets.QCheckBox("Trigger enabled")
        g.addWidget(self.triggerEnabled,1,0,1,2)
        self.plusTrigger = QtWidgets.QCheckBox("+ trig")
        g.addWidget(self.plusTrigger,2,0,1,2)

class AdcControl(QtWidgets.QWidget):
    def __init__(self,parent):
        super(AdcControl,self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.readAllAdcStatusButton = QtWidgets.QPushButton("Read all ADC status")
        self.layout.addWidget(self.readAllAdcStatusButton)

        self.adc = []
        self.adcTabs = QtWidgets.QTabWidget(self)
        self.layout.addWidget(self.adcTabs)

        self.setAdcs(4)

        self.factoryResetButton = QtWidgets.QPushButton("Factory reset")
        self.factoryResetButton.factorySetting = True
        self.layout.addWidget(self.factoryResetButton)

        self.readFromHwButton = QtWidgets.QPushButton("Read from HW")
        self.layout.addWidget(self.readFromHwButton)

    def addAdc(self):
        adc = Adc(self,len(self.adc)+1)
        self.adc.append(adc)
        self.adcTabs.addTab(adc,adc.name())

    def setAdcs(self,number):
        if number > self.adcTabs.count():
            while number > self.adcTabs.count():
                self.addAdc()
        if number < self.adcTabs.count():
            while number < self.adcTabs.count():
                self.adcTabs.removeTab(self.adcTabs.count()-1)
                
