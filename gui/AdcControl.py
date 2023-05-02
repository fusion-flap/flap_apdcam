import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox, QScrollArea
from PyQt6.QtCore import Qt,QLocale
from PyQt6.QtGui import QDoubleValidator
from ApdcamUtils import *

class Adc(QWidget):
    def name(self):
        return "ADC " + str(self.number)

    def __init__(self,parent,number):
        super(Adc,self).__init__(parent)
        self.number = number

        layout = QHBoxLayout()
        self.setLayout(layout)

        l = QGridLayout()
        layout.addLayout(l)
        l.addWidget(QLabel("DVDD:"),1,0)
        self.dvdd = QLineEdit()
        self.dvdd.setEnabled(False)
        l.addWidget(self.dvdd,1,1)
        
        l.addWidget(QLabel("AVDD:"),2,0)
        self.avdd = QLineEdit()
        self.avdd.setEnabled(False)
        l.addWidget(self.avdd,2,1)

        l.addWidget(QLabel("1.8 V:"),3,0)
        self.v18 = QLineEdit()
        self.v18.setEnabled(False)
        l.addWidget(self.v18,3,1)

        l.addWidget(QLabel("2.5 V:"),4,0)
        self.v25 = QLineEdit()
        self.v25.setEnabled(False)
        l.addWidget(self.v25,4,1)

        l.addWidget(QLabel("Temp:"),5,0)
        self.temperature = QLineEdit()
        self.temperature.setEnabled(False)
        l.addWidget(self.temperature,5,1)

        l.setRowStretch(l.rowCount(),1)

        l = QVBoxLayout()
        layout.addLayout(l)
        g = QVGroupBox(self)
        l.addWidget(g)
        self.pllLocked = QCheckBox("PLL Locked")
        self.pllLocked.setEnabled(False)
        g.addWidget(self.pllLocked)
        self.internalTriggerDisplay = QCheckBox("Internal trigger")
        self.internalTriggerDisplay.setEnabled(False)
        g.addWidget(self.internalTriggerDisplay)
        self.overload = QCheckBox("Overload")
        self.overload.setEnabled(False)
        g.addWidget(self.overload)
        self.led1 = QCheckBox("LED 1")
        self.led1.setEnabled(False)
        g.addWidget(self.led1)
        self.led2 = QCheckBox("LED 2")
        self.led2.setEnabled(False)
        g.addWidget(self.led2)
        self.allChannelsOnButton = QPushButton("All channels on")
        l.addWidget(self.allChannelsOnButton)
        self.allChannelsOffButton = QPushButton("All channels off")
        l.addWidget(self.allChannelsOffButton)
        h = QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QLabel("Error:"))
        self.error = QLineEdit()
        self.error.setReadOnly(True)
        h.addWidget(self.error)
        l.addStretch(1)

        self.whatIsThis = [None]*32
        l = QGridLayout()
        l.setContentsMargins(10,0,0,0)
        l.setSpacing(15)
        layout.addLayout(l)
        l.setVerticalSpacing(10)
        for col in range(4):
            l.setColumnMinimumWidth(col,1)
            for row in range(8):
                l.setRowMinimumHeight(row,1)
                self.whatIsThis[col*row] = QCheckBox(str(col*8+row+1))
                self.whatIsThis[col*row].setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                self.whatIsThis[col*row].setContentsMargins(0,0,0,0)
                l.addWidget(self.whatIsThis[col*row],row,col)
        l.setRowStretch(l.rowCount(),1)

        g = QVGroupBox(self)
        layout.addWidget(g)
        self.sataOn = QCheckBox()
        self.sataOn.setText("SATA On")
        self.sataOn.factorySetting = True
        g.addWidget(self.sataOn)
        self.dualSata = QCheckBox()
        self.dualSata.setText("Dual SATA")
        self.dualSata.factorySetting = True
        g.addWidget(self.dualSata)
        self.sataSync = QCheckBox()
        self.sataSync.setText("SATA Sync")
        g.addWidget(self.sataSync)
        self.test = QCheckBox()
        self.test.setText("Test")
        g.addWidget(self.test)
        self.filter = QCheckBox()
        self.filter.setText("Filter")
        g.addWidget(self.filter)
        self.internalTrigger = QCheckBox("Internal trigger")
        g.addWidget(self.internalTrigger)
        self.reverseBitOrder = QCheckBox("Rev. bitord.")
        self.reverseBitOrder.factorySetting = True
        g.addWidget(self.reverseBitOrder)
        g.addStretch(1)

        g = QGridGroupBox(self)
        layout.addWidget(g)
        g.addWidget(QLabel("Bits:"),0,0)
        self.bits = QLineEdit()
        g.addWidget(self.bits,0,1)
        g.addWidget(QLabel("Ring buffer:"),1,0)
        self.ringBuffer = QLineEdit()
        g.addWidget(self.ringBuffer,1,1)
        g.addWidget(QLabel("SATA CLK Mult:"),2,0)
        self.sataClkMult = QSpinBox()
        g.addWidget(self.sataClkMult,2,1)
        g.addWidget(QLabel("SATA CLK Div:"),3,0)
        self.sataClkDiv = QSpinBox()
        g.addWidget(self.sataClkDiv,3,1)
        g.addWidget(QLabel("Test pattern:"),4,0)
        self.testPattern = QLineEdit()
        g.addWidget(self.testPattern,4,1)
        g.setRowStretch(g.rowCount(),1)

        g = QGridGroupBox(self)
        g.setTitle("FIR filter")
        layout.addWidget(g)
        self.firCoeff = [0,0,0,0,0]
        for i in range(5):
            g.addWidget(QLabel("Coeff" + str(i+1)),i,0)
            self.firCoeff[i] = QSpinBox()
            self.firCoeff[i].setMinimum(0)
            self.firCoeff[i].setMaximum(65535)
            g.addWidget(self.firCoeff[i],i,1)
        g.setRowStretch(g.rowCount(),1)

        b = QVBoxLayout()
        layout.addLayout(b)
        g = QGridGroupBox("Int. Filter")
        b.addWidget(g)
        g.addWidget(QLabel("Coeff:"),0,0)
        self.internalFilterCoeff = QSpinBox()
        self.internalFilterCoeff.setMinimum(0)
        self.internalFilterCoeff.setMaximum(4095)
        g.addWidget(self.internalFilterCoeff,0,1)
        self.internalFilterDiv = QSpinBox()
        self.internalFilterDiv.setMinimum(0)
        self.internalFilterDiv.setMaximum(14)
        g.addWidget(QLabel("Filter div.:"),1,0)
        g.addWidget(self.internalFilterDiv,1,1)
        b.addStretch(1)
        l = QGridLayout()
        b.addLayout(l)
        l.addWidget(QLabel("FIR Freq. [MHz]:"),0,0)
        self.firFrequency = QDoubleEdit()
        l.addWidget(self.firFrequency,0,1)
        l.addWidget(QLabel("Rec. Freq. [MHz]:"),1,0)
        self.recFrequency = QDoubleEdit()
        l.addWidget(self.recFrequency,1,1)
        l.addWidget(QLabel("Filter gain:"),2,0)
        self.filterGain = QSpinBox()
        self.filterGain.setMinimum(0)
        l.addWidget(self.filterGain,2,1)
        b.addStretch(1)

        v = QVBoxLayout()
        layout.addLayout(v)

        g = QGridGroupBox("Overload")
        v.addWidget(g)
        g.addWidget(QLabel("Overl. level:"),0,0)
        self.overloadLevel = QDoubleEdit()
        g.addWidget(self.overloadLevel,0,1)
        g.addWidget(QLabel("Overl. time [\u03bcs]:"),1,0)
        self.overloadTime = QDoubleEdit()
        g.addWidget(self.overloadTime,1,1)
        self.overloadEnabled = QCheckBox()
        self.overloadEnabled.setText("Overload en.")
        g.addWidget(self.overloadEnabled,2,0,1,2)
        self.ovrPlus = QCheckBox("Ovr +")
        g.addWidget(self.ovrPlus,3,0,1,2)
        self.overload = QCheckBox("OVERLOAD")
        g.addWidget(self.overload,4,0,1,2)

        g = QGridGroupBox("Trigger")
        v.addWidget(g)
        g.addWidget(QLabel("Trig. level (all)"),0,0)
        self.triggerLevelAll = QDoubleEdit()
        g.addWidget(self.triggerLevelAll,0,1)
        self.triggerEnabled = QCheckBox("Trigger enabled")
        g.addWidget(self.triggerEnabled,1,0,1,2)
        self.plusTrigger = QCheckBox("+ trig")
        g.addWidget(self.plusTrigger,2,0,1,2)

class AdcControl(QWidget):
    def __init__(self,parent):
        super(AdcControl,self).__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.readAllAdcStatusButton = QPushButton("Read all ADC status")
        self.layout.addWidget(self.readAllAdcStatusButton)

        self.adc = []
        self.adcTabs = QTabWidget(self)
        self.layout.addWidget(self.adcTabs)

        self.setAdcs(4)

        self.factoryResetButton = QPushButton("Factory reset")
        self.factoryResetButton.factorySetting = True
        self.layout.addWidget(self.factoryResetButton)

        self.readFromHwButton = QPushButton("Read from HW")
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
                
