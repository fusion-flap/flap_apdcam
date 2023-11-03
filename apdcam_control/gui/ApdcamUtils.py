import configparser
import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")
Qt = QtCore.Qt

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
#from PyQt6.QtCore import Qt
#from PyQt6.QtGui import QDoubleValidator




def readOnly(c):
    style = """
    QCheckBox, QLineEdit, QDoubleSpinBox, QSpinBox {
      background-color: rgb(245,252,245)
    }
    QToolTip {
      background-color: black;
    }
    """
#    style = "background-color: rgb(245,252,245)"
    if isinstance(c,QtWidgets.QCheckBox):
        c.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        c.setStyleSheet(style)
        c.setFocusPolicy(Qt.NoFocus)
    elif isinstance(c,QtWidgets.QLineEdit):
        c.setReadOnly(True)
        c.setStyleSheet(style)
        c.setFocusPolicy(Qt.NoFocus)
    elif isinstance(c,QtWidgets.QDoubleSpinBox):
        c.setReadOnly(True)
        c.setStyleSheet(style)
        c.setFocusPolicy(Qt.NoFocus)
    elif isinstance(c,QtWidgets.QSpinBox):
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
