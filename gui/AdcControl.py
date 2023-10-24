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
    def updateGui(self):
        a = self.gui.camera.codes_ADC
        r = self.gui.camera.status.ADC_registers[self.number-1]
        # (error,dvdd33,dvdd25,avdd33,avdd18) = self.gui.camera.getAdcPowerVoltages(self.number)
        # self.dvdd33.setText("{:.3f}".format(dvdd33/1000.0))
        # self.dvdd25.setText("{:.3f}".format(dvdd25/1000.0))
        # self.avdd33.setText("{:.3f}".format(avdd33/1000.0))
        # self.avdd18.setText("{:.3f}".format(avdd18/1000.0))
        self.dvdd33.setText("{:.3f}".format(int.from_bytes(r[a.ADC_REG_DVDD33:a.ADC_REG_DVDD33+2],'little')/1000.0))
        self.dvdd25.setText("{:.3f}".format(int.from_bytes(r[a.ADC_REG_DVDD25:a.ADC_REG_DVDD25+2],'little')/1000.0))
        self.avdd33.setText("{:.3f}".format(int.from_bytes(r[a.ADC_REG_AVDD33:a.ADC_REG_AVDD33+2],'little')/1000.0))
        self.avdd18.setText("{:.3f}".format(int.from_bytes(r[a.ADC_REG_AVDD18:a.ADC_REG_AVDD18+2],'little')/1000.0))

        # (error,T) = self.gui.camera.getAdcTemperature(self.number)
        # self.temperature.setText("{:.1f}".format(T))
        self.temperature.setText("{:.1f}".format(r[a.ADC_REG_TEMP]))

        # (error,pllLocked) = self.gui.camera.getAdcPllLocked(self.number)
        # self.pllLocked.setChecked(pllLocked)
        self.pllLocked.setChecked(r[a.ADC_REG_STATUS1]&1)

        # (error,overload) = self.gui.camera.getAdcOverload(self.number)
        # self.overload.setChecked(overload)
        self.overload.setChecked(r[a.ADC_REG_OVDSTATUS]&1)
