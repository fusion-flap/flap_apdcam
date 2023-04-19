import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Flickable {
    id: controlTimingTabContent;
    topMargin: 15;
    clip: true;
    anchors.fill: parent;
    contentHeight: theLayout.height;
    contentWidth: theLayout.width;

    ColumnLayout {
        id: theLayout;
        GroupBox {
            Layout.fillWidth: true;
            RowLayout {
                Label { text: "CC card temp: "; } TextField { id: ccCardTemp; } 
                Label { anchors.leftMargin: 20; text: "CC card max temp: "; } TextField { id: ccCardMaxTemp; }
            }
        }
        GroupBox {
            Layout.fillWidth: true;
            title: "CC card voltages";
            GridLayout {
                columns: 4;
                Label { text: "3.3 V: "; } TextField {} Label { text: "1.8 V XC: "; } TextField {}
                Label { text: "2.5 V: "; } TextField {} Label { text: "1.2 V ST: "; } TextField {}
            }
        }
        GridLayout {
            columns: 6;
            Label { text: "Base PLL Mult: "; } TextField {} 
            Label { text: "Div: "; } TextField {} 
            Label { text: "ADC f.[MHz]: "; } TextField {} 
            Label { text: "EXT CLK mult.:"; } TextField {} 
            GroupBox {
                Layout.columnSpan: 4;
                Layout.rowSpan: 3;
                Layout.fillWidth: true;
                ColumnLayout {
                    CheckBox { text: "ADC Clock Ext"; }
                    CheckBox { text: "Auto Ext. Clock"; }
                    CheckBox { text: "Ext. Sample"; }
                }
            }
            Label { text: "EXT CLK div.:"; } TextField {} 
            Label { text: "Sample div.:"; } TextField {} 
        }
        RowLayout {
            Layout.fillWidth: true;
            GroupBox {
                ColumnLayout {
                    CheckBox { text: "Basic PLL Locked"; }
                    CheckBox { text: "SATA PLL Locked"; }
                    CheckBox { text: "Ext. DCM Locked"; }
                    CheckBox { text: "Ext. Clock Valid"; }
                }
            }
            GroupBox {
                CheckBox { text: "Dual SATA"; }
            }
        }
        RowLayout {
            Label { text: "Ext. clock frequench [kHz]: "; }
            TextField { enabled: false; }
        }
        GroupBox {
            Layout.fillWidth: true;
            ColumnLayout {
                CheckBox { id: trigPlus; text: "Trig. +"; }
                CheckBox { id: trigMinus; text: "Trig. -"; }
                CheckBox { id: maxTrig; text: "Max. trig."; }
                CheckBox { id: disableWhenStreamOff; text: "Disable when stream off"; }
                RowLayout {
                    Label { text: "Trigger delay [\u03bcs]:"; }
                    SpinBox {id: triggerDelay; }
                }
            }
        }
        RowLayout {
            Label { text: "Sample number: "; }
            TextField { }
        }
        
    }
}
