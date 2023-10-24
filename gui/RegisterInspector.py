import sys
from functools import partial

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from ApdcamUtils import *
from GuiMode import *

class RegisterInspector(QtWidgets.QWidget):
    def __init__(self,parent,gui):
        self.gui = gui
        super(RegisterInspector,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addStretch(1)

        l1 = QtWidgets.QHBoxLayout()
        layout.addLayout(l1)

        self.cardSelector = QtWidgets.QComboBox()
        # if you change these labels, update the function getRegister!
        self.cardSelector.addItem("Choose card")
        self.cardSelector.addItem("ADC1")
        self.cardSelector.addItem("ADC2")
        self.cardSelector.addItem("ADC3")
        self.cardSelector.addItem("ADC4")
        self.cardSelector.addItem("Power and control card (PC)")
        self.cardSelector.addItem("Communication Card (CC) settings")
        self.cardSelector.addItem("Communication Card (CC) variables")
        self.cardSelector.insertSeparator(1)
        l1.addWidget(self.cardSelector)

        l1.addStretch(1)
        l1.addWidget(QtWidgets.QLabel("Register:"))
        self.register = QtWidgets.QLineEdit()
        self.register.setToolTip("Specify the register address (either decimal or hex format), according to the tables in \"APDCAM-10G user's guide\"!")
        self.register.returnPressed.connect(self.getRegister)
        l1.addWidget(self.register)

        l1.addStretch(1)
        l1.addWidget(QtWidgets.QLabel("Number of bytes:"))
        self.numberOfBytes = QtWidgets.QSpinBox()
        self.numberOfBytes.setMinimum(1)
        self.numberOfBytes.setFixedWidth(150)
        self.numberOfBytes.lineEdit().returnPressed.connect(self.getRegister)
        l1.addWidget(self.numberOfBytes)

        l1.addStretch(1)
        self.endian = QtWidgets.QComboBox()
        self.endian.addItem("LSB")
        self.endian.addItem("MSB")
        l1.addWidget(self.endian)

        l1.addStretch(1)
        self.getRegisterButton = QtWidgets.QPushButton("Get register")
        l1.addWidget(self.getRegisterButton)
        self.getRegisterButton.clicked.connect(self.getRegister)

        l1.addStretch(20)

        l2 = QtWidgets.QGridLayout()
        layout.addLayout(l2)

        l2.addWidget(QtWidgets.QLabel("Bytes:"),0,0)
        self.registerValueBytes = QtWidgets.QLineEdit()
        readOnly(self.registerValueBytes)
        l2.addWidget(self.registerValueBytes,0,1)

        l2.addWidget(QtWidgets.QLabel("Bytes (binary):"),1,0)
        self.registerValueBytesBinary = QtWidgets.QLineEdit()
        readOnly(self.registerValueBytesBinary)
        l2.addWidget(self.registerValueBytesBinary,1,1)

        l2.addWidget(QtWidgets.QLabel("Integer value:"),2,0)
        self.registerValueInt = QtWidgets.QLineEdit()
        self.registerValueInt.setFixedWidth(150)
        readOnly(self.registerValueInt)
        l2.addWidget(self.registerValueInt,2,1)

        l2.addWidget(QtWidgets.QLabel("As string: "),3,0)
        self.registerValueAsString = QtWidgets.QLineEdit()
        readOnly(self.registerValueAsString)
        l2.addWidget(self.registerValueAsString,3,1)

        #l2.setColumnStretch(l2.columnCount(),1)

        layout.addStretch(10)


    def getRegister(self):
        reg_address = self.register.text()
        try:
            if reg_address.find("0x") == 0:
                reg_address = int(reg_address,16)
            else:
                reg_address = int(reg_address,10)
        except:
            self.gui.show_error("Register address can not be interpreted (must be an integer in either hex or dec format)")
            return
            
        n = self.numberOfBytes.value()

        data = None
        card = self.cardSelector.currentText()
        if card.find("ADC") == 0 or card == "Power and control card (PC)":
            card_address = 0
            if card == "ADC1":
                card_address = self.gui.camera.status.ADC_address[0]
            elif card == "ADC2":
                card_address = self.gui.camera.status.ADC_address[1]
            elif card == "ADC3":
                card_address = self.gui.camera.status.ADC_address[2]
            elif card == "ADC4":
                card_address = self.gui.camera.status.ADC_address[3]
            else:
                card_address = 2

            err,d = self.gui.camera.readPDI(card_address,reg_address,n,arrayData=True)
            if err != "":
                self.gui.show_error(err)
                return
            data = d[0]

        elif card == "Communication Card (CC) settings":
            self.gui.camera.readCCdata(dataType=0)
            data = self.gui.camera.status.CC_settings[reg_address-2:reg_address-2+n] # CC_settings stores the registers starting at offset 2, so we need to subtract i
        elif card == "Communication Card (CC) variables":
            self.gui.camera.readCCdata(dataType=1)
            data = self.gui.camera.status.CC_variables[reg_address:reg_address+n]
        else:
            self.gui.show_warning("Please choose a card")
            return
            

        t_int = ""
        t_bin = ""
        for i in range(self.numberOfBytes.value()):
            if i>0:
                t_int += " "
                t_bin += " "
            t_int += str(data[i])
            t_bin += bin(data[i])[2:].zfill(8)
        self.registerValueBytes.setText(t_int)
        self.registerValueBytesBinary.setText(t_bin)
        self.registerValueInt.setText(str(int.from_bytes(data,'little' if self.endian.currentText()=="LSB" else 'big')))

        self.registerValueAsString.setText("")
        try:
            self.registerValueAsString.setText(data.decode())
        except:
            self.registerValueAsString.setText("-- Failed to convert --")

        # font = QtGui.QFont("", 0)
        # fm = QtGui.QFontMetrics(font)
        # pixelsWide = fm.width(self.registerValueBytes.text())
        # self.registerValueBytes.setFixedWidth(int(pixelsWide*1.1+20))
        # pixelsWide = fm.width(self.registerValueBytesBinary.text())
        # self.registerValueBytesBinary.setFixedWidth(int(pixelsWide*1.1+20))
        # pixelsWide = fm.width(self.registerValueInt.text())
        # self.registerValueInt.setFixedWidth(int(pixelsWide*1.1+20))
        # pixelsWide = fm.width(self.registerValueAsString.text())
        # self.registerValueAsString.setFixedWidth(int(pixelsWide*1.1+20))