#        print("we should clear the latched bit")
#        self.gui.show_warning("We should clear the latched overload bit")

        #error,status2 = self.gui.camera.getAdcRegister(self.number,self.gui.camera.codes_ADC.ADC_REG_STATUS2)
        status2 = r[a.ADC_REG_STATUS2]
        self.led1.setChecked((status2>>2)&1) 
        self.led2.setChecked((status2>>3)&1)
        self.internalTriggerDisplay.setChecked((status2>>0)&1)

        
    def name(self):
        return "ADC " + str(self.number) + " (@" + str(self.address) + ")"

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

    def setTestPattern(self):
        values = self.testPattern.text().split()
        if len(values) == 1:
            error = self.gui.camera.setTestPattern(adcBoardNo=self.number,value=values[0])
        else:
            if len(values) != 4:
                self.gui.show_error("Test pattern must be a single or four integers")
                return
            error = self.gui.camera.setTestPattern(adcBoardNo=self.number,value=values)
        return error

    def calculateFilterCoeffs(self,f_fir,f_recurs):
        print("This function should be crosschecked")
        sys.exit(1);
        f_adc = 10e6
        gain = 1
        Nyquist_freq = f_adc/2
        tau = f_adc/f_recurs/2/math.pi
        c = math.exp(-1./double(tau))
        c = long(c*4096)
        order = 5
        r = digital_filter(0,f_fir/(f_adc/2)<1,50,order)
        s1 = [0]*(order*10)
        s1[2*order]=1000
        s2=convol(s1,r)
        coeff1 = s2[2*order:3*order-1]
        coeff=fix(coeff1/total(coeff1)*(4096-c)/16)*2^gain
        filt = [0]*8
        for i in range(5):
            filt[i] = coeff[i]
        filt[5] = c
        filt[7] = 8+gain

    def set_test_pattern_mode(self):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            print('Shift+Click')
        else:
            print("no shift")

    def __init__(self,parent,number,address):
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
        self.address = address

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topRow = QtWidgets.QHBoxLayout()
        layout.addLayout(topRow)

        g = QGridGroupBox()
        topRow.addWidget(g)
        g.addWidget(QtWidgets.QLabel("DVDD33:"),1,0)
        self.dvdd33 = QtWidgets.QLineEdit()
        readOnly(self.dvdd33)
        self.dvdd33.setToolTip("DVDD 3.3 V")
        g.addWidget(self.dvdd33,1,1)
        
        g.addWidget(QtWidgets.QLabel("AVDD33:"),2,0)
        self.avdd33 = QtWidgets.QLineEdit()
        readOnly(self.avdd33)
        self.avdd33.setToolTip("AVDD 3.3 V")
        g.addWidget(self.avdd33,2,1)

        g.addWidget(QtWidgets.QLabel("DVDD 2.5 V:"),4,0)
        self.dvdd25 = QtWidgets.QLineEdit()
        readOnly(self.dvdd25)
        self.dvdd25.setToolTip("DVDD 2.5 V")
        g.addWidget(self.dvdd25,4,1)

        g.addWidget(QtWidgets.QLabel("AVDD 1.8 V:"),3,0)
        self.avdd18 = QtWidgets.QLineEdit()
        readOnly(self.avdd18)
        self.avdd18.setToolTip("AVDD 1.8 V")
        g.addWidget(self.avdd18,3,1)


        g.addWidget(QtWidgets.QLabel("Temp:"),5,0)
        self.temperature = QtWidgets.QLineEdit()
        readOnly(self.temperature)
        self.temperature.setToolTip("ADC board temperature")
        g.addWidget(self.temperature,5,1)

        g.setRowStretch(g.rowCount(),1)

        l = QtWidgets.QVBoxLayout()
        topRow.addLayout(l)
        g = QVGroupBox(self)
        l.addWidget(g)
        self.pllLocked = QtWidgets.QCheckBox("PLL Locked")
        readOnly(self.pllLocked)
        self.pllLocked.setToolTip("Indicate whether the PLL of the ADC board is locked")
        g.addWidget(self.pllLocked)
        self.internalTriggerDisplay = QtWidgets.QCheckBox("Internal trigger")
        self.internalTriggerDisplay.setToolTip("???")
        readOnly(self.internalTriggerDisplay)
        g.addWidget(self.internalTriggerDisplay)
        self.overload = QtWidgets.QCheckBox("Overload")
        self.overload.setToolTip("Indicating whether any of the channels of this ADC have gone to overload since the last status update")
        readOnly(self.overload)
        g.addWidget(self.overload)
        self.led1 = QtWidgets.QCheckBox("SATA1 data out")
        self.led1.setToolTip("Indicator for data output through SATA1")
        readOnly(self.led1)
        g.addWidget(self.led1)
        self.led2 = QtWidgets.QCheckBox("SATA2 data out")
        self.led2.setToolTip("Indicator for data output through SATA2")
        readOnly(self.led2)
        g.addWidget(self.led2)


        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("Error:"))
        self.error = QtWidgets.QLineEdit()
        readOnly(self.error)
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
                chk.settingsName = "Channel " + str(channel) + " on"
                chk.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                chk.setContentsMargins(0,0,0,0)
                # chk.stateChanged.connect(self.gui.call(partial(lambda channel,checkbox: self.gui.camera.setAdcChannelEnable(channel,checkbox.isChecked()),\
                #                                                (self.number-1)*32+channel,\
                #                                                chk), \
                #                                        name = "APDCAM10G.setAdcChannelEnable(" + str(self.number) + "," + str(channel) + ",state)"
                #                                        ))
                chk.stateChanged.connect(self.gui.call(partial(self.set_adc_channel_enable,channel=channel)))
                chk.setToolTip("Enable/disable a given channel")
                chk.channelNumber = channel
                self.channelOn[channel-1] = chk
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

        # this is removed here, one can not set it on a per-ADC basis (it would break the system). The tab "Control & Timing"
        # has a global switch, which sets this flag in the CC board and all ADC boards as well.
        # self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        # self.dualSata.setToolTip("Switch dual SATA mode on (must be done for ALL ADCs!)")
        # self.dualSata.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setAdcDualSata(self.number,self.dualSata.isChecked())))
        # self.dualSata.guiMode = GuiMode.factory
        # g.addWidget(self.dualSata,1,0)
        
        self.sataSync = QtWidgets.QCheckBox("SATA Sync")
        self.sataSync.settingsName = "SATA sync"
        self.sataSync.setToolTip("Switch SATA sync for this ADC")
        self.sataSync.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setSataSync(self.number,self.sataSync.isChecked())))
        g.addWidget(self.sataSync,2,0)

        self.test = QtWidgets.QCheckBox("Test")
        self.test.settingsName = "Test"
        self.test.setToolTip("Switch Test mode on (?)")
        self.test.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setTestPatternMode(self.number,self.test.isChecked())))
        g.addWidget(self.test,3,0)

        self.internalTrigger = QtWidgets.QCheckBox("Internal trigger")
        self.internalTrigger.settingsName = "Internal trigger"
        self.internalTrigger.setToolTip("Enable internal trigger output from this ADC board")
        #self.internalTrigger.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setInternalTriggerAdc(adcBoardNo=self.number,enable=self.internalTrigger.isChecked())))
        self.internalTrigger.clicked.connect(self.set_test_pattern_mode)
        g.addWidget(self.internalTrigger,4,0)

        self.reverseBitOrder = QtWidgets.QCheckBox("Rev. bitord.")
        self.reverseBitOrder.settingsName = "Reverse bit order"
        self.reverseBitOrder.setToolTip("Set reverse bit order in the stream. If checked, least significant bit comes first.")
        self.reverseBitOrder.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setReverseBitord(self.number,self.reverseBitOrder.isChecked())))
        self.reverseBitOrder.guiMode = GuiMode.factory
        g.addWidget(self.reverseBitOrder,5,0)
        g.setRowStretch(g.rowCount(),10)

        g = QGridGroupBox(self)
        topRow.addWidget(g)
        g.addWidget(QtWidgets.QLabel("Bits:"),0,0)
        self.bits = QtWidgets.QComboBox()
        self.bits.settingsName = "Bits"
        self.bits.setToolTip("Choose the resolution (number of bits) for the data")
        self.bits.addItem("14")
        self.bits.addItem("12")
        self.bits.addItem("8")
        self.bits.activated[str].connect(self.gui.call(self.set_adc_resolution))
        g.addWidget(self.bits,0,1)

        g.addWidget(QtWidgets.QLabel("Ring buffer:"),1,0)
        self.ringBuffer = QtWidgets.QSpinBox()
        self.ringBuffer.settingsName = "Ring buffer"
        self.ringBuffer.setMinimum(0)
        self.ringBuffer.setMaximum(1023)
        self.ringBuffer.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.ringBuffer.setToolTip("Ring buffer size. Ring buffer is disabled if zero. Takes effect when you press Enter")
        self.ringBuffer.editingFinished.connect(self.gui.call(lambda: self.gui.camera.setRingBufferSize(self.number,self.ringBuffer.value()),name="setRingBufferSize",where=__file__))
        g.addWidget(self.ringBuffer,1,1)

        # g.addWidget(QtWidgets.QLabel("SATA CLK Mult (REDUNDANT?):"),2,0)
        # self.sataClkMult = QtWidgets.QSpinBox()
        # g.addWidget(self.sataClkMult,2,1)
        # g.addWidget(QtWidgets.QLabel("SATA CLK Div (REDUNDANT?):"),3,0)
        # self.sataClkDiv = QtWidgets.QSpinBox()
        # g.addWidget(self.sataClkDiv,3,1)

        g.addWidget(QtWidgets.QLabel("Test pattern:"),4,0)
        self.testPattern = QtWidgets.QLineEdit()
        self.testPattern.settingsName = "Test pattern"
        #self.testPattern.returnPressed.connect(self.gui.call(self.setTestPattern))
        self.testPattern.editingFinished.connect(self.gui.call(self.setTestPattern))
        self.testPattern.setToolTip("Test pattern for this ADC. Either an integer (value for all four 8-channel blocks), or 4 integers (for the blocks separately)")
        g.addWidget(self.testPattern,4,1)
        g.setRowStretch(g.rowCount(),1)

        g.addWidget(QtWidgets.QLabel("Bytes/chip:"),5,0)
        self.bytes_per_chip = QtWidgets.QLineEdit()
        self.bytes_per_chip.setToolTip("Values of the BPSCH1..BPSCH4 registers of the ADC board indicating the number of bytes per sample for the 4 chips (i.e. 8-channel blocks) in the data stream")
        readOnly(self.bytes_per_chip)
        g.addWidget(self.bytes_per_chip,5,1)
        g.addWidget(QtWidgets.QLabel("Bytes/sample:"),6,0)
        self.bytes_per_sample = QtWidgets.QLineEdit()
        self.bytes_per_sample.setToolTip("Number of bytes per sample for this ADC board")
        readOnly(self.bytes_per_sample)
        g.addWidget(self.bytes_per_sample,6,1)

        g = QGridGroupBox(self)
        topRow.addWidget(g)
        self.firCoeff = [0,0,0,0,0]
        for i in range(5):
            g.addWidget(QtWidgets.QLabel("FIR" + str(i+1)),i,0)
            self.firCoeff[i] = QtWidgets.QSpinBox()
            self.firCoeff[i].settingsName = "FIR" + str(i+1)
            self.firCoeff[i].setMinimum(0)
            self.firCoeff[i].setMaximum(65535)
            self.firCoeff[i].setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.firCoeff[i].setToolTip("Coefficient " + str(i+1) + " of the FIR filter. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
            self.firCoeff[i].editingFinished.connect(self.gui.call(self.setFilterCoeffs))
            g.addWidget(self.firCoeff[i],i,1)

        g.addWidget(QtWidgets.QLabel("IIR:"),0,2)
        self.iirCoeff = QtWidgets.QSpinBox()
        self.iirCoeff.settingsName = "IIR"
        self.iirCoeff.setMinimum(0)
        self.iirCoeff.setMaximum(4095)
        self.iirCoeff.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.iirCoeff.setToolTip("Coefficient of the IIR (infinite impulse response/recursive) filter. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
        self.iirCoeff.editingFinished.connect(self.gui.call(self.setFilterCoeffs))
        g.addWidget(self.iirCoeff,0,3)

        g.addWidget(QtWidgets.QLabel("Div.:"),1,2)
        self.internalFilterDiv = QtWidgets.QSpinBox()
        self.internalFilterDiv.settingsName = "Internal filter divisor"
        self.internalFilterDiv.setMinimum(0)
        self.internalFilterDiv.setMaximum(14)
        self.internalFilterDiv.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.internalFilterDiv.editingFinished.connect(self.gui.call(self.setFilterCoeffs))
        self.internalFilterDiv.setToolTip("Defines the factor to divide the filter output, as 2 to the power specified here. Must press Enter to take effect (but then all filter coeffs are sent to the camera)!")
        g.addWidget(self.internalFilterDiv,1,3)


        g.addWidget(QtWidgets.QLabel("FIR Freq. [MHz]:"),2,2)
        #self.firFrequency = QDoubleEdit()
        self.firFrequency = QtWidgets.QDoubleSpinBox()
        self.firFrequency.settingsName = "FIR frequency"
        self.firFrequency.setMinimum(0)
        self.firFrequency.setMaximum(100)
        self.firFrequency.setSingleStep(0.1)
        self.firFrequency.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        g.addWidget(self.firFrequency,2,3)
        g.addWidget(QtWidgets.QLabel("Rec. Freq. [MHz]:"),3,2)
        #self.recFrequency = QDoubleEdit()
        self.recFrequency = QtWidgets.QDoubleSpinBox()
        self.recFrequency.settingsName = "Rec. frequency"
        self.recFrequency.setMinimum(0)
        self.recFrequency.setMaximum(100)
        self.recFrequency.setSingleStep(0.1)
        self.recFrequency.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        g.addWidget(self.recFrequency,3,3)

        self.filterEnable = QtWidgets.QCheckBox("Enable")
        self.filterEnable.settingsName = "Enable filter"
        self.filterEnable.setToolTip("Enable the filter (takes immediate effect)")
        self.filterEnable.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setFilterOn(self.number,self.filterEnable.isChecked()),name="APDCAM10G.filterOnOff",where=__file__))
        g.addWidget(self.filterEnable,4,2,1,2)
        
        g.setRowStretch(g.rowCount(),1)

        g = QVGroupBox("")
        layout.addWidget(g)
        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)

        title = QtWidgets.QLabel("Internal trigger")
        title.setStyleSheet("font-weight:bold")
        h.addWidget(title)
        h.addStretch(1)

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
                en.settingsName = "Internal trigger enabled " + str(channel)
                en.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                en.setContentsMargins(0,0,0,0)
                en.setToolTip("Enable channel " + str(channel) + " (takes immediate effect)")
                self.internalTriggerEnabled[row*cols+col] = en
                h1.addWidget(en)

                polarity = QtWidgets.QCheckBox("+")
                polarity.settingsName = "Internal trigger positive edge " + str(channel)
                polarity.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                polarity.setContentsMargins(0,0,0,0)
                polarity.setToolTip("Set polarity to positive (takes immediate effect)")
                h1.addWidget(polarity)
                self.internalTriggerPositive[row*cols+col] = polarity

                level = QtWidgets.QSpinBox()
                level.settingsName = "Internal trigger level " + str(channel)
                level.setMinimum(0)
                level.setMaximum(65535)
                level.setStyleSheet("padding: 0px; margin: 0px; margin-top:0px; margin-bottom:0px;")
                level.setContentsMargins(0,0,0,0)
                level.setToolTip("Specify the trigger level (takes immediate effect)")
                h1.addWidget(level)
                self.internalTriggerLevel[row*cols+col] = level

                func = self.gui.call(partial(lambda channel_local,en_local,polarity_local,level_local : self.gui.camera.setInternalTrigger(channel_local,\
                                                                                                                                           en_local.isChecked(),\
                                                                                                                                           level_local.value(), \
                                                                                                                                           self.gui.camera.codes_ADC.INT_TRIG_POSITIVE if polarity_local.isChecked() else self.gui.camera.codes_ADC.INT_TRIG_NEGATIVE),
                                             (self.number-1)*32+channel,en,polarity,level))
                en.stateChanged.connect(func) # enabled changes
                polarity.stateChanged.connect(func)  # polarity changes
                level.editingFinished.connect(func)


        g = QVGroupBox("")
        layout.addWidget(g)

        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)

        title = QtWidgets.QLabel("Channel offsets (DAC)")
        title.setStyleSheet("font-weight:bold")
        h.addWidget(title)
        h.addStretch(1)

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

        h = QtWidgets.QHBoxLayout()
        g.addLayout(h)
        h.setSpacing(0)
        self.dac = [None]*32
        for i in range(32):
            #self.dac[i] = QIntEdit(0,65535)
            self.dac[i] = QtWidgets.QSpinBox()
            self.dac[i].settingsName = "DAC " + str(i+1)
            self.dac[i].setMinimum(0)
            self.dac[i].setMaximum(65535)
            self.dac[i].setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.dac[i].setMaximumWidth(54)
            f = partial(lambda ch: self.gui.camera.setOffset(self.number,ch,self.dac[ch-1].value()),i+1)
            self.dac[i].lineEdit().returnPressed.connect(self.gui.call(f,name="APDCAM10G.setOffset(" + str(self.number) + "," + str(i+1) + ",value)",where=__file__))
            self.dac[i].setToolTip("Specify the value (0..65535) for the DAC for the given channel, which defines the ADC offset. Changes take effect when you hit Enter")
            h.addWidget(self.dac[i])
        h.addStretch(1)

    def show_bytes_per_sample(self):
        err,adcAddresses = self.gui.camera.adcAddresses(self.number)
        err,bpsch = self.gui.camera.readPDI(adcAddresses[0],self.gui.camera.codes_ADC.ADC_REG_BPSCH1,4,arrayData=True)
        if err != "":
            self.gui.show_error(err)
            self.bytes_per_chip.setText("")
            self.bytes_per_sample.setText("")
        else:
            bpsch = bpsch[0]
            bpc = "" # bytes per chip
            bps = 0
            for i in range(4):
                if i > 0:
                    bpc += " "
                bpc += str(int(bpsch[i]))
                bps += int(bpsch[i])

            self.bytes_per_chip.setText(bpc)

            # bytes-per-sample needs to be rounded up to integer times 32 bits, i.e. integer times 4 bytes
            n = bps//4
            if n*4 != bps:
                n += 1
            bps = n*4
            self.bytes_per_sample.setText(str(bps))

    def set_adc_channel_enable(self,channel):
        """
        Set the bit in the ADC register corresponding to this channel on/off, and in addition
        query the "bytes per sample of chip" registers (BPSCH1 .. BPSCH4) of the ADC board, and display it
        """
        self.bytes_per_sample.setText("")
        self.bytes_per_chip.setText("")
        err = self.gui.camera.setAdcChannelEnable((self.number-1)*32+channel,self.channelOn[channel-1].isChecked())
        if err != "":
            return err
        self.show_bytes_per_sample()
        return ""

    def set_adc_resolution(self):
        self.bytes_per_sample.setText("")
        self.bytes_per_chip.setText("")
        err = self.gui.camera.setAdcResolution(self.number,int(self.bits.currentText()))
        if err != "":
            return err
        self.show_bytes_per_sample()
        return ""

    def loadSettingsFromCamera(self):

        # channelOn checkboxes
        for i in range(4): # loop over the 4 ADCs on the board
            err,reg = self.gui.camera.getAdcRegister(self.number,self.gui.camera.codes_ADC.ADC_REG_CHENABLE1+i)
            if err == "":
                for c in range(8):
                    self.channelOn[i*8+c].blockSignals(True)
                    self.channelOn[i*8+c].setChecked(reg & (1<<(7-c)))
                    self.channelOn[i*8+c].blockSignals(False)
            else:
                self.gui.show_error(err)    

        err,bit = self.gui.camera.getSataOn(self.number)
        if err=="":
            self.sataOn.blockSignals(True)
            self.sataOn.setChecked(bit)
            self.sataOn.blockSignals(False)
        else:
            self.show_error("Failed to read 'Sata on' bit: " + err)
        err,bit = self.gui.camera.getSataSync(self.number)
        if err=="":
            self.sataSync.blockSignals(True)
            self.sataSync.setChecked(bit)
            self.sataSync.blockSignals(False)
        else:
            self.show_error("Failed to read 'Sata sync' bit: " + err)
        err,bit = self.gui.camera.getTestPatternMode(self.number)
        if err=="":
            self.test.blockSignals(True)
            self.test.setChecked(bit)
            self.test.blockSignals(False)
        else:
            self.show_error("Failed to read 'Test pattern mode' bit: " + err)

        err,bit = self.gui.camera.getInternalTriggerAdc(self.number)
        if err=="":
            self.internalTrigger.blockSignals(True)
            self.internalTrigger.setChecked(bit)
            self.internalTrigger.blockSignals(False)
        else:
            self.show_error("Failed to read 'ADC internal trigger' bit: " + err)
        err,bit = self.gui.camera.getReverseBitord(self.number)
        if err=="":
            self.reverseBitOrder.blockSignals(True)
            self.reverseBitOrder.setChecked(bit)
            self.reverseBitOrder.blockSignals(False)
        else:
            self.show_error("Failed to read 'reverse bit order' bit: " + err)

        err,bits = self.gui.camera.getAdcResolution(self.number)
        if err=="":
            i = self.bits.findText(str(bits))
            if i<0:
                self.show_error("Invalid resolution obtained from camera: " + str(bits))
            else:
                self.bits.blockSignals(True)
                self.bits.setCurrentIndex(i)
                self.bits.blockSignals(False)
        else:
            self.show_error("Failed to read resolution: " + err)
        
        err,ringbufsize = self.gui.camera.getRingBufferSize(self.number)
        if err=="":
            self.ringBuffer.blockSignals(True)
            self.ringBuffer.setValue(ringbufsize)
            self.ringBuffer.blockSignals(False)
        else:
            self.show_error("Failed to read ring buffer size: " + err)

        err,testpattern = self.gui.camera.getTestPattern(self.number)
        if err=="":
            s = ""
            for i in range(len(testpattern)):
                if i>0:
                    s += " ";
                s += str(testpattern[i])
            self.testPattern.blockSignals(True)
            self.testPattern.setText(s)
            self.testPattern.blockSignals(False)
        else:
            self.show_error("Failed to read test pattern: " + err)

        err,filtercoeffs = self.gui.camera.getFilterCoeffs(self.number)
        if err=="":
            for i in range(5):
                self.firCoeff[i].blockSignals(True)
                self.firCoeff[i].setValue(filtercoeffs[i])
                self.firCoeff[i].blockSignals(False)
            self.iirCoeff.blockSignals(True)
            self.iirCoeff.setValue(filtercoeffs[5])
            self.iirCoeff.blockSignals(False)
            self.internalFilterDiv.blockSignals(True)
            self.internalFilterDiv.setValue(filtercoeffs[7])
            self.internalFilterDiv.blockSignals(False)

        err,adcAddresses = self.gui.camera.adcAddresses(self.number)
        if err=="":
            adcAddress = adcAddresses[0]
            err,regs = self.gui.camera.readPDI(adcAddress,self.gui.camera.codes_ADC.ADC_REG_MAXVAL11,32*2,arrayData=True)
            if err=="":
                regs = regs[0]
                for i in range(32):
                    reg = int.from_bytes(regs[i*2:(i+1)*2],'big')
                    self.internalTriggerEnabled[i].blockSignals(True)
                    self.internalTriggerEnabled[i].setChecked(True if ((reg>>15)&1) else False)
                    self.internalTriggerEnabled[i].blockSignals(False)
                    self.internalTriggerPositive[i].blockSignals(True)
                    self.internalTriggerPositive[i].setChecked(False if ((reg>>14)&1) else True)  # yes, the 14th bit means 'negative' trigger
                    self.internalTriggerPositive[i].blockSignals(False)
                    self.internalTriggerLevel[i].blockSignals(True)
                    self.internalTriggerLevel[i].setValue(reg&(2**14-1)) # mask the lowest 13 bits
                    self.internalTriggerLevel[i].blockSignals(False)
            else:
                self.show_error("Failed to read trigger settings for ADC board " + str(self.number))    
        else:
            self.show_error("Failed to read trigger settings for ADC board " + str(self.number))
            
        err,offsets = self.gui.camera.getOffsets(self.number)
        if err=="":
            for i in range(32):
                self.dac[i].setValue(offsets[i]);
        else:
            self.show_error("Failed to get read offsets for ADC board " + str(self.number))
            
