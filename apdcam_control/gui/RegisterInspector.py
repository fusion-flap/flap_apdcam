import sys
import os
from functools import partial
import re
import html

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

        def __init__(self,pattern,regexp=False,name=True,shortDescription=True,longDescription=True):
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
            self.searchShortDescription = shortDescription
            self.searchLongDescription = longDescription

        def __call__(self,register):

            #print("-----")
            #print("symbol: " + register.symbol)
            #print("shortd: " + str(register.shortDescription))

            regexp = None
            if self.regexp:
                regexp = re.compile(self.pattern)

            if self.searchRegisterName:
                if self.regexp and regexp.search(register.symbol) is not None:
                    return True
                if not self.regexp and register.symbol.lower().find(self.pattern.lower()) >= 0:
                    return True

            if self.searchShortDescription:
                if self.regexp and regexp.search(register.shortDescription) is not None:
                    return True
                if not self.regexp and register.shortDescription.lower().find(self.pattern.lower()) >= 0:
                    return True

            if self.searchLongDescription:
                if self.regexp and regexp.search(register.longDescription) is not None:
                    return True
                if not self.regexp and register.longDescription.lower().find(self.pattern.lower()) >= 0:
                    return True

            if hasattr(register,"sortedBits"):
                for b in register.sortedBits:
                    if self.searchRegisterName:
                        if self.regexp and regexp.search(b.symbol) is not None:
                            return True
                        if not self.regexp and b.symbol.lower().find(self.pattern.lower()) > 0:
                            return True
                    if self.searchLongDescription or self.searchShortDescription:
                        if self.regexp and regexp.search(b.description) is not None:
                            return True
                        if not self.regexp and b.description.lower().find(self.pattern.lower()) > 0:
                            return True
                
            return False

    def __init__(self,parent,gui):
        self.gui = gui
        super(RegisterInspector,self).__init__(parent)

        self.html = ""
        self.defaultExportFileName = "registers.html"
        self.lastExportDir = "."

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

        self.searchShortDescription = QtWidgets.QCheckBox("Search short descriptions")
        self.searchShortDescription.setChecked(True)
        searchLayout.addWidget(self.searchShortDescription)

        self.searchLongDescription = QtWidgets.QCheckBox("Search long descriptions")
        self.searchLongDescription.setChecked(True)
        searchLayout.addWidget(self.searchLongDescription)

        self.searchButton = QtWidgets.QPushButton("Search registers")
        searchLayout.addWidget(self.searchButton)
        self.searchButton.clicked.connect(self.showRegisterSearch)

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        
        self.registerVersionSelector = QtWidgets.QComboBox()
        self.registerVersionSelector.addItem("Actual camera")
        self.registerVersionSelector.addItem("Firmware <=1.03")
        self.registerVersionSelector.addItem("Firmware >=1.05")
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
        self.showAllButton = QtWidgets.QPushButton("ALL")
        buttons.addWidget(self.showAllButton)
        self.showAllButton.clicked.connect(lambda: self.showRegisterSearch(True))
        self.exportButton = QtWidgets.QPushButton("Export")
        buttons.addWidget(self.exportButton)
        self.exportButton.clicked.connect(self.export)

        self.registerTable = QtWidgets.QScrollArea()
        layout.addWidget(self.registerTable)
        self.registerTable.setWidgetResizable(True)
        self.registerTableWidget = QtWidgets.QWidget()
        self.registerTable.setWidget(self.registerTableWidget)
        self.registerTableLayout = QtWidgets.QGridLayout()
        self.registerTableLayout.setContentsMargins(0,0,0,0)
        self.registerTableLayout.setSpacing(0)
        self.registerTableWidget.setLayout(self.registerTableLayout)

    def loadSettingsFromCamera(self):
        n = len(self.gui.camera.status.ADC_address)
        if n<4:
            self.showADC4RegistersButton.setEnabled(False)
        else:
            self.showADC4RegistersButton.setEnabled(True)
        if n<3:
            self.showADC3RegistersButton.setEnabled(False)
        else:
            self.showADC3RegistersButton.setEnabled(True)
        if n<2:
            self.showADC2RegistersButton.setEnabled(False)
        else:
            self.showADC2RegistersButton.setEnabled(True)
        if n<1:
            self.showADC1RegistersButton.setEnabled(False)
        else:
            self.showADC1RegistersButton.setEnabled(True)

    def export(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Export register table to...",\
                                                            self.lastExportDir + os.sep + self.defaultExportFileName,\
                                                            "HTML Files (*.html);;All Files (*)", options=options)
        if fileName == "":
            return

        self.lastExportDir = os.path.dirname(fileName)

        file = open(fileName,"w")
        file.write("<html>\n")
        file.write("  <head>\n")
        file.write("    <style>\n")
        file.write("       table, th, td { border-collapse: collapse; border: 1px solid black; }\n")
        file.write("       th            { background-color: rgb(180,200,255); font-weight: bold; text-align:left; padding:5px; }\n")
        file.write("       td            { margin-right:10px; margin-left:10px; }\n")
        file.write("       tr:nth-child(even) { background-color: rgb(240,240,240); }\n")
        file.write("       .colnames     { position: sticky; top: 0; font-weight: bold; background-color: rgb(140,110,255); }\n")
        file.write("    </style>\n")
        file.write("  </head>\n")
        file.write("<body>\n")
        file.write("  <table style='position:relative'>")
        file.write(self.html)
        file.write("  </table>")
        file.write("</body></html>")
        file.close()

    def showRegisterSearch(self,showAll=False):
        #self.gui.camera.ADC_register_table = APDCAM10G_adc_registers_v1()
        #self.gui.camera.CC_settings_table  = APDCAM10G_cc_settings_v1()
        #self.gui.camera.CC_variables_table = APDCAM10G_cc_variables_v1()
        #self.gui.camera.PC_register_table  = APDCAM10G_pc_registers_v1()

        self.defaultExportFileName = "register-search.html"

        pattern = self.searchPattern.text()
        regexp = self.searchRegexp.isChecked()
        name = self.searchName.isChecked()
        shortDescription = self.searchShortDescription.isChecked()
        longDescription = self.searchLongDescription.isChecked()

        self.clearRegisterTableDisplay()

        found = False

        filter = lambda r: True
        if showAll==False:
            filter = self.RegisterSearch(pattern=pattern,regexp=regexp,name=name,shortDescription=shortDescription,longDescription=longDescription)

        register_table = self.gui.camera.ADC_registers.filter(filter)
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

        register_table = self.gui.camera.PC_registers.filter(filter)
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

        register_table = self.gui.camera.CC_settings.filter(filter)
        nbytes = register_table.size()
        if nbytes > 0:
            found = True
            err= self.gui.camera.readCCdata(dataType=0)
            #err = ''
            if err != "":
                self.gui.show_error(err)
            else:
                self.showRegisterTable(register_table,self.gui.camera.status.CC_settings,title='Communication & Control Card settings',clear=False)

        register_table = self.gui.camera.CC_variables.filter(filter)
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

        self.defaultExportFileName = "adc" + str(adcNumber) + "-registers.html"

        adcNumber -= 1
        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.ADC_registers
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

        self.defaultExportFileName = "pc-registers.html"

        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.PC_registers
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

        self.defaultExportFileName = "CC-settings.html"

        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            register_table = self.gui.camera.CC_settings
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

        self.defaultExportFileName = "CC-variables.html"
        
        v = self.registerVersionSelector.currentText()
        if v=="Actual camera":
            err= self.gui.camera.readCCdata(dataType=1)
            register_table = self.gui.camera.CC_variables
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
        self.html = ""

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

        self.html += "    <tr>\n"
        self.html += "      <th class='colnames'>Symbol</th>"
        self.html += "      <th class='colnames'>Address</th>"
        self.html += "      <th class='colnames'>Num. bytes</th>"
        self.html += "      <th class='colnames'>Byte order</th>"
        self.html += "      <th class='colnames'>Description</th>"
        self.html += "      <th class='colnames'>Value(s)</th>"
        self.html += "    </tr>\n"

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
            self.html += "    <tr><th colspan='6'>" + title + "</th></tr>\n"
            line += 1

        registerNames = regtable.registerNames()

        for registerName in registerNames:

            self.html += "    <tr>"
            lll = QtWidgets.QLabel(registerName)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,0)
            self.html += "<td>" + registerName + "</td>"

            
            reg = None

            # Check if this register name is of the form XXXX[number], indicating that the underlying
            # variable is a list
            match = re.match(r'([a-zA-Z_]+)\[([0-9]+)\]',registerName)
            if match is not None:
                listname = match.group(1)
                index = int(match.group(2))
                lll = getattr(regtable,listname)
                reg = lll[index]
            else:
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
            self.html += "<td>" + tmp + "</td>"

            lll = QtWidgets.QLabel(str(reg.numberOfBytes))
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            self.registerTableLayout.addWidget(lll,line,2)
            self.html += "<td>" + str(reg.numberOfBytes) + "</td>"

            byteorder = ('MSB' if reg.byteOrder=='big' else 'LSB')
            if reg.byteOrderUncertain:
                byteorder += " (???)"
            lll = QtWidgets.QLabel(byteorder)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if reg.byteOrderUncertain:
                lll.setStyleSheet("QLabel { color: red; }")
            self.registerTableLayout.addWidget(lll,line,3)
            self.html += "<td>" + byteorder + "</td>"

            tmp = str(reg.shortDescription + (' (see tooltip)' if reg.longDescription!='' else ''))
            lll = QtWidgets.QLabel(tmp)
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            if reg.longDescription != '':
                lll.setToolTip(reg.longDescription)
            self.registerTableLayout.addWidget(lll,line,4)
            self.html += "<td title='" = html.escape(reg.longDescription) + "'>" + tmp + "</td>"

            lll = QtWidgets.QFrame()
            lll.setFrameStyle(QtWidgets.QFrame.Box)
            lll.setLineWidth(1)
            if line%2==1:
                lll.setStyleSheet(style)
            hhh = QtWidgets.QHBoxLayout()
            lll.setLayout(hhh)
            self.registerTableLayout.addWidget(lll,line,5)
            self.html += "<td>"

            # for bit-coded registers, loop over all bit group, and display them one-by-one
            if hasattr(reg,'sortedBits'):
                for b in reg.sortedBits:
                    s = b.symbol + "(" + str(b.firstBit)
                    if b.lastBit > b.firstBit:
                        s += ".." + str(b.lastBit)
                    s += "):"
                    symbol = QtWidgets.QLabel(s)
                    symbol.setToolTip(b.description)
                    hhh.addWidget(symbol)

                    hhh.addWidget(QtWidgets.QLabel(b.display_value(data)))
                    hhh.addStretch(1)

                    self.html += "<span title='" + html.escape(b.description) + "' style='margin-right:20px;'>" + s + " " + b.display_value(data) + "</span>"
            else:
                hhh.addWidget(QtWidgets.QLabel(reg.display_value(data)))
                self.html += reg.display_value(data)

            hhh.addStretch(2)

            self.html += "</td>"
            self.html += "</tr>\n"
            line += 1
