import sys
import datetime
import inspect
import types

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

from ApdcamUtils import *

from MainPage import MainPage
from CameraControl import CameraControl
from Infrastructure import Infrastructure
from OffsetNoise import OffsetNoise
from AdcControl import AdcControl
from ControlTiming import ControlTiming
from CameraTimer import CameraTimer
from CameraConfig import CameraConfig
from FactoryTest import FactoryTest
from Plot import Plot
from SimpleMeasurementControl import SimpleMeasurementControl
from GuiMode import *


"""
The setEnabled method of a QWidget, when it is a tab of a QTabWidget, makes apparantly nothing.
The correct way to disable a tab within a QTabWidget is QTabWidget.setTabEnabled(index,status)
This function therefore implements this functionality, and this method will be assigned (overwrite)
the default setEnabled member function of the given widget used as a tab.
It is the responsibility of the programmer to set this function for the given tab, as follows
t = SomeClassUsedAsTab()
t.guiMode = GuiMode.factory
t.setEnabled = types.MethodType(setTabEnabled,t)
self.tabs.addTab(t,"Tab title")  # must record the index!
"""
def setTabEnabled(self,enabled):
    o = self.parent()
    while o is not None and not isinstance(o,QtWidgets.QTabWidget):
        o = o.parent()
    if o is not None:
        i = o.indexOf(self)
        if i >= 0:
            o.setTabEnabled(i,enabled)
        else:
            print("This widget doesn't seem to be the child of this QTabWidget")
    else:
        print("This widget is not within a QTabWidget")

