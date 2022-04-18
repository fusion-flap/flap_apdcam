#pragma once
#ifndef __APDLIB_H__

#define __APDLIB_H__

#include "TypeDefs.h"

#ifdef __cplusplus
extern "C"
{
#endif

void APDCAM_Init();
void APDCAM_Done();
void APDCAM_GetSWOptios();

void APDCAM_FindFirst(ApdCam10G_t *devices, UINT32 from_ip_h, UINT32 to_ip_h, const char *filter_str = NULL, int timeout = 1000);
void APDCAM_List(UINT32 from_ip_h, UINT32 to_ip_h, UINT32 *ip_table, int table_size, int *no_of_elements, const char *filter_str = NULL, int timeout = 1000);
void APDCAM_Find(ApdCam10G_t *devices, UINT32 from_ip_h, UINT32 to_ip_h, UINT32 *ip_table, int table_size, int *no_of_elements, const char *filter_str = NULL, int timeout = 1000);

//--------------------------
ADT_RESULT APDCAM_WritePDI(ADT_HANDLE handle, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes);
ADT_RESULT APDCAM_ReadPDI(ADT_HANDLE handle, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes);
ADT_RESULT APDCAM_SetupAllTS(ADT_HANDLE handle);
ADT_RESULT APDCAM_ShutupAllTS(ADT_HANDLE handle);
//--------------------------

ADT_HANDLE APDCAM_Open(UINT32 ip_h);
ADT_HANDLE APDCAM_OpenDevice(ApdCam10G_t *device);
ADT_RESULT APDCAM_Save(ADT_HANDLE handle, uint64_t sampleCount);
ADT_RESULT APDCAM_Close(ADT_HANDLE handle);

ADT_RESULT APDCAM_SyncADC(ADT_HANDLE handle);
ADT_RESULT APDCAM_SetAllOffset(ADT_HANDLE handle, unsigned int offset);

//ADT_RESULT APDCAM_Test(ADT_HANDLE handle);

// If sampleCount < 0 uses default (read back from the APD). For valid values sampleCount must be in thr 0 < sampleCount < 0xFFFFFFFF range.
// sampleCount allocated buffer size
// If bits < 0, uses default (read back from APD). The valid values are 8,12,14
// If The channelMask_n < 0 uses default. Else they must be in 0 <= channelMask_n <= 255.
ADT_RESULT APDCAM_Allocate(ADT_HANDLE handle, uint64_t sampleCount, int bits, uint32_t channelMask_1, uint32_t channelMask_2, uint32_t channelMask_3, uint32_t channelMask_4, int primary_buffer_size = 10);
ADT_RESULT APDCAM_GetBuffers(ADT_HANDLE handle, INT16 **buffers);
ADT_RESULT APDCAM_GetSampleInfo(ADT_HANDLE handle, ULONGLONG *sampleCounts, ULONGLONG *sampleIndices);

ADT_RESULT APDCAM_SetTiming(ADT_HANDLE handle, int basicPLLmul, int basicPLLdiv_0, int basicPLLdiv_1, int clkSorce, int extDCMmul, int extDCMdiv);
ADT_RESULT APDCAM_Sampling(ADT_HANDLE handle, int sampleDiv, int sampleSrc);

// sampleCount: requested data volume.
// mode = MM_ONE_SHOT, MM_CYCLIC
// calibrated or non-calibrated mode ?
ADT_RESULT APDCAM_ARM(ADT_HANDLE handle, ADT_MEASUREMENT_MODE mode, uint64_t sampleCount, ADT_CALIB_MODE calibMode, int signalFrequency = 100);
ADT_RESULT APDCAM_Trigger(ADT_HANDLE handle, ADT_TRIGGER trigger, ADT_TRIGGER_MODE mode, ADT_TRIGGER_EDGE edge, int triggerDelay, ADT_TRIGGERINFO* triggerInfo);

ADT_RESULT APDCAM_StreamDump(ADT_HANDLE handle, uint8_t streamNo, const char *dumpFileName);
ADT_RESULT APDCAM_Start(ADT_HANDLE handle);
ADT_RESULT APDCAM_Wait(ADT_HANDLE handle, int timeout);
ADT_RESULT APDCAM_Stop(ADT_HANDLE handle);
ADT_RESULT APDCAM_SWTrigger(ADT_HANDLE handle);

ADT_RESULT APDCAM_SetIP(ADT_HANDLE handle, UINT32 ip_h);
ADT_RESULT APDCAM_SetStreamInterface(ADT_HANDLE handle, const char *ifname);

ADT_RESULT APDCAM_DataMode(ADT_HANDLE handle, int modeCode);
ADT_RESULT APDCAM_Filter(ADT_HANDLE handle, FILTER_COEFFICIENTS filterCoefficients);

ADT_RESULT APDCAM_Gain(ADT_HANDLE handle, double highVoltage1, double highVoltage2, double highVoltage3, double highVoltage4, int state); // BIAS_ON ENABLE SET (Voltban) converzios faktor a tablazatban:Output HV statusban olvas:Input
ADT_RESULT APDCAM_GetHV(ADT_HANDLE handle, double &highVoltage1, double &highVoltage2, double &highVoltage3, double &highVoltage4, int &state);

ADT_RESULT APDCAM_Shutter(ADT_HANDLE handle, int open);
ADT_RESULT SetShutterMode(ADT_HANDLE handle, int mode);
ADT_RESULT GetShutterMode(ADT_HANDLE handle, int *mode);

ADT_RESULT APDCAM_CalibLight(ADT_HANDLE handle, int value);
ADT_RESULT APDCAM_GetCalibLight(ADT_HANDLE handle, int *value);

ADT_RESULT APDCAM_SetRingbufferSize(ADT_HANDLE handle, unsigned short bufferSize);
ADT_RESULT APDCAM_GetRingbufferSize(ADT_HANDLE handle, unsigned short *bufferSize);

/* Not realized yet */



ADT_RESULT APDCAM_Calibrate(ADT_HANDLE handle);

ADT_RESULT APDCAM_MeasMode(ADT_HANDLE handle);
ADT_RESULT APDCAM_SetOffset(ADT_HANDLE handle);


// APD-ben. Atszamolas
ADT_RESULT APDCAM_Overload(ADT_HANDLE handle);

// Kellene egy szal, ami periodikusan kiolvassa a statuszokat.
/*
rendszerido
struktura tomb, utolso valahany status meres
fix meretu (10.000-es meretu), 1 s, forditasi parameter.
statusz:
ADC
3 pll status
4 db mintaszam
overload status

APD
homersekletek 5 adc + kb 5 mashol homeresklet + power1 & power2 csak az ujban. 16 helyet fenntartunk.
4 dv highVoltage: detector bias voltage (bias monitor)
peltier out
3 fan allapotok
error code
shutter_state
calibration light
Analog power (meg nincs de majd lesz) 

*/
/* APD panel felkapcsolasa meg nincs de lesz. sorozatszam fuggo.*/

//ADT_RESULT APDCAM_CalibLight(ADT_HANDLE handle);
//ADT_RESULT APDCAM_Shutter(ADT_HANDLE handle);

ADT_RESULT APDCAM_Temperature(ADT_HANDLE handle); // Csak a detektor referencia homersekletete


ADT_RESULT APDCAM_Control(ADT_HANDLE handle);// Analog power bit allitas, meg nincs. hiba ertek, ha a kamera nem tudja. gyari szam alapjan. 5 folott uj


ADT_RESULT APDCAM_Fans(ADT_HANDLE handle);
ADT_RESULT APDCAM_Reset(ADT_HANDLE handle);
//ADT_RESULT APDCAM_Calibrate(ADT_HANDLE handle);
ADT_RESULT APDCAM_SaveCalibration(ADT_HANDLE handle);
ADT_RESULT APDCAM_LoadCalibration(ADT_HANDLE handle);
ADT_RESULT APDCAM_SaveSetup(ADT_HANDLE handle);
ADT_RESULT APDCAM_LoadSetup(ADT_HANDLE handle);
ADT_RESULT APDCAM_GetStatus(ADT_HANDLE handle);
ADT_RESULT APDCAM_GetInfo(ADT_HANDLE handle);
ADT_RESULT APDCAM_CheckSetup(ADT_HANDLE handle);

//10G fuggvenyek
ADT_RESULT APDCAM_CCControl(ADT_HANDLE handle, int opcode, int length, unsigned char *buffer);
ADT_RESULT APDCAM_ReadCC(ADT_HANDLE handle, int acktype, unsigned char *value, int firstreg, int length);
ADT_RESULT APDCAM_ReadFlashPage(ADT_HANDLE, int PgAddress, unsigned char *value);
ADT_RESULT APDCAM_StartFUP(ADT_HANDLE handle);
ADT_RESULT APDCAM_SetBasicPLL(ADT_HANDLE handle, unsigned char mul, unsigned char div0, unsigned char div1);

#ifdef __cplusplus
}
#endif

#endif  /* __APDLIB_H__ */
