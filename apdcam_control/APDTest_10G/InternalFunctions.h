#pragma once
#ifndef __INTERNALFUNCTIONS_H__

#define __INTERNALFUNCTIONS_H__

#include "TypeDefs.h"
class CAPDClient;

#define ADC_BOARD 8
#define PC_BOARD 2

// Calibration data structures
// AFD: ADC or APD Factory Data
enum ADT_FACTORY_DATA {
// ADC factory table
	AFD_PRODUCT_CODE, AFD_ADC_TABLE_VERSION, AFD_ADC_TABLE_STATUS, AFD_ADC_LOW_LIMIT,
	AFD_ADC_HIGH_LIMIT, AFD_ADC_BLOCK_CAL, AFD_ADC_OFFSET, AFD_DAC_OFFSET,
	AFD_DAC_BLOCK_CAL, AFD_ANALOF_BW1, AFD_ANALOG_BW2, AFD_ANALOG_CONVERSION,
	AFD_MAX_OFFSET, AFD_DETECTOR_ID,
// PC Factory table
	AFD_PC_TABLE_VERSION, AFD_PC_TABLE_STATUS, AFD_INPUT_HV_CALIB, AFD_OUTPUT_HV_CALIB,
	AFD_TEMP_CALIB, AFD_MIN_HV, AFD_GAIN_TABLE, AFD_GAIN_VOLTS, 
	AFD_GAIN_TEMPS, AFD_OUTPUT_HV_CALIB_2
};

typedef struct
{
	union
	{
// ADC related fields
		char ProductCode[6];
		unsigned char ADCTableVersion;
		unsigned char ADCTableStatus;
		unsigned short ADCLowLimit;
		unsigned short ADCHighLimit;
		float ADCBlockCali[4];
		unsigned short ADCOffset[32];
		unsigned short DACOffset[32];
		float DACBlockCali[2];
// The following fields are in the ADC table, but realy releted to the APD control card.
		float AnalogBW1;
		float AnalogBW2;
		float AnalogConversion;
		unsigned short MaxOffset;
		unsigned char DetectorId[10];
// APD related fields
		unsigned char PCTableVersion;
		unsigned char PCTableStatus;
		float InputHVCalib[2];
		float OutputHVCalib[2];
		short int TempCalib[16];
		unsigned short MinHV;
		unsigned char GainTable[256]; // Must be replaced with a meaningfull structure.
		unsigned short GainVolts[8];
		unsigned short GainTemps[5];
		float OutputHVCalib2[2];
// General buffer
		unsigned char data[256];
	};
}FACTORY_DATA;

bool syncADCs(CAPDClient * client, int numADC, int * addresses);
bool setAllOffset(CAPDClient *  client, int numADC, int * addresses, unsigned int offset);

bool EnumerateADCBoards(CAPDClient *client, ApdCam10G_t *device);

bool GetADCBoardVersion(CAPDClient *client, unsigned char *boardVersion, UINT32 ipAddress_h, UINT16 ipPort_h, int timeout);
bool GetADCBoardVersion(CAPDClient *client, unsigned char *boardVersion);
bool GetADCBoardVersion(CAPDClient *client, unsigned char address, unsigned char *boardVersion);
bool GetMCVersion(CAPDClient *client, unsigned char address, UINT16 *mcVersion);
bool GetADCSerial(CAPDClient *client, unsigned char address, UINT16 *serial);
bool GetFPGAVersion(CAPDClient *client, unsigned char address, UINT16 *fpgaVersion);

bool GetBoardTemp(CAPDClient *client, unsigned char address, unsigned char *temp);

bool GetControl(CAPDClient *client, unsigned char address, unsigned char *control);

bool GetStatus1(CAPDClient *client, unsigned char address, unsigned char *status1);
bool GetStatus2(CAPDClient *client, unsigned char address, unsigned char *status2);

bool SetADCControl(CAPDClient *client, unsigned char address, unsigned char adcControl);
bool GetADCControl(CAPDClient *client, unsigned char address, unsigned char *adcControl);

bool SetADCPLLMult(CAPDClient *client, unsigned char address, unsigned char mult);
bool GetADCPLLMult(CAPDClient *client, unsigned char address, unsigned char *mult);

bool SetADCPLLDiv(CAPDClient *client, unsigned char address, unsigned char div);
bool GetADCPLLDiv(CAPDClient *client, unsigned char address, unsigned char *div);

bool SetADCPLL(CAPDClient *client, unsigned char address, unsigned char mult, unsigned char div);
bool GetADCPLL(CAPDClient *client, unsigned char address, unsigned char *mult, unsigned char *div);

bool SetStreamPLLMult(CAPDClient *client, unsigned char address, unsigned char mult);
bool GetStreamPLLMult(CAPDClient *client, unsigned char address, unsigned char *mult);

bool SetStreamPLLDiv(CAPDClient *client, unsigned char address, unsigned char div);
bool GetStreamPLLDiv(CAPDClient *client, unsigned char address, unsigned char *div);

