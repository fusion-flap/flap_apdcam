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

    ColumnLayout {
        id: theLayout;
        GroupBox {
            GridLayout {
                columns: 2;
                Label { text: "Address: "; } TextField { id: address; text: "10.123.13.101"; }
                Label { text: "IF: "; }      TextField { id: ifInput; }
            }
        }
        Label { text: "Camera connected locally"; Layout.alignment: Qt.AlignCenter; }
        ApdcamButton { text: "Find camera"; Layout.fillWidth: true; }
        GroupBox {
            title: "What is coming here? ";
        }
        ApdcamButton { text: "Control factory reset"; property bool factorySetting: true; }
        RowLayout {
            Label { text: "PC Error: "; }
            TextField { enabled: false; Layout.preferredWidth: 60; }
        }
    }
}
