import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

MenuBar 
{
    Menu 
    {
        title: "File"
        MenuItem 
        { 
            text: "&Open..."; 
            onTriggered: { fiapp.show_message("Opening..."); }
        }
        MenuItem 
        { 
            text: "Close" 
            onTriggered: { fiapp.show_message("Closing..."); }
        }
        MenuItem{
            text: "Exit (works)";
            onTriggered: { Qt.quit(); }
        }
    }
    Menu 
    {
        title: "Edit"
        MenuItem { text: "Cut" }
        MenuItem { text: "Copy" }
        MenuItem { text: "Paste" }
    }
}
