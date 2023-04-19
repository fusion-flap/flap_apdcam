import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4
import "utils.js" as Utils

Item
{
    id: measurementControlTabContent;
    y: 15;
    GridLayout
    {
        columns: 2


        ApdcamButton {
            text: "START Measurement";
            tooltip: "Start the measurement";
            property bool factorySetting: true;
            onClicked : { 
                apdcamMain.showMessage("message");
                apdcamMain.showWarning("warning");
                apdcamMain.showError("error");
            }
        }
        ApdcamButton {
            text: "STOP Measurement";
            tooltip: "Stops the measurement";
        }
        TextArea {
            Layout.columnSpan: 2;
            text: "Measurement logs or whatever is coming here";
            Layout.fillWidth: true
            Layout.minimumWidth: 200;
        }
        Label {
            text: "Measurement ID: "
        }
        TextField {
            enabled: false;
        }
        Label {
            text: "Measurement length [s]: "
        }
        TextField {
            property bool factorySetting: true;
        }
        ComboBox {
            property bool factorySetting: true;
            Layout.columnSpan: 2;
            model: ["SW Trigger", "External Trigger","Internal Trigger"]
        }
    }
}
