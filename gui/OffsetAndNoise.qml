import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Flickable {
    id: offsetAndNoiseTabContent;
    topMargin: 15;
    clip: true; 
    anchors.fill: parent
    contentHeight: theLayout.height
    contentWidth: theLayout.width;
    
    ColumnLayout {
        id: theLayout;
        AdcOffsetAndNoise { adcNumber: 1; }
        AdcOffsetAndNoise { adcNumber: 2; }
        RowLayout {
            ApdcamButton { text: "Measure all data"; }
            ApdcamButton { text: "Get all DAC values"; }
            ApdcamButton { text: "Set all DAC outputs"; }
            Label { text: "Set all DAC values to: "; }
            TextField { }
        }
    }
}
