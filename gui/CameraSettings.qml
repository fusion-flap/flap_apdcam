import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Flickable {
    id: cameraSettingsTabContent;
    topMargin: 15;
    clip: true; 
    anchors.fill: parent
    contentHeight: theLayout.height
    
    ColumnLayout {
        id: theLayout;
        GroupBox {
            title: "General settings"
            Layout.fillWidth: true;
            RowLayout {
                GroupBox {
                    title: "Camera selection"
                    RowLayout {
                        Label { text: "Camera type: " }
                        ComboBox {id: camera_type; model: ["APDCAM-10G_4x32","APDCAM-10G_8x8","APDCAM-10G_4x16","APDCAM-10G_8x16","APDCAM-10G_8x16A","APDCAM-10G_FC"] }
                    }
                }
                ApdcamButton { id: factoryReset; text: "FACTORY RESET"; property bool factorySetting: true;}
                CheckBox { id: dualSata; text: "Dual SATA"; property bool factorySetting: true; }
            }
        }
        GroupBox {
            title: "Settings"
            Layout.fillWidth: true;
            RowLayout {
                Label { text: "Test pattern: " }
                ComboBox { id: test_pattern; model: ["0000","1111", "etc" ] }
            }
        }
        GroupBox {
            title: "Power and temperature"
            Layout.fillWidth: true;
            RowLayout {
                CheckBox { id: analog_power; text: "Analog power" }
            }
        }
        Label { text: "Demonstration of scrollable content, croll down... " }
        Label { text: "Scrollbar should appear when window size is too small to accommodate all content..." }
        Label { text: "I don't know why it does not appear. " }
        Rectangle {
            color: "red"
            width: 300;
            height: 300; 
        }
        Rectangle {
            color: "green"
            width: 300;
            height: 300; 
        }
        Rectangle {
            color: "blue"
            width: 300;
            height: 300; 
        }
    }
}
