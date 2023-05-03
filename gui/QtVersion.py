import importlib
QtVersion = "PyQt6"
Qt = importlib.import_module(QtVersion+".QtCore")

AlignCenter = Qt.Qt.AlignCenter if QtVersion == "PyQt5" else Qt.Qt.AlignmentFlag.AlignCenter
AlignLeft = Qt.Qt.AlignLeft if QtVersion == "PyQt5" else Qt.Qt.AlignmentFlag.AlignLeft
AlignRight = Qt.Qt.AlignRight if QtVersion == "PyQt5" else Qt.Qt.AlignmentFlag.AlignRight
    