bool SetStreamPLL(CAPDClient *client, unsigned char address, unsigned char mult, unsigned char div);
bool GetStreamPLL(CAPDClient *client, unsigned char address, unsigned char *mult, unsigned char *div);

bool SetStreamControl(CAPDClient *client, unsigned char address, unsigned char streamControl);
bool GetStreamControl(CAPDClient *client, unsigned char address, unsigned char *streamControl);

bool GetSampleCount(CAPDClient *client, uint8_t streamNum, uint64_t *sampleCount);
bool GetSampleCounts(CAPDClient *client, uint64_t *sampleCounts);

bool SetChannel_1(CAPDClient *client, unsigned char address, unsigned char channelMask_1);
bool SetChannel_2(CAPDClient *client, unsigned char address, unsigned char channelMask_2);
bool SetChannel_3(CAPDClient *client, unsigned char address, unsigned char channelMask_3);
bool SetChannel_4(CAPDClient *client, unsigned char address, unsigned char channelMask_4);
bool SetChannels(CAPDClient *client, unsigned char address, unsigned char channelMask_1, unsigned char channelMask_2, unsigned char channelMask_3, unsigned char channelMask_4);
bool GetChannels(CAPDClient *client, unsigned char address, unsigned char *channelMask_1, unsigned char *channelMask_2, unsigned char *channelMask_3, unsigned char *channelMask_4);

bool SetRingbufferSize(CAPDClient *client, unsigned char address, UINT16 bufferSize);
bool GetRingbufferSize(CAPDClient *client, unsigned char address, UINT16 *bufferSize);

bool SetResolution(CAPDClient *client, unsigned char address, int bitNum);
bool GetResolution(CAPDClient *client, unsigned char address, int *bitNum);


bool SetTestMode(CAPDClient *client, unsigned int mode);
bool GetTestMode(CAPDClient *client, unsigned int *mode);

bool FactoryReset(CAPDClient *client, unsigned char address);

bool GetBytesPerSample(CAPDClient *client, unsigned char address, unsigned int *counters);


/* These are 32x2 byte offset settings for the 32 analog channels. Standard values are 500...1000 */
bool SetDACOffset(CAPDClient *client, INT16 *offsets, int first, int no);
bool GetDACOffset(CAPDClient *client, INT16 *offsets, int first, int no);

/* 32x2 bytes internal trigger setting for each channel */
bool SetInternalTriggerLevels(CAPDClient *client, UINT16 *levels);
bool GetInternalTriggerLevels(CAPDClient *client, UINT16 *levels);

/* 4x4 byte indicating the number of acquired samples per stream */
bool GetAquiredSampleCount(CAPDClient *client, unsigned int *counters);

bool SetOverloadLevel(CAPDClient *client, unsigned char address, UINT16 level);
bool GetOverloadLevel(CAPDClient *client, unsigned char address, UINT16 *level);

bool SetOverloadStatus(CAPDClient *client, unsigned char address, unsigned char status);
bool GetOverloadStatus(CAPDClient *client, unsigned char address, unsigned char *status);

bool SetOverloadTime(CAPDClient *client, unsigned char address, UINT16 time);
bool GetOverloadTime(CAPDClient *client, unsigned char address, UINT16 *time);

#if 0
bool SetTriggerDelay(CAPDClient *client, unsigned char address, unsigned int delay);
bool GetTriggerDelay(CAPDClient *client, unsigned char address, unsigned int *delay);
#endif

/* 8 signed 16 bit integer coefficients for digital filters */
bool SetFilterCoefficients(CAPDClient *client, unsigned char address, UINT16 *coefficints);
bool GetSetFilterCoefficients(CAPDClient *client, unsigned char address, UINT16 *coefficints);


// Calibration table handling routines
// Values - stored in the calibration table - not efect the hardware. That table is a non-volative storage place only.
bool RetrieveADCSerialNo(CAPDClient *client, unsigned char boardVersion, char *serial_no, int len, UINT32 ip_h = 0, UINT16 port_h = 0);
bool StoreADCOffsets_01mV(CAPDClient *client, INT16 *adcOffsets, int first, int no);
bool RetrieveADCOffsets_01mV(CAPDClient *client, INT16 *adcOffsets, int first, int no);
bool StoreDACOffsets_01mV(CAPDClient *client, INT16 *dacOffsets, int first, int no);
bool RetrieveDACOffsets_01mV(CAPDClient *client, INT16 *dacOffsets, int first, int no);
bool StoreADCOffsets(CAPDClient *client, INT16 *adcOffsets, int first, int no);
bool RetrieveADCOffsets(CAPDClient *client, INT16 *adcOffsets, int first, int no);

//P&C Commands

