#ifndef __PCREGS_H__

#define __PCREGS_H__

#define PC_BOARD     2

//P&C Registers
// Control board functions

#define PC_REG_BOARD_VERSION     0x00
#define PC_REG_BOARD_VERSION_LEN 0x01

#define PC_REG_MC_VERSION     0x02
#define PC_REG_MC_VERSION_LEN 0x02
#define PC_REG_FW_VERSION     PC_REG_MC_VERSION
#define PC_REG_FW_VERSION_LEN PC_REG_MC_VERSION_LEN

#define PC_REG_BIAS_MONITOR     0x04
#define PC_REG_BIAS_MONITOR_LEN 0x02

#define PC_REG_TEMP_ADC     0x0C
#define PC_REG_TEMP_ADC_LEN 0x08

#define PC_REG_TEMP_DETECTOR     0x14
#define PC_REG_TEMP_DETECTOR_LEN 0x02

#define PC_REG_TEMP_ANALOG     0x16
#define PC_REG_TEMP_ANALOG_LEN 0x02

#define PC_REG_TEMP_DETHOUSE     0x18
#define PC_REG_TEMP_DETHOUSE_LEN 0x02

#define PC_REG_TEMP_PELTIER     0x1A
#define PC_REG_TEMP_PELTIER_LEN 0x02

#define PC_REG_TEMP_CONTROL     0x1C
#define PC_REG_TEMP_CONTROL_LEN 0x02

#define PC_REG_TEMP_BASE     0x1E
#define PC_REG_TEMP_BASE_LEN 0x02

#define PC_REG_TEMP_DAQ     0x28
#define PC_REG_TEMP_DAQ_LEN 0x02

#define PC_REG_PELTIER_OUT     0x2C
#define PC_REG_PELTIER_OUT_LEN 0x02

#define PC_REG_PID_P     0x50
#define PC_REG_PID_P_LEN 0x02

#define PC_REG_PID_I     0x52
#define PC_REG_PID_I_LEN 0x02

#define PC_REG_PID_D     0x54
#define PC_REG_PID_D_LEN 0x02

#define PC_REG_BIAS_SET     0x56
#define PC_REG_BIAS_SET_LEN 0x02

#define PC_REG_BIAS_ON     0x5E
#define PC_REG_BIAS_ON_LEN 0x01

#define PC_REG_BIAS_ENABLE     0x60
#define PC_REG_BIAS_ENABLE_LEN 0x01

#define PC_REG_DET_TEMP_SET     0x6A
#define PC_REG_DET_TEMP_SET_LEN 0x02

#define PC_REG_FAN_PELTIER     0x6C
#define PC_REG_FAN_PELTIER_LEN 0x01

#define PC_REG_FAN_ELECTRONICS     0x6E
#define PC_REG_FAN_ELECTRONICS_LEN 0x01

#define PC_REG_FAN_DAQ_DET     0x70
#define PC_REG_FAN_DAQ_DET_LEN 0x01

#define PC_REG_CALIB_LIGHT     0x7A
#define PC_REG_CALIB_LIGHT_LEN 0x02

#define PC_REG_SHUTTER_MODE     0x80
#define PC_REG_SHUTTER_MODE_LEN 0x01

#define PC_REG_SHUTTER_STATE     0x82
#define PC_REG_SHUTTER_STATE_LEN 0x01

#define PC_REG_FACTORY_RESET     0x84
#define PC_REG_FACTORY_RESET_LEN 0x01

#define PC_REG_ERROR_CODE     0x86
#define PC_REG_ERROR_CODE_LEN 0x01

#define PC_REG_BOARD_SERIAL     0x100
#define PC_REG_BOARD_SERIAL_LEN 0x02

#define PC_REG_BIAS_MAX     0x102
#define PC_REG_BIAS_MAX_LEN 0x02

#define PC_REG_HV1_MONITOR         0x04
#define PC_REG_HV2_MONITOR         0x06
#define PC_REG_HV3_MONITOR         0x08
#define PC_REG_HV4_MONITOR         0x0A
#define PC_REG_HV_MONITOR_LEN      0x02
#define PC_REG_ALL_HV_MONITORS_LEN 0x08

#define PC_REG_TEMP_SENSOR_1        0x0C
#define PC_REG_TEMP_SENSOR_2        0x0E
#define PC_REG_TEMP_SENSOR_3        0x10
#define PC_REG_TEMP_SENSOR_4        0x12
#define PC_REG_TEMP_SENSOR_5        0x14
#define PC_REG_TEMP_SENSOR_6        0x16
#define PC_REG_TEMP_SENSOR_7        0x18
#define PC_REG_TEMP_SENSOR_8        0x1A
#define PC_REG_TEMP_SENSOR_9        0x1C
#define PC_REG_TEMP_SENSOR_10       0x1E
#define PC_REG_TEMP_SENSOR_11       0x20
#define PC_REG_TEMP_SENSOR_12       0x22
#define PC_REG_TEMP_SENSOR_13       0x24
#define PC_REG_TEMP_SENSOR_14       0x26
#define PC_REG_TEMP_SENSOR_15       0x28
#define PC_REG_TEMP_SENSOR_16       0x2A
#define PC_REG_TEMP_SENSOR_LEN      0x02
#define PC_REG_ALL_TEMP_SENSORS_LEN 0x20

