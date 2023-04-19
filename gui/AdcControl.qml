import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Item {
    id: adcTabContent;
    y: 15;
    Layout.fillWidth: true;
    Layout.fillHeight: true;

    TabView {
        anchors.fill: parent;
        Layout.fillHeight: true;
        Layout.fillWidth: true;
        Repeater {
            model: 3;
            Adc {}
        }
    }
}
