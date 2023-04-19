import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Button {
    id: button;

    property string color: "black";
    property string colorHovered: "black";
    property string colorPressed: "black";
    property string colorDisabled: "#999999";

    property string backgroundColor: "#cccccc";
    property string backgroundColorHovered: "#bbbbbb";
    property string backgroundColorPressed: "#999999";
    property string backgroundColorDisabled: "#dddddd";

    style: ButtonStyle {
        background: Rectangle { 
            Layout.preferredHeight: 40;
            color: (enabled ? (pressed ? button.backgroundColorPressed : (hovered? button.backgroundColorHovered : button.backgroundColor)) : button.backgroundColorDisabled); 
            radius: 3; 
            border.width: 1; 
            border.color: "#888888";  }
        label: Label { 
            text: button.text; 
            color: (enabled ? (pressed ? button.colorPressed : (hovered? button.colorHovered : button.color)) : button.colorDisabled); 
        }
    }
}