bool GetPCSerial(CAPDClient *client, uint16_t *serial);
bool GetPCFWVersion(CAPDClient *client, unsigned char *ver);
bool GetAllHVMonitor(CAPDClient *client, unsigned short *binValues);
bool GetAllTempSensors(CAPDClient *client, double *values);
bool SetHV1(CAPDClient *client, int binValue);
bool GetHV1(CAPDClient *client, int *binValue);
bool SetHV2(CAPDClient *client, int binValue);
bool GetHV2(CAPDClient *client, int *binValue);
bool SetHV3(CAPDClient *client, int binValue);
bool GetHV3(CAPDClient *client, int *binValue);
bool SetHV4(CAPDClient *client, int binValue);
bool GetHV4(CAPDClient *client, int *binValue);
bool SetHVState(CAPDClient *client, int state);
bool GetHVState(CAPDClient *client, int *state);
bool EnableHV(CAPDClient *client, bool enable);
bool SetCalibLight(CAPDClient *client, int current);
bool GetCalibLight(CAPDClient *client, int *current);
bool SetShutterMode(CAPDClient *client, int mode);
bool GetShutterMode(CAPDClient *client, int *mode);
bool SetShutterState(CAPDClient *client, int state);
bool GetShutterState(CAPDClient *client, int *state);
bool SetAnalogPower(CAPDClient *client, int state);
bool GetAnalogPower(CAPDClient *client, int *state);

bool EnableFactoryWrite(CAPDClient *client, int boardId, bool enable);
bool SetFactoryData(CAPDClient *client, ADT_FACTORY_DATA dataType, FACTORY_DATA* pFactoryData);
bool GetFactoryData(CAPDClient *client, ADT_FACTORY_DATA dataType, FACTORY_DATA* pFactoryData);


//10Gb C&C commands

bool GetCCReg(CAPDClient *client, int acktype, unsigned char *value, int firstreg, int length, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0, int timeout = 5000);

bool GetFlashPage(CAPDClient *client, int PgAddress, unsigned char *value, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0, int timeout = 5000);

bool StartFirmwareUpdate(CAPDClient * client, unsigned char * date, UINT32 ipAddress_h = 0, UINT16 iiPort_h = 0, int timeout =  5000);

bool GetCCDeviceType(CAPDClient *client, uint16_t *deviceType, UINT32 ipAddress_h, UINT16 ipPort_h, int timeout);

bool GetCCStreamSerial(CAPDClient *client, uint32_t *serial);

bool SetBasicPLL(CAPDClient *client, unsigned char  mul, unsigned char  div0, unsigned char  div1);
bool GetBasicPLL(CAPDClient *client, unsigned char *mul, unsigned char *div0, unsigned char *div1);

bool SetExtDCM(CAPDClient *client, unsigned char  mul, unsigned char  div);
bool GetExtDCM(CAPDClient *client, unsigned char *mul, unsigned char *div);

bool SetClockControl(CAPDClient *client, unsigned char  adClockSource, unsigned char  extClockMode, unsigned char  sampleSource);
bool GetClockControl(CAPDClient *client, unsigned char *adClockSource, unsigned char *extClockMode, unsigned char *sampleSource);

bool SetClockEnable(CAPDClient *client, unsigned char  eioSampleOut, unsigned char  controlSampleOut, unsigned char  eioClockOut, unsigned char  controlClockOut);
bool GetClockEnable(CAPDClient *client, unsigned char *eioSampleOut, unsigned char *controlSampleOut, unsigned char *eioClockOut, unsigned char *controlClockOut);

bool SetSampleDiv(CAPDClient *client, UINT16  sampleDiv);
bool GetSampleDiv(CAPDClient *client, UINT16 *sampleDiv);

bool SetCCStreamControl(CAPDClient *client, unsigned char  streamControl);
bool GetCCStreamControl(CAPDClient *client, unsigned char *streamControl);

bool SetCCSampleCount(CAPDClient *client, uint64_t  sampleCount);
bool GetCCSampleCount(CAPDClient *client, uint64_t *sampleCount);

bool SetTrigger(CAPDClient *client, ADT_TRIGGER_MODE  triggerSource, ADT_TRIGGER_EDGE  triggerEdge, uint32_t  delay);
bool SetTrigger(CAPDClient *client, ADT_TRIGGER_CONTROL  triggerControl, uint32_t triggerDelay);
bool GetTrigger(CAPDClient *client, ADT_TRIGGER_CONTROL *triggerControl, uint32_t *triggerDelay);
bool GetTrigger(CAPDClient *client, ADT_TRIGGER_MODE *triggerSource, ADT_TRIGGER_EDGE *triggerEdge, uint32_t *delay);

bool ClearTrigger(CAPDClient *client);

bool SetMulticastUDPStream(CAPDClient *client, uint8_t streamNum, uint16_t octet, uint32_t ip_h, uint16_t port);
bool SetUDPStream(CAPDClient *client, uint8_t streamNum, uint16_t octet, uint8_t mac[6], uint32_t ip_h, uint16_t port);

#endif  /* __INTERNALFUNCTIONS_H__ */
