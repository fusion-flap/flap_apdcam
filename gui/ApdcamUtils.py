import configparser
import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")
Qt = QtCore.Qt

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt
#from PyQt6.QtGui import QDoubleValidator


def saveSettings(widget, file, indent=0):
    '''
    Scan recursively all control inputs within the given widget (typically a tab). Skip those, which do not have a 'saveName' attribute.
    Save the value into the given file as saveName=value lines.
    indent is the level of indentation
    '''
    # loop over all controls within this tab
    controls = widget.findChildren(QtWidgets.QWidget)
    for control in controls:
        # skip those without the saveName attribute
        if not hasattr(control,"saveName"):
            continue
        for i in range(indent):
            f.write("  ")
        file.write(control.saveName + "=" )
        if isinstance(control,QtWidgets.QSpinBox) or isinstance(control,QtWidgets.QDoubleSpinBox):
            file.write(str(control.value()))
        elif isinstance(control,QtWidgets.QLineEdit):
            file.write(control.text() + "\n")
        elif isinstance(control,QtWidgets.QCheckBox):
            file.write("true" if control.isChecked() else "false")
        elif isinstance(control,QtWidgets.QComboBox):
            file.write(control.currentText())
        file.write("\n")
    file.flush()

def loadSettings(widget, fileName, sectionName):
    settings = configparser.ConfigParser()
    settings.read(fileName)
    if not sectionName in settings:
        return "Section '" + sectionName +"' is not found in the config file '" + fileName + "'";
    s = settings[sectionName]

    error = ""

    controls = widget.findChildren(QtWidgets.QWidget)
    for control in controls:
        # skip those without the saveName attribute
        if not hasattr(control,"saveName"):
            continue

        # skip this control if its value is not in the config file
        if not control.saveName in s:
            continue

        if isinstance(control,QtWidgets.QSpinBox):
            control.setValue(int(s[control.saveName]))
        elif isinstance(control,QtWidgets.QDoubleSpinBox):
            control.setValue(float(s[control.saveName]))
        elif isinstance(control,QtWidgets.QLineEdit):
            control.setText(s[control.saveName])
        elif isinstance(control,QtWidgets.QCheckBox):
            if s[control.saveName].lower() == "yes" or s[control.saveName].lower() == "true" or s[control.saveName] == "1":
                control.setChecked(True)
            else:
                control.setChecked(False)
        elif isinstance(control,QtWidgets.QComboBox):
            if control.findText(s[control.saveName]) >= 0:
                control.setCurrentText(s[control.saveName])
            else:
                error += "Bad value (" + s[control.saveName] + ") for the variable '" + control.saveName + "' in section [" + sectionName + "] of the settings file '" + fileName + "'\n"
    return error
    

def readOnly(c):
    style = "background-color: rgb(245,252,245)"
    if isinstance(c,QtWidgets.QCheckBox):
        c.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        c.setStyleSheet(style)
        c.setFocusPolicy(Qt.NoFocus)
    if isinstance(c,QtWidgets.QLineEdit):
        c.setReadOnly(True)
        c.setStyleSheet(style)
        c.setFocusPolicy(Qt.NoFocus)
        

class QCheckBoxIndicator(QtWidgets.QCheckBox):
    def __init__(self,title):
        super(QCheckBoxIndicator,self).__init__(title)
        


class QHGroupBox(QtWidgets.QGroupBox):
    def __init__(self,title=""):
        super(QHGroupBox,self).__init__(title)
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

    def addWidget(self,w):
        self.layout.addWidget(w)

#    def addWidget(self,w,alignment):
#        self.layout.addWidget(w,alignment=alignment)

    def addLayout(self,l):
        self.layout.addLayout(l)

    def addStretch(self,s):
        self.layout.addStretch(s)


class QVGroupBox(QtWidgets.QGroupBox):
    def __init__(self,title=""):
        super(QVGroupBox,self).__init__(title)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

#    def addWidget(self,w):
#        self.layout.addWidget(w)

    def addWidget(self,w,alignment=None):
        if alignment is None:
            self.layout.addWidget(w)
        else:
            self.layout.addWidget(w,alignment=alignment)
        
    def addLayout(self,l):
        self.layout.addLayout(l)

    def addStretch(self,s):
        self.layout.addStretch(s)

class QGridGroupBox(QtWidgets.QGroupBox):
    def __init__(self,title=""):
        super(QGridGroupBox,self).__init__(title)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

#    def addWidget(self,w,row,col):
#        self.layout.addWidget(w,row,col)

    def addWidget(self,w,row,col,rowspan=1,colspan=1):
        self.layout.addWidget(w,row,col,rowspan,colspan)
        
#    def addLayout(self,l,row,col):
#        self.layout.addLayout(l,row,col)

    def addLayout(self,l,row,col,rowspan=1,colspan=1):
        self.layout.addLayout(l,row,col,rowspan,colspan)

    def setRowStretch(self,rownum,stretch):
        self.layout.setRowStretch(rownum,stretch)

    def rowCount(self):
        return self.layout.rowCount()

# class QDoubleEdit(QtWidgets.QLineEdit):
#     def __init__(self,min=None,max=None):
#         super(QDoubleEdit,self).__init__()
#         self.validator = QtGui.QDoubleValidator()
#         if not min is None:
#             self.validator.setBottom(min)
#         if not max is None:
#             self.validator.setTop(max)
#         self.setValidator(self.validator)
        
#     def value(self):
#         return float(text())
#     def setMinimum(self,v):
#         self.validator.setBottom(v)
#     def setMaximum(self,v):
#         self.validator.setTop(v)

# class QIntEdit(QtWidgets.QLineEdit):
#     def __init__(self,min=None,max=None):
#         super(QIntEdit,self).__init__()
#         #self.setMaximumWidth(60)
#         validator = QtGui.QIntValidator()
#         if not min is None:
#             validator.setBottom(min)
#         if not max is None:
#             validator.setTop(max)
#         self.setValidator(validator)

class Empty:
    pass
