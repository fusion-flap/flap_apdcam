import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4
import "utils.js" as Utils

ApplicationWindow 
{
    id: apdcamMain
    title: "APDCAM Control"
    minimumWidth: 1000
    minimumHeight: 800
    menuBar: APDCAM_MenuBar { }

    // APDCAM variable is set from within the python code, i.e. it is not declared here,
    // and is the main python class UI
    // embedded event handlers (javascript code) can use this variable to access the
    // functionality (i.e. communication to the camera, etc) implemented in the Python code

    Component.onCompleted: {
        Utils.setChildrenEnabled(apdcamMain,false);
        let children = Utils.getAllChildren(apdcamMain,function(o) { return ("factorySetting" in o) && o.factorySetting; });
        for(let i=0; i<children.length; ++i)
        {
            if("color" in children[i]) children[i].color = "red";
            if("textColor" in children[i]) children[i].textColor = "red";
        }
    }

    property string messages;

    function dateNow()
    {
        let d = new Date();
        return d.getFullYear() + "/" + d.getMonth() + "/" + d.getDay() + " " + d.getHours() + ":" + d.getMinutes() + ":" + d.getSeconds();
    }

    function showMessage(msg)
    {
        apdcamMain.messages += dateNow() + " -- " + msg + "<br>";
    }
    function showError(msg)
    {
        apdcamMain.messages += "<font color='red'>" + dateNow() + " -- " + msg + "</font><br>";
    }
    function showWarning(msg)
    {
        apdcamMain.messages += "<font color='orange'>" + dateNow() + " -- " + msg + "</font><br>";
    }

    property bool factorySettingsMode: false;

    ColumnLayout
    {
        id: layout;
        anchors.fill: parent

        FactorySettingsControl { } 

        TabView
        {
            id: tabs
            Layout.fillHeight: true
            Layout.fillWidth: true

            Tab {
                title: "Main";
                MainPage {}
            }

            Tab {
                title: "Camera control"
                CameraControl {}
            }
            Tab {
                title: "Measurement control"
                MeasurementControl {}
            }
            Tab {
                title: "Camera settings"
                CameraSettings {}
            }

            Tab {
                title: "Camera timer"
                CameraTimer {}
            }

            Tab {
                title: "Control timing"
                ControlTiming {}
            }

            Tab {
                title: "ADC control";
                AdcControl {}
            }

            Tab {
                title: "HV, Shutter, Light";
                HvShutterLight {}
            }

            Tab {
                title: "Temperature";
                Temperature {}
            }

            Tab {
                title: "Offset/Noise";
                OffsetAndNoise {}
            }
        }

        TextArea {
            id: messages;
            Layout.fillWidth: true;
            textFormat: TextEdit.RichText;
            text: apdcamMain.messages;
            onTextChanged: {
                cursorPosition = length-1;
            }
        }
    }
}
