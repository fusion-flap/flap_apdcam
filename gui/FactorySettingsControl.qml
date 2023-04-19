import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4
import "utils.js" as Utils

/*
  Factory settings mode enables control items in the GUI which are by default disabled. 
  GUI controls are marked as 'factory settings' controls by setting their property factorySetting to true
  as follows in the QML code:
  property bool factorySetting: true;
  Setting this property will result in
  - automatically setting this control as disabled when the GUI starts (without explicitely specifying it to be disabled)
  - automatically being controlled by the factory settings mode
*/


GroupBox
{
    id: factorySettingsControl;
    title: "Factory settings mode"
    Layout.fillWidth: true;

    property string buttonText: "Enter factory settings mode";
    property string buttonColor:        "#66ff66";
    property string buttonColorHovered: "#00ff00";

    function enterFactoryMode() {
        if(factoryPassword.text == "hello")
        {
            factorySettingsControl.title = "You are in factory settings mode, take responsibility!!!";
            factorySettingsControl.buttonColor        = "#ff5555";
            factorySettingsControl.buttonColorHovered = "#ff0000";
            factorySettingsControl.buttonText = "Quit factory settings mode";

            apdcamMain.factorySettingsMode = true;
            Utils.setChildrenEnabled(apdcamMain,true);
            factoryPassword.text = "";
        }
        else
        {
            apdcamMain.showError("Wrong password...");
        }
    }

    function quitFactoryMode() {
        factorySettingsControl.title = "Normal user mode";
        factorySettingsControl.buttonColor        = "#66ff66";
        factorySettingsControl.buttonColorHovered = "#00ff00";
        factorySettingsControl.buttonText = "Enter factory settings mode";

        apdcamMain.factorySettingsMode = false;
        Utils.setChildrenEnabled(apdcamMain,false);
    }
           
    RowLayout {
        Label {text: "Password: " }
        TextField { id: factoryPassword; echoMode: TextInput.Password; onAccepted: { factorySettingsControl.enterFactoryMode();}}
        ApdcamButton { 
            id: factorySettingsButton;
            text: factorySettingsControl.buttonText;
            backgroundColor:        factorySettingsControl.buttonColor;
            backgroundColorHovered: factorySettingsControl.buttonColorHovered;
            onClicked : {
                if(apdcamMain.factorySettingsMode) factorySettingsControl.quitFactoryMode();
                else factorySettingsControl.enterFactoryMode();
            }
        }
    }
}
