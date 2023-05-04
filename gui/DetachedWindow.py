# https://stackoverflow.com/questions/43293056/move-qwidget-from-one-window-to-another-in-pyqt

import importlib
from QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
Qt = importlib.import_module(QtVersion+".QtCore")

class DetachedWindow(QtWidgets.QMainWindow):
    """
    Create a detached window containing a widget, which was so far contained in another window

    Parameters:
    ^^^^^^^^^^^
    widget    -- the widget to be reparented into the new window
    layout    -- the original layout the widget was in
    index     -- the index of the widget within the original layout. It will be re-inserted into the
                 original layout automatically when the detached window is closed, at this index
    """
    # def __init__(self, widget, layout, index):
    #     QtWidgets.QMainWindow.__init__(self)
    #     self.oldParent = None
    #     self.oldLayout = None
    #     self.oldLayoutIndex = 0
    #     self.widget = None
    #     if widget is not None:
    #         self.widget = widget
    #         self.oldLayout = layout
    #         self.oldLayoutIndex = index
    #         self.oldParent = widget.parent()
    #         self.setCentralWidget(widget)
    #         widget.setParent(self)
    #         widget.show()
    #     self.show()

    def __init__(self, widget, closeAction):
        QtWidgets.QMainWindow.__init__(self)
        self.closeAction = closeAction
        self.widget = None
        if widget is not None:
            self.widget = widget
            self.setCentralWidget(widget)
            widget.setParent(self)
            widget.show()
        self.show()

        
    """
    Overwritten 'close' event handler. The contained widget is automatically moved back to its original
    location when the detached window is closed
    """
    # def closeEvent(self,event):
    #     self.widget.setParent(self.oldParent)
    #     self.oldLayout.insertWidget(self.oldLayoutIndex,self.widget)
    #     self.widget.show()
    #     event.accept()  # accept the event, i.e. close the window
    def closeEvent(self,event):
        self.closeAction(self.widget)
        self.widget.show()
        event.accept()  # accept the event, i.e. close the window
