import sys

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ApdcamUtils import *
import matplotlib.pyplot as plt
from DetachedWindow import DetachedWindow

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Plot(QtWidgets.QWidget):
    def restorePlot(self,widget):
        widget.setParent(self)
        self.plotLayout.insertWidget(0,widget)
        widget.show()

    def popOutAction(self):
        if self.popOutWindow:
            self.popOutWindow.close()
            self.popOutWindow = None
            self.popOutButton.setToolTip("Move the plot to a new window")
            self.popOutButton.setIcon(QtGui.QIcon("popout.png"))
        else:
            self.popOutWindow = DetachedWindow(self.plotWidget,self.restorePlot)
            self.popOutButton.setToolTip("Move the plot back here")
            self.popOutButton.setIcon(QtGui.QIcon("popin.png"))

    def __init__(self,parent):
        super(Plot,self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.popOutWindow = None

        controls = QtWidgets.QHBoxLayout()
        self.layout.addLayout(controls)

        data = QVGroupBox("Data")
        controls.addWidget(data)

        row1 = QtWidgets.QHBoxLayout()
        data.addLayout(row1)
        row1.addWidget(QtWidgets.QLabel("Data dir.:"))
        self.dataDir = QtWidgets.QLineEdit()
        row1.addWidget(self.dataDir)

        row2 = QtWidgets.QHBoxLayout()
        data.addLayout(row2)

        row2.addWidget(QtWidgets.QLabel("Signals"))
        self.signals = QtWidgets.QLineEdit()
        row2.addWidget(self.signals)

        row2.addStretch(1)

        l = QtWidgets.QLabel("Time range [s]")
        #l.setStyleSheet("margin-left:20px")
        row2.addWidget(l)
        self.timeFrom = QtWidgets.QSpinBox()
        row2.addWidget(self.timeFrom)
        row2.addWidget(QtWidgets.QLabel("-"))
        self.timeTo = QtWidgets.QSpinBox()
        row2.addWidget(self.timeTo)

        row2.addStretch(1)

        self.getDataButton = QtWidgets.QPushButton("GET DATA")
        #self.getDataButton.setStyleSheet("margin-left: 20px")
        row2.addWidget(self.getDataButton)

        self.whatIsThis = QtWidgets.QTextEdit()
        data.addWidget(self.whatIsThis)
        
        rawDataPlot = QGridGroupBox("Raw data plot")
        controls.addWidget(rawDataPlot)

        self.rawDataPlotButton = QtWidgets.QPushButton("PLOT")
        rawDataPlot.addWidget(self.rawDataPlotButton,0,0)
        rawDataPlot.addWidget(QtWidgets.QLabel("Plot type:"),1,0)
        self.rawDataPlotType = QtWidgets.QComboBox()
        self.rawDataPlotType.addItem("xy")
        self.rawDataPlotType.addItem("grid xy")
        self.rawDataPlotType.addItem("image")
        self.rawDataPlotType.addItem("anim-image")
        rawDataPlot.addWidget(self.rawDataPlotType,2,0)
        rawDataPlot.setRowStretch(rawDataPlot.rowCount(),1)

        self.plotAllPoints = QtWidgets.QCheckBox("Plot all points")
        rawDataPlot.addWidget(self.plotAllPoints,0,1)
        self.autoscale = QtWidgets.QCheckBox("Autoscale")
        rawDataPlot.addWidget(self.autoscale,1,1)

        h = QtWidgets.QHBoxLayout()
        rawDataPlot.addLayout(h,2,1)
        h.addWidget(QtWidgets.QLabel("Range"))
        self.rawDataPlotFrom = QtWidgets.QSpinBox()
        h.addWidget(self.rawDataPlotFrom)
        h.addWidget(QtWidgets.QLabel("-"))
        self.rawDataPlotTo = QtWidgets.QSpinBox()
        h.addWidget(self.rawDataPlotTo)

        spectrumPlot = QGridGroupBox("Spectrum plot")
        controls.addWidget(spectrumPlot)

        self.spectrumPlotButton = QtWidgets.QPushButton("PLOT")
        spectrumPlot.addWidget(self.spectrumPlotButton,0,0)
        spectrumPlot.addWidget(QtWidgets.QLabel("Plot type:"),1,0)
        self.spectrumPlotType = QtWidgets.QComboBox()
        self.spectrumPlotType.addItem("xy")
        self.spectrumPlotType.addItem("grid xy")
        self.spectrumPlotType.addItem("image")
        self.spectrumPlotType.addItem("anim-image")
        spectrumPlot.addWidget(self.spectrumPlotType,2,0)

        spectrumPlot.addWidget(QtWidgets.QLabel("Frequency resolution [Hz]"),0,1)
        self.frequencyResolution = QtWidgets.QSpinBox()
        self.frequencyResolution.setMinimum(0)
        self.frequencyResolution.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        spectrumPlot.addWidget(self.frequencyResolution,1,1)

        spectrumPlot.setRowStretch(spectrumPlot.rowCount(),1)

        
        self.plotLayout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.plotLayout)

        self.plotWidget = MplCanvas(self,width=10,height=10,dpi=100)
        self.plotLayout.addWidget(self.plotWidget)

        # dummy layout to add some stretch below the pop-out button
        # This stretch is also used when the plot widget is moved out to a new window
        hh = QtWidgets.QVBoxLayout() 
        self.plotLayout.addLayout(hh)
        self.popOutButton = QtWidgets.QPushButton("")
        self.popOutButton.setToolTip("Move the plot to a new window")
        self.popOutButton.setIcon(QtGui.QIcon("popout.png"))
        self.popOutButton.clicked.connect(self.popOutAction)
        self.popOutButton.setFixedWidth(20)
        hh.addWidget(self.popOutButton)
        hh.addStretch(1)
        
