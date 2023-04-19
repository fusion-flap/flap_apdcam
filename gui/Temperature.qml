import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Flickable {
    id: temperatureTabContent;
    topMargin: 15;
    clip: true; 
    anchors.fill: parent
    contentHeight: theLayout.height

    GridLayout {
        id: theLayout;
        columns: 7;
        Layout.fillWidth: true;

        Label { text: "Fan 1"; Layout.column: 2; }
        Label { text: "Fan 2"; Layout.column: 3; }
        Label { text: "Fan 3"; Layout.column: 4; }
        Label { text: "Peltier"; Layout.column: 5; }
        Label { text: "Peltier PID"; Layout.column: 6; }
        Label {
            text: "Temperatures";
            Layout.alignment: Qt.AlignBottom;
            Layout.columnSpan: 2;
        }
        Repeater {
            model: 3;
            GroupBox {
//                Layout.row: 1;
//                Layout.column: index+2;
                GridLayout {
                    columns: 2;
                    ComboBox { Layout.columnSpan: 2; model: ["Auto"]; }
                    Label { text: "Speed: "; } SpinBox { Layout.preferredWidth: 60; minimumValue: 0; maximumValue: 10; }
                    Label { text: "Diff: "; }  SpinBox { Layout.preferredWidth: 60; minimumValue: 0; maximumValue: 10; }
                    Label { text: "Ref: "; }  SpinBox { Layout.preferredWidth: 60; minimumValue: 0; maximumValue: 10; }
                    Label { text: "Ctrl: "; } TextField { enabled: false; Layout.preferredWidth: 60;}
                }
            }
        }
        GroupBox {
            Layout.fillWidth: true;
            Layout.fillHeight: true;
            GridLayout {
                columns: 2;
                Label { text: "Actual out: "; } TextField { Layout.preferredWidth: 60;enabled: false; }
                Label { text: "Temp. ref.: "; } TextField { Layout.preferredWidth: 60;}
                Label { text: "Act. ctrl.: "; } TextField { Layout.preferredWidth: 60; enabled: false; }
            }
        }
        GroupBox {
            Layout.fillWidth: true;
            Layout.fillHeight: true;
            GridLayout {
                columns: 2;
                Label { text: "P: "; } TextField { Layout.preferredWidth: 60;}
                Label { text: "I: "; } TextField { Layout.preferredWidth: 60;}
                Label { text: "D: "; } TextField { Layout.preferredWidth: 60;}
            }
        }

        Label { Layout.column: 0; Layout.row: 3; text: "O1"; }                TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 4; text: "O2"; }                TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 5; text: "O3"; }                TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 6; text: "O4"; }                TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 7; text: "Detector 1"; }        TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 8; text: "Analog panel 1"; }    TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 9; text: "Detector 2"; }        TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 10; text: "Analog panel 2"; }   TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 11; text: "Analog panel 3"; }   TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 12; text: "Analog panel 4"; }   TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 13; text: "Baseplate"; }        TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 14; text: "12"; }               TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 15; text: "13"; }               TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 16; text: "PC card heatsink"; } TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 17; text: "Power panel 1"; }    TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }
        Label { Layout.column: 0; Layout.row: 18; text: "Power panel 2"; }    TextField { Layout.preferredWidth: 60; enabled: false; } Repeater { model: 4; TextField { Layout.alignment: Qt.AlignCenter; } }

        RowLayout {
            Layout.column: 0; 
            Layout.row: 19; 
            Layout.columnSpan: 7;
            ApdcamButton { text: "Read temperatures"; }
            ApdcamButton { text: "Read weights"; }
        }

    }

}
