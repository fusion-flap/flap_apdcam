import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")
Qt = QtCore.Qt

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox
# from PyQt6.QtCore import Qt
from ApdcamUtils import *

def null_func():
    print("clicked")


class ControlTiming(QtWidgets.QWidget):

    def updateGui(self):
        T = self.gui.camera.status.CCTemp
        self.ccCardTemp.setText("{:3d}".format(T))
        if T>int(self.ccCardMaxTemp.text()):
            self.ccCardMaxTemp.setText("{:3d}".format(T))

        self.ccCardVoltage33.setText("{3.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_33V:APDCAM10G_control.CC_REGISTER_33V+2],'little')))
        self.ccCardVoltage25.setText("{3.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_33V:APDCAM10G_control.CC_REGISTER_33V+2],'little')))
        self.ccCardVoltage18XC.setText("{3.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_18VXC:APDCAM10G_control.CC_REGISTER_18VXC+2],'little')))
        self.ccCardVoltage12ST.setText("{3.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_12VST:APDCAM10G_control.CC_REGISTER_12VST+2],'little')))
        
        self.basicPllLocked.setChecked((self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_PLLSTAT]>>0)&1)
        self.sataPllLocked.setChecked((self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_PLLSTAT]>>1)&1)
        self.extDcmLocked.setChecked((self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_PLLSTAT]>>2)&1)
        self.extClockValid.setChecked((self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_PLLSTAT]>>3)&1)
        self.extClockFrequency.setText("{3.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[APDCAM10G_control.CC_REGISTER_EXTCLKFREQ:APDCAM10G_control.CC_REGISTER_EXTCLKFREQ:2],'big')/1000.0))

    def __init__(self,parent):
        super(ControlTiming,self).__init__(parent)

        self.gui = parent

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QHGroupBox("CC card temperatures")
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("CC card temp.:"))
        self.ccCardTemp = QtWidgets.QLineEdit()
        self.ccCardTemp.setReadOnly(True)
        self.ccCardTemp.setToolTip("The actual temperature of the Control Card (CC)")
        g.addWidget(self.ccCardTemp)
        g.addWidget(QtWidgets.QLabel("CC card max. temp.:"))
        self.ccCardMaxTemp = QtWidgets.QLineEdit()
        self.ccCardMaxTemp.setReadOnly(True)
        self.ccCardMaxTemp.setToolTip("Maximum temperature of the board since.... since what?")
        g.addWidget(self.ccCardMaxTemp)

        g = QGridGroupBox("CC card voltages")
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("3.3 V [mV]:"),0,0)
        self.ccCardVoltage33 = QtWidgets.QLineEdit()
        self.ccCardVoltage33.setReadOnly(False)
        self.ccCardVoltage33.setToolTip("Display of the actual value of the VDD 3.3V (main) power supply in mV")
        g.addWidget(self.ccCardVoltage33,0,1)

        g.addWidget(QtWidgets.QLabel("1.8 V XC [mV]:"),0,2)
        self.ccCardVoltage18XC = QtWidgets.QLineEdit()
        self.ccCardVoltage18XC.setReadOnly(False)
        self.ccCardVoltage18XC.setToolTip("Display of the actual value of the 1.8 V XC power supply in mV")
        g.addWidget(self.ccCardVoltage18XC,0,3)

        g.addWidget(QtWidgets.QLabel("2.5 V [mV]:"),1,0)
        self.ccCardVoltage25 = QtWidgets.QLineEdit()
        self.ccCardVoltage25.setReadOnly(True)
        self.ccCardVoltage25.setToolTip("Display of the actual value of the VDD 2.5V power supply in mV")
        g.addWidget(self.ccCardVoltage25,1,1)

        g.addWidget(QtWidgets.QLabel("1.2 V ST [mV]:"),1,2)
        self.ccCardVoltage12ST = QtWidgets.QLineEdit()
        self.ccCardVoltage12ST.setReadOnly(True)
        self.ccCardVoltage12ST.setToolTip("Display of the actual value of the VDD 1.2 V ST power supply in mV")
        g.addWidget(self.ccCardVoltage12ST,1,3)

        g = QGridGroupBox()
        l.addWidget(g)

        g.addWidget(QtWidgets.QLabel("Serial (SATA) PLL Mult.:"),0,0)
        self.serialPllMult = QtWidgets.QSpinBox()
        self.serialPllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllMult.setToolTip("Set the multiplier value for the serial PLL. Takes effect when you press Enter.")
        g.addWidget(self.serialPllMult,0,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),0,2)
        self.serialPllDiv = QtWidgets.QSpinBox()
        self.serialPllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllDiv.setToolTip("Set the divider value for the serial PLL. Takes effect when you press Enter")
        g.addWidget(self.serialPllDiv,0,3)

        serialPllFunction = self.gui.call(lambda: self.gui.camera.setSerialPll(self.serialPllMult.value(),self.serialPllDiv.value()))
        self.serialPllMult.lineEdit().returnPressed.connect(serialPllFunction)
        self.serialPllDiv.lineEdit().returnPressed.connect(serialPllFunction)

        # # Calculate possible frequencies in a combo box
        # # Create all mult/div combinations
        # adcPllFreqs = []
        # for mult in range(20,51):
        #     for div in range(8,101):
        #         adcPllFreqs.append([20.0*mult/div,mult,div])
        # adcPllFreqs.sort()

        # # Remove duplicates
        # i=1
        # print(len(adcPllFreqs))
        # while i<len(adcPllFreqs):
        #     if adcPllFreqs[i][0] == adcPllFreqs[i-1][0]:
        #         adcPllFreqs.pop(i)
        #     else:
        #         i=i+1

        # g.addWidget(QtWidgets.QLabel("ADC frequency [MHz]"),1,0)
        # self.adcPllFrequency = QtWidgets.QComboBox()
        # for f in adcPllFreqs:
        #     self.adcPllFrequency.addItem(str(f[0]),[f[1],f[2]])
        # g.addWidget(self.adcPllFrequency,1,1)

        # self.adcPllFrequency.activated[str].connect(lambda: print(self.adcPllFrequency.currentText()))

        g.addWidget(QtWidgets.QLabel("ADC PLL Mult.:"),1,0)
        self.basePllMult = QtWidgets.QSpinBox()
        self.basePllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.basePllMult.setToolTip("Multiplier for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.basePllMult.setMinimum(20)
        self.basePllMult.setMaximum(50)
        g.addWidget(self.basePllMult,1,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),1,2)
        self.basePllDiv = QtWidgets.QSpinBox()
        self.basePllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.basePllDiv.setToolTip("Divider for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.basePllDiv.setMinimum(8)
        self.basePllDiv.setMaximum(100)
        g.addWidget(self.basePllDiv,1,3)

        g.addWidget(QtWidgets.QLabel("EXT CLK Mult.:"),2,0)
        self.extClockMult = QtWidgets.QSpinBox()
        self.extClockMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockMult.setToolTip("Multiplier for the external clock frequency. Takes effect when you press Enter.")
        self.extClockMult.setMinimum(2)
        self.extClockMult.setMaximum(33)
        g.addWidget(self.extClockMult,2,1)
        g.addWidget(QtWidgets.QLabel("Div.:"),2,2)
        self.extClockDiv = QtWidgets.QSpinBox()
        self.extClockDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockDiv.setToolTip("Divider for the external clock frequency. Takes effect when you press Enter.")
        self.extClockDiv.setMinimum(1)
        self.extClockDiv.setMaximum(32)
        g.addWidget(self.extClockDiv,2,3)

        
        # setClockFunction = self.gui.call(lambda: self.gui.camera.setClock(APDCAM10G_regCom.CLK_EXTERNAL if self.adcClockExt.isChecked() else APDCAM10G_regCom.CLK_INTERNAL,
        #                                                                   adcdiv=self.basePllDiv.value(),
        #                                                                   adcmult=self.basePllMult.value(),
        #                                                                   extdiv=self.extClockDiv.value(),
        #                                                                   extmult=self.extClockMult.value(),
        #                                                                   autoExternal=self.autoExtClock.isChecked()))
        def setClockFunction(self):
            self.adcFrequency.setText("{3.3f}".format(20*adcmult/adcdiv))
            self.gui.camera.setClock(APDCAM10G_regCom.CLK_EXTERNAL if self.adcClockExt.isChecked() else APDCAM10G_regCom.CLK_INTERNAL,
                                     adcdiv=self.basePllDiv.value(),
                                     adcmult=self.basePllMult.value(),
                                     extdiv=self.extClockDiv.value(),
                                     extmult=self.extClockMult.value(),
                                     autoExternal=self.autoExtClock.isChecked())
            

        self.basePllMult.lineEdit().returnPressed.connect(setClockFunction)
        self.basePllDiv.lineEdit().returnPressed.connect(setClockFunction)
        self.extClockMult.lineEdit().returnPressed.connect(setClockFunction)
        self.extClockDiv.lineEdit().returnPressed.connect(setClockFunction)

        g.addWidget(QtWidgets.QLabel("Sample Div.:"),3,0)
        self.sampleDiv = QtWidgets.QSpinBox()
        g.addWidget(self.sampleDiv,3,1)
        g.setRowStretch(g.rowCount(),1)
        self.sampleDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.sampleDiv.lineEdit().returnPressed.connect(self.gui.call(lambda : self.gui.camera.setSampleDivider(self.sampleDiv.value())))
        self.sampleDiv.setToolTip("Sample clock divider (sampling frequency w.r.t. ADC clock frequency, APDCAM User Guide Fig. 6). Takes effect when you press Enter")

        l.addStretch(1)

        self.readFromHwButton = QtWidgets.QPushButton("Read from HW")
        l.addWidget(self.readFromHwButton)


        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QtWidgets.QGridLayout()
        l.addLayout(g)
        g.addWidget(QtWidgets.QLabel("ADC freq. [MHz]:"),0,0)
        self.adcFrequency = QtWidgets.QLineEdit()
        self.adcFrequency.setReadOnly(True)
        g.addWidget(self.adcFrequency,0,1)
        g.addWidget(QtWidgets.QLabel("SATA freq. [MHz]:"),1,0)
        self.sataFrequency = QtWidgets.QSpinBox()
        g.addWidget(self.sataFrequency,1,1)

        g = QVGroupBox()
        l.addWidget(g)

        self.adcClockExt = QtWidgets.QCheckBox("ADC Clock Ext.")
        self.adcClockExt.setToolTip("Use external clock if checked, and internal clock if unchecked")
        self.adcClockExt.stateChanged.connect(setClockFunction)
        g.addWidget(self.adcClockExt)
        
        self.autoExtClock = QtWidgets.QCheckBox("Auto Ext. Clock")
        self.autoExtClock.setToolTip("Enable auto external clock mode: external clock is used if quality is good, will fall back to internal otherwise")
        self.autoExtClock.stateChanged.connect(setClockFunction)
        g.addWidget(self.autoExtClock)

        self.extSample = QtWidgets.QCheckBox("Ext. Sample")
        g.addWidget(self.extSample)


        g = QVGroupBox()
        l.addWidget(g)
        self.basicPllLocked = QtWidgets.QCheckBox("Basic PLL Locked")
        self.basicPllLocked.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.basicPllLocked.setToolTip("Indicator for the basic (ADC) PLL being in lock")
        g.addWidget(self.basicPllLocked)
        
        self.sataPllLocked = QtWidgets.QCheckBox("SATA PLL Locked")
        self.sataPllLocked.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.sataPllLocked.setToolTip("Indicator for the serial (SATA) PLL being in lock")
        g.addWidget(self.sataPllLocked)
        
        self.extDcmLocked = QtWidgets.QCheckBox("Ext. DCM Locked")
        self.extDcmLocked.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.extDcmLocked.setToolTip("Indicator for the external clock module (DCM) being in lock")
        g.addWidget(self.extDcmLocked)
        
        self.extClockValid = QtWidgets.QCheckBox("Ext. Clock Valid")
        self.extClockValid.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.extClockValid.setToolTip("Indicator for the external clock giving a valid clock signal")
        g.addWidget(self.extClockValid)

        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Ext. clock freq. [MHz]"))
        self.extClockFrequency = QtWidgets.QLineEdit()
        self.extClockFrequency.setReadOnly(True)
        self.extClockFrequency.setToolTip("Frequency of the external clock, measured by the control card of the camera, in MHz")
        h.addWidget(self.extClockFrequency)

        l.addStretch(1)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        self.dualSata.factorySetting = True
        l.addWidget(self.dualSata)


        g = QVGroupBox("Trigger")
        l.addWidget(g)
        self.trigPlus = QtWidgets.QCheckBox("Ext. Trig. +")
        self.trigPlus.setToolTip("Enable triggering on rising edge of external signal")
        g.addWidget(self.trigPlus)
        self.trigMinus = QtWidgets.QCheckBox("Ext. Trig. -")
        self.trigMinus.setToolTip("Enable triggering on falling edge of external signal")
        g.addWidget(self.trigMinus)
        self.internalTrig = QtWidgets.QCheckBox("Internal trigger")
        self.internalTrig.setToolTip("Enable triggering on ADC channels (individual channels need to be enabled, and their threshold set in the 'ADC Control' tab)")
        g.addWidget(self.internalTrig)
        self.disableWhenStreamOff = QtWidgets.QCheckBox("Disable when stream off")
        self.disableWhenStreamOff.setToolTip("If set, trigger events are disabled while streams are off. Otherwise triggers are registered even if streams are off, and data transmission starts immediately when streams are enabled again")
        g.addWidget(self.disableWhenStreamOff)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Trigger delay [\u03bcs]:"))
        self.triggerDelay = QtWidgets.QSpinBox()
        self.triggerDelay.setToolTip("Data stream output will start with this delay after the trigger")
        h.addWidget(self.triggerDelay)

        triggerFunc = self.gui.call(lambda: self.gui.camera.setTrigger(self.trigPlus.isChecked(),self.trigMinus.isChecked(),self.internalTrig.isChecked(),self.triggerDelay.value()))

        self.trigPlus.stateChanged.connect(triggerFunc)
        self.trigMinus.stateChanged.connect(triggerFunc)
        self.internalTrig.stateChanged.connect(triggerFunc)
        self.triggerDelay.lineEdit().returnPressed.connect(triggerFunc)

        

        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Sample number: "))
        self.sampleNumber = QtWidgets.QSpinBox()
        h.addWidget(self.sampleNumber)

        l.addStretch(1)

        layout.addStretch(1)
