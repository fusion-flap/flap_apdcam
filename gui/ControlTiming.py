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
    """
    Set the text of a combo-box (which contains a pre-selected list of possible (but not all) frequencies,
    to the value 20*mult/div (where 20 [MHz] is the (hard-coded) frequency of the internal clock.
    If this value is contained in the combo box list, choose that item. Otherwise choose the first item
    of the combo box (which is reserved for this purpose) and change its text value
    """

    try:
        mult.value()
        div.value()
    except:
        return False

    combo.setItemText(0,"")
    text = frequencyFormat.format(20.0*mult.value()/div.value())
    i = combo.findText(text)
    #combo.blockSignals(True)
    if i<0:
        combo.setItemText(0,frequencyFormat.format(20.0*mult.value()/div.value()))
        combo.setItemData(0,[mult.value(),div.value()])
        combo.setCurrentIndex(0)
    else:
        combo.setCurrentIndex(i)
    #combo.blockSignals(False)
    return True
    
def populateFrequencyCombo(multFrom,multTo,divFrom,divTo,combo):
    # Calculate possible frequencies in a combo box
    # Create all mult/div combinations
    freqs = []
    for mult in range(multFrom,multTo+1):
        for div in range(divFrom,divTo+1):
            val = 20.0*mult/div
            if abs(round(val/2)-val/2) < 0.0001:
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

    combo.addItem(frequencyFormat.format(freqs[0][0]),[freqs[0][1],freqs[0][2]])
    for f in freqs:
        combo.addItem(frequencyFormat.format(f[0]),[f[1],f[2]])

    
