import configparser
import importlib
from .QtVersion import QtVersion
QtWidgets = importlib.import_module(QtVersion+".QtWidgets")
QtGui     = importlib.import_module(QtVersion+".QtGui")
QtCore = importlib.import_module(QtVersion+".QtCore")
Qt = QtCore.Qt

def settingsSection(widget):
    result = ""
    parent = widget
    while parent is not None:
        if hasattr(parent,"settingsSection"):
            result = parent.settingsSection if result == "" else parent.settingsSection + "/" + result
        parent = parent.parent()
    return result

def saveSettings(widget,fileName):
    '''
    Scan recursively all control inputs within the given widget (typically a tab). Skip those, which do not have a 'settingsName' attribute.
    Save the value into the given file as settingsName=value lines.
    indent is the level of indentation
    '''

    error = ""
    settings = configparser.ConfigParser()

    # loop over all controls within this tab
    controls = widget.findChildren(QtWidgets.QWidget)
    for control in controls:
        section = settingsSection(control)
        if section == "":
            continue
        if not section in settings:
            settings[section] = {}

        # skip those without the settingsName attribute
        if not hasattr(control,"settingsName"):
            continue

        if isinstance(control,QtWidgets.QSpinBox) or isinstance(control,QtWidgets.QDoubleSpinBox):
            settings[section][control.settingsName] = str(control.value())
        elif isinstance(control,QtWidgets.QLineEdit):
            settings[section][control.settingsName] = control.text()
        elif isinstance(control,QtWidgets.QCheckBox):
            settings[section][control.settingsName] = ("true" if control.isChecked() else "false")
        elif isinstance(control,QtWidgets.QComboBox):
            settings[section][control.settingsName] = control.currentText()

    file = None
    try:
        file = open(fileName,"wt")
    except:
        error += "Failed to open file '" + fileName + "'"
        return error
    settings.write(file)
    return error

def loadSettings(widget, fileName):
    settings = configparser.ConfigParser()
    if len(settings.read(fileName))==0:
        return "Could not read the file '" + fileName + "'"

    error = ""

    controls = widget.findChildren(QtWidgets.QWidget)
    for control in controls:
        # skip those without the settingsName attribute
        if not hasattr(control,"settingsName"):
            continue
        section = settingsSection(control)
        if section == "":
            error += "Control '" + control.settingsName + "' is not within a section"
            continue

        if not section in settings or not control.settingsName in settings[section]:
            error += "No settings are found for '" + control.settingsName + "'"

        if isinstance(control,QtWidgets.QSpinBox):
            control.setValue(int(settings[section][control.settingsName]))
        elif isinstance(control,QtWidgets.QDoubleSpinBox):
            control.setValue(float(settings[section][control.settingsName]))
        elif isinstance(control,QtWidgets.QLineEdit):
            control.setText(settings[section][control.settingsName])
        elif isinstance(control,QtWidgets.QCheckBox):
            if settings[section][control.settingsName].lower() == "yes" or settings[section][control.settingsName].lower() == "true" or settings[section][control.settingsName] == "1":
                control.setChecked(True)
            else:
                control.setChecked(False)
        elif isinstance(control,QtWidgets.QComboBox):
            if control.findText(settings[section][control.settingsName]) >= 0:
                control.setCurrentText(settings[section][control.settingsName])
            else:
                error += "Bad value (" + settings[section][control.settingsName] + ") for the variable '" + control.settingsName + "' in section [" + section + "] of the settings file '" + fileName + "'\n"
    return error
        
