from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

class QHGroupBox(QGroupBox):
    def __init__(self,title=""):
        super(QHGroupBox,self).__init__(title)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def addWidget(self,w):
        self.layout.addWidget(w)

#    def addWidget(self,w,alignment):
#        self.layout.addWidget(w,alignment=alignment)

    def addLayout(self,l):
        self.layout.addLayout(l)

    def addStretch(self,s):
        self.layout.addStretch(s)


class QVGroupBox(QGroupBox):
    def __init__(self,title=""):
        super(QVGroupBox,self).__init__(title)
        self.layout = QVBoxLayout()
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

class QGridGroupBox(QGroupBox):
    def __init__(self,title=""):
        super(QGridGroupBox,self).__init__(title)
        self.layout = QGridLayout()
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

class QDoubleEdit(QLineEdit):
    def __init__(self,min=None,max=None):
        super(QDoubleEdit,self).__init__()
        #self.setMaximumWidth(60)
        validator = QDoubleValidator()
        if not min is None:
            validator.setBottom(min)
        if not max is None:
            validator.setTop(max)
        self.setValidator(validator)

class Empty:
    pass