class AdcControl(QtWidgets.QWidget):
    def updateGui(self):
        for adc in self.adc:
            adc.updateGui()

    def __init__(self,parent):
        self.gui = parent
        super(AdcControl,self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.adc = []
        self.adcTabs = QtWidgets.QTabWidget(self)
        self.layout.addWidget(self.adcTabs)

        #self.setAdcs(4)

        h = QtWidgets.QHBoxLayout()
        self.layout.addLayout(h)

        self.loadSettingsFromCameraButton = QtWidgets.QPushButton("Load settings from camera")
        self.loadSettingsFromCameraButton.clicked.connect(self.loadSettingsFromCamera)
        h.addWidget(self.loadSettingsFromCameraButton)

        self.factoryResetButton = QtWidgets.QPushButton("Factory reset")
        self.factoryResetButton.guiMode = GuiMode.factory
        h.addWidget(self.factoryResetButton)


        
    def addAdc(self,number,address):
        adc = Adc(self,number,address)
        adc.settingsSection = "ADC " + str(number)
        self.adc.append(adc)
        self.adcTabs.addTab(adc,adc.name())

    def clearAdcs(self):
        self.adc = []
        while self.adcTabs.count() > 0:
            self.adcTabs.removeTab(0)

    # def setAdcs(self,number):
    #     self.adc = []
    #     if number > self.adcTabs.count():
    #         while number > self.adcTabs.count():
    #             self.addAdc()
    #     if number < self.adcTabs.count():
    #         while number < self.adcTabs.count():
    #             self.adcTabs.removeTab(self.adcTabs.count()-1)
                
    def loadSettingsFromCamera(self):
        for adc in self.adc:
            adc.loadSettingsFromCamera()
