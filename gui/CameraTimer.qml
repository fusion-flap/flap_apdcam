import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4

Flickable {
    id: cameraTimerTabContent;
    topMargin: 15;
    clip: true;
    anchors.fill: parent;
    contentHeight: theLayout.height;
    Layout.fillWidth: true;
    contentWidth: theLayout.width;

    ColumnLayout {
        id: theLayout;
        RowLayout {
            Label { text: "20 MHz divider value: " } SpinBox {id: frequency20MHzDividerValue; minimumValue: 1; maximumValue: 65535; } 
        }
        RowLayout {
            ApdcamButton {
                text: "Read camera timer settings";
            }
            ApdcamButton {
                text: "Save camera timer settings";
            }
        }
        GridLayout {
            columns: 5
            Repeater {
                model: 10;
                GroupBox {
                    title: "Timer-" + (index+1);
                    RowLayout {
                        GroupBox {
                            GridLayout {
                                columns: 2;
                                Label { text: "Delay: "; } SpinBox {}
                                Label { text: "ON time: "; } SpinBox {}
                                Label { text: "OFF time: "; } SpinBox {}
                                Label { text: "# of pulses: "; } SpinBox {}
                            }
                        }
                        GroupBox {
                            title: "Out";
                            ColumnLayout {
                                CheckBox { text: "CH1"; } 
                                CheckBox { text: "CH2"; } 
                                CheckBox { text: "CH3"; } 
                                CheckBox { text: "CH4"; } 
                            }
                        }
                    }
                }
            }
            GroupBox {
                title: "Control register";
                Layout.fillWidth: true;
                Layout.columnSpan: 5;
                ColumnLayout {
                    CheckBox { id: idleArmedState;  text: "Idle/Armed state"; }
                    CheckBox { id: manualStopStart; text: "Manual stop/start"; }
                    CheckBox { id: returnToArmed;  text: "Return to armed"; }
                    CheckBox { id: returnToRun;  text: "Return to run"; }
                    CheckBox { id: externalTriggerRisingSlopeEnableDisable;  text: "External trigger rising slope enable/disable"; }
                    CheckBox { id: externalTriggerFallingSlopeEnableDisable;  text: "External trigger falling slope enable/disable"; }
                    CheckBox { id: internalTriggerEnableDisable;  text: "Internal trigger enable/disable"; }
                }
            }
            GroupBox {
                Layout.fillWidth: true;
                Layout.columnSpan: 5;
                RowLayout {
                    Label { text: "Output polarity: "; }
                    Repeater {
                        model: 4;
                        CheckBox { text: "XOR-" + (index+1); }
                    }
                }
            }
            GroupBox {
                Layout.fillWidth: true;
                Layout.columnSpan: 5;
                RowLayout {
                    Label { text: "Output enable: "; }
                    Repeater {
                        model: 4;
                        CheckBox { text: "AND-" + (index+1); }
                    }
                }
            }
            RowLayout {
                Layout.columnSpan: 5;
                ApdcamButton {text: "Camera timer IDLE"; }
                ApdcamButton {text: "Camera timer ARMED"; }
                ApdcamButton {text: "Camera timer RUN"; }
            }
        }
    }
}