class ControlTiming(QtWidgets.QWidget):
    def versionSpecificSetup(self,fw):
        version = int(fw[11:14])
        if version >= 105:
            self.sampleDiv.setMinimum(1)
            self.adcOutFreqDiv.setEnabled(True)
        else:
            self.sampleDiv.setMinimum(3)
            self.adcOutFreqDiv.setEnabled(False)

    def setSerialPll(self):
        self.gui.camera.setSerialPll(self.serialPllMult.value(),self.serialPllDiv.value())

    def setSampleDivider(self):
        self.updateSamplingFrequency()
        if self.gui.status.connected:
            self.gui.camera.setSampleDivider(self.sampleDiv.value())

    def updateSamplingFrequency(self):
        try:
            if self.adcClockExt.isChecked():
                self.sampleFreqRef.setValue(self.extClockFreqScaled.value())
            else:
                self.sampleFreqRef.setValue(float(self.adcPllFreq.currentText()))
            self.sampleFreq.setValue(self.sampleFreqRef.value()/self.sampleDiv.value())
        except:
            pass

    def setAdcClockParameters(self):
        if not self.gui.status.connected:
            return
        #self.adcFrequency.setText("{0:.3f}".format(20*adcmult/adcdiv))
        self.gui.camera.setClock(self.gui.camera.CLK_EXTERNAL if self.adcClockExt.isChecked() else self.gui.camera.CLK_INTERNAL,
                                 adcdiv=self.adcPllDiv.value(),
                                 adcmult=self.adcPllMult.value(),
                                 extdiv=self.extClockDiv.value(),
                                 extmult=self.extClockMult.value(),
                                 autoExternal=self.autoExtClock.isChecked(),
                                 externalSample=self.extSample.isChecked())


    def updateGui(self):
        T = self.gui.camera.status.CCTemp
        self.ccCardTemp.setText("{:3d}".format(T))
        if self.ccCardMaxTemp.text()=="" or T>int(self.ccCardMaxTemp.text()):
            self.ccCardMaxTemp.setText("{:3d}".format(T))

        v = self.gui.camera.status.CC_variables
        c = self.gui.camera.codes_CC
        self.ccCardVoltage33.setText("{0:.3f}".format(int.from_bytes(v[c.CC_REGISTER_33V:c.CC_REGISTER_33V+2],'little')/1000.0))
        self.ccCardVoltage25.setText("{0:.3f}".format(int.from_bytes(v[c.CC_REGISTER_25V:c.CC_REGISTER_25V+2],'little')/1000.0))
        self.ccCardVoltage18XC.setText("{0:.3f}".format(int.from_bytes(v[c.CC_REGISTER_18VXC:c.CC_REGISTER_18VXC+2],'little')/1000.0))
        self.ccCardVoltage12ST.setText("{0:.3f}".format(int.from_bytes(v[c.CC_REGISTER_12VST:c.CC_REGISTER_12VST+2],'little')/1000.0))
        
        self.basicPllLocked.setChecked((v[c.CC_REGISTER_PLLSTAT]>>0)&1)
        self.sataPllLocked.setChecked((v[c.CC_REGISTER_PLLSTAT]>>1)&1)
        self.extDcmLocked.setChecked((v[c.CC_REGISTER_PLLSTAT]>>2)&1)
        self.extClockValid.setChecked((v[c.CC_REGISTER_PLLSTAT]>>3)&1)

        # external clock in MHz (register value is in kHz)
        extClockFreq = int.from_bytes(v[c.CC_REGISTER_EXTCLKFREQ:c.CC_REGISTER_EXTCLKFREQ:2],'big')/1000.0
        self.extClockFreq.setValue(extClockFreq*self.extClockMult.value()/self.extClockDiv.value())

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

        g.addWidget(QtWidgets.QLabel("Ref. freq. [MHz]"),0,1)
        g.addWidget(QtWidgets.QLabel("Multiplier"),0,2)
        g.addWidget(QtWidgets.QLabel("Divisor"),0,3)
        g.addWidget(QtWidgets.QLabel("Actual frequency"),0,4)

        g.addWidget(QtWidgets.QLabel("Serial (SATA):"),1,0)

        g.addWidget(QtWidgets.QLabel("20"),1,1)

        serialPllMultMin = 10
        serialPllMultMax = 10
        self.serialPllMult = QtWidgets.QSpinBox()
        self.serialPllMult.guiMode = GuiMode.factory
        self.serialPllMult.settingsName = "SATA frequency multiplier"
        self.serialPllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllMult.setToolTip("Set the multiplier value for the serial PLL. Takes effect when you press Enter.")
        self.serialPllMult.setMinimum(serialPllMultMin)
        self.serialPllMult.setMaximum(serialPllMultMax)
        self.serialPllMult.setValue(serialPllMultMin)
        g.addWidget(self.serialPllMult,1,2)

        serialPllDivMin = 10
        serialPllDivMax = 10
        self.serialPllDiv = QtWidgets.QSpinBox()
        self.serialPllDiv.guiMode = GuiMode.factory
        self.serialPllDiv.settingsName = "SATA frequency divisor"
        self.serialPllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.serialPllDiv.setToolTip("Set the divider value for the serial PLL. Takes effect when you press Enter")
        self.serialPllDiv.setMinimum(serialPllDivMin)
        self.serialPllDiv.setMaximum(serialPllDivMax)
        self.serialPllDiv.setValue(serialPllDivMin)
        g.addWidget(self.serialPllDiv,1,3)


        self.serialPllFreq = QtWidgets.QComboBox()
        self.serialPllFreq.guiMode = GuiMode.factory
        g.addWidget(self.serialPllFreq,1,4)
        self.serialPllFreq.setToolTip("The frequency [MHz] for the serial (SATA) line (20 MHz base clock frequency multiplied/divided by the values given on the left")
        populateFrequencyCombo(serialPllMultMin,serialPllMultMax,serialPllDivMin,serialPllDivMax,self.serialPllFreq)
        self.serialPllFreq.setCurrentText(frequencyFormat.format(20.0*self.serialPllMult.value()/self.serialPllDiv.value()))

        self.serialPllFreq.activated               .connect(self.gui.call(lambda: setFreqMultDiv(self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
        self.serialPllMult.lineEdit().returnPressed.connect(self.gui.call(lambda: setFreqCombo  (self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
        self.serialPllDiv .lineEdit().returnPressed.connect(self.gui.call(lambda: setFreqCombo  (self.serialPllMult,self.serialPllDiv,self.serialPllFreq) and self.setSerialPll()))
                                                                                 

        # ----------------------- ADC PLL parameters/frequency -----------------------------------------

        g.addWidget(QtWidgets.QLabel("ADC:"),2,0)

        tmp = QtWidgets.QLabel("20")
        tmp.setToolTip("The frequency of the built-in internal clock")
        g.addWidget(tmp,2,1)

        self.adcPllMult = QtWidgets.QSpinBox()
        self.adcPllMult.settingsName = "ADC frequency multiplier"
        self.adcPllMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.adcPllMult.setToolTip("Multiplier for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.adcPllMult.setMinimum(20)
        self.adcPllMult.setMaximum(50)
        self.adcPllMult.setValue(20)
        g.addWidget(self.adcPllMult,2,2)

        self.adcPllDiv = QtWidgets.QSpinBox()
        self.adcPllDiv.settingsName = "ADC frequency divisor"
        self.adcPllDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.adcPllDiv.setToolTip("Divider for the internal clock frequency (20 MHz). Takes effect when you press Enter.")
        self.adcPllDiv.setMinimum(8)
        self.adcPllDiv.setMaximum(100)
        self.adcPllDiv.setValue(20)
        g.addWidget(self.adcPllDiv,2,3)

        self.adcPllFreq = QtWidgets.QComboBox()
        g.addWidget(self.adcPllFreq,2,4)
        populateFrequencyCombo(20,50,8,100,self.adcPllFreq)
        self.adcPllFreq.setCurrentText(frequencyFormat.format(20.0*self.adcPllMult.value()/self.adcPllDiv.value()))
        self.adcPllFreq.setToolTip("The frequency [MHz] for the ADC (20 MHz base clock frequency multiplied/divided by the values given on the left")

        self.adcPllFreq.currentTextChanged.connect(self.updateSamplingFrequency)

        self.adcPllFreq.activated.connect               (lambda: setFreqMultDiv(self.adcPllMult,self.adcPllDiv,self.adcPllFreq) and self.setAdcClockParameters())
        self.adcPllMult.lineEdit().returnPressed.connect(lambda: setFreqCombo  (self.adcPllMult,self.adcPllDiv,self.adcPllFreq) and self.setAdcClockParameters())
        self.adcPllDiv.lineEdit() .returnPressed.connect(lambda: setFreqCombo  (self.adcPllMult,self.adcPllDiv,self.adcPllFreq) and self.setAdcClockParameters())
        
        

        # ----------------------- External clock parameters/frequency -----------------------------------------
        
        g.addWidget(QtWidgets.QLabel("Ext. clock:"),3,0)

        self.extClockFreq = QtWidgets.QDoubleSpinBox()
        self.extClockFreq.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        readOnly(self.extClockFreq)
        self.extClockFreq.setToolTip("The measured frequency [MHz] of the external clock, to be multiplied and divided by the multiplicator and divisor on the right")
        g.addWidget(self.extClockFreq,3,1)

        self.extClockMult = QtWidgets.QSpinBox()
        self.extClockMult.settingsName = "External clock frequency multiplier"
        self.extClockMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockMult.setToolTip("Multiplier for the external clock frequency. Takes effect when you press Enter.")
        self.extClockMult.setMinimum(2)
        self.extClockMult.setMaximum(33)
        g.addWidget(self.extClockMult,3,2)

        self.extClockDiv = QtWidgets.QSpinBox()
        self.extClockDiv.settingsName = "External clock frequency divisor"
        self.extClockDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.extClockDiv.setToolTip("Divider for the external clock frequency. Takes effect when you press Enter.")
        self.extClockDiv.setMinimum(1)
        self.extClockDiv.setMaximum(32)
        g.addWidget(self.extClockDiv,3,3)

        self.extClockFreqScaled = QtWidgets.QDoubleSpinBox()
        self.extClockFreqScaled.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        readOnly(self.extClockFreqScaled)
        self.extClockFreqScaled.setToolTip("The multiplied/divided actual value derived from the external clock signal")
        g.addWidget(self.extClockFreqScaled,3,4)
        self.extClockFreqScaled.valueChanged.connect(self.updateSamplingFrequency)

        self.extClockMult.lineEdit().returnPressed.connect(self.setAdcClockParameters)
        self.extClockDiv.lineEdit() .returnPressed.connect(self.setAdcClockParameters)

        # -----------------------------  Sampling frequency -------------------------------------------------
        
        g.addWidget(QtWidgets.QLabel("Sampling:"),4,0)

        self.sampleFreqRef = QtWidgets.QDoubleSpinBox()
        self.sampleFreqRef.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.sampleFreqRef.setToolTip("Reference frequency [MHz] of the sampling: either the ADC of the external clock's frequency (depending on the checkbox 'ADC Clock Ext.'), to be divided by the divisor on the right")
        g.addWidget(self.sampleFreqRef,4,1)
        readOnly(self.sampleFreqRef)
        self.sampleFreqRef.setValue(float(self.adcPllFreq.currentText()))

        self.sampleDiv = QtWidgets.QSpinBox()
        self.sampleDiv.settingsName = "Sampling frequency divisor"
        g.addWidget(self.sampleDiv,4,3)
        g.setRowStretch(g.rowCount(),1)
        self.sampleDiv.setMinimum(2)
        self.sampleDiv.setValue(10)
        self.sampleDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.sampleDiv.lineEdit().returnPressed.connect(self.setSampleDivider)
        self.sampleDiv.setToolTip("Sample clock divisor (sampling frequency w.r.t. ADC clock frequency, APDCAM User Guide Fig. 6). Takes effect when you press Enter")

        self.sampleFreq = QtWidgets.QDoubleSpinBox()
        self.sampleFreq.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        readOnly(self.sampleFreq)
        self.sampleFreq.setValue(float(frequencyFormat.format(2)))
        g.addWidget(self.sampleFreq,4,4)

        l.addStretch(1)

        l = QtWidgets.QVBoxLayout()
        layout.addLayout(l)

        g = QVGroupBox()
        l.addWidget(g)

        self.adcClockExt = QtWidgets.QCheckBox("ADC Clock Ext.")
        self.adcClockExt.settingsName = "External ADC clock"
        self.adcClockExt.setToolTip("Use external clock if checked, and internal clock if unchecked")
        self.adcClockExt.stateChanged.connect(lambda: self.updateSamplingFrequency() and self.setAdcClockParameters())
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

        hh = QtWidgets.QHBoxLayout()
        g.addLayout(hh)
        hh.addWidget(QtWidgets.QLabel("ADC out freq. divisor:"))
        self.adcOutFreqDiv = QtWidgets.QSpinBox()
        hh.addWidget(self.adcOutFreqDiv)
        self.adcOutFreqDiv.settingsName = "ADC output frequency divisor"
        self.adcOutFreqDiv.setToolTip("Divisor for the ADC output frequency going to the panel. Only available from FW version 105.")
        self.gui.show_error("Control & Timing / ADC output frequency divisor is not yet connected to an action")

        g = QVGroupBox()
        l.addWidget(g)

        self.sataPllLocked = QtWidgets.QCheckBox("SATA frequency valid")
        readOnly(self.sataPllLocked)
        self.sataPllLocked.setToolTip("Indicator for the serial (SATA) PLL being in lock")
        g.addWidget(self.sataPllLocked)

        self.basicPllLocked = QtWidgets.QCheckBox("Internal ADC frequency valid")
        readOnly(self.basicPllLocked)
        self.basicPllLocked.setToolTip("Indicator for the basic (ADC) PLL being in lock")
        g.addWidget(self.basicPllLocked)
        
        
        self.extDcmLocked = QtWidgets.QCheckBox("External ADC frequency valid")
        readOnly(self.extDcmLocked)
        self.extDcmLocked.setToolTip("Indicator for the external clock module (DCM) PLL being in lock")
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

        triggerFunc = self.gui.call(lambda: self.gui.camera.setTrigger(self.trigPlus.isChecked(),self.trigMinus.isChecked(),self.internalTrig.isChecked(),self.triggerDelay.value(),self.disableWhenStreamOff.isChecked()))

        self.trigPlus.stateChanged.connect(triggerFunc)
        self.trigMinus.stateChanged.connect(triggerFunc)
        self.internalTrig.stateChanged.connect(triggerFunc)
        self.disableWhenStreamOff.stateChanged.connect(triggerFunc)
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

    def loadSettingsFromCamera(self):

        # Set the base (adc) pll mult/div values, and frequency
        mult = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_BASE_PLL_MULT]
        div = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_BASE_PLL_DIV_ADC]
        self.adcPllMult.setValue(mult)
        self.adcPllDiv.setValue(div)
        setFreqCombo(self.adcPllMult,self.adcPllDiv,self.adcPllFreq)

        # Set the external clock PLL mult/div values
        mult = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_EXT_DCM_MULT]
        div = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_EXT_DCM_DIV]
        self.extClockMult.setValue(mult)
        self.extClockDiv.setValue(div)
        
        # sample dividier value
        div = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV:self.gui.camera.codes_CC.CC_REGISTER_SAMPLEDIV+2]
        div = int.from_bytes(div,'big')
        self.sampleDiv.setValue(div)

        # Clock source
        clock_control = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_CLOCK_CONTROL]
        sourceExternal = clock_control & (1<<2)
        autoExternal = clock_control & (1<<3)
        externalSample = clock_control & (1<<4)
        self.adcClockExt.setChecked(sourceExternal)
        self.autoExtClock.setChecked(autoExternal)
        self.extSample.setChecked(externalSample)

        # Trigger settings
        reg = self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_TRIGSTATE]
        self.trigPlus.setChecked(reg & (1<<0))
        self.trigMinus.setChecked(reg & (1<<1))
        self.internalTrig.setChecked(reg & (1<<2))
        self.disableWhenStreamOff.setChecked(reg & (1<<6))
        td = int.from_bytes(self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_TRIGDELAY:self.gui.camera.codes_CC.CC_REGISTER_TRIGDELAY+4],'big',signed=False)
        self.triggerDelay.setValue(td)

