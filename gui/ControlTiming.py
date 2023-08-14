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
from GuiMode import *
from functools import partial

def null_func():
    print("clicked")


frequencyFormat = "{0:.4f}";    

def setFreqMultDiv(mult,div,combo):
    mult.blockSignals(True)
    mult.setValue(combo.currentData()[0])
    mult.blockSignals(False)
    div.blockSignals(True)
    div.setValue(combo.currentData()[1])
    div.blockSignals(False)
    return True

def setFreqCombo(mult,div,combo):
    text = frequencyFormat.format(20.0*mult.value()/div.value())
    i = combo.findText(text)
    if i<0:
        print("This should not happen")
        return False
    combo.blockSignals(True)
    combo.setCurrentIndex(i)
    combo.blockSignals(False)
    return True
    
def populateFrequencyCombo(multFrom,multTo,divFrom,divTo,combo):
    # Calculate possible frequencies in a combo box
    # Create all mult/div combinations
    freqs = []
    for mult in range(multFrom,multTo+1):
        for div in range(divFrom,divTo+1):
            # first value is true frequency, for sorting, then mult and div
            freqs.append([20.0*mult/div,mult,div])
    # sort by first element (frequency) of tuples
    freqs.sort()

    # Remove duplicates
    i=1
    print(len(freqs))
    while i<len(freqs):
        # If same as previous, remove current and keep iterator unchanged
        if freqs[i][0] == freqs[i-1][0]:
            freqs.pop(i)
        # otherwise just go to the next element
        else:
            i=i+1

    for f in freqs:
        combo.addItem(frequencyFormat.format(f[0]),[f[1],f[2]])

    
