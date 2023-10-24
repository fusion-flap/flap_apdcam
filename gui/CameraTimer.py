import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")


# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox
# from PyQt6.QtCore import Qt
from ApdcamUtils import *


class CameraTimer(QtWidgets.QWidget):
    def updateGui(self):
        pass

    def loadSettingsFromCamera(self):
        self.gui.show_message("Loading the settings from the camera is not yet implemented for Camera & Timer tab")


    def __init__(self,parent):
        self.gui = parent
        super(CameraTimer,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        horiz = QtWidgets.QHBoxLayout()
        layout.addLayout(horiz)

        g = QVGroupBox()
        horiz.addWidget(g)
        # h = QtWidgets.QHBoxLayout()
        # self.readCameraTimerSettingsButton = QtWidgets.QPushButton("Read camera timer settings")
        # h.addWidget(self.readCameraTimerSettingsButton)
        # self.saveCameraTimerSettingsButton = QtWidgets.QPushButton("Save camera timer settings")
        # h.addWidget(self.saveCameraTimerSettingsButton)
        # g.addLayout(h)

        r = QtWidgets.QGridLayout()
        g.addLayout(r)
        self.timer = [Empty()]*10
        for row in range(2):
            for col in range(5):
                timerindex = row*5+col
                t = QHGroupBox() 
                r.addWidget(t,row,col)
                g1 = QGridGroupBox("Timer " + str(timerindex+1))
                t.addWidget(g1)
                g1.addWidget(QtWidgets.QLabel("Delay:"),0,0)
                self.timer[timerindex].delay = QtWidgets.QSpinBox()
                g1.addWidget(self.timer[timerindex].delay,0,1)
                g1.addWidget(QtWidgets.QLabel("ON time:"),1,0)
                self.timer[timerindex].onTime = QtWidgets.QSpinBox()
                g1.addWidget(self.timer[timerindex].onTime,1,1)
                g1.addWidget(QtWidgets.QLabel("OFF time:"),2,0)
                self.timer[timerindex].offTime = QtWidgets.QSpinBox()
                g1.addWidget(self.timer[timerindex].offTime,2,1)
                g1.addWidget(QtWidgets.QLabel("# of pulses:"),3,0)
                self.timer[timerindex].nofPulses = QtWidgets.QSpinBox()
                g1.addWidget(self.timer[timerindex].nofPulses,3,1)
                g2 = QVGroupBox("Out")
                t.addWidget(g2)
                self.timer[timerindex].out = [None]*4
                for out in range(4):
                    self.timer[timerindex].out[out] = QtWidgets.QCheckBox("CH " + str(out+1))
                    g2.addWidget(self.timer[timerindex].out[out])
                
        l = QtWidgets.QVBoxLayout()
        horiz.addLayout(l)

        h = QtWidgets.QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QtWidgets.QLabel("20 MHz divider value:"))
        self.divider20MHz = QtWidgets.QSpinBox()
        self.divider20MHz.setMinimum(1)
        self.divider20MHz.setMaximum(65535)
        h.addWidget(self.divider20MHz)
        l.addStretch(1)
        g = QVGroupBox("Control registers")
        l.addWidget(g)
        self.idleArmedState = QtWidgets.QCheckBox("Idle/armed state")
        g.addWidget(self.idleArmedState)
        self.manualStopStart = QtWidgets.QCheckBox("Manual stop/start")
        g.addWidget(self.manualStopStart)
        self.returnToArmed = QtWidgets.QCheckBox("Return to armed")
        g.addWidget(self.returnToArmed)
        self.returnToRun = QtWidgets.QCheckBox("Return to run")
        g.addWidget(self.returnToRun)
        self.externalTriggerRisingSlopeEnable = QtWidgets.QCheckBox("External trigger rising slope enable")
        g.addWidget(self.externalTriggerRisingSlopeEnable)
        self.externalTriggerFallingSlopeEnable = QtWidgets.QCheckBox("External trigger falling slope enable")
        g.addWidget(self.externalTriggerFallingSlopeEnable)
        self.internalTriggerEnable = QtWidgets.QCheckBox("Internal trigger enable")
        g.addWidget(self.internalTriggerEnable)
        l.addStretch(1)

        g = QHGroupBox("Output polarity")
        l.addWidget(g)
        self.outputPolarityXor = [None]*4
        for i in range(4):
            self.outputPolarityXor[i] = QtWidgets.QCheckBox("XOR-" + str(i+1))
            g.addWidget(self.outputPolarityXor[i])
        g = QHGroupBox("Output enable")
        l.addWidget(g)
        self.outputEnableAnd = [None]*4
        for i in range(4):
            self.outputEnableAnd[i] = QtWidgets.QCheckBox("AND-" + str(i+1))
            g.addWidget(self.outputEnableAnd[i])

        h = QtWidgets.QHBoxLayout()
        layout.addLayout(h)
        self.cameraTimerIdleButton = QtWidgets.QPushButton("Camera timer IDLE")
        h.addWidget(self.cameraTimerIdleButton)
        self.cameraTimerArmedButton = QtWidgets.QPushButton("Camera timer ARMED")
        h.addWidget(self.cameraTimerArmedButton)
        self.cameraTimerRunButton = QtWidgets.QPushButton("Camera timer RUN")
        h.addWidget(self.cameraTimerRunButton)
            
