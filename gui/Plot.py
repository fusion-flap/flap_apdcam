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

        controlGroup = QVGroupBox("Plot controls")
        controlGroup.addWidget(QtWidgets.QPushButton("First buttom"))
        controlGroup.addWidget(QtWidgets.QPushButton("Second buttom"))
        self.layout.addWidget(controlGroup)

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
        
