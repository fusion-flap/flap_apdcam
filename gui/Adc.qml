import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Tab {
    title: "ADC #" + (index+1); 

    Flickable {
        topMargin: 10;
        clip: true;
        Layout.fillWidth: true;
        anchors.fill: parent;
        contentHeight: adcLayout.height;
        contentWidth: adcLayout.width;
        width: adcLayout.width;
        
        ColumnLayout {
            id: adcLayout;
            ApdcamButton { text: "Reset all ADC status"; }

            RowLayout {
                GroupBox {
                    Layout.fillHeight: true;
                    GridLayout {
                        columns: 2;
                        Label { text: "DVDD: "; } TextField { id: dvdd; enabled: false; }
                        Label { text: "AVDD: "; } TextField { id: avdd; enabled: false; }
                        Label { text: "1.8 V: "; } TextField { id: adc18Vj; enabled: false; }
                        Label { text: "2.5 V: "; } TextField { id: adc25V; enabled: false; }
                        Label { text: "Temp: "; } TextField { id: temp; enabled: false; }
                    }
                }
                GroupBox {
                    Layout.fillHeight: true;
                    ColumnLayout {
                        CheckBox { id: pllLocked; text: "PLL Locked"; }
                        CheckBox { id: intTrigger; text: "Int. trigger"; }
                        CheckBox { id: overload; text: "Overload"; }
                        CheckBox { id: led1; text: "LED 1"; }
                        CheckBox { id: led2; text: "LED 2"; }
                        ApdcamButton { Layout.fillWidth: true; text: "All channel on"; }
                        ApdcamButton { Layout.fillWidth: true; text: "All channel off"; }
                        RowLayout {
                            Label { text: "Error: "; }
                            TextField { id: error; enabled: false; }
                        }
                    }
                }
                GroupBox {
                    Layout.fillHeight: true;
                    GridLayout{
                        columns: 4;
                        Repeater {
                            model: 32;
                            CheckBox { text: (index+1); }
                        }
                    }
                }
            }
            RowLayout {
                GroupBox {
                    Layout.fillHeight: true;
                    ColumnLayout {
                        CheckBox { id: sataOn; text: "SATA On"; }
                        CheckBox { id: dualSata; text: "Dual SATA"; }
                        CheckBox { id: sataSync; text: "SATA Sync"; }
                        CheckBox { id: test; text: "Test"; }
                        CheckBox { id: filter; text: "Filter"; }
                        CheckBox { id: intTrig; text: "Int. trig"; }
                        CheckBox { id: revBitord; text: "Rev. bitord."; }
                    }
                }
                GroupBox {
                    Layout.fillHeight: true;
                    GridLayout {
                        columns: 2;
                        Label { text: "Bits: "; } TextField { id: bits; }
                        Label { text: "Ring buffer: "; } TextField { id: ringBuffer; }
                        Label { text: "SATA CLK mult.: "; } TextField { id: sataClkMult; }
                        Label { text: "SATA CLK div.: "; } TextField { id: sataClkDiv; }
                        Label { text: "Test pattern: "; } TextField { id: testPattern; }
                    }
                }
                GroupBox {
                    title: "FIR Filter";
                    Layout.fillHeight: true;
                    GridLayout {
                        columns: 2;
                        Label { text: "Coeff 1: "; } TextField { id: coeff1; }
                        Label { text: "Coeff 2: "; } TextField { id: coeff2; }
                        Label { text: "Coeff 3: "; } TextField { id: coeff3; }
                        Label { text: "Coeff 4: "; } TextField { id: coeff4; }
                        Label { text: "Coeff 5: "; } TextField { id: coeff5; }
                    }
                }
                ColumnLayout {
                    GroupBox {
                        title: "Int Filter";
                        Layout.fillWidth: true;
                        GridLayout {
                            columns: 2;
                            Label { text: "Coeff: "; } TextField { id: coeff; }
                            Label { text: "Filter Div: "; } TextField { id: filterDiv; }
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true;
                        columns: 2;
                        Label { text: "FIR freq. [MHz]: "; } TextField { id: firFreq; }
                        Label { text: "Rec. freq. [MHz]: "; } TextField { id: recFreq; }
                        Label { text: "Filter gain: "; } SpinBox { id: filterGain; }
                        
                    }
                }
            }
            RowLayout {
                GroupBox {
                    Layout.fillHeight: true;
                    ColumnLayout {
                        Layout.fillWidth: true;
                        GridLayout {
                            Layout.fillWidth: true;
                            columns: 2;
                            Label { text: "Overl. level: "; } TextField { id: overlLevel; }
                            Label { text: "Overl. time [\u03bcs]: "; } TextField { id: overlTime; }
                        }
                        CheckBox { text: "Overload enabled"; }
                        CheckBox { text: "Ovr+"; }
                        CheckBox { text: "OVERLOAD"; }
                    }
                }
                ColumnLayout {
                    GroupBox {
                        ColumnLayout {
                            Layout.fillWidth: true;
                            RowLayout { Label {text: "Trig. level (all): "; } TextField { id: trigLevelAll; } }
                            CheckBox { text: "Trig enabled"; id: trigEnabled; }
                            CheckBox { text: "+ trig"; id: plusTrig; }
                        }
                    }
                    ApdcamButton {
                        text: "FACTORY RESET";
                        property bool factorySetting: true;
                    }
                    ApdcamButton {
                        text: "Read from HW";
                    }
                }
            }
        }
       
    }
}