class ControlTiming(QtWidgets.QWidget):
    def setSerialPll(self):
        self.gui.camera.setSerialPll(self.serialPllMult.value(),self.serialPllDiv.value())

    def setAdcClockParameters(self):
        #self.adcFrequency.setText("{0:.3f}".format(20*adcmult/adcdiv))
        self.gui.camera.setClock(self.gui.camera.CLK_EXTERNAL if self.adcClockExt.isChecked() else self.gui.camera.CLK_INTERNAL,
                                 adcdiv=self.basePllDiv.value(),
                                 adcmult=self.basePllMult.value(),
                                 extdiv=self.extClockDiv.value(),
                                 extmult=self.extClockMult.value(),
                                 autoExternal=self.autoExtClock.isChecked(),
                                 externalSample=self.extSample.isChecked())


    def updateGui(self):
        T = self.gui.camera.status.CCTemp
        self.ccCardTemp.setText("{:3d}".format(T))
        if self.ccCardMaxTemp.text()=="" or T>int(self.ccCardMaxTemp.text()):
            self.ccCardMaxTemp.setText("{:3d}".format(T))

        self.ccCardVoltage33.setText("{0:.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_33V:self.gui.camera.codes_CC.CC_REGISTER_33V+2],'little')/1000.0))
        self.ccCardVoltage25.setText("{0:.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_33V:self.gui.camera.codes_CC.CC_REGISTER_33V+2],'little')/1000.0))
        self.ccCardVoltage18XC.setText("{0:.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_18VXC:self.gui.camera.codes_CC.CC_REGISTER_18VXC+2],'little')/1000.0))
        self.ccCardVoltage12ST.setText("{0:.3f}".format(int.from_bytes(self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_12VST:self.gui.camera.codes_CC.CC_REGISTER_12VST+2],'little')/1000.0))
        
        self.basicPllLocked.setChecked((self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_PLLSTAT]>>0)&1)
        self.sataPllLocked.setChecked((self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_PLLSTAT]>>1)&1)
        self.extDcmLocked.setChecked((self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_PLLSTAT]>>2)&1)
        self.extClockValid.setChecked((self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_PLLSTAT]>>3)&1)

        # external clock in MHz (register value is in kHz)
        extClockFreq = int.from_bytes(self.gui.camera.status.CC_variables[self.gui.camera.codes_CC.CC_REGISTER_EXTCLKFREQ:self.gui.camera.codes_CC.CC_REGISTER_EXTCLKFREQ:2],'big')/1000.0
        self.extClockFreq.setText("{0:.3f}".format(extClockFreq*self.extClockMult.value()/self.extClockDiv.value()))

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
        readOnly(self.ccCardTemp)
        self.ccCardTemp.setToolTip("The actual temperature of the Control Card (CC)")
        g.addWidget(self.ccCardTemp)
        g.addWidget(QtWidgets.QLabel("CC card max. temp.:"))
        self.ccCardMaxTemp = QtWidgets.QLineEdit()
        readOnly(self.ccCardMaxTemp)
        self.ccCardMaxTemp.setToolTip("Maximum temperature of the board since.... since what?")
        g.addWidget(self.ccCardMaxTemp)

        g = QGridGroupBox("CC card voltages")
        l.addWidget(g)
        g.addWidget(QtWidgets.QLabel("3.3 V:"),0,0)
        self.ccCardVoltage33 = QtWidgets.QLineEdit()
        readOnly(self.ccCardVoltage33)
        self.ccCardVoltage33.setToolTip("Display of the actual value of the VDD 3.3V (main) power supply in V")
        g.addWidget(self.ccCardVoltage33,0,1)

        g.addWidget(QtWidgets.QLabel("1.8 V XC:"),0,2)
        self.ccCardVoltage18XC = QtWidgets.QLineEdit()
        readOnly(self.ccCardVoltage18XC)
        self.ccCardVoltage18XC.setToolTip("Display of the actual value of the 1.8 V XC power supply in V")
        g.addWidget(self.ccCardVoltage18XC,0,3)

        g.addWidget(QtWidgets.QLabel("2.5 V:"),1,0)
        self.ccCardVoltage25 = QtWidgets.QLineEdit()
        readOnly(self.ccCardVoltage25)
        self.ccCardVoltage25.setToolTip("Display of the actual value of the VDD 2.5V power supply in V")
        g.addWidget(self.ccCardVoltage25,1,1)

        g.addWidget(QtWidgets.QLabel("1.2 V ST:"),1,2)
        self.ccCardVoltage12ST = QtWidgets.QLineEdit()
        readOnly(self.ccCardVoltage12ST)
        self.ccCardVoltage12ST.setToolTip("Display of the actual value of the VDD 1.2 V ST power supply in V")
        g.addWidget(self.ccCardVoltage12ST,1,3)

        g = QGridGroupBox()
        l.addWidget(g)

        title = QtWidgets.QLabel("Frequencies      ")
        title.setStyleSheet("font-weight:bold")
        g.addWidget(title,0,0)

        g.addWidget(QtWidgets.QLabel("Multiplier"),0,1)
        g.addWidget(QtWidgets.QLabel("Divisor"),0,2)
        g.addWidget(QtWidgets.QLabel("Ref. freq."),0,3)
        g.addWidget(QtWidgets.QLabel("Actual freq."),0,4)

        g.addWidget(QtWidgets.QLabel("Serial (SATA):"),1,0)

        serialPllMultMin = 10
        serialPllMultMax = 10
        self.serialPllMult = QtWidgets.QSpinBox()
        self.serialPllMult.settingsName = "SATA frequency multiplier"
        self.serialPllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllMult.setToolTip("Set the multiplier value for the serial PLL. Takes effect when you press Enter.")
        self.serialPllMult.setMinimum(serialPllMultMin)
        self.serialPllMult.setMaximum(serialPllMultMax)
        self.serialPllMult.setValue(serialPllMultMin)
        g.addWidget(self.serialPllMult,1,1)

        serialPllDivMin = 10
        serialPllDivMax = 10
        self.serialPllDiv = QtWidgets.QSpinBox()
        self.serialPllDiv.settingsName = "SATA frequency divisor"
        self.serialPllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllDiv.setToolTip("Set the divider value for the serial PLL. Takes effect when you press Enter")
        self.serialPllDiv.setMinimum(serialPllDivMin)
        self.serialPllDiv.setMaximum(serialPllDivMax)
        self.serialPllDiv.setValue(serialPllDivMin)
        g.addWidget(self.serialPllDiv,1,2)

        self.serialPllFreq = QtWidgets.QComboBox()
        g.addWidget(self.serialPllFreq,1,3)
        self.serialPllFreq.setToolTip("The frequency [MHz] for the serial (SATA) line (20 MHz base clock frequency multiplied/divided by the values given on the left")
        populateFrequencyCombo(serialPllMultMin,serialPllMultMax,serialPllDivMin,serialPllDivMax,self.serialPllFreq)
        self.serialPllFreq.setCurrentText(frequencyFormat.format(20.0*self.serialPllMult.value()/self.serialPllDiv.value()))

        self.serialPllFreq.activated               .connect(self.gui.call(lambda: setFreqMultDiv(self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
        self.serialPllMult.lineEdit().returnPressed.connect(self.gui.call(lambda: setFreqCombo  (self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
        self.serialPllDiv .lineEdit().returnPressed.connect(self.gui.call(lambda: setFreqCombo  (self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
                                                                                 

        # ----------------------- ADC PLL parameters/frequency -----------------------------------------

        g.addWidget(QtWidgets.QLabel("ADC:"),2,0)

        self.basePllMult = QtWidgets.QSpinBox()
        self.basePllMult.settingsName = "ADC frequency multiplier"
        self.basePllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.basePllMult.setToolTip("Multiplier for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.basePllMult.setMinimum(20)
        self.basePllMult.setMaximum(50)
        self.basePllMult.setValue(20)
        g.addWidget(self.basePllMult,2,1)

        self.basePllDiv = QtWidgets.QSpinBox()
        self.basePllDiv.settingsName = "ADC frequency divisor"
        self.basePllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.basePllDiv.setToolTip("Divider for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.basePllDiv.setMinimum(8)
        self.basePllDiv.setMaximum(100)
        self.basePllDiv.setValue(8)
        g.addWidget(self.basePllDiv,2,2)

        self.basePllFreq = QtWidgets.QComboBox()
        g.addWidget(self.basePllFreq,2,3)
        populateFrequencyCombo(20,50,8,100,self.basePllFreq)
        self.basePllFreq.setCurrentText(frequencyFormat.format(20.0*self.basePllMult.value()/self.basePllDiv.value()))
        self.basePllFreq.setToolTip("The frequency [MHz] for the ADC (20 MHz base clock frequency multiplied/divided by the values given on the left")

        

        # ----------------------- External clock parameters/frequency -----------------------------------------
        
        g.addWidget(QtWidgets.QLabel("Ext. clock:"),3,0)

        self.extClockMult = QtWidgets.QSpinBox()
        self.extClockMult.settingsName = "External clock frequency multiplier"
        self.extClockMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockMult.setToolTip("Multiplier for the external clock frequency. Takes effect when you press Enter.")
        self.extClockMult.setMinimum(2)
        self.extClockMult.setMaximum(33)
        g.addWidget(self.extClockMult,3,1)

        self.extClockDiv = QtWidgets.QSpinBox()
        self.extClockDiv.settingsName = "External clock frequency divisor"
        self.extClockDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockDiv.setToolTip("Divider for the external clock frequency. Takes effect when you press Enter.")
        self.extClockDiv.setMinimum(1)
        self.extClockDiv.setMaximum(32)
        g.addWidget(self.extClockDiv,3,2)

        self.extClockFreq = QtWidgets.QLineEdit()
        readOnly(self.extClockFreq)
        self.extClockFreq.setToolTip("The measured frequency [MHz] of the external clock, multiplied and divided by the multiplicator and divisor on the left")
        g.addWidget(self.extClockFreq,3,3)
        

        self.basePllFreq.activated.connect               (lambda: setFreqMultDiv(self.basePllMult,self.basePllDiv,self.basePllFreq) and self.setAdcClockParameters())
        self.basePllMult.lineEdit().returnPressed.connect(lambda: setFreqCombo  (self.basePllMult,self.basePllDiv,self.basePllFreq) and self.setAdcClockParameters())
        self.basePllDiv.lineEdit() .returnPressed.connect(lambda: setFreqCombo  (self.basePllMult,self.basePllDiv,self.basePllFreq) and self.setAdcClockParameters())
        self.extClockMult.lineEdit().returnPressed.connect(self.setAdcClockParameters)
        self.extClockDiv.lineEdit() .returnPressed.connect(self.setAdcClockParameters)

        g.addWidget(QtWidgets.QLabel("Sample:"),4,0)
        self.sampleDiv = QtWidgets.QSpinBox()
        self.sampleDiv.settingsName = "Sampling frequency divisor"
        g.addWidget(self.sampleDiv,4,2)
        g.setRowStretch(g.rowCount(),1)
        self.sampleDiv.setMinimum(1)
        self.sampleDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.sampleDiv.lineEdit().returnPressed.connect(self.gui.call(lambda : self.gui.camera.setSampleDivider(self.sampleDiv.value())))
        self.sampleDiv.setToolTip("Sample clock divider (sampling frequency w.r.t. ADC clock frequency, APDCAM User Guide Fig. 6). Takes effect when you press Enter")

        self.sampleFreq = QtWidgets.QLineEdit()
        g.addWidget(self.sampleFreq,4,4)

        l.addStretch(1)


        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QVGroupBox()
        l.addWidget(g)

        self.adcClockExt = QtWidgets.QCheckBox("ADC Clock Ext.")
        self.adcClockExt.settingsName = "External ADC clock"
        self.adcClockExt.setToolTip("Use external clock if checked, and internal clock if unchecked")
        self.adcClockExt.stateChanged.connect(self.setAdcClockParameters)
        g.addWidget(self.adcClockExt)
        
        self.autoExtClock = QtWidgets.QCheckBox("Auto Ext. Clock")
        self.autoExtClock.settingsName = "Auto external clock"
        self.autoExtClock.setToolTip("Enable auto external clock mode: external clock is used if quality is good, will fall back to internal otherwise")
        self.autoExtClock.stateChanged.connect(self.setAdcClockParameters)
        g.addWidget(self.autoExtClock)

        self.extSample = QtWidgets.QCheckBox("Ext. Sample")
        self.extSample.settingsName = "External sampling signal"
        self.extSample.setToolTip("Use external signal for sampling, rather than ADC frequency divided by SAMPLEDIVIDER")
        g.addWidget(self.extSample)


        g = QVGroupBox()
        l.addWidget(g)
        self.basicPllLocked = QtWidgets.QCheckBox("Basic PLL Locked")
        readOnly(self.basicPllLocked)
        self.basicPllLocked.setToolTip("Indicator for the basic (ADC) PLL being in lock")
        g.addWidget(self.basicPllLocked)
        
        self.sataPllLocked = QtWidgets.QCheckBox("SATA PLL Locked")
        readOnly(self.sataPllLocked)
        self.sataPllLocked.setToolTip("Indicator for the serial (SATA) PLL being in lock")
        g.addWidget(self.sataPllLocked)
        
        self.extDcmLocked = QtWidgets.QCheckBox("Ext. DCM Locked")
        readOnly(self.extDcmLocked)
        self.extDcmLocked.setToolTip("Indicator for the external clock module (DCM) being in lock")
        g.addWidget(self.extDcmLocked)
        
        self.extClockValid = QtWidgets.QCheckBox("Ext. Clock Valid")
        readOnly(self.extClockValid)
        self.extClockValid.setToolTip("Indicator for the external clock giving a valid clock signal")
        g.addWidget(self.extClockValid)


        l.addStretch(1)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        #self.dualSata.factorySetting = True
        self.dualSata.guiMode = GuiMode.factory
        self.dualSata.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setDualSata(self.dualSata.isChecked())))
        self.dualSata.setToolTip("Enable dual SATA mode for the system (CC card and all ADC boards)")
        l.addWidget(self.dualSata)


        g = QVGroupBox("Trigger")
        l.addWidget(g)
        self.trigPlus = QtWidgets.QCheckBox("Ext. Trig. +")
        self.trigPlus.settingsName = "External trigger positive edge"
        self.trigPlus.setToolTip("Enable triggering on rising edge of external signal")
        g.addWidget(self.trigPlus)
        self.trigMinus = QtWidgets.QCheckBox("Ext. Trig. -")
        self.trigMinus.settingsName = "External trigger negative edge"
        self.trigMinus.setToolTip("Enable triggering on falling edge of external signal")
        g.addWidget(self.trigMinus)
        self.internalTrig = QtWidgets.QCheckBox("Internal trigger")
        self.internalTrig.settingsName = "Internal trigger"
        self.internalTrig.setToolTip("Enable triggering on ADC channels (individual channels need to be enabled, and their threshold set in the 'ADC Control' tab)")
        g.addWidget(self.internalTrig)
        self.disableWhenStreamOff = QtWidgets.QCheckBox("Disable when stream off")
        self.disableWhenStreamOff.settingsName = "Disable when stream off"
        self.disableWhenStreamOff.setToolTip("If set, trigger events are disabled while streams are off. Otherwise triggers are registered even if streams are off, and data transmission starts immediately when streams are enabled again")
        g.addWidget(self.disableWhenStreamOff)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Trigger delay [\u03bcs]:"))
        self.triggerDelay = QtWidgets.QSpinBox()
        self.triggerDelay.settingsName = "Trigger delay [us]"
        self.triggerDelay.setToolTip("Data stream output will start with this delay after the trigger")
        h.addWidget(self.triggerDelay)

        triggerFunc = self.gui.call(lambda: self.gui.camera.setTrigger(self.trigPlus.isChecked(),self.trigMinus.isChecked(),self.internalTrig.isChecked(),self.triggerDelay.value()))

        self.trigPlus.stateChanged.connect(triggerFunc)
        self.trigMinus.stateChanged.connect(triggerFunc)
        self.internalTrig.stateChanged.connect(triggerFunc)
        self.triggerDelay.lineEdit().returnPressed.connect(triggerFunc)

        # h = QtWidgets.QHBoxLayout()
        # l.addLayout(h)
        # h.addWidget(QtWidgets.QLabel("Sample number: "))
        # self.sampleNumber = QtWidgets.QSpinBox()
        # self.sampleNumber.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        # self.sampleNumber.lineEdit().returnPressed.connect(lambda: self.gui.camera.setSampleNumber(self.sampleNumber.value()))
        # self.sampleNumber.setToolTip("Set the number of samples to acquire")
        # h.addWidget(self.sampleNumber)

        l.addStretch(1)

        layout.addStretch(1)

