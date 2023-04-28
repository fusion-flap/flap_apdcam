import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox
from PyQt6.QtCore import Qt
from ApdcamUtils import *


class CameraTimer(QWidget):
    def __init__(self,parent):
        super(CameraTimer,self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        horiz = QHBoxLayout()
        layout.addLayout(horiz)

        g = QVGroupBox()
        horiz.addWidget(g)
        h = QHBoxLayout()
        self.readCameraTimerSettingsButton = QPushButton("Read camera timer settings")
        h.addWidget(self.readCameraTimerSettingsButton)
        self.saveCameraTimerSettingsButton = QPushButton("Save camera timer settings")
        h.addWidget(self.saveCameraTimerSettingsButton)
        g.addLayout(h)

        r = QGridLayout()
        g.addLayout(r)
        self.timer = [Empty()]*10
        for row in range(2):
            for col in range(5):
                timerindex = row*5+col
                t = QHGroupBox() 
                r.addWidget(t,row,col)
                g1 = QGridGroupBox("Timer " + str(timerindex+1))
                t.addWidget(g1)
                g1.addWidget(QLabel("Delay:"),0,0)
                self.timer[timerindex].delay = QSpinBox()
                g1.addWidget(self.timer[timerindex].delay,0,1)
                g1.addWidget(QLabel("ON time:"),1,0)
                self.timer[timerindex].onTime = QSpinBox()
                g1.addWidget(self.timer[timerindex].onTime,1,1)
                g1.addWidget(QLabel("OFF time:"),2,0)
                self.timer[timerindex].offTime = QSpinBox()
                g1.addWidget(self.timer[timerindex].offTime,2,1)
                g1.addWidget(QLabel("# of pulses:"),3,0)
                self.timer[timerindex].nofPulses = QSpinBox()
                g1.addWidget(self.timer[timerindex].nofPulses,3,1)
                g2 = QVGroupBox("Out")
                t.addWidget(g2)
                self.timer[timerindex].out = [None]*4
                for out in range(4):
                    self.timer[timerindex].out[out] = QCheckBox("CH " + str(out+1))
                    g2.addWidget(self.timer[timerindex].out[out])
                
        l = QVBoxLayout()
        horiz.addLayout(l)

        h = QHBoxLayout()
        l.addLayout(h)
        h.addWidget(QLabel("20 MHz divider value:"))
        self.divider20MHz = QSpinBox()
        self.divider20MHz.setMinimum(1)
        self.divider20MHz.setMaximum(65535)
        h.addWidget(self.divider20MHz)
        l.addStretch(1)
        g = QVGroupBox("Control registers")
        l.addWidget(g)
        self.idleArmedState = QCheckBox("Idle/armed state")
        g.addWidget(self.idleArmedState)
        self.manualStopStart = QCheckBox("Manual stop/start")
        g.addWidget(self.manualStopStart)
        self.returnToArmed = QCheckBox("Return to armed")
        g.addWidget(self.returnToArmed)
        self.returnToRun = QCheckBox("Return to run")
        g.addWidget(self.returnToRun)
        self.externalTriggerRisingSlopeEnable = QCheckBox("External trigger rising slope enable")
        g.addWidget(self.externalTriggerRisingSlopeEnable)
        self.externalTriggerFallingSlopeEnable = QCheckBox("External trigger falling slope enable")
        g.addWidget(self.externalTriggerFallingSlopeEnable)
        self.internalTriggerEnable = QCheckBox("Internal trigger enable")
        g.addWidget(self.internalTriggerEnable)
        l.addStretch(1)

        g = QHGroupBox("Output polarity")
        l.addWidget(g)
        self.outputPolarityXor = [None]*4
        for i in range(4):
            self.outputPolarityXor[i] = QCheckBox("XOR-" + str(i+1))
            g.addWidget(self.outputPolarityXor[i])
        g = QHGroupBox("Output enable")
        l.addWidget(g)
        self.outputEnableAnd = [None]*4
        for i in range(4):
            self.outputEnableAnd[i] = QCheckBox("AND-" + str(i+1))
            g.addWidget(self.outputEnableAnd[i])

        h = QHBoxLayout()
        layout.addLayout(h)
        self.cameraTimerIdleButton = QPushButton("Camera timer IDLE")
        h.addWidget(self.cameraTimerIdleButton)
        self.cameraTimerArmedButton = QPushButton("Camera timer ARMED")
        h.addWidget(self.cameraTimerArmedButton)
        self.cameraTimerRunButton = QPushButton("Camera timer RUN")
        h.addWidget(self.cameraTimerRunButton)
            