class ApdcamGui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # set this property to make it defined. However, this has no effect here
        self.guiMode = GuiMode.simple
        
        self.setWindowTitle('APDCAM Control')

        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        layout = QtWidgets.QGridLayout(self.centralWidget)
        self.centralWidget.setLayout(layout)

        QAction = None
        if QtVersion == "PyQt6":
            QAction = QtGui.QAction
        else:
            QAction = QtWidgets.QAction

        menuBar = self.menuBar()

        # File menu --------------------
        fileMenu = menuBar.addMenu("&File")
        exitAction = QAction("&Exit",self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        # Run mode menu ------------------
        modeMenu = menuBar.addMenu("&GUI Mode")
        self.simpleModeAction = QAction("&Simple",self)
        self.simpleModeAction.triggered.connect(lambda: self.setGuiMode(GuiMode.simple))
        self.simpleModeAction.setIcon(QtGui.QIcon("./checkmark.png"))
        modeMenu.addAction(self.simpleModeAction)
        self.expertModeAction = QAction("&Expert",self)
        self.expertModeAction.triggered.connect(lambda: self.setGuiMode(GuiMode.expert))
        modeMenu.addAction(self.expertModeAction)
        
        self.factorySettingsGroupBox = QHGroupBox("Factory settings")
        self.factorySettingsGroupBox.guiMode = GuiMode.expert
        layout.addWidget(self.factorySettingsGroupBox,0,0)
        self.factorySettingsPassword = QtWidgets.QLineEdit(self)
        self.factorySettingsPassword.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.factorySettingsPassword.returnPressed.connect(self.toggleFactorySettingsMode)
        self.factorySettingsGroupBox.addWidget(self.factorySettingsPassword)
        self.factorySettingsModeButton = QtWidgets.QPushButton("Enter factory settings mode")
        self.factorySettingsGroupBox.addWidget(self.factorySettingsModeButton)
        self.factorySettingsModeButton.clicked.connect(self.toggleFactorySettingsMode)

        # ------------------ Expert tabs ----------------------------------
        self.expertTabs = QtWidgets.QTabWidget(self)
        self.expertTabs.guiMode = GuiMode.expert
        layout.addWidget(self.expertTabs, 1, 0)
        self.expertTabs.addTab(MainPage(self),"Main")
        self.expertTabs.addTab(Infrastructure(self),"Infrastructure")
        self.expertTabs.addTab(OffsetNoise(self),"Offset/Noise")
        self.expertTabs.addTab(CameraControl(self),"Camera control")
        self.expertTabs.addTab(AdcControl(self),"ADC control")
        self.expertTabs.addTab(ControlTiming(self),"Control timing")
        self.expertTabs.addTab(CameraTimer(self),"Camera timer")
        self.expertTabs.addTab(CameraConfig(self),"Camera configuration")

        fs = FactoryTest(self)
        fs.guiMode = GuiMode.factory
        fs.setEnabled = types.MethodType(setTabEnabled,fs)
        self.expertTabs.addTab(fs,"Factory test")

        self.expertTabs.addTab(Plot(self),"Plot")

        # ------------------ Simple tabs ----------------------------------
        self.simpleTabs = QtWidgets.QTabWidget(self)
        self.simpleTabs.guiMode = GuiMode.simple
        layout.addWidget(self.simpleTabs)

        self.simpleTabs.addTab(SimpleMeasurementControl(self),"Measurement control")


        layout.addWidget(QtWidgets.QLabel("Messages/<font color='orange'>Warnings</font>/<font color='red'>Errors</font>:"))
        self.messages = QtWidgets.QTextEdit(self)
        self.messages.setReadOnly(True)
        layout.addWidget(self.messages,3,0)

        self.show()
        self.setGuiMode(GuiMode.expert)

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
        if isinstance(control,QtWidgets.QPushButton):
            control.setStyleSheet("color: " + ("rgba(255,0,0,1)" if status else "rgba(255,0,0,0.25)"))
        if isinstance(control,QtWidgets.QCheckBox):
            control.setStyleSheet("color: " + ("rgba(255,0,0,1)" if status else "rgba(255,0,0,0.25)"))

    def setGuiMode(self,mode):
        oldMode = self.guiMode
        self.guiMode = mode
        self.factorySettingsPassword.setText("")
        if mode == GuiMode.simple:
            self.simpleModeAction.setIcon(QtGui.QIcon("checkmark.png"))
            self.expertModeAction.setIcon(QtGui.QIcon())
        if mode == GuiMode.factory:
            self.factorySettingsModeButton.setText("Quit factory settings mode")
            self.showWarning("Enter factory settings mode")
            self.expertModeAction.setIcon(QtGui.QIcon("checkmark.png"))
            self.simpleModeAction.setIcon(QtGui.QIcon())
        if mode == GuiMode.expert:
            self.factorySettingsModeButton.setText("Enter factory settings mode")
            if oldMode == GuiMode.factory:
                self.showMessage("Quit factory settings mode")
            self.expertModeAction.setIcon(QtGui.QIcon("checkmark.png"))
            self.simpleModeAction.setIcon(QtGui.QIcon())
        children = self.findChildren(QtWidgets.QWidget)
        for child in children:
            if hasattr(child,"guiMode") and child.guiMode == GuiMode.simple:
                if self.guiMode == GuiMode.simple:
                    child.setHidden(False)
                else:
                    child.setHidden(True)
            if hasattr(child,"guiMode") and child.guiMode == GuiMode.expert:
                if self.guiMode == GuiMode.simple:
                    child.setHidden(True)
                else:
                    child.setHidden(False)
            if hasattr(child,"guiMode") and child.guiMode == GuiMode.factory:
                if self.guiMode == GuiMode.simple or self.guiMode == GuiMode.expert:
                    self.setControlEnabled(child,False)
                else:
                    self.setControlEnabled(child,True)
                    
    def toggleFactorySettingsMode(self):
        if self.guiMode == GuiMode.simple:
            self.showError("This should never happen")
            return

        if self.guiMode == GuiMode.expert:
            if self.factorySettingsPassword.text() != "hello":
                self.showError("Incorrect password")
                self.factorySettingsPassword.setText("")
                return
            self.factorySettingsPassword.setText("")
            self.setGuiMode(GuiMode.factory)
            return

        if self.guiMode == GuiMode.factory:
            self.setGuiMode(GuiMode.expert)

                    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ApdcamGui()
    sys.exit(app.exec())
