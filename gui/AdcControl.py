import sys
from functools import partial

import importlib
from QtVersion import *
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox, QScrollArea
# from PyQt6.QtCore import Qt,QLocale
# from PyQt6.QtGui import QDoubleValidator
from ApdcamUtils import *
from GuiMode import *

class Adc(QtWidgets.QWidget):
    def updateFromCamera():
        (error,dvdd33,dvdd25,avdd33,avdd18) = self.gui.camera.getAdcPowerVoltages(self.number)
        self.dvdd33.setText(str(dvdd33))
        self.dvdd25.setText(str(dvdd25))
        self.avdd33.setText(str(avdd33))
        self.avdd18.setText(str(avdd18))

        (error,pllLocked) = self.gui.camera.getAdcPllLocked(self.number)
        self.pllLocked.setChecked(pllLocked)

        (error,T) = self.gui.camera.getAdcTemperature(self.number)
        self.temperature.setText(str(T))

        (error,overload) = self.gui.camera.getAdcOverload(self.number)
        self.overload.setChecked(overload)

    def name(self):
        return "ADC " + str(self.number)

    def channelOnOff(self,i,state):
        if i > 32 or i <= 0:
            return "Channel index " + str(i) + " out of range"
        self.channelOn[i-1].setChecked(state)

    def allChannelsOn(self):
        for i in range(32):
            self.channelOnOff(i+1,True)

    def allChannelsOff(self):
        for i in range(32):
            self.channelOnOff(i+1,False)

    def internalTriggerEnable(self,i,state):
        if i > 32 or i <= 0:
            return "Channel index " + str(i) + " out of range"
        self.internalTriggerEnabled[i-1].setChecked(state)

    def allInternalTriggersEnabled(self):
        for i in range(32):
            self.internalTriggerEnable(i+1,True)

    def allInternalTriggersDisabled(self):
        for i in range(32):
            self.internalTriggerEnable(i+1,False)

    def setInternalTriggerPositive(self,i,state):
        if i > 32 or i <= 0:
            return "Channel index " + str(i) + " out of range"
        self.internalTriggerPositive[i-1].setChecked(state)
        
    def allInternalTriggersPositive(self):
        for i in range(32):
            self.setInternalTriggerPositive(i+1,True)

    def allInternalTriggersNegative(self):
        for i in range(32):
            self.setInternalTriggerPositive(i+1,False)

    def allTriggerLevels(self,value):
        for i in range(32):
            self.internalTriggerLevel[i].setValue(value)

    def setFilterCoeffs(self):
        values = [65535]*8
        for i in range(5):
            values[i] = self.firCoeff[i].value()
        values[5] = self.iirCoeff.value()
        values[6] = 0 # reserved for later use, not used now
        values[7] = self.internalFilterDiv.value()
        self.gui.camera.setFilterCoeffs(self.number,values)

    def __init__(self,parent,number):
        """
        Constructor

        Parameters
        ^^^^^^^^^^
        parent: widget
            The parent widget
        number: int
            ADC board number (1..4)
        """

        self.adcControl = parent
        self.gui = parent.gui
        super(Adc,self).__init__(parent)
        self.number = number

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topRow = QtWidgets.QHBoxLayout()
        layout.addLayout(topRow)

        g = QGridGroupBox()
        topRow.addWidget(g)
        g.addWidget(QtWidgets.QLabel("DVDD33:"),1,0)
        self.dvdd33 = QtWidgets.QLineEdit()
        self.dvdd33.setEnabled(False)
        g.addWidget(self.dvdd33,1,1)
        
        g.addWidget(QtWidgets.QLabel("AVDD33:"),2,0)
        self.avdd33 = QtWidgets.QLineEdit()
        self.avdd33.setEnabled(False)
        g.addWidget(self.avdd33,2,1)

        g.addWidget(QtWidgets.QLabel("DVDD 2.5 V:"),4,0)
        self.dvdd25 = QtWidgets.QLineEdit()
        self.dvdd25.setEnabled(False)
        g.addWidget(self.dvdd25,4,1)

        g.addWidget(QtWidgets.QLabel("AVDD 1.8 V:"),3,0)
        self.avdd18 = QtWidgets.QLineEdit()
        self.avdd18.setEnabled(False)
        g.addWidget(self.avdd18,3,1)


        g.addWidget(QtWidgets.QLabel("Temp:"),5,0)
        self.temperature = QtWidgets.QLineEdit()
        self.temperature.setEnabled(False)
        self.temperature.setToolTip("ADC board temperature")
        g.addWidget(self.temperature,5,1)

        g.setRowStretch(g.rowCount(),1)

        l = QtWidgets.QVBoxLayout()
        topRow.addLayout(l)
        g = QVGroupBox(self)
        l.addWidget(g)
        self.pllLocked = QtWidgets.QCheckBox("PLL Locked")
        self.pllLocked.setEnabled(False)
        self.pllLocked.setToolTip("Indicate whether the PLL of the ADC board is locked")
        g.addWidget(self.pllLocked)
        self.internalTriggerDisplay = QtWidgets.QCheckBox("Internal trigger")
        self.internalTriggerDisplay.setEnabled(False)
        self.internalTriggerDisplay.setToolTip("Indicating whether the board is using an internal trigger")
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


        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Error:"))
        self.error = QtWidgets.QLineEdit()
        self.error.setReadOnly(True)
        h.addWidget(self.error)
        l.addStretch(1)

        channelStatusGroup = QVGroupBox("Channels on/off")
        topRow.addWidget(channelStatusGroup)
        self.channelOn = [None]*32
        l = QtWidgets.QGridLayout()
        l.setContentsMargins(10,0,0,0)
        l.setSpacing(15)
        channelStatusGroup.addLayout(l)
        l.setVerticalSpacing(10)
        cols = 8
        rows = 4
        for col in range(cols):
            l.setColumnMinimumWidth(col,1)
            for row in range(rows):
                l.setRowMinimumHeight(row,1)
                channel = row*cols+col+1
                chk = QtWidgets.QCheckBox(str(channel))
                chk.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                chk.setContentsMargins(0,0,0,0)
                chk.stateChanged.connect(self.gui.call(partial(lambda channel,checkbox: self.gui.camera.setAdcChannelEnable(channel,checkbox.isChecked()),\
                                                               (self.number-1)*32+channel,\
                                                               chk), \
                                                       name = "APDCAM10G_control.setAdcChannelEnable(" + str(self.number) + "," + str(channel) + ",state)"
                                                       ))
                chk.setToolTip("Enable/disable a given channel")
                self.channelOn[row*cols+col] = chk
                l.addWidget(chk,row,col)
        l.setRowStretch(l.rowCount(),1)
        h = QtWidgets.QHBoxLayout()
        channelStatusGroup.addLayout(h)
        self.allChannelsOnButton = QtWidgets.QPushButton("All channels on")
        self.allChannelsOnButton.setToolTip("Enable all channels of this ADC board")
        self.allChannelsOnButton.clicked.connect(self.allChannelsOn)
        h.addWidget(self.allChannelsOnButton)
        self.allChannelsOffButton = QtWidgets.QPushButton("All channels off")
        self.allChannelsOffButton.setToolTip("Disable all channels of this ADC board")
        self.allChannelsOffButton.clicked.connect(self.allChannelsOff)
        h.addWidget(self.allChannelsOffButton)
        

        g = QGridGroupBox(self)
        topRow.addWidget(g)
        self.sataOn = QtWidgets.QCheckBox("SATA On")
        self.sataOn.setToolTip("Switch on SATA (must be done for ALL ADCs!)")
        self.sataOn.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setSataOn(self.number,self.sataOn.isChecked())))
        self.sataOn.guiMode = GuiMode.factory
        g.addWidget(self.sataOn,0,0)

        self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        self.dualSata.setToolTip("Switch dual SATA mode on (must be done for ALL ADCs!)")
        self.dualSata.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setDualSata(self.number,self.dualSata.isChecked())))
        self.dualSata.guiMode = GuiMode.factory
        g.addWidget(self.dualSata,1,0)
        
        self.sataSync = QtWidgets.QCheckBox("SATA Sync")
        self.sataSync.setToolTip("Switch SATA sync for this ADC")
        self.sataSync.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setSataSync(self.number,self.sataSync.isChecked())))
        g.addWidget(self.sataSync,2,0)

        self.test = QtWidgets.QCheckBox("Test")
        self.test.setToolTip("Switch Test mode on (?)")
        self.test.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setTestPatternMode(self.number,self.test.isChecked())))
        g.addWidget(self.test,3,0)

        self.internalTrigger = QtWidgets.QCheckBox("Internal trigger")
        g.addWidget(self.internalTrigger,4,0)

        self.reverseBitOrder = QtWidgets.QCheckBox("Rev. bitord.")
        self.reverseBitOrder.setToolTip("Set reverse bit order in the stream. If checked, least significant bit comes first.")
        self.reverseBitOrder.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setReverseBitord(self.number,self.reverseBitOrder.isChecked())))
        self.reverseBitOrder.guiMode = GuiMode.factory
        g.addWidget(self.reverseBitOrder,5,0)
        g.setRowStretch(g.rowCount(),10)

        g = QGridGroupBox(self)
        topRow.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Bits:"),0,0)
        self.bits = QtWidgets.QLineEdit()
        g.addWidget(self.bits,0,1)
        g.addWidget(QtWidgets.QLabel("Ring buffer:"),1,0)
        self.ringBuffer = QtWidgets.QSpinBox()
        self.ringBuffer.setMinimum(0)
        self.ringBuffer.setMaximum(1023)
        self.ringBuffer.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.ringBuffer.setToolTip("Ring buffer size. Ring buffer is disabled if zero. Takes effect when you press Enter")
        self.ringBuffer.lineEdit().returnPressed.connect(self.gui.call(lambda: self.gui.camera.setRingBufferSize(self.number,self.ringBuffer.value()),name="setRingBufferSize",where=__file__))
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
        g.setTitle("Filter")
        topRow.addWidget(g)
        self.firCoeff = [0,0,0,0,0]
        for i in range(5):
            g.addWidget(QtWidgets.QLabel("FIR" + str(i+1)),i,0)
            self.firCoeff[i] = QtWidgets.QSpinBox()
            self.firCoeff[i].setMinimum(0)
            self.firCoeff[i].setMaximum(65535)
            self.firCoeff[i].setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.firCoeff[i].setToolTip("Coefficient " + str(i+1) + " of the FIR filter. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
            self.firCoeff[i].lineEdit().returnPressed.connect(self.gui.call(self.setFilterCoeffs))
            #self.firCoeff[i].valueChanged.connect(self.gui.call(self.setFilterCoeffs))
            g.addWidget(self.firCoeff[i],i,1)

        g.addWidget(QtWidgets.QLabel("IIR:"),0,2)
        self.iirCoeff = QtWidgets.QSpinBox()
        self.iirCoeff.setMinimum(0)
        self.iirCoeff.setMaximum(4095)
        self.iirCoeff.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.iirCoeff.setToolTip("Coefficient of the IIR (infinite impulse response/recursive) filter. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
        self.iirCoeff.lineEdit().returnPressed.connect(self.gui.call(self.setFilterCoeffs))
        g.addWidget(self.iirCoeff,0,3)

        g.addWidget(QtWidgets.QLabel("Div.:"),1,2)
        self.internalFilterDiv = QtWidgets.QSpinBox()
        self.internalFilterDiv.setMinimum(0)
        self.internalFilterDiv.setMaximum(14)
        self.internalFilterDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.internalFilterDiv.lineEdit().returnPressed.connect(self.gui.call(self.setFilterCoeffs))
        self.internalFilterDiv.setToolTip("Defines the factor to divide the filter output, as 2 to the power specified here. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
        g.addWidget(self.internalFilterDiv,1,3)

        g.addWidget(QtWidgets.QLabel("FIR Freq. [MHz]:"),2,2)
        self.firFrequency = QDoubleEdit()
        g.addWidget(self.firFrequency,2,3)
        g.addWidget(QtWidgets.QLabel("Rec. Freq. [MHz]:"),3,2)
        self.recFrequency = QDoubleEdit()
        g.addWidget(self.recFrequency,3,3)

        self.filter = QtWidgets.QCheckBox("Enable")
        self.filter.setToolTip("Enable the filter (takes immediate effect)")
        self.filter.stateChanged.connect(self.gui.call(lambda state: self.gui.camera.setFilterOn(self.number,state>0),name="APDCAM10G_control.filterOnOff",where=__file__))
        g.addWidget(self.filter,4,2,1,2)
        
        g.setRowStretch(g.rowCount(),1)

        g = QVGroupBox("Internal trigger")
        layout.addWidget(g)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        triggerLevelAllButton = QtWidgets.QPushButton("Set all trigger levels")
        triggerLevelAllButton.clicked.connect(lambda: self.allTriggerLevels(self.triggerLevelAll.value()))
        triggerLevelAllButton.setToolTip("Set all trigger levels to the specified value (takes immediate effect)")
        h.addWidget(triggerLevelAllButton)
        self.triggerLevelAll = QtWidgets.QSpinBox()
        self.triggerLevelAll.setMinimum(0)
        self.triggerLevelAll.setMaximum(65535)
        self.triggerLevelAll.setToolTip("Specify here the trigger level for all channels. Takes effect only when pushing the button")
        h.addWidget(self.triggerLevelAll)
        h.addStretch(1)

#        h = QtWidgets.QHBoxLayout()
#        g.addLayout(h)
        b = QtWidgets.QPushButton("All triggers enabled")
        b.clicked.connect(self.allInternalTriggersEnabled)
        b.setToolTip("Enable all triggers (takes immediate effect)")
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers disabled")
        b.clicked.connect(self.allInternalTriggersDisabled)
        b.setToolTip("Disable all triggers (takes immediate effect)")
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers positive")
        b.clicked.connect(self.allInternalTriggersPositive)
        b.setToolTip("Set all triggers positive (takes immediate effect)")
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers negative.")
        b.clicked.connect(self.allInternalTriggersNegative)
        b.setToolTip("Set all triggers negative (takes immediate effect)")
        h.addWidget(b)
        h.addStretch(10)

        grid = QtWidgets.QGridLayout()
        g.addLayout(grid)
        self.internalTriggerEnabled = [None]*32
        self.internalTriggerLevel = [None]*32
        self.internalTriggerPositive = [None]*32
        cols = 8
        rows = 4
        for col in range(cols):
            grid.setColumnMinimumWidth(col,1)
            for row in range(rows):
                grid.setRowMinimumHeight(row,1)
                c = QVGroupBox()
                c.setStyleSheet("padding-top:-5px; padding-bottom:-5px;")
                grid.addWidget(c,row,col)
                h1 = QtWidgets.QHBoxLayout()
                channel = row*cols+col+1
                label = QtWidgets.QLabel("<b>" + str(channel) + "</b>")
                label.setStyleSheet("background-color: rgba(0,0,0,0.2); padding-left:5px; padding-right:5px; padding-top:-1px; padding-bottom:-1px; margin:0px;")
                label.setAlignment(AlignCenter)
                h1.addWidget(label)
                c.addLayout(h1)
                en = QtWidgets.QCheckBox("En.")
                en.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                en.setContentsMargins(0,0,0,0)
                en.setToolTip("Enable channel " + str(channel) + " (takes immediate effect)")
                self.internalTriggerEnabled[row*cols+col] = en
                h1.addWidget(en)

                polarity = QtWidgets.QCheckBox("+")
                polarity.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                polarity.setContentsMargins(0,0,0,0)
                polarity.setToolTip("Set polarity to positive (takes immediate effect)")
                h1.addWidget(polarity)
                self.internalTriggerPositive[row*cols+col] = polarity

                level = QtWidgets.QSpinBox()
                level.setMinimum(0)
                level.setMaximum(65535)
                level.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                level.setContentsMargins(0,0,0,0)
                level.setToolTip("Specify the trigger level (takes immediate effect)")
                h1.addWidget(level)
                self.internalTriggerLevel[row*cols+col] = level

                func = self.gui.call(partial(lambda channel,en,polarity,level : self.gui.camera.setInternalTrigger(channel,\
                                                                                                                   en.isChecked(),\
                                                                                                                   level.value(), \
                                                                                                                   self.gui.camera.codes_ADC.INT_TRIG_POSITIVE if polarity.isChecked() else self.codes_ADC.INT_TRIG_NEGATIVE),
                                             (self.number-1)*32+channel,en,polarity,level))
                en.stateChanged.connect(func) # enabled changes
                polarity.stateChanged.connect(func)  # polarity changes
                level.valueChanged.connect(func)


        g = QVGroupBox("Channel offsets (DAC)")
        layout.addWidget(g)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.setSpacing(0)
        self.dac = [None]*32
        for i in range(32):
            #self.dac[i] = QIntEdit(0,65535)
            self.dac[i] = QtWidgets.QSpinBox()
            self.dac[i].setMinimum(0)
            self.dac[i].setMaximum(65535)
            self.dac[i].setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.dac[i].setMaximumWidth(54)
            f = partial(lambda ch: self.gui.camera.setOffset(self.number,ch,self.dac[ch-1].value()),i+1)
            self.dac[i].lineEdit().returnPressed.connect(self.gui.call(f,name="APDCAM10G_control.setOffset(" + str(self.number) + "," + str(i+1) + ",value)",where=__file__))
            self.dac[i].setToolTip("Specify the value (0..65535) for the DAC for the given channel, which defines the ADC offset. Changes take effect when you hit Enter")
            h.addWidget(self.dac[i])
        h.addStretch(1)

        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)


        self.allDacValues = QtWidgets.QSpinBox()
        self.allDacValues.setMinimum(0)
        self.allDacValues.setMaximum(65535)
        self.allDacValues.setToolTip("The value to be set for all channels of this board, or all channels of all boards, when pushing the appropriate button")
        h.addWidget(self.allDacValues)

        setBoardDacButton = QtWidgets.QPushButton("Set all board channels")
        def setBoardDac():
            value = self.allDacValues.value()
            self.gui.call(lambda: self.gui.camera.setOffsets(self.number,[value]*32))()
            for ch in range(32):
                self.dac[ch].setValue(value)
        setBoardDacButton.clicked.connect(setBoardDac)
        setBoardDacButton.setToolTip("Set the DAC values of all channels of this board to the value specified on the left")
        h.addWidget(setBoardDacButton)

        setAllDacButton = QtWidgets.QPushButton("Set all channels")
        def setAllDac():
            value = self.allDacValues.value()
            # loop over all ADC boards of the parent tab
            for board in range(len(self.adcControl.adc)):
                self.gui.call(lambda: self.gui.camera.setOffsets(self.adcControl.adc[board].number,[value]*32))()
                # set the "All DAC values" user input in all ADC tabs
                self.adcControl.adc[board].allDacValues.setValue(value)
                # loop over the 32 channels of the GUI and change the values
                for ch in range(32):
                    self.adcControl.adc[board].dac[ch].setValue(value) 
        setAllDacButton.clicked.connect(setAllDac)
        setAllDacButton.setToolTip("Set the DAC values of all channels of all boards to the value specified on the left")
        h.addWidget(setAllDacButton)

        h.addStretch(10)

class AdcControl(QtWidgets.QWidget):
    def __init__(self,parent):
        self.gui = parent
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
        self.factoryResetButton.guiMode = GuiMode.factory
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
                
