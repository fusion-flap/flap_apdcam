import sys
from functools import partial
import re

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
    class RegisterSearch:

        def __init__(self,pattern,regexp=False,name=True,description=True,tooltip=True):
            """
            Parameters:
            ^^^^^^^^^^^
            pattern       - a regular expression string
            regexp        - (bool): treat 'pattern' as a regular expression
            name          - (bool): search in register name
            descritiption - (bool): search in description
            tooltip       - (bool): search in tooltip
            """
            self.pattern = pattern
            self.regexp = regexp
            self.searchRegisterName = name
            self.searchDescription = description
            self.searchTooltip = tooltip

        def __call__(self,register):

            regexp = None
            if self.regexp:
                regexp = re.compile(self.pattern)

            if self.searchRegisterName:
                if self.regexp and regexp.search(register.symbol) is not None:
                    return True
                if not self.regexp and register.symbol.lower().find(self.pattern.lower()) >= 0:
                    return True

            if self.searchDescription:
                if self.regexp and regexp.search(register.description) is not None:
                    return True
                if not self.regexp and register.description.lower().find(self.pattern.lower()) >= 0:
                    return True

            if self.searchTooltip:
                if self.regexp and regexp.search(register.tooltip) is not None:
                    return True
                if not self.regexp and register.tooltip.lower().find(self.pattern.lower()) >= 0:
                    return True

            if type(register.interpreter) == APDCAM10G_register2bits:
                for b in register.interpreter.bits:
                    if self.searchDescription:
                        if self.regexp and regexp.search(b.shortName) is not None:
                            return True
                        if not self.regexp and b.shortName.lower().find(self.pattern.lower()) > 0:
                            return True
                    if self.searchTooltip:
                        if self.regexp and regexp.search(b.description) is not None:
                            return True
                        if not self.regexp and b.description.lower().find(self.pattern.lower()) > 0:
                            return True
                
            return False

    def __init__(self,parent,gui):
        self.gui = gui
        super(RegisterInspector,self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        #layout.addStretch(1)


        searchLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(searchLayout)

        searchLayout.addWidget(QtWidgets.QLabel("Pattern:"))

        self.searchPattern = QtWidgets.QLineEdit()
        searchLayout.addWidget(self.searchPattern)
        self.searchPattern.setToolTip("Search string or regular expression")
        self.searchPattern.returnPressed.connect(self.showRegisterSearch)

        self.searchRegexp = QtWidgets.QCheckBox("Regular expression")
        searchLayout.addWidget(self.searchRegexp)

        self.searchName = QtWidgets.QCheckBox("Search register names")
        self.searchName.setChecked(True)
        searchLayout.addWidget(self.searchName)

        self.searchDescription = QtWidgets.QCheckBox("Search descriptions")
        self.searchDescription.setChecked(True)
        searchLayout.addWidget(self.searchDescription)

        self.searchTooltip = QtWidgets.QCheckBox("Search tooltips")
        self.searchTooltip.setChecked(True)
        searchLayout.addWidget(self.searchTooltip)

        self.searchButton = QtWidgets.QPushButton("Search registers")
        searchLayout.addWidget(self.searchButton)
        self.searchButton.clicked.connect(self.showRegisterSearch)

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        
        self.registerVersionSelector = QtWidgets.QComboBox()
        self.registerVersionSelector.addItem("Actual camera")
        self.registerVersionSelector.addItem("Firmware <=1.03 (zero data)")
        self.registerVersionSelector.addItem("Firmware >=1.05 (zero data)")
        buttons.addWidget(self.registerVersionSelector)

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
        self.showPCRegistersButton = QtWidgets.QPushButton("PC registers")
        buttons.addWidget(self.showPCRegistersButton)
        self.showPCRegistersButton.clicked.connect(self.showPcRegisterTable)
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

    def showRegisterSearch(self):
        #self.gui.camera.ADC_register_table = APDCAM10G_adc_registers_v1()
        #self.gui.camera.CC_settings_table  = APDCAM10G_cc_settings_v1()
        #self.gui.camera.CC_variables_table = APDCAM10G_cc_variables_v1()
        #self.gui.camera.PC_register_table  = APDCAM10G_pc_registers_v1()

        pattern = self.searchPattern.text()
        regexp = self.searchRegexp.isChecked()
        name = self.searchName.isChecked()
        description = self.searchDescription.isChecked()
        tooltip = self.searchTooltip.isChecked()

        self.clearRegisterTableDisplay()

        found = False

        register_table = self.gui.camera.ADC_register_table.filter(self.RegisterSearch(pattern=pattern,regexp=regexp,name=name,description=description,tooltip=tooltip))
        nbytes = register_table.size()
        if nbytes > 0:
            found = True
            for i_adc in range(len(self.gui.camera.status.ADC_address)):
                adc_address = self.gui.camera.status.ADC_address[i_adc]
                err,d = self.gui.camera.readPDI(adc_address,0,numberOfBytes=nbytes,arrayData=True)
                #err = ''
                #d = [bytearray(nbytes)]
                if err != "":
                    self.gui.show_error(err)
                else:
                    self.showRegisterTable(register_table,d[0],title='ADC ' + str(i_adc+1) + ' registers',clear=False)

        register_table = self.gui.camera.PC_register_table.filter(self.RegisterSearch(pattern=pattern,regexp=regexp,name=name,description=description,tooltip=tooltip))
        nbytes = register_table.size()
        if nbytes > 0:
            found = True
            err,d = self.gui.camera.readPDI(self.gui.camera.codes_PC.PC_CARD,0,numberOfBytes=nbytes,arrayData=True)
            #err = ''
            #d = [bytearray(nbytes)]
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,d[0],title='PC card registers',clear=False)

        register_table = self.gui.camera.CC_settings_table.filter(self.RegisterSearch(pattern=pattern,regexp=regexp,name=name,description=description,tooltip=tooltip))
        nbytes = register_table.size()
        if nbytes > 0:
            found = True
            err= self.gui.camera.readCCdata(dataType=0)
            #err = ''
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,self.gui.camera.status.CC_settings,title='Communication & Control Card settings',clear=False)

        register_table = self.gui.camera.CC_variables_table.filter(self.RegisterSearch(pattern=pattern,regexp=regexp,name=name,description=description,tooltip=tooltip))
        nbytes = register_table.size()
        if nbytes > 0:
            found = True
            err= self.gui.camera.readCCdata(dataType=1)
            #err = ''
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,self.gui.camera.status.CC_settings,title='Communication & Control Card variables',clear=False)

        if not found:
            self.registerTableLayout.addWidget(QtWidgets.QLabel("No matches found"),self.registerTableLayout.rowCount(),0,1,5)


    def showAdcRegisterTable(self,adcNumber):

        adcNumber -= 1
        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.ADC_register_table
            err,d = self.gui.camera.readPDI(self.gui.camera.status.ADC_address[adcNumber],0,numberOfBytes=register_table.size(),arrayData=True)
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,d[0])
        elif v=="Firmware <=1.03":
            register_table = APDCAM10G_adc_registers_v1()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        elif v=="Firmware >=1.05":
            register_table = APDCAM10G_adc_registers_v2()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        else:
            self.gui.show_error("Invalid register version selector (this should never happen)")

    def showPcRegisterTable(self):

        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.PC_register_table
            err,d = self.gui.camera.readPDI(self.gui.camera.codes_PC.PC_CARD,0,numberOfBytes=register_table.size(),arrayData=True)
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,d[0])
        elif v=="Firmware <=1.03":
            register_table = APDCAM10G_pc_registers_v1()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        elif v=="Firmware >=1.05":
            register_table = APDCAM10G_pc_registers_v2()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        else:
            self.gui.show_error("Invalid register version selector (this should never happen)")
            

    def showCCSettingsTable(self):

        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.CC_settings_table
            err= self.gui.camera.readCCdata(dataType=0)
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,self.gui.camera.status.CC_settings)
        elif v=="Firmware <=1.03":
            register_table = APDCAM10G_cc_settings_v1()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        elif v=="Firmware >=1.05":
            register_table = APDCAM10G_cc_settings_v2()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        else:
            self.gui.show_error("Invalid register version selector (this should never happen)")
            
    def showCCVariablesTable(self):

        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            err= self.gui.camera.readCCdata(dataType=1)
            register_table = self.gui.camera.CC_variables_table
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,self.gui.camera.status.CC_settings)
        elif v=="Firmware <=1.03":
            register_table = APDCAM10G_cc_variables_v1()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        elif v=="Firmware >=1.05":
            register_table = APDCAM10G_cc_variables_v2()
            data = bytearray(register_table.size())
            self.showRegisterTable(register_table,data)
        else:
            self.gui.show_error("Invalid register version selector (this should never happen)")
            
    def clearRegisterTableDisplay(self):
        # Clear the regtable layout
        for i in reversed(range(self.registerTableLayout.count())):
            self.registerTableLayout.itemAt(i).widget().deleteLater()
            self.registerTableLayout.itemAt(i).widget().setParent(None)

        def addHeader(layout,text,cell):
            w = QtWidgets.QLabel(text)
            w.setStyleSheet("font-weight:bold; padding-left: 3px; padding-right: 3px; background-color: rgb(180,180,220); ")
            w.setLineWidth(1)
            layout.addWidget(w,0,cell)
        addHeader(self.registerTableLayout,"Symbol",0)
        addHeader(self.registerTableLayout,"Address",1)
        addHeader(self.registerTableLayout,"Num. bytes",2)
        addHeader(self.registerTableLayout,"Byte order",3)
        addHeader(self.registerTableLayout,"Description",4)
        addHeader(self.registerTableLayout,"Value(s)",5)

    def showRegisterTable(self,regtable,data,title='',clear=True):
        """
        Show a register table 'regtable', evaluated on the byte array 'data', in the register table display area of the GUI.
        """

        if clear:
            self.clearRegisterTableDisplay()
            
        style = """
        QCheckBox, QLineEdit, QDoubleSpinBox, QSpinBox, QLabel, QFrame {
        background-color: rgb(242,242,242)
        }
        QToolTip {
        background-color: black;
        }
        """

        styleTitle = """
        QCheckBox, QLineEdit, QDoubleSpinBox, QSpinBox, QLabel, QFrame {
        background-color: rgb(220,220,240);
        font-weight: bold;
        }
        QToolTip {
        background-color: black;
        }
        """
        
        line = self.registerTableLayout.rowCount()

        if title != '':
            t = QtWidgets.QLabel(title)
            t.setStyleSheet(styleTitle)
            t.setLineWidth(1)
            self.registerTableLayout.addWidget(t,line,0,1,6)
            line += 1

        registerNames = regtable.registerNames()
        for registerName in registerNames:

            lll = QtWidgets.QLabel(registerName)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,0)

            reg = getattr(regtable,registerName)

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

            byteorder = ('MSB' if reg.byteOrder=='big' else 'LSB')
            if reg.byteOrderUncertain:
                byteorder += " (???)"
            lll = QtWidgets.QLabel(byteorder)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if reg.byteOrderUncertain:
                lll.setStyleSheet("QLabel { color: red; }")
            self.registerTableLayout.addWidget(lll,line,3)

            lll = QtWidgets.QLabel(str(reg.shortDescription + (' (see tooltip)' if reg.longDescription!='' else '')))
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            if reg.longDescription != '':
                lll.setToolTip(reg.longDescription)
            self.registerTableLayout.addWidget(lll,line,4)

            lll = QtWidgets.QFrame()
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            hhh = QtWidgets.QHBoxLayout()
            lll.setLayout(hhh)
            self.registerTableLayout.addWidget(lll,line,5)

            # for bit-coded registers, loop over all bit group, and display them one-by-one
            if hasattr(reg,'sortedBits'):
                counter = 0
                for b in reg.sortedBits:
                    s = b.symbol + "(" + str(b.firstBit)
                    if b.lastBit > b.firstBit:
                        s += ".." + str(b.lastBit)
                    s += "):"
                    symbol = QtWidgets.QLabel(s)
                    symbol.setToolTip(b.description)
                    hhh.addWidget(symbol)

                    hhh.addWidget(QtWidgets.QLabel(b.display_value(data)))

                    if counter>0:
                        hhh.addStretch(1)
                    counter += 1
            else:
                hhh.addWidget(QtWidgets.QLabel(reg.display_value(data)))

            hhh.addStretch(2)

            line += 1
