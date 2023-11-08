import sys
from functools import partial

import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

#from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QTextEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
#from PyQt6.QtCore import Qt
from .ApdcamUtils import *
from .GuiMode import *
from ..APDCAM10G_control import *


class RegisterInspector(QtWidgets.QWidget):
    def __init__(self,parent,gui):
        self.gui = gui
        super(RegisterInspector,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        #layout.addStretch(1)

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

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        self.showADC1RegistersButton = QtWidgets.QPushButton("ADC1 registers")
        buttons.addWidget(self.showADC1RegistersButton)
        self.showADC1RegistersButton.clicked.connect(lambda: self.showAdcRegisterTable(1))
        self.showADC2RegistersButton = QtWidgets.QPushButton("ADC2 registers")
        buttons.addWidget(self.showADC2RegistersButton)
        self.showADC2RegistersButton.clicked.connect(lambda: self.showAdcRegisterTable(2))
        self.showADC3RegistersButton = QtWidgets.QPushButton("ADC3 registers")
        buttons.addWidget(self.showADC3RegistersButton)
        self.showADC3RegistersButton.clicked.connect(lambda: self.showAdcRegisterTable(3))
        self.showADC4RegistersButton = QtWidgets.QPushButton("ADC4 registers")
        buttons.addWidget(self.showADC4RegistersButton)
        self.showADC4RegistersButton.clicked.connect(lambda: self.showAdcRegisterTable(4))
        self.showCCSettingsButton = QtWidgets.QPushButton("CC settings")
        buttons.addWidget(self.showCCSettingsButton)
        self.showCCSettingsButton.clicked.connect(self.showCCSettingsTable)
        self.showCCVariablesButton = QtWidgets.QPushButton("CC variables")
        buttons.addWidget(self.showCCVariablesButton)
        self.showCCVariablesButton.clicked.connect(self.showCCVariablesTable)

        self.registerTable = QtWidgets.QScrollArea()
        layout.addWidget(self.registerTable)
        self.registerTable.setWidgetResizable(True)
        self.registerTableWidget = QtWidgets.QWidget()
        self.registerTable.setWidget(self.registerTableWidget)
        self.registerTableLayout = QtWidgets.QGridLayout()
        self.registerTableLayout.setContentsMargins(0,0,0,0)
        self.registerTableLayout.setSpacing(0)
        self.registerTableWidget.setLayout(self.registerTableLayout)
        #layout.addStretch(10)

    def showAdcRegisterTable(self,adcNumber):

        adcNumber -= 1

        err,d = self.gui.camera.readPDI(self.gui.camera.status.ADC_address[adcNumber],0,numberOfBytes=266,arrayData=True)
        register_table = self.gui.camera.ADC_register_table

        # err = ""
        # d = bytearray(266)
        # for i in range(266):
        #     d[i] = i%256
        # d = [d]
        # register_table = APDCAM10G_adc_register_table_v1()
            
        if err != "":
            self.gui.show_error(err)
        else:
            self.showRegisterTable(register_table,d[0])

    def showCCSettingsTable(self):

        err= self.gui.camera.readCCdata(dataType=0)
        register_table = self.gui.camera.CC_settings_table

        if err != "":
            self.gui.show_error(err)
        else:
            self.showRegisterTable(register_table,self.gui.camera.status.CC_settings)
            
    def showCCVariablesTable(self):

        err= self.gui.camera.readCCdata(dataType=1)
        register_table = self.gui.camera.CC_variables_table

        if err != "":
            self.gui.show_error(err)
        else:
            self.showRegisterTable(register_table,self.gui.camera.status.CC_settings)
            

    def showRegisterTable(self,regtable,data):
        # Clear the regtable layout
        for i in reversed(range(self.registerTableLayout.count())):
            self.registerTableLayout.itemAt(i).widget().deleteLater()
            self.registerTableLayout.itemAt(i).widget().setParent(None)

        def addHeader(layout,text,cell):
            w = QtWidgets.QLabel(text)
            w.setStyleSheet("font-weight:bold")
            layout.addWidget(w,0,cell)
        addHeader(self.registerTableLayout,"Symbol",0)
        addHeader(self.registerTableLayout,"Address",1)
        addHeader(self.registerTableLayout,"Num. bytes",2)
        addHeader(self.registerTableLayout,"Description",3)
        addHeader(self.registerTableLayout,"Value(s)",4)

        # collect register names (symbols) and their addresses in two parallel arrays for sorting
        # (because 'dir' is in alphabetic order, and we want to list in the order of address)
        regnames = []
        addresses = []
        for regname in dir(regtable):
            # skip attributes starting with _ or not being fully uppercase
            if regname.startswith("_") or regname.upper() != regname:
                continue
            regnames.append(regname)
            r = getattr(regtable,regname)
            addresses.append(r.startByte)
            
        style = """
        QCheckBox, QLineEdit, QDoubleSpinBox, QSpinBox, QLabel, QFrame {
        background-color: rgb(242,242,242)
        }
        QToolTip {
        background-color: black;
        }
        """


        line = 1
        for aaa in sorted(zip(addresses,regnames)):
            regname = aaa[1]

            lll = QtWidgets.QLabel(regname)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,0)

            reg = getattr(regtable,regname)

            tmp = str(reg.startByte)
            try:
                tmp = regtable.addressDisplay(reg.startByte)
            except:
                pass
            lll = QtWidgets.QLabel(tmp)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,1)

            lll = QtWidgets.QLabel(str(reg.numberOfBytes))
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,2)

            lll = QtWidgets.QLabel(str(reg.description))
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,3)

            lll = QtWidgets.QFrame()
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            values = reg.value(data)
            lll.setLayout(QtWidgets.QVBoxLayout())
            self.registerTableLayout.addWidget(lll,line,4)
            lineindex=0
            for value_line in values:
                hhh = QtWidgets.QHBoxLayout()
                lll.layout().addLayout(hhh)
                if len(values) > 1:
                    hhh.addWidget(QtWidgets.QLabel(str(lineindex) + " - "))
                for v in value_line:
                    if v[1] != "":
                        label = QtWidgets.QLabel(v[1] + ":")
                        if v[2] != "":
                            label.setToolTip(v[2])
                        hhh.addWidget(label)
                    value = QtWidgets.QLabel(str(v[0]))
                    if v[2] != "":
                        value.setToolTip(v[2])
                    hhh.addWidget(value)
                    hhh.addStretch(1)
                hhh.addStretch(2)
                lineindex += 1

            line += 1

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
