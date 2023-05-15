import sys

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

        self.gui = parent.gui
        super(Adc,self).__init__(parent)
        self.number = number

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topRow = QtWidgets.QHBoxLayout()
        layout.addLayout(topRow)

        g = QGridGroupBox()
        topRow.addWidget(g)
        g.addWidget(QtWidgets.QLabel("DVDD:"),1,0)
        self.dvdd = QtWidgets.QLineEdit()
        self.dvdd.setEnabled(False)
        g.addWidget(self.dvdd,1,1)
        
        g.addWidget(QtWidgets.QLabel("AVDD:"),2,0)
        self.avdd = QtWidgets.QLineEdit()
        self.avdd.setEnabled(False)
        g.addWidget(self.avdd,2,1)

        g.addWidget(QtWidgets.QLabel("1.8 V:"),3,0)
        self.v18 = QtWidgets.QLineEdit()
        self.v18.setEnabled(False)
        g.addWidget(self.v18,3,1)

        g.addWidget(QtWidgets.QLabel("2.5 V:"),4,0)
        self.v25 = QtWidgets.QLineEdit()
        self.v25.setEnabled(False)
        g.addWidget(self.v25,4,1)

        g.addWidget(QtWidgets.QLabel("Temp:"),5,0)
        self.temperature = QtWidgets.QLineEdit()
        self.temperature.setEnabled(False)
        g.addWidget(self.temperature,5,1)

        g.setRowStretch(g.rowCount(),1)

        l = QtWidgets.QVBoxLayout()
        topRow.addLayout(l)
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
                chk.stateChanged.connect(self.gui.call(lambda channel=(self.number-1)*32+channel,chk=chk: \
                                                              self.gui.camera.setAdcChannelEnable(channel,chk.isChecked()), \
                                                       name = "APDCAM10G_control.setAdcChannelEnable(" + str(self.number) + "," + str(channel) + ",state)"
                                                       ))
                self.channelOn[row*cols+col] = chk
                l.addWidget(chk,row,col)
        l.setRowStretch(l.rowCount(),1)
        h = QtWidgets.QHBoxLayout()
        channelStatusGroup.addLayout(h)
        self.allChannelsOnButton = QtWidgets.QPushButton("All channels on")
        self.allChannelsOnButton.clicked.connect(self.allChannelsOn)
        h.addWidget(self.allChannelsOnButton)
        self.allChannelsOffButton = QtWidgets.QPushButton("All channels off")
        self.allChannelsOffButton.clicked.connect(self.allChannelsOff)
        h.addWidget(self.allChannelsOffButton)
        

        g = QGridGroupBox(self)
        topRow.addWidget(g)
        self.sataOn = QtWidgets.QCheckBox()
        self.sataOn.setText("SATA On")
        self.sataOn.guiMode = GuiMode.factory
        g.addWidget(self.sataOn,0,0)
        self.dualSata = QtWidgets.QCheckBox()
        self.dualSata.setText("Dual SATA")
        self.dualSata.guiMode = GuiMode.factory
        g.addWidget(self.dualSata,1,0)
        self.sataSync = QtWidgets.QCheckBox()
        self.sataSync.setText("SATA Sync")
        g.addWidget(self.sataSync,2,0)
        self.test = QtWidgets.QCheckBox()
        self.test.setText("Test")
        g.addWidget(self.test,3,0)
        self.filter = QtWidgets.QCheckBox()
        self.filter.setText("Filter")
        g.addWidget(self.filter,0,1)
        self.internalTrigger = QtWidgets.QCheckBox("Internal trigger")
        g.addWidget(self.internalTrigger,1,1)
        self.reverseBitOrder = QtWidgets.QCheckBox("Rev. bitord.")
        self.reverseBitOrder.guiMode = GuiMode.factory
        g.addWidget(self.reverseBitOrder,2,1)
        g.setRowStretch(g.rowCount(),10)

        g = QGridGroupBox(self)
        topRow.addWidget(g)
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
        topRow.addWidget(g)
        self.firCoeff = [0,0,0,0,0]
        for i in range(5):
            g.addWidget(QtWidgets.QLabel("Coeff" + str(i+1)),i,0)
            self.firCoeff[i] = QtWidgets.QSpinBox()
            self.firCoeff[i].setMinimum(0)
            self.firCoeff[i].setMaximum(65535)
            g.addWidget(self.firCoeff[i],i,1)
        g.setRowStretch(g.rowCount(),1)

        b = QtWidgets.QVBoxLayout()
        topRow.addLayout(b)
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

        g = QVGroupBox("Internal trigger")
        layout.addWidget(g)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        triggerLevelAllButton = QtWidgets.QPushButton("Set all trigger levels")
        triggerLevelAllButton.clicked.connect(lambda: self.allTriggerLevels(self.triggerLevelAll.value()))
        h.addWidget(triggerLevelAllButton)
        self.triggerLevelAll = QtWidgets.QSpinBox()
        self.triggerLevelAll.setMinimum(0)
        self.triggerLevelAll.setMaximum(65535)
        h.addWidget(self.triggerLevelAll)
        h.addStretch(1)

#        h = QtWidgets.QHBoxLayout()
#        g.addLayout(h)
        b = QtWidgets.QPushButton("All triggers enabled")
        b.clicked.connect(self.allInternalTriggersEnabled)
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers disabled")
        b.clicked.connect(self.allInternalTriggersDisabled)
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers positive")
        b.clicked.connect(self.allInternalTriggersPositive)
        h.addWidget(b)
        b = QtWidgets.QPushButton("All triggers negative.")
        b.clicked.connect(self.allInternalTriggersNegative)
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
                self.internalTriggerEnabled[row*cols+col] = en
                h1.addWidget(en)

                polarity = QtWidgets.QCheckBox("+")
                polarity.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                polarity.setContentsMargins(0,0,0,0)
                h1.addWidget(polarity)
                self.internalTriggerPositive[row*cols+col] = polarity

                level = QtWidgets.QSpinBox()
                level.setMinimum(0)
                level.setMaximum(65535)
                level.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                level.setContentsMargins(0,0,0,0)
                h1.addWidget(level)
                self.internalTriggerLevel[row*cols+col] = level

                func = self.gui.call(lambda channel=(self.number-1)*32+channel,en=en,polarity=polarity,level=level : \
                                                      self.gui.camera.setInternalTrigger(channel,\
                                                                                         en.isChecked(),\
                                                                                         level.value(), \
                                                                                         self.codes_ADC.INT_TRIG_POSITIVE if polarity.isChecked() else self.codes_ADC.INT_TRIG_NEGATIVE))
                en.stateChanged.connect(func) # enabled changes
                polarity.stateChanged.connect(func)  # polarity changes
                level.valueChanged.connect(func)



        g = QVGroupBox("DAC")
        layout.addWidget(g)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.setSpacing(0)
        self.dac = [None]*32
        for i in range(32):
            self.dac[i] = QIntEdit(0,65535)
            self.dac[i].setMaximumWidth(54)
            h.addWidget(self.dac[i])
        h.addStretch(1)

        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        self.setAllDacButton = QtWidgets.QPushButton("Set all values")
        h.addWidget(self.setAllDacButton)
        self.allDacValues = QtWidgets.QSpinBox()
        self.allDacValues.setMinimum(0)
        self.allDacValues.setMaximum(65535)
        h.addWidget(self.allDacValues)
        h.addStretch(1)

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
                
