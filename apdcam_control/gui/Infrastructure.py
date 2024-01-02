import sys
from functools import partial

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from .ApdcamUtils import *
from .GuiMode import *

class Infrastructure(QtWidgets.QWidget):
    def __init__(self,parent):
        self.gui = parent
        super(Infrastructure,self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        l1 = QtWidgets.QVBoxLayout()
        layout.addLayout(l1)

        hv = QVGroupBox("HV settings")
        l1.addWidget(hv)
#        self.readHvStatusButton = QtWidgets.QPushButton("Read HV Status")
#        self.readHvStatusButton.clicked.connect(self.readHvStatus)
#        hv.addWidget(self.readHvStatusButton)

        l = QtWidgets.QHBoxLayout()
        hv.addLayout(l)
        self.hvSet = [None]*4
        self.hvActual = [None]*4
        self.hvMax = [None]*4
        self.hvOn = [None]*4
        self.hvOff = [None]*4
        self.hvGroup = [None]*4
        for i in range(4):
            self.hvGroup[i] = QGridGroupBox()
            l.addWidget(self.hvGroup[i])

            self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" set"),0,0)
            self.hvSet[i] = QtWidgets.QDoubleSpinBox()
            self.hvSet[i].settingsName = "HV" + str(i+1) + " set"
            self.hvSet[i].setMinimum(0)
            self.hvSet[i].setMaximum(4095*self.gui.camera.HV_conversion[i])
            self.hvSet[i].valueChanged.connect(self.gui.call(partial(lambda i:self.gui.camera.setHV(i+1,self.hvSet[i].value()),i)))
            self.hvSet[i].setToolTip("Set the voltage of HV generator #" + str(i+1) + ". The command takes effect immediately when the value is changed.")
            self.hvGroup[i].addWidget(self.hvSet[i],0,1)

            self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" act."),1,0)
            self.hvActual[i] = QtWidgets.QLineEdit()
            readOnly(self.hvActual[i])
            self.hvActual[i].setToolTip("Actual value of the high-voltage generator #" + str(i+1))
            self.hvGroup[i].addWidget(self.hvActual[i],1,1)

            #self.hvGroup[i].addWidget(QtWidgets.QLabel("HV"+str(i+1)+" max."),2,0)

            setMaxButton = QtWidgets.QPushButton("Set max.")
            setMaxButton.guiMode = GuiMode.factory
            setMaxButton.setToolTip("Set the maximum in the camera hardware, and apply it to the above numerical input")
            self.hvGroup[i].addWidget(setMaxButton,2,0)

            self.hvMax[i] = QtWidgets.QDoubleSpinBox()
            self.hvMax[i].setMinimum(0)
            self.hvMax[i].setMaximum(4095*self.gui.camera.HV_conversion[i])
            self.hvMax[i].setToolTip("Maximum value for the high voltage of a detector")
            self.hvMax[i].guiMode = GuiMode.factory
            self.hvGroup[i].addWidget(self.hvMax[i],2,1)
            setMaxButton.clicked.connect(partial(self.setHvMax,i+1))

            self.hvOn[i] = QtWidgets.QCheckBox("HV #" + str(i+1) + " On")
            self.hvOn[i].stateChanged.connect(self.gui.call(partial(lambda i: self.gui.camera.hvOnOff(i+1,self.hvOn[i].isChecked()),i), \
                                                            name="self.gui.camera.hvOnOff(i+1,self.hvOn[i].isChecked()())", \
                                                            where=__file__))
            self.hvOn[i].setToolTip("Switch on this HV generator")
            self.hvGroup[i].addWidget(self.hvOn[i],3,0,1,2)

        l.addStretch(1)

        self.hvEnabled = QtWidgets.QCheckBox("HV enabled")
        self.hvEnabled.setToolTip("Enable the high-voltage for all generators")
        self.hvEnabled.stateChanged.connect(self.gui.call(self.hvEnable))

        hv.addWidget(self.hvEnabled)
        
        h = QtWidgets.QHBoxLayout()
        l1.addLayout(h)
        
        shutter = QHGroupBox("Shutter control")
        h.addWidget(shutter)

        self.shutterOpen = QtWidgets.QCheckBox("Shutter open")
        self.shutterOpen.settingsName = "Shutter open"
        self.shutterOpen.stateChanged.connect(self.gui.call(lambda: self.gui.camera.shutterOpen(self.shutterOpen.isChecked())))
        self.shutterOpen.setToolTip("Open/close the shutter")
        shutter.addWidget(self.shutterOpen)

        self.shutterMode = QtWidgets.QCheckBox("External control")
        self.shutterMode.settingsName = "Shutter external control"
        self.shutterMode.stateChanged.connect(lambda: self.setShutterMode(self.shutterMode.isChecked()))
        self.shutterMode.setToolTip("If checked, shutter is driven by the state of 'shutter control input'. If unchecked (manual), the 'Open shutter' control to the left is driving the shutter")
        shutter.addWidget(self.shutterMode)

        shutter.addStretch(1)

        calib = QHGroupBox("Calibration light control")
        h.addWidget(calib)
        calib.addWidget(QtWidgets.QLabel("Intensity:"))
        self.calibrationLightIntensity = QtWidgets.QSpinBox()
        self.calibrationLightIntensity.settingsName = "Calibration light intensity"
        self.calibrationLightIntensity.setMinimum(0)
        self.calibrationLightIntensity.setMaximum(4095)
        self.calibrationLightIntensity.valueChanged.connect(self.gui.call(lambda: self.gui.camera.setCallight(self.calibrationLightIntensity.value()),\
                                                                          name="APDCAM10G.controller.setCallight(...)",\
                                                                          where=__file__))
        self.calibrationLightIntensity.setToolTip("Set the current of the calibration LED. 0 is complete darkness, maximum value is 4096")
        calib.addWidget(self.calibrationLightIntensity)
        calib.addStretch(1)

        l = QtWidgets.QHBoxLayout()
        l1.addLayout(l)
        l.addWidget(QtWidgets.QLabel("PC Error:"))
        self.pcError = QtWidgets.QLineEdit()
        readOnly(self.pcError)
        l.addWidget(self.pcError)

        self.dualSata = QtWidgets.QCheckBox("Dual SATA")
        #self.dualSata.factorySetting = True
        self.dualSata.guiMode = GuiMode.factory
        self.dualSata.stateChanged.connect(self.gui.call(lambda: self.gui.camera.setDualSata(self.dualSata.isChecked())))
        self.dualSata.setToolTip("Enable dual SATA mode for the system (CC card and all ADC boards)")
        l1.addWidget(self.dualSata)
        

        l1.addStretch(1)

        self.controlFactoryResetButton = QtWidgets.QPushButton("Control factory reset")
        self.controlFactoryResetButton.guiMode = GuiMode.factory
        l1.addWidget(self.controlFactoryResetButton)
        
        l1.addStretch(2)

        vv = QtWidgets.QVBoxLayout()
        layout.addLayout(vv)

        g = QGridGroupBox("Temperatures")
        vv.addWidget(g)
        vv.addStretch(1)
        tmp = [["01","temp01"],
               ["02","temp02"],
               ["03","temp03"],
               ["04","temp04"],
               ["Detector 1","tempDetector1"],
               ["Analog panel 1","tempAnalog1"],
               ["Analog panel 2","tempAnalog2"],
               ["Detector 2","tempDetector2"],
               ["Analog panel 3","tempAnalog3"],
               ["Analog panel 4","tempAnalog4"],
               ["Baseplate","tempBasePlate"],
               ["12","temp12"],
               ["Diode","temp13"],
               ["Peltier (detector) heatsink","tempPcCardHeatsink"],
               ["Power panel 1","tempPowerPanel1"],
               ["Power panel 2","tempPowerPanel2"]]

        # The list of temperature reading display widgets
        self.temps = [None]*16  # placeholders
        for i in range(len(tmp)):
            row = i
            col = 0
            if i > 7:
                row -= 8
                col = 2
            g.addWidget(QtWidgets.QLabel(tmp[i][0]),row,col)
            t = QtWidgets.QLineEdit()
            #setattr(self,tmp[i][1],t)
            self.temps[i] = t
            self.temps[i].setToolTip(tmp[0][0] + " temperature")
            readOnly(t)
            g.addWidget(t,row,col+1)

