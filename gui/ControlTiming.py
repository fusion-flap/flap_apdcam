import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox
# from PyQt6.QtCore import Qt
from ApdcamUtils import *


class ControlTiming(QtWidgets.QWidget):
    def __init__(self,parent):
        super(ControlTiming,self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QHGroupBox("CC card temperatures")
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("CC card temp.:"))
        self.ccCardTemp = QDoubleEdit()
        g.addWidget(self.ccCardTemp)
        g.addWidget(QtWidgets.QLabel("CC card max. temp.:"))
        self.ccCardMaxTemp = QDoubleEdit()
        g.addWidget(self.ccCardMaxTemp)

        g = QGridGroupBox("CC card voltages")
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("3.3 V:"),0,0)
        self.ccCardVoltage33 = QDoubleEdit()
        g.addWidget(self.ccCardVoltage33,0,1)
        g.addWidget(QtWidgets.QLabel("1.8 V XC:"),0,2)
        self.ccCardVoltage18XC = QDoubleEdit()
        g.addWidget(self.ccCardVoltage18XC,0,3)
        g.addWidget(QtWidgets.QLabel("2.5 V:"),1,0)
        self.ccCardVoltage25 = QDoubleEdit()
        g.addWidget(self.ccCardVoltage25,1,1)
        g.addWidget(QtWidgets.QLabel("1.2 V ST:"),1,2)
        self.ccCardVoltage12ST = QDoubleEdit()
        g.addWidget(self.ccCardVoltage12ST,1,3)

        g = QGridGroupBox()
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Base PLL Mult.:"),0,0)
        self.basePllMult = QtWidgets.QSpinBox()
        g.addWidget(self.basePllMult,0,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),0,2)
        self.basePllDiv = QtWidgets.QSpinBox()
        g.addWidget(self.basePllDiv,0,3)
        g.addWidget(QtWidgets.QLabel("Serial PLL Mult.:"),1,0)
        self.serialPllMult = QtWidgets.QSpinBox()
        g.addWidget(self.serialPllMult,1,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),1,2)
        self.serialPllDiv = QtWidgets.QSpinBox()
        g.addWidget(self.serialPllDiv,1,3)
        g.addWidget(QtWidgets.QLabel("EXT CLK Mult.:"),2,0)
        self.extClockMult = QtWidgets.QSpinBox()
        g.addWidget(self.extClockMult,2,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),2,2)
        self.extClockDiv = QtWidgets.QSpinBox()
        g.addWidget(self.extClockDiv,2,3)
        g.addWidget(QtWidgets.QLabel("Sample Div.:"),3,0)
        self.sampleDiv = QtWidgets.QSpinBox()
        g.addWidget(self.sampleDiv,3,1)
        g.setRowStretch(g.rowCount(),1)

        l.addStretch(1)

        self.readFromHwButton = QtWidgets.QPushButton("Read from HW")
        l.addWidget(self.readFromHwButton)


        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QtWidgets.QGridLayout()
        l.addLayout(g)
        g.addWidget(QtWidgets.QLabel("ADC freq. [MHz]:"),0,0)
        self.adcFrequency = QtWidgets.QSpinBox()
        g.addWidget(self.adcFrequency,0,1)
        g.addWidget(QtWidgets.QLabel("SATA freq. [MHz]:"),1,0)
        self.sataFrequency = QtWidgets.QSpinBox()
        g.addWidget(self.sataFrequency,1,1)

        g = QVGroupBox()
        l.addWidget(g)
        self.adcClockExt = QtWidgets.QCheckBox("ADC Clock Ext.")
        g.addWidget(self.adcClockExt)
        self.autoExtClock = QtWidgets.QCheckBox("Auto Ext. Clock")
        g.addWidget(self.autoExtClock)
        self.extSample = QtWidgets.QCheckBox("Ext. Sample")
        g.addWidget(self.extSample)
        
        g = QVGroupBox()
        l.addWidget(g)
        self.basicPllLocked = QtWidgets.QCheckBox("Basic PLL Locked")
        g.addWidget(self.basicPllLocked)
        self.sataPllLocked = QtWidgets.QCheckBox("SATA PLL Locked")
        g.addWidget(self.sataPllLocked)
        self.extDcmLocked = QtWidgets.QCheckBox("Ext. DCM Locked")
        g.addWidget(self.extDcmLocked)
        self.extClockValid = QtWidgets.QCheckBox("Ext. Clock Valid")
        g.addWidget(self.extClockValid)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Ext. clock freq. [MHz]"))
        self.extClockFrequency = QtWidgets.QSpinBox()
        h.addWidget(self.extClockFrequency)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        self.dualSata.factorySetting = True
        l.addWidget(self.dualSata)

        g = QVGroupBox()
        l.addWidget(g)
        self.trigPlus = QtWidgets.QCheckBox("Trig +")
        g.addWidget(self.trigPlus)
        self.trigMinus = QtWidgets.QCheckBox("Trig -")
        g.addWidget(self.trigMinus)
        self.maxTrig = QtWidgets.QCheckBox("Max. trig.")
        g.addWidget(self.maxTrig)
        self.disableWhenStreamOff = QtWidgets.QCheckBox("Disable when stream off")
        g.addWidget(self.disableWhenStreamOff)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Trigger delay [\u03bcs]:"))
        self.triggerDelay = QtWidgets.QSpinBox()
        h.addWidget(self.triggerDelay)

        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Sample number: "))
        self.sampleNumber = QtWidgets.QSpinBox()
        h.addWidget(self.sampleNumber)

        layout.addStretch(1)
