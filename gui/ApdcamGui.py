import sys
from datetime import datetime
import time
import inspect
import types
import threading
import os
import glob

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")


from ApdcamUtils import *
from ApdcamSettings import *
from MainPage import MainPage
from Measure import Measure
from Diagnostics import Diagnostics
from Infrastructure import Infrastructure
from AdcControl import AdcControl
from ControlTiming import ControlTiming
from CameraTimer import CameraTimer
from FactoryTest import FactoryTest
from Plot import Plot
from SimpleMeasurementControl import SimpleMeasurementControl
from GuiMode import *

#sys.path.append('/home/apdcam/Python/apdcam_devel/apdcam_control')
sys.path.append('/home/barna/fusion-instruments/apdcam/sw/flap_apdcam/apdcam_control')
from APDCAM10G_control import *

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

    DETECTOR_TEMP_SENSOR = 5 # 1...
    BASE_TEMP_SENSOR = 11
    AMP_TEMP_SENSOR = 6
    POWER_TEMP_SENSOR = 16

    cameraStateRefreshed = QtCore.pyqtSignal()

    def pollCameraStatus(self):
        while True:

            # if the camera is disconnected, we break the infinite loop of the update thread
            # and return, terminating the thread
            if not self.status.connected:
                print("Camera is  disconnected, stopping the GUI update loop")
                self.showMessage("Camera is disconnected, stopping the GUI update loop")
                return

            if self.updateGuiThreadStop:
                print("Stopping GUI update loop")
                self.showMessage("Stopping GUI update loop")
                return
            
            time.sleep(1)

            self.camera.readStatus()

            self.cameraStateRefreshed.emit()
        
    def versionSpecificSetup(self):
        children = self.findChildren(QtWidgets.QWidget)
        for child in children:
            if hasattr(child,"versionSpecificSetup"):
                child.versionSpecificSetup(self.camera.status.CC_firmware.decode('utf-8'))

    def updateGui(self):
        """
        This function updates the GUI widgets from the camera status self.camera.status
        """
        self.infrastructure.updateGui()
        self.adcControl.updateGui()
        self.controlTiming.updateGui()
        self.cameraTimer.updateGui()

    
    def onTabChange(self):
        pass


    def __init__(self, parent=None):
        super().__init__(parent)

        self.cameraStateRefreshed.connect(self.updateGui)

        self.camera = APDCAM10G_regCom()
        self.camera.setErrorHandler(lambda msg: self.showError(msg))

        # Status info is collected into a sub-class 'status'
        class Status:
            pass
        self.status = Status()
        self.status.connected = False
        

        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.logfile = None
        #self.logfile = open("apdcam-gui-log_" + time,"w")
        
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

        saveSettingsAction = QAction("&Save settings",self)
        fileMenu.addAction(saveSettingsAction)
        saveSettingsAction.triggered.connect(lambda: self.saveSettings())

        loadSettingsAction = QAction("&Load settings",self)
        fileMenu.addAction(loadSettingsAction)
        loadSettingsAction.triggered.connect(lambda: self.loadSettings())

        exitAction = QAction("&Exit",self)
        fileMenu.addAction(exitAction)

        restartAction = QAction("&Restart",self)
        restartAction.triggered.connect(lambda: self.exit(123))
        fileMenu.addAction(restartAction)

        # Run mode menu ------------------
        modeMenu = menuBar.addMenu("&GUI Mode")
        self.simpleModeAction = QAction("&Simple",self)
        self.simpleModeAction.triggered.connect(lambda: self.setGuiMode(GuiMode.simple))
        self.simpleModeAction.setIcon(QtGui.QIcon("./checkmark.png"))
        modeMenu.addAction(self.simpleModeAction)
        self.expertModeAction = QAction("&Expert",self)
        self.expertModeAction.triggered.connect(lambda: self.setGuiMode(GuiMode.expert))
        modeMenu.addAction(self.expertModeAction)

        # Developer menu ------------------
        developerMenu = menuBar.addMenu("&Developer")
        self.markFunctionlessAction = QAction("&Mark functionless (=no tooltip...) controls",self)
        self.markFunctionlessAction.triggered.connect(self.markFunctionlessControls)
        developerMenu.addAction(self.markFunctionlessAction)

        self.factorySettingsGroupBox = QHGroupBox()
        self.factorySettingsGroupBox.guiMode = GuiMode.expert
        layout.addWidget(self.factorySettingsGroupBox,0,0)
        self.factorySettingsPassword = QtWidgets.QLineEdit(self)
        self.factorySettingsPassword.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.factorySettingsPassword.returnPressed.connect(self.toggleFactorySettingsMode)
        self.factorySettingsPassword.setToolTip("Specify the password here and hit Enter (or click the button) to have access to factory factory settings")
        self.factorySettingsGroupBox.addWidget(self.factorySettingsPassword)
        self.factorySettingsModeButton = QtWidgets.QPushButton("Enter factory settings mode")
        self.factorySettingsGroupBox.addWidget(self.factorySettingsModeButton)
        self.factorySettingsModeButton.clicked.connect(self.toggleFactorySettingsMode)
        self.factorySettingsModeButton.setToolTip("Enter or quit factory settings mode with elevated control rights")

        # ------------------ Expert tabs ----------------------------------
        self.expertTabs = QtWidgets.QTabWidget(self)
        self.expertTabs.guiMode = GuiMode.expert
        layout.addWidget(self.expertTabs, 1, 0)
        self.expertTabs.addTab(MainPage(self),"Main")

        self.infrastructure = Infrastructure(self)
        self.expertTabs.addTab(self.infrastructure,"Infrastructure")
        self.infrastructure.settingsSection = "Infrastructure"

        self.adcControl = AdcControl(self)
        self.expertTabs.addTab(self.adcControl,"ADC control")
        self.adcControl.settingsSection = "ADC control"

        # for testing without camera
        #self.adcControl.addAdc(1,10)

        self.controlTiming = ControlTiming(self)
        self.expertTabs.addTab(self.controlTiming,"Control && Timing")
        self.controlTiming.settingsSection = "Control & Timing"

        self.cameraTimer = CameraTimer(self)
        self.expertTabs.addTab(self.cameraTimer,"Camera timer")
        self.cameraTimer.settingsSection = "Camera timer"

        self.measure = Measure(self)
        self.expertTabs.addTab(self.measure,"Measure")
        self.measure.settingsSection = "Measure"


        self.plot = Plot(self)
        self.expertTabs.addTab(self.plot,"Plot")
        self.plot.settingsSection = "Plot"

        self.diagnostics = Diagnostics(self)
        self.expertTabs.addTab(self.diagnostics,"Diagnostics")
        self.diagnostics.settingsSection = "Diagnostics"


        fs = FactoryTest(self)
        fs.guiMode = GuiMode.factory
        fs.setEnabled = types.MethodType(setTabEnabled,fs)
        self.expertTabs.addTab(fs,"Factory test")

        self.expertTabs.currentChanged.connect(self.onTabChange)