#        self.readTempsButton = QtWidgets.QPushButton("Read temps")
#        g.addWidget(self.readTempsButton,len(tmp),0)
#        self.readTempsButton.setToolTip("Read the temperature sensors of the camera and display their values here")
#        self.readTempsButton.clicked.connect(self.readTemperatures)

#        self.readWeightsButton = QtWidgets.QPushButton("Read weights")
#        g.addWidget(self.readWeightsButton,len(tmp),1)
#        g.setRowStretch(g.rowCount(),1)

        # g = QGridGroupBox("Fan 1")
        # layout.addWidget(g)
        # self.fan1Mode = QtWidgets.QComboBox()
        # self.fan1Mode.addItem("Auto")
        # self.fan1Mode.addItem("Manual")
        # g.addWidget(self.fan1Mode,0,0,1,2)
        # g.addWidget(QtWidgets.QLabel("Speed"),1,0)
        # self.fan1Speed = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Speed,1,1)
        # g.addWidget(QtWidgets.QLabel("Diff"),2,0)
        # self.fan1Diff = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Diff,2,1)
        # g.addWidget(QtWidgets.QLabel("Ref"),3,0)
        # self.fan1Ref = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Ref,3,1)
        # g.addWidget(QtWidgets.QLabel("Ctrl"),4,0)
        # self.fan1Ctrl = QtWidgets.QLineEdit()
        # g.addWidget(self.fan1Ctrl,4,1)
        

        layout.addStretch(1)

    def hvEnable(self):
        self.gui.camera.hvEnable(self.hvEnabled.isChecked())

        # if the user checked the individual "HV #i On" checkboxes while HV was disabled, these took
        # no effect on the camera (it seems the camera does not allow setting the PC_REG_HVON register, if
        # PC_REG_HVENABLE is not true.
        # So propagate these settings to the camera in this case
        if(self.hvEnabled.isChecked()):
            for i in range(4):
                self.gui.camera.hvOnOff(i+1,self.hvOn[i].isChecked())
        return ""

    def loadSettingsFromCamera(self):

        # load the HV values
        err, hvon = self.gui.camera.getPcRegister(self.gui.camera.PC_registers.HVON)
        if err != "":
            return err

        for n in range(4):
            err,hv = self.gui.camera.getHV(n+1)
            if err=="":
                self.hvSet[n].setValue(hv)
                self.hvOn[n].setChecked(hvon.HV[n]())
            else:
                self.gui.show_error("Failed to read HV " + str(n+1) + " from camera: " + err)
                
        # shutter
        err,sh = self.gui.camera.getPcRegister(self.gui.camera.PC_registers.SHSTATE)
        if err=="":
            self.shutterOpen.setChecked(sh())
        else:
            self.gui.show_error("Failed to read shutter status from camera: " + err)

        # shutter external control
        err,ext = self.gui.camera.getPcRegister(self.gui.camera.PC_registers.SHMODE)
        ext = ext()
        if err=="":
            self.shutterMode.setChecked(ext)
            if ext==0:
                self.shutterOpen.setEnabled(True)
            else:
                self.shutterOpen.setEnabled(False)
        else:
            self.gui.show_error("Failed to read shutter mode from camera: " + err)

        # Calibration light
        err,callight = self.gui.camera.getCallight()
        if err=="":
            self.calibrationLightIntensity.setValue(callight)
        else:
            self.gui.show_error("Failed to read calibration light intensity from camera: " + err)

        ccDualSata = bool(self.gui.camera.status.CC_settings[self.gui.camera.codes_CC.CC_REGISTER_SATACONTROL] & 1)
        err,adcDualSata = self.gui.camera.getAdcRegisterBit('all',self.gui.camera.ADC_registers.CONTROL.DSM)
        dualSataOk = True
        for aaa in adcDualSata:
            if bool(aaa) != ccDualSata:
                self.gui.show_error("Inconsistency in the camera: some ADC has a different 'Dual SATA' setting from that of the CC board")
                dualSataOk = False
                break
        if dualSataOk:
            self.dualSata.blockSignals(True)
            self.dualSata.setChecked(ccDualSata)
            self.dualSata.blockSignals(False)

    def updateGui(self):
        for i in range(4):
            self.hvActual[i].setText("{:.1f}".format(self.gui.camera.status.HV_act[i]))

        for i in range(16):
            T = self.gui.camera.status.temps[i]
            self.temps[i].setText("{:3.1f}".format(T) if T<100 else "---")

        # r = self.gui.camera.status.PC_registers
        # c = self.gui.camera.codes_PC
        # hv1max = int.from_bytes(r[c.PC_REG_HV1MAX:c.PC_REG_HV1MAX+2],'little')
        # print("hv1 max: " + str(hv1max*0.12))


    def setHvMax(self,n):
        """
        Sets the maximum value of the high voltage for a detector both on the hardware, and in the gui.
        The maximum value is taken from the corresponding GUI entry.

        Parameters
        ^^^^^^^^^^
        n: int
            HV generator number (1..4)
        """

        value = self.hvMax[n-1].value()

        # First, apply it to the HV input field
        self.hvSet[n-1].setMaximum(value)

        # Then make standard checks before calling the hardware function
        if not self.gui.beforeBackendCall(name="setHvMax(" + str(n) + ")",where=__file__):
            return

        # call the hardware function
        err = self.gui.camera.setHVMax(n,value)

        # Then report errors
        self.gui.afterBackendCall(True if err=="" else False, [err],name="self.gui.camera.setHVMax(" + str(n) + "," + str(value) + ")")

    def setShutterMode(self,mode):
        """
        Set the shutter mode. Disables the "Open" checkbox if mode is External (1)

        Parameters
        ^^^^^^^^^^
        mode: int
            0 - Manual, the 'Open' manual control checkbox is enabled, one can control the shutter from the GUI
            1 - External, 'Open' manual control checkbox is disabled, an external electronic signal can control the shutter

        """

        # External mode
        if mode==0:
            self.shutterOpen.setEnabled(True)
        else:
            self.shutterOpen.setEnabled(False)
        
        if not self.gui.beforeBackendCall(name="setShutterMode(" + str(mode) + ")",where=__file__):
            return

        err = self.gui.camera.shutterMode(mode)

        self.gui.afterBackendCall(True if err=="" else False, [err],name="self.gui.camera.shutterMode(" + str(mode) + ")")

#    def readHvStatus(self):
#        self.gui.show_error("Infrastructure.readHvStatus not implemented yet")

    def setHvGroups(self,n):
        """
        Set the number of HV groups, i.e.the number of ADC Boards.
        Instead of dynamically adding/removing them, the GUI creates the maximally possible 4 groups,
        and disables those which are not in the hardware
        """
        for i in range(4):
            if i >= n:
                self.hvGroup[i].setEnabled(False)
            else:
                self.hvGroup[i].setEnabled(True)

