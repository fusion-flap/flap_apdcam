import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.0
import QtQuick.Extras 1.4


Flickable {
    topMargin: 15;
    id: cameraControlTabContent;
    clip: true; 
    anchors.fill: parent;
    contentHeight: theLayout.height;
    contentWidth: theLayout.width;

    ColumnLayout {
        id: theLayout;
        RowLayout {
            ApdcamButton { 
                text: "APDCAM On" 
                property bool factorySetting: true;
            }
            ApdcamButton { 
                text: "APDCAM Off" 
            }
            Label {
                color: "red"
                text: "Not connected"
            }
        }
        GroupBox {
            title: "Detector voltages"
            Layout.fillWidth: true;
            GridLayout {
                columns: 7;
                Label { text: "HV1 set"; }
                SpinBox { id: hv1_set; maximumValue: 2000; enabled: false; }
                Label { text: "actual"; }
                TextField { id: hv1_actual; enabled:false; width: 50;}
                ApdcamButton { id: hv1_on; text: "HV1 on"; onClicked: {apdcamMain.showMessage("clicked");}}
                ApdcamButton { id: hv1_off; text: "HV1 off"; }
                ApdcamButton { id: hv_enable; text: "HV Enable"; }

                Label { text: "HV2 set"; }
                SpinBox { id: hv2_set; maximumValue: 2000; }
                Label { text: "actual"; }
                TextField { id: hv2_actual; enabled:false; width: 50;}
                ApdcamButton { id: hv2_on; text: "HV2 on"; }
                ApdcamButton { id: hv2_off; text: "HV2 off"; }
                ApdcamButton { id: hv_disable; text: "HV Disable"; }

                Label { text: "HV3 set"; }
                SpinBox { id: hv3_set; maximumValue: 2000; }
                Label { text: "actual"; }
                TextField { id: hv3_actual; enabled:false; width: 50;}
                ApdcamButton { id: hv3_on; text: "HV3 on"; }
                ApdcamButton { id: hv3_off; text: "HV3 off"; }

                Label { text: "HV3 set"; Layout.row: 4;}
                SpinBox { id: hv4_set; maximumValue: 2000; }
                Label { text: "actual"; }
                TextField { id: hv4_actual; enabled:false; width: 50;}
                ApdcamButton { id: hv4_on; text: "HV4 on"; }
                ApdcamButton { id: hv4_off; text: "HV4 off"; }
            }
        }
        RowLayout {
            Layout.fillWidth: true;

            GroupBox {
                title: "Detector temperature"
                RowLayout {
                    Label { text: "Set: " } 
                    SpinBox {id: detector_temperature_set; maximumValue: 100; }
                    Label { text: "Actual: "}
                    TextField { id: detector_temperature_actual; enabled: false; width: 50; }
                }
            }
            GroupBox {
                title: "Temperatures"
                GridLayout {
                    columns: 4;
                    Label { text: "Base: " } SpinBox { id: base_temperature; maximumValue: 100; } Label { text: "Amplifier: " } SpinBox { id: amplifier_temperature; maximumValue: 100; }
                    Label { text: "Power: " } SpinBox { id: power_temperature; maximumValue: 100; } Label { text: "Communication: " } SpinBox { id: communication_temperature; maximumValue: 100; }
                }
            }
        }
        RowLayout {
            Label { text: "Sample rate: " }
            ComboBox { model: ["4 MHz","2 MHz","1 MHz","500 kHz"] }
        }
        RowLayout {
            Label { text: "Clock source: " }
            ComboBox { model: ["Internal","External"] }
            Label { text: "Ext. clock: " }
            TextField { id: ext_clock; text: "---"; }
        }
        RowLayout {
            Label { text: "Calib. light: "}
            Slider { id: calib_light; minimumValue: 0; maximumValue: 1000; }
            Label { text: "Offset: "}
            SpinBox { id: calib_light_offset; minimumValue: 0; maximumValue: 100; }
        }
    }
}
