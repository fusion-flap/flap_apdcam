import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

GroupBox {
    id: adcOffsetAndNoise;
    property int adcNumber: 1;
    Layout.fillWidth: true;
    ColumnLayout {
        GridLayout {
            columns: 33;
            Label { text: "ADC " + adcOffsetAndNoise.adcNumber; }
            Repeater { model: 32; Label { text: index+1; } }
            Label { text: "Mean"; }
            Repeater { model: 32; TextField { enabled: false; Layout.preferredWidth: 30;}}
            Label { text: "HF"; }
            Repeater { model: 32; TextField { enabled: false; Layout.preferredWidth: 30;}}
            Label { text: "LF"; }
            Repeater { model: 32; TextField { enabled: false; Layout.preferredWidth: 30;}}
            Label { text: "<b>DAC</b>"; }
            Repeater { model: 32; TextField { Layout.preferredWidth: 30;}}
        }
        RowLayout {
            ApdcamButton { text: "Measure data"; }
            ApdcamButton { text: "Get DAC values"; }
            ApdcamButton { text: "Set DAC outputs"; }
            Label { text: "Set all 32 DAC values to: "; }
            SpinBox {}
        }
    }
}