#define PC_REG_PELT_CONTROL_OUT     0x2C
#define PC_REG_PELT_CONTROL_OUT_LEN 0x02

#define PC_REG_P_GAIN   0x50
#define PC_REG_I_GAIN   0x52
#define PC_REG_D_GAIN   0x54
#define PC_REG_GAIN_LEN 0x02

#define PC_REG_HV1_SET    0x56
#define PC_REG_HV2_SET    0x58
#define PC_REG_HV3_SET    0x5A
#define PC_REG_HV4_SET    0x5C
#define PC_REG_HV_SET_LEN 0x02

#define PC_REG_HV_ON     0x5E
#define PC_REG_HV_ON_LEN 0x01

#define PC_REG_HV_ENABLE     0x60
#define PC_REG_HV_ENABLE_LEN 0x01

#define PC_REG_DETECTOR_TEMP_SET     0x6A
#define PC_REG_DETECTOR_TEMP_SET_LEN 0x02

#define PC_REG_FAN1_SPEED    0x6C
#define PC_REG_FAN2_SPEED    0x6E
#define PC_REG_FAN3_SPEED    0x70
#define PC_REG_FAN_SPEED_LEN 0x01

#define PC_REG_FAN1_TEMP_SET     0x72
#define PC_REG_FAN1_TEMP_SET_LEN 0x02
#define PC_REG_FAN1_TEMP_DIF     0x74
#define PC_REG_FAN1_TEMP_DIF_LEN 0x02
#define PC_REG_FAN2_TEMP_LIMIT    0x76
#define PC_REG_FAN3_TEMP_LIMIT    0x78
#define PC_REG_FAN_TEMP_LIMIT_LEN 0x02

// CALIB_LIGHT 12 bit
#define PC_REG_CALIB_LIGHT     0x7A
#define PC_REG_CALIB_LIGHT_LEN 0x02

#define PC_REG_SHMODE     0x80
#define PC_REG_SHMODE_LEN 0x01

#define PC_REG_SHSTATE     0x82
#define PC_REG_SHSTATE_LEN 0x01

// Factory write enable
#define PC_REG_FACTORY_WRITE_ENABLE 0x88
#define PC_REG_FACTORY_WRITE_LEN    0x02
#define PC_REG_FACTORY_WRITE_CODE   0x00CD

#define PC_REG_BOARD_SERIAL     0x100
#define PC_REG_BOARD_SERIAL_LEN 0x02

/* ****** PC Calibration (factory) table ****** */
#define PC_REG_CALIBRATION_TABLE     0x200
#define PC_REG_CALIBRATION_TABLE_LEN 0xB2

// Table version
#define PC_REG_TABLE_VERSION     0x200
#define PC_REG_TABLE_VERSION_LEN 0x01
// Table status
#define PC_REG_TABLE_STATUS     0x201
#define PC_REG_TABLE_STATUS_LEN 0x01
// float InputHVCalib[2];
#define PC_REG_INPUT_HV_CALIB     0x202
#define PC_REG_INPUT_HV_CALIB_LEN 0x08
// float OutputHVCalib[2];
#define PC_REG_OUTPUT_HV_CALIB     0x20A
#define PC_REG_OUTPUT_HV_CALIB_LEN 0x08
// short int TempCalib[16];
#define PC_REG_TEMP_CALIB     0x212
#define PC_REG_TEMP_CALIB_LEN 0x20
// unsigned short MinHV;
#define PC_REG_MIN_HV     0x232
#define PC_REG_MIN_HV_LEN 0x02
// unsigned char GainTable[256]; // Must be replaced with a meaningfull structure.
#define PC_REG_GAIN_TABLE     0x234
#define PC_REG_GAIN_TABLE_LEN 0x64
// unsigned short GainVolts[8];
#define PC_REG_GAIN_VOLTS     0x298
#define PC_REG_GAIN_VOLTS_LEN 0x10
// unsigned short GainTemps[5];
#define PC_REG_GAIN_TEMPS     0x2A8
#define PC_REG_GAIN_TEMPS_LEN 0x0A
//new OutputHVCalib, 4 HV values
#define PC_REG_OUTPUT_HV_CALIB_2     0x2B2
#define PC_REG_OUTPUT_HV_CALIB_2_LEN 0x08

#endif  /* __PCREGS_H__ */
