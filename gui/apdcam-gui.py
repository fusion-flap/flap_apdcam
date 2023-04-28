import sys
import datetime
import inspect
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QCheckBox
from PyQt6.QtCore import Qt

from ApdcamUtils import *

from MainPage import MainPage
from CameraControl import CameraControl
from HvShutterLight import HvShutterLight
from OffsetNoise import OffsetNoise
from AdcControl import AdcControl
from ControlTiming import ControlTiming
from CameraTimer import CameraTimer

class ApdcamGui(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('APDCAM Control')

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.factorySettingsGroupBox = QHGroupBox("Factory settings")
        layout.addWidget(self.factorySettingsGroupBox,0,0)
        self.factorySettingsMode = False
        self.factorySettingsPassword = QLineEdit(self)
        self.factorySettingsPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.factorySettingsPassword.returnPressed.connect(self.toggleFactorySettingsMode)
        self.factorySettingsGroupBox.addWidget(self.factorySettingsPassword)
        self.factorySettingsModeButton = QPushButton("Enter factory settings mode")
        self.factorySettingsGroupBox.addWidget(self.factorySettingsModeButton)
        self.factorySettingsModeButton.clicked.connect(self.toggleFactorySettingsMode)
        
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs, 1, 0)

        self.tabs.addTab(MainPage(self),"Main")
        self.tabs.addTab(HvShutterLight(self),"HV/Shutter/Light")
        self.tabs.addTab(OffsetNoise(self),"Offset/Noise")
        self.tabs.addTab(CameraControl(self),"Camera control")
        self.tabs.addTab(AdcControl(self),"ADC control")
        self.tabs.addTab(ControlTiming(self),"Control timing")
        self.tabs.addTab(CameraTimer(self),"Camera timer")
        

        layout.addWidget(QLabel("Messages/<font color='orange'>Warnings</font>/<font color='red'>Errors</font>:"))
        self.messages = QTextEdit(self)
        self.messages.setReadOnly(True)
        layout.addWidget(self.messages,3,0)

        self.show()
        children = self.findChildren(QWidget)
        for child in children:
            if hasattr(child,"factorySetting") and child.factorySetting:
                self.setControlEnabled(child,False)

    def showMessageWithTime(self,msg):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append(time + " - " + msg)

    def showMessage(self,msg):
        self.showMessageWithTime(msg)

    def showWarning(self,msg):
        self.showMessageWithTime("<font color='orange'>" + msg + "</font>");

    def showError(self,msg):
        self.showMessageWithTime("<font color='red'>" + msg + "</font>");

    def setControlEnabled(self,control,status):
        if hasattr(control,"setEnabled"):
            control.setEnabled(status)
        else:
            self.showError("A factory-setting control can not be be toggled between enabled/disabled (alert the developer!)")
        if isinstance(control,QPushButton):
            control.setStyleSheet("color: " + ("rgba(255,0,0,1)" if status else "rgba(255,0,0,0.25)"))
        if isinstance(control,QCheckBox):
            control.setStyleSheet("color: " + ("rgba(255,0,0,1)" if status else "rgba(255,0,0,0.25)"))
        

    def toggleFactorySettingsMode(self):
        if not self.factorySettingsMode and self.factorySettingsPassword.text() != "hello":
            self.showError("Incorrect password")
            self.factorySettingsPassword.setText("")
            return
        self.factorySettingsPassword.setText("")
        self.factorySettingsMode = not self.factorySettingsMode
        if self.factorySettingsMode:
            self.showWarning("Enter factory settings mode")
        else:
            self.showMessage("Quit factory settings mode")
        if self.factorySettingsMode:
            self.factorySettingsModeButton.setText("Quit factory settings mode")
        else:
            self.factorySettingsModeButton.setText("Enter factory settings mode")
        children = self.findChildren(QWidget)
        for child in children:
            if hasattr(child,"factorySetting") and child.factorySetting:
                self.setControlEnabled(child,self.factorySettingsMode)


                    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ApdcamGui()
    sys.exit(app.exec())
