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

class Debug(QtWidgets.QWidget):
    def __init__(self,parent):
        self.gui = parent
        super(Debug,self).__init__(parent)
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

        l2 = QtWidgets.QHBoxLayout()
        layout.addLayout(l2)

        l2.addWidget(QtWidgets.QLabel("Bytes:"))
        self.registerValueBytes = QtWidgets.QLineEdit()
        readOnly(self.registerValueBytes)
        l2.addWidget(self.registerValueBytes)

        l2.addStretch(1)
        l2.addWidget(QtWidgets.QLabel("Bytes (binary):"))
        self.registerValueBytesBinary = QtWidgets.QLineEdit()
        readOnly(self.registerValueBytesBinary)
        l2.addWidget(self.registerValueBytesBinary)

        l2.addStretch(1)
        l2.addWidget(QtWidgets.QLabel("Integer value:"))
        self.registerValueInt = QtWidgets.QLineEdit()
        readOnly(self.registerValueInt)
        l2.addWidget(self.registerValueInt)

        l2.addStretch(20)

        layout.addStretch(10)


    def getRegister(self):
        reg_address = self.register.text()
        try:
            if reg_address.find("0x") == 0:
                reg_address = int(reg_address,16)
            else:
                reg_address = int(reg_address,10)
        except:
            self.gui.showError("Register address can not be interpreted (must be an integer in either hex or dec format)")
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
                self.gui.showError(err)
                return
            data = d[0]

        elif card == "Communication Card (CC) settings":
            self.gui.camera.readCCdata(dataType=0)
            data = self.gui.camera.status.CC_settings[reg_address-2:reg_address-2+n] # CC_settings stores the registers starting at offset 2, so we need to subtract i
        elif card == "Communication Card (CC) variables":
            self.gui.camera.readCCdata(dataType=1)
            data = self.gui.camera.status.CC_variables[reg_address:reg_address+n]
        else:
            self.gui.showWarning("Please choose a card")
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


        font = QtGui.QFont("", 0)
        fm = QtGui.QFontMetrics(font)
        pixelsWide = fm.width(self.registerValueBytes.text());
        self.registerValueBytes.setFixedWidth(pixelsWide+10);
        pixelsWide = fm.width(self.registerValueBytesBinary.text());
        self.registerValueBytesBinary.setFixedWidth(pixelsWide+10);
        pixelsWide = fm.width(self.registerValueInt.text());
        self.registerValueInt.setFixedWidth(pixelsWide+10);
