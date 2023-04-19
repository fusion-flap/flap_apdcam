import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4
import "utils.js" as Utils


Flickable {
    id: hvShutterLightTabContent;
    topMargin: 15;
    clip: true; 
    anchors.fill: parent
    contentHeight: theLayout.height

    ColumnLayout {
        id: theLayout;
        GroupBox {
            title: "HV Settings";
            Layout.fillWidth: true;
            ColumnLayout {
                ApdcamButton {
                    text: "READ HV status";
                    Layout.fillWidth: true;
                }
                RowLayout {
                    Layout.fillWidth: true;
                    Repeater {
                        model: 4;
                        GroupBox {
                            GridLayout {
                                columns: 2;
                                Label { text: "HV1 set: "; } TextField {}
                                Label { text: "HV1 act: "; } TextField { enabled: false; }
                                Label { text: "HV1 max: "; } TextField { }
                            }
                        }
                    }
                }
                RowLayout {
                    Label { id: hvStatus; text: "HV Disabled";  }
                    ApdcamButton { text: "HV Enable"; onClicked: {hvStatus.text = "HV Enabled"; hvStatus.color = "green";}}
                    ApdcamButton { text: "HV Disable";onClicked: {hvStatus.text = "HV Disabled"; hvStatus.color = "black";} }
                }
            }
        }
        GroupBox {
            title: "Shutter control";
            Layout.fillWidth: true;
            RowLayout {
                ApdcamButton { text: "Open"; }
                ApdcamButton { text: "Close"; }
                CheckBox { text: "External control"; }
            }
        }
        GroupBox {
            title: "Calibration light control";
            Layout.fillWidth: true;
            RowLayout {
                Label { text: "Intensity: "; }
                SpinBox { minimumValue: 0; maximumValue: 4095; }
            }
        }
    }
    
}