#        self.expertTabs.addTab(Plot(self),"Plot")

        # ------------------ Simple tabs ----------------------------------
        self.simpleTabs = QtWidgets.QTabWidget(self)
        self.simpleTabs.guiMode = GuiMode.simple
        layout.addWidget(self.simpleTabs)

        self.simpleTabs.addTab(SimpleMeasurementControl(self),"Measurement control")

        layout.addWidget(QtWidgets.QLabel("Messages/<font color='orange'>Warnings</font>/<font color='red'>Errors</font>:"))
        self.messages = QtWidgets.QTextEdit(self)
        self.messages.setReadOnly(True)
        self.messages.setMinimumHeight(200)
        layout.addWidget(self.messages,3,0)

        self.show()
        self.setGuiMode(GuiMode.expert)

        if self.early_messages:
            self.messages.setText(self.early_messages)

        self.updateGuiThreadStop = True
        self.updateGuiThread = None 
        exitAction.triggered.connect(self.exit)
        #self.startGuiUpdate()

        self.adcControl.addAdc(1,1)


    def exit(self,rc):
        self.stopGuiUpdate()
        sys.exit(rc)
        
    def startGuiUpdate(self):
        if not self.status.connected:
            self.showMessage("Camera is not connected")
            return
        if self.updateGuiThread == None:
            self.showMessage("Starting GUI update")
            self.updateGuiThreadStop = False
            self.updateGuiThread = threading.Thread(target=self.pollCameraStatus)
            self.updateGuiThread.start()
        else:
            self.showMessage("GUI update is already running")

    def stopGuiUpdate(self):
        """
        Sets the 'stop' flag for the thread making the periodic update of the widgets from the values
        obtained from the camera, and waits for the thread to terminate
        """
        
        self.showMessage("Signaling the GUI update to stop")
        self.updateGuiThreadStop = True
        while hasattr(self.updateGuiThread,"is_alive") and self.updateGuiThread.is_alive():
            print("Still alive")
            time.sleep(0.1)
        self.updateGuiThread = None

    def beforeBackendCall(self,*,name="",where=""):
        if not self.status.connected:
            msg = "Camera is not connected. Failed to call '"
            if name != "":
                msg += name
            else:
                msg += '(no name provided)'
            msg += "'"
            if where != "":
                msg += " [" + where + "]"
            self.showError(msg)
            return False
        return True

    def afterBackendCall(self,success,errors,*,n=1,name='no name given',showall=False):
        if not success:
            msg = "Function '" + name + "' failed " + str(n) + " times. ";
            if not showall:
                msg += "Last error: " + errors[len(errors)-1]
            self.showError(msg)


    def call(self,function,*,n=1,wait=1,critial=False,showall=False,name='',where=''):
        """
        Creates a callable proxy object running the given function, to be used as push-button or other widget actions.
        The function is assumed to return an error message in case of a fault, or an empty string in the case of success.
        The proxy will report eventual error messages.

        Parameters
        ^^^^^^^^^^
        function
            a callable object, which will be called with no arguments (if you want to run
            a function with given arguments, make the binding using a lambda)
        n=1
            Number of times the function should be called
        wait=1
            Number of seconds the routine should wait before subsequent calls of the function
        critical=False
            If True, the GUI will shut down the connection to the camera, and report a critical error
        showall=False
            If True, all function calls and error messages will be reported individually. If
            only the last error message is shown, and individual calls are not reported
        name=''
            Give a descriptive name to your function, to be displayed along with error messages, if any
        where=''
            Give a source file/location info for debugging (should be done more automatically using
            python's built-in functionality)

        Returns
        ^^^^^^^
        A python function is returned, which can be connected to a Qt signal
        """

        def wrapper():
            if not self.beforeBackendCall(name=name,where=where):
                return

            errors = []
            success = False
            ncalls = 0
            for i in range(n):
                if showall:
                    self.showMessage("Calling " + function.__qualname__)
                e = function()

                if not isinstance(e,str):
                    e = "Returned value from function is not an error string: '" + str(e) + "'"

                ncalls += 1
                if e == "":
                    success = True
                    break
                else:
                    if showall:
                        self.showError(e)
                    errors.append(e)
                if n > 1:
                    time.sleep(wait)

            self.afterBackendCall(success,errors,n=n,name=name,showall=showall)

        return wrapper

    def settingsDirName(self):
        """
        Returns (and if it does not exist, creates) the global settings directory name
        ~/.fusion-instruments/apdcam
        It returns an empty string upon error
        """

        settingsDir = os.path.expanduser("~") + "/.fusion-instruments/apdcam"
        if not os.path.exists(settingsDir):
            try:
                os.makedirs(settingsDir)
            except:
                return ""
        return settingsDir

    def cameraSettingsDirName(self):
        """
        If the camera is connected, it returns the name of the settings directory for this specific camera,
        identified by its serial number (that of the CC card). If this directory does not exist yet,
        it is automatically created
        (by default ~/.fusion-instruments/apdcam/XXX, where XXX is the serial number of the camera)
        If the camera is not connected, it returns the empty string
        """
        dir = self.settingsDirName() + "/UNKNOWN-DEVICE"
        if self.status.connected:
            dir = self.settingsDirName() + "/" + str(self.camera.status.CC_serial);
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except:
                self.showError("Could not create camera-specific settings directory " + dir)
                return ""
        return dir

    def cameraSettingsFileName(self):
        """
        Returns an absolute file name containing the actual time for the GUI settings to be saved into.
        It returns an empty string if the camera is not connected.
        """

        dir = self.cameraSettingsDirName()
        if dir=="":
            return

        fileName = dir + "/settings_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
        return fileName

    def cameraLastSettingsFileName(self):
        """
        Searches the camera-specific settings directory (identified by the camera CC card serial number)
        for files named settings_YYYY-MM-DD_HH-MM-SS.txt
        and returns the last one, or an empty string, if no such files exist, or the camera is not connected.
        """

        dir = self.cameraSettingsDirName()
        if dir == "":
            return ""

        # Look for files settings_YYYY-MM-DD_HH-MM-SS.txt
        files = glob.glob(dir + "/settings_[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]-[0-9][0-9]-[0-9][0-9].txt")
        if len(files) == 0:
            return ""
        files.sort()
        return files[len(files)-1]

    def loadSettings(self,fileName = "", ask=True):
        """
        Load the settings from a file

        Parameters
        ^^^^^^^^^^
        fileName (string)
        - if "", find the last previously saved settings file under ~/.fusion-instruments/apdcam/XXX/ where XXX is the CC card's serial number.
        - Otherwise the filename to open

        ask (bool)
          Require to ask the user via a file dialog. If false, the user is asked via a file dialog to choose the file, using
          the provided file name as the default (or the eventually automatically found last settings file, if it exists)

        """

        # if fileName is "auto", get the last saved file for this camera
        if fileName == "":
            fileName = self.cameraLastSettingsFileName()
            # If no last settings is found, set fileName to None so that the next block asks
            # for the filename interactively
            if fileName == "":
                ask = True
                self.showMessage("No previous settings file is found in " + self.cameraSettingsDirName())
                fileName = self.cameraSettingsDirName()

        # If fileName is None, pop up a dialog and ask the user
        if ask:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Save settings",fileName,"Text Files (*.txt);;All Files (*)", options=options)
            if fileName == "":
                return

        error = loadSettings(self,fileName)
        if error != "":
            self.showError(error)
        else:
            self.showMessage("Settings have been loaded from " + fileName)

    def saveSettings(self,fileName = "", ask=True):
        '''
        Save the GUI settings into a file.

        Parameters 
        ^^^^^^^^^^

        fileName (string)
        - If "", save as settingsDir/serialnumber/settings_YYYY-MM-DD_HH-MM_SS.txt
        - Otherwise the filename to save to

        ask (bool)
          Require an interactive dialog so that the user can choose
        '''

        if fileName == "":
            fileName = self.cameraSettingsFileName();

        if  ask:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Save settings",fileName,"Text Files (*.txt);;All Files (*)", options=options)
            if fileName == "":
                return

        if fileName == "":
            self.showError("No filename could be determined. Settings are not saved")
            return

        # call the global function which loads the settings for a given widget. Call it for the topmost widget (self)
        error = saveSettings(self,fileName)
        if error != "":
            self.showError(error)
        else:
            self.showMessage("Settings have been saved to " + fileName)


    def initSettingsOnConnect(self):
        fileName = self.cameraLastSettingsFileName()
        if fileName != "" and os.path.exists(fileName):
            reply = QtWidgets.QMessageBox.question(self, 'Yes', 
                                                   "There exists a saved settings file for this camera:\n" + fileName + ".\nDo you want to load it? If you choose No, the actual values from the camera will be used.",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.loadSettings(fileName,False)
                return

        self.loadSettingsFromCamera()
        
    def loadSettingsFromCamera(self):
        if not self.status.connected:
            self.showError("Camera is not connected, can not read settings")
            return

        self.infrastructure.loadSettingsFromCamera()
        self.adcControl.loadSettingsFromCamera()
        self.controlTiming.loadSettingsFromCamera()
        self.cameraTimer.loadSettingsFromCamera()


    def markFunctionlessControls(self):
        children = self.findChildren(QtWidgets.QWidget)
        for child in children:
            if isinstance(child,QtWidgets.QPushButton) or \
               isinstance(child,QtWidgets.QSpinBox) or \
               isinstance(child,QtWidgets.QCheckBox) or \
               isinstance(child,QtWidgets.QComboBox):
                if child.toolTip() == "":
                    child.setStyleSheet("background-color: red")
            if isinstance(child,QtWidgets.QLineEdit):
                withinSpinBox = False
                for child2 in children:
                    if (isinstance(child2,QtWidgets.QSpinBox) or isinstance(child2,QtWidgets.QDoubleSpinBox)) and child2.isAncestorOf(child):
                        withinSpinBox = True
                        break
                if not withinSpinBox and child.toolTip() == "":
                    child.setStyleSheet("background-color: red")


    def showMessageWithTime(self,msg):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = time + " - " + msg
        if hasattr(self,"messages"):
            self.messages.append(msg)
        else:
            if hasattr(self,"early_messages"):
                self.early_messages += "\n" + msg
            else:
                self.early_messages = msg
            
        if self.logfile != None:
            self.logfile.write(msg + "\n")
            self.logfile.flush()

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

class ApdcamGuiApp(QtWidgets.QApplication):
    def __init__(self):
        super(ApdcamGuiApp,self).__init__(sys.argv)
        self.window = ApdcamGui()
        self.exec()

    def run(self):
        self.exec()

    

        
if __name__ == '__main__':
    app = ApdcamGuiApp()
    #sys.stderr.write = app.showError
    #sys.stdout.write = app.showMessage
    app.run()
