// APDTest.cpp : Converted from the Windows version on 30.09.2012
//

//#include "stdafx.h"
//#include "char.h"
//#include "ShortTextFile.h"
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

#include "helper.h"
#include "APDLib.h"

#define MAX_RW_BYTES      1030  // Maximum number of bytes in register read/write
#define MAX_LINE_LENGTH   (5 * 1030)

int ProcessLine(char *buffer);

ADT_HANDLE g_handle = 0;
int g_sampleCount = 0;

int Open(char *param0, int ignore_errors);
int Close();

int ReadLine(FILE * f, char * buffer, int size);
char *GetToken(char *str, char *token);
char *GetString(char *str, char *param);
char *GetInt(char *str, int *param);



int main(int argc, char* argv[])
{
	printf("APDTest Version 2.2\nFusion Instruments Kft.\nwww.fusioninstruments.com\n\n");
	fflush(stdout);
	APDCAM_Init();

	char batchFileName[512];
	strcpy(batchFileName, "APDMain.txt");

	FILE * batchFile;

	if (argc > 1)
	{
		strcpy(batchFileName, argv[1]);
	}

	if ((batchFile = fopen(batchFileName, "rt")) == NULL)
	{
		fprintf(stderr, "%s file not found\n", batchFileName);
		return 1;
	}

	while (!feof(batchFile))
	{
		char buffer[MAX_LINE_LENGTH];
		ReadLine(batchFile, buffer, sizeof(buffer));
		if (ProcessLine(buffer) < 0)
		{
			break;
		}
	}

	fclose(batchFile);

	APDCAM_Done();
	return 0;
}

char *GetToken(char *str, char *token)
{
	while (*str == ' ')
		str++;

	char *p = str;
	int c = 0;
	while (*p != '\0' && *p != ' ')
	{
		p++;
		c++;
	}
	if (c)
		memcpy(token, str, c);
	token[c] = '\0';
	while (*p == ' ')
		p++;
	return p;
}

char *GetString(char *str, char *param)
{
	while (*str == ' ') str++;
	char *p = str;
	int c = 0;
	while (*p != 0 && *p !=' ')
	{
		p++; c++;
	}
	if (c) memcpy(param, str, c);
	param[c] = '\0';
	while (*p == ' ') p++;
	return p;
}

char *GetInt(char *str, int *param)
{
	char strParam[64];
	char *p = GetString(str, strParam);

	if (p != str)
	{
		if (strParam[0] == '0' && (strParam[1] == 'x' || strParam[1] == 'X'))
			*param = strtol(strParam, NULL, 16);
		else
			*param = atoi(strParam);
	}
	return p;
}


void SwOptions()
{
	APDCAM_GetSWOptios();
}

int Open(char *param0, int ignore_errors)
{
	ApdCam10G_t devices;

	devices.ip = ntohl(inet_addr(param0));
	APDCAM_FindFirst(&devices, devices.ip, devices.ip, NULL, 5000);

	if (devices.numADCBoards == 0 && ignore_errors == 0)
		return -1;

	printf("%d ADCs found\n", devices.numADCBoards);
	fflush(stdout);
	if (devices.numADCBoards || ignore_errors)
		g_handle = APDCAM_OpenDevice(&devices);
	else
		g_handle = APDCAM_Open(devices.ip);

	if (g_handle == 0)
		return -1;

	return 0;
}

int Close()
{
	if (g_handle != 0)
	{
		APDCAM_Close(g_handle);
		g_handle = 0;
	}
	return 0;
}

int SetTiming(int basicPLLmul, int basicPLLdiv_0, int basicPLLdiv_1, int clkSrc, int extDCMmul, int extDCMdiv)
{
//printf("SetTiming  %d %d %d %d %d %d %d\n",adcMult, adcDiv,strMult, strDiv, clkSrc,clkMult, clkDiv);
	ADT_RESULT res = APDCAM_SetTiming(g_handle, basicPLLmul, basicPLLdiv_0, basicPLLdiv_1, clkSrc, extDCMmul, extDCMdiv);
	if (res != ADT_OK) return -1;
	return 0;
}

int Sampling(int sampleDiv, int sampleSrc)
{
//printf("Sampling %d %d\n",sampleDiv,sampleSrc);
	ADT_RESULT res = APDCAM_Sampling(g_handle, sampleDiv, sampleSrc);
	if (res != ADT_OK) return -1;
	return 0;
}

int Allocate(LONGLONG sampleCount, int bits, uint32_t channelMask_1, uint32_t channelMask_2, uint32_t channelMask_3, uint32_t channelMask_4, int primaryBufferSize)
{
//printf("Allocate %d %d %d %d %d %d\n",bits,channelMask_1,channelMask_2,channelMask_3,channelMask_4,primaryBufferSize);
	ADT_RESULT res = APDCAM_Allocate(g_handle, sampleCount, bits, channelMask_1, channelMask_2, channelMask_3, channelMask_4, primaryBufferSize);
	if (res != ADT_OK) return -1;
	return 0;
}

int ARM(int measurementMode, int sampleCount, int calibrationMode, int signalFrequency)
{
	ADT_MEASUREMENT_MODE amm;
	switch (measurementMode)
	{
		case 0:
			amm = MM_ONE_SHOT;
			break;
		case 1:
			amm = MM_CYCLIC;
			break;
		default:
			return -1;
			break;
	}

	ADT_CALIB_MODE acm;
	switch (calibrationMode)
	{
		case 0:
			acm = CM_NONCALIBRATED;
			break;
		case 1:
			acm = CM_CALIBRATED;
			break;
		default:
			return -1;
			break;
	}

	g_sampleCount = sampleCount;

	if (APDCAM_ARM(g_handle, amm, sampleCount, acm, signalFrequency) == ADT_OK)
		return 0;

	return -1;
}


// triggerSource 0:software, 1:hardware
// triggerMode 0:external (hardware), 1:internal (hardware)
// triggerEdge 0:rising, 1:falling
int Trigger(int triggerSource, int triggerMode, int triggerEdge, int delay, char * triggerFileName)
{
/*
This will be needed for internal trigger
S. Zoletnik 8.9.2018
	if (g_handle == 0)
	{
		fprintf(stderr,"Error in trigger. Camera not open.");
		fflush(stderr);
		return -1;
	}

	int index = GetIndex(g_handle);
	if (index < 0)
	{
		fprintf(stderr,"Error in trigger. Camera not open.");
		fflush(stderr);
		return -1;
	}
	WORKING_SET &WorkingSet = g_WorkingSets[index];
	int channelNumber =  WorkingSet.n_streams*32;

	ADT_TRIGGERINFO trigger[channelNumber];
	LoadTriggerInfo(triggerFileName, trigger, channelNumber);
*/


	ADT_TRIGGER ts;
	switch (triggerSource)
	{
	case 0:
		ts = TR_SOFTWARE;
		break;
	case 1:
		ts = TR_HARDWARE;
		break;
	default:
		return -1;
		break;
	}

	ADT_TRIGGER_MODE tm;
	switch (triggerMode)
	{
	case 0:
		tm = TRM_EXTERNAL;
		break;
	case 1:
		tm = TRM_INTERNAL;
		break;
	default:
		return -1;
		break;
	}

	ADT_TRIGGER_EDGE te;
	switch (triggerEdge)
	{
	case 0:
		te = TRE_RISING;
		break;
	case 1:
		te = TRE_FALLING;
		break;
	default:
		return -1;
		break;
	}

	ADT_RESULT res = APDCAM_Trigger(g_handle, ts, tm, te, delay, NULL);
	if (res != ADT_OK) return -1;
	return 0;
}


int Start()
{
	ADT_RESULT res = APDCAM_Start(g_handle);
	if (res != ADT_OK) return -1;
	return 0;
}

int Wait(int timeout)
{
	ADT_RESULT res = APDCAM_Wait(g_handle, timeout);
	if (res != ADT_OK) return -1;
	return 0;
}

int Stop()
{
	ADT_RESULT res = APDCAM_Stop(g_handle);
	if (res != ADT_OK) return -1;
	return 0;
}

int APDTest_Save(int ndata)
{
//	ULONGLONG sampleCounts[4];
//	ULONGLONG sampleIndices[4];
//	ADT_RESULT res = APDCAM_GetSampleInfo(g_handle, sampleCounts, sampleIndices);
//	if (res != ADT_OK) return -1;
//	printf("Save %d \n",ndata);
	APDCAM_Save(g_handle, ndata);

	return 0;
}


/*
 * DATAMODE
 */
int DataMode(int mode)
{
	if (APDCAM_DataMode(g_handle, mode) == ADT_OK)
		return 0;
	return -1;
}


int Filter(int *coeffs)
{
	FILTER_COEFFICIENTS filterCoefficients;
	filterCoefficients.FIR[0] = coeffs[0];
	filterCoefficients.FIR[1] = coeffs[1];
	filterCoefficients.FIR[2] = coeffs[2];
	filterCoefficients.FIR[3] = coeffs[3];
	filterCoefficients.FIR[4] = coeffs[4];
	filterCoefficients.RecursiveFilter = coeffs[5];
	filterCoefficients.Reserved = 0;
	filterCoefficients.FilterDevideFactor = 9;
	ADT_RESULT res = APDCAM_Filter(g_handle, filterCoefficients);
	if (res != ADT_OK) return -1;
	return 0;
}


int Calibrate()
{
	ADT_RESULT res = APDCAM_Calibrate(g_handle);
	if (res != ADT_OK) return -1;
	return 0;
}


int LoadTriggerInfo(char *fileName, ADT_TRIGGERINFO *trigger, int channelNumber)
{
	
	FILE * triggerFile;
	if ((triggerFile = fopen(fileName,"rt")) == NULL)
	{
		for (int i=0; i<channelNumber; i++) {
			trigger[i].TriggerLevel = 0;
			trigger[i].Sensitivity = 0;
			trigger[i].Enable = 0;
		}
		fprintf(stderr, "Warning. %s trigger file not found, internal trigger disabled.\n", fileName);
		fflush(stderr);
		return -1;
	}

	int index = 0;
	while (!feof(triggerFile) && index < channelNumber)
	{
		char buffer[MAX_LINE_LENGTH];
		char *p;
		ReadLine(triggerFile, buffer, sizeof(buffer));
		int level = 0;
		int sensitivity = 0;
		int enable = 0;
		if (strlen(buffer) == 0) return -1;
		p = GetInt(buffer, &level);
		if (p == NULL)  
		{
			fprintf(stderr, "Warning. Invalid trigger file.\n");
			fflush(stderr);
			return -1;
		}	
		p = GetInt(p, &sensitivity);
		if (p == NULL)
		{
			fprintf(stderr, "Warning. Invalid trigger file.\n");
			fflush(stderr);
			return -1;
		}	
		p = GetInt(p, &enable);
		{
			fprintf(stderr, "Warning. Invalid trigger file.\n");
			fflush(stderr);
			return -1;
		}	

		trigger[index].TriggerLevel = level;
		trigger[index].Sensitivity = sensitivity;
		trigger[index].Enable = enable;

		index++;
	}
	fclose(triggerFile);
	if (index < channelNumber) 
	{
		fprintf(stderr, "Error in trigger. Too short trigger file .\n");
		fflush(stderr);
		return -1;
	}	
	return 0;
}


/*
 * READ
 */
int Read(unsigned char address, UINT32 subaddress, int numbytes)
{
	if (numbytes > MAX_RW_BYTES)
	{
		fprintf(stderr, "Error, cannot read %d bytes truncating to %d!\n", numbytes, MAX_RW_BYTES);
		fflush(stderr);
	}

	if (g_handle != 0)
	{
		unsigned char data[MAX_RW_BYTES];
		numbytes = (numbytes > MAX_RW_BYTES) ? MAX_RW_BYTES : numbytes;

		if (APDCAM_ReadPDI(g_handle, address, subaddress, (unsigned char *)&data, numbytes) == ADT_OK)
		{
			printf("READ result, Address: %d, subaddress: %d, data: ", address, subaddress);
			for (int i = 0; i < numbytes; ++i)
				printf("%d ",data[i]);
			printf("\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error in READ operation\n");
			fflush(stderr);
		}
	}

	return 0;
}


/*
 * WRITE
 */
int Write(unsigned char address, UINT32 subaddress, int numbytes, unsigned char *data)
{
	if (g_handle != 0)
	{
		if (APDCAM_WritePDI(g_handle, address, subaddress, data, numbytes) == ADT_OK)
		{
			printf("WRITE success\n");
			fflush(stdout);
		}	
		else
		{
			fprintf(stderr, "Error writing register(s)\n");
			fflush(stderr);
		}	
	}

	return 0;
}

//10G C&C Read & Write
/*
 * CCREAD
 */
int ReadCC(int acktype, unsigned char *value, int firstreg, int length)
{
	if (g_handle != 0)
	{
		if (APDCAM_ReadCC(g_handle, acktype, value, firstreg, length) != ADT_OK)
		{
			fprintf(stderr, "Error reading C&C.\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}

/*
 * SYNC
 */
int SyncADC()
{
	if (g_handle != 0)
	{
		if (APDCAM_SyncADC(g_handle) != ADT_OK)
		{
			fprintf(stderr, "Error syncing ADCs.\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}

/*
 * SET_OFFSET
 */
int SetOffset(unsigned int offset)
{
	if (g_handle != 0)
	{
		if (APDCAM_SetAllOffset(g_handle,offset) != ADT_OK)
		{
			fprintf(stderr, "Error setting offset.\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}

//10G C&C Flash read
/*
 * FLREAD
 */
int ReadFlashPage(int PgAddress, unsigned char *value)
{
	if (g_handle != 0)
	{
		if (APDCAM_ReadFlashPage(g_handle, PgAddress, value) != ADT_OK)
		{
			fprintf(stderr, "Error reading C&C flash.\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}


//10G C&C Firmware Update (STARTFUP instrution and wait for FUP CHECKSUM
/*
 * STARTFUP
 */
int StartFUP()
{
	if (g_handle != 0)
	{
		if (APDCAM_StartFUP(g_handle) != ADT_OK)
		{
			fprintf(stderr, "Error starting firmware update.\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}



/*
 * CCONTROL
 */
int CCControl(int opcode, int length, unsigned char *data)
{
	if (g_handle != 0)
	{
		if (APDCAM_CCControl(g_handle, opcode, length, data) != ADT_OK)
		{
			fprintf(stderr, "Error writing C&C register\n");
			fflush(stderr);
			return 1;
		}
	}

	return 0;
}


/*
 * SETPLL
 */
int SetPLL(int mul, int div0, int div1)
{
	if (g_handle != 0)
	{
		if (APDCAM_SetBasicPLL(g_handle, mul, div0, div1) == ADT_OK)
		{
			printf("Basic PLL setting success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error setting basic PLL\n");
			fflush(stderr);
       }
	}

	return 0;
}


int ProcessLine(char *buffer)
{
	char token[64];
	buffer = GetToken(buffer, token);

	if (token[0] == '\r' || token[0] == '\n' || token[0] == '\0')
	{
		return 0;
	}

	for (int i = 0;  token[i] != '\0'; i++)
		token[i] = toupper(token[i]);

	if (strcmp("PAUSE", token) == 0)
	{
		int pauseTime;
		buffer = GetInt(buffer, &pauseTime);
		if (pauseTime == 0) 
		{
		   printf("Press enter to continue...\n");
		   fflush(stdout);
		   getchar();
		}
		else
		{
			usleep(pauseTime*1000);
		} 
	}
	else if (strcmp("REM", token) == 0 || token[0] == '#')
	{
	}
	else if (strcmp("MESSAGE", token) == 0)
	{
		printf("%s\n", buffer);
		fflush(stdout);
	}
	else if (strcmp("OPEN", token) == 0 || strcmp("FORCE-OPEN", token) == 0)
	{
		char param0[32];
		buffer = GetString(buffer, param0);
		if (strlen(param0) == 0) return -1;

		int res = Open(param0, strcmp("OPEN", token));
		if (res == 0)
		{
			printf("Open success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, open failed\n");
			fflush(stderr);
       }
		return res;
	}
	else if (strcmp("CLOSE", token) == 0)
	{
		int res = Close();
		if (res == 0)
		{
			printf("Close success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, close failed\n");
			fflush(stderr);
       		}
		return res;
	}
	else if (strcmp("SYNC", token) == 0)
	{
		int res = SyncADC();
		if (res == 0)
		{
			printf("Sync success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, sync failed\n");
			fflush(stderr);
        	}
		return res;
	}
	else if (strcmp("SET_OFFSET", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

                int offset;
		if (buffer) buffer = GetInt(buffer, &offset);

		int res = SetOffset((unsigned int)offset);
		if (res == 0)
		{
			printf("Set_offset success\n");
			fflush(stdout);
		}	
	}
	else if (strcmp("SETTIMING", token) == 0)
	{
		// SETTIMING ADC_MULT ADC_DIV CLK_SOURCE, EXT_MUL, EXT_DIV
		//  CLK_SOURCE: 0: internal, 1: external
		int basicPLLmul;
		int basicPLLdiv_0;
		int basicPLLdiv_1;
		int clkSrc = 0;
		int extDCMmul = -1;
		int extDCMdiv = -1;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		buffer = GetInt(buffer, &basicPLLmul);
		basicPLLdiv_0 = 0;
		buffer = GetInt(buffer, &basicPLLdiv_1);
		if (strlen(buffer)) buffer = GetInt(buffer, &clkSrc);
		if (strlen(buffer)) buffer = GetInt(buffer, &extDCMmul);
		if (strlen(buffer)) buffer = GetInt(buffer, &extDCMdiv);

		int res = SetTiming(basicPLLmul, basicPLLdiv_0, basicPLLdiv_1, clkSrc, extDCMmul, extDCMdiv);
		if (res == 0)
		{
			printf("SetTiming success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, SetTiming failed\n");
			fflush(stderr);
       }

		return res;
	}
	else if (strcmp("SAMPLING", token) == 0)
	{
		// SAMPLING SAMPLEDIV
		int sampleDiv;
		int sampleSrc;
		
		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		
		buffer = GetInt(buffer, &sampleDiv);
		buffer = GetInt(buffer, &sampleSrc);
		int res = Sampling(sampleDiv, sampleSrc);
		if (res == 0)
		{
			printf("Sampling success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, sampling failed\n");
			fflush(stderr);
		}

		return res;
	}
	else if (strcmp("ALLOCATE", token) == 0)
	{
		int sampleCount;
		int bits;
		int channelMask_1;
		int channelMask_2;
		int channelMask_3;
		int channelMask_4;
		int primaryBufferSize = 10;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		buffer = GetInt(buffer, &sampleCount);
		buffer = GetInt(buffer, &bits);
		buffer = GetInt(buffer, &channelMask_1);
		buffer = GetInt(buffer, &channelMask_2);
		buffer = GetInt(buffer, &channelMask_3);
		buffer = GetInt(buffer, &channelMask_4);
		GetInt(buffer, &primaryBufferSize);

		int res = Allocate(sampleCount, bits, channelMask_1, channelMask_2, channelMask_3, channelMask_4, primaryBufferSize);
		if (res == 0)
		{
			printf("Allocate success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, allocate failed\n");
			fflush(stderr);
       }
	}
	else if (strcmp("ARM", token) == 0)
	{
		int measurementMode;
		int sampleCount;
		int calibrationMode;
		int signalFrequency = 100;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		buffer = GetInt(buffer, &measurementMode);
		buffer = GetInt(buffer, &sampleCount);
		buffer = GetInt(buffer, &calibrationMode);
		GetInt(buffer, &signalFrequency);

		int res = ARM(measurementMode, sampleCount, calibrationMode, signalFrequency);
		if (res == 0)
		{
			printf("Arm succes\n");
			fflush(stdout);
		}	
		else
		{
			fprintf(stderr, "Error, arm failed\n");
			fflush(stderr);
       }
	}
	else if (strcmp("TRIGGER", token) == 0)
	{
		int triggerSource;
		int triggerMode;
		int triggerEdge;
		int delay;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	
		
		buffer = GetInt(buffer, &triggerSource);
		buffer = GetInt(buffer, &triggerMode);
		buffer = GetInt(buffer, &triggerEdge);
		buffer = GetInt(buffer, &delay);
		// Internal trigger setting is not implemented  S. Zoletnik 8.9.2018
		// buffer = GetString(buffer, triggerFileName);

		int res = Trigger(triggerSource, triggerMode, triggerEdge, delay, NULL);
		if (res == 0)
		{
			printf("Trigger success\n");
			fflush(stdout);
       }
		else
		{
			fprintf(stderr, "Error, trigger setup failed\n");
			fflush(stderr);
		}		
	}
	else if (strcmp("STREAMDUMP", token) == 0)
	{
		int streamNo;
		char streamFileName[512];

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	


		buffer = GetInt(buffer, &streamNo);
		buffer = GetString(buffer, streamFileName);

		if (APDCAM_StreamDump(g_handle, streamNo, streamFileName) == ADT_OK)
		{
			printf("StreamDump success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, streamDump failed\n");
			fflush(stderr);
		}	
	}
			
	else if (strcmp("START", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int res = Start();
		if (res == 0)
		{
			printf("Start succes\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, start failed\n");
			fflush(stderr);
		}	
	}
	else if (strcmp("WAIT", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int timeout = -1;
		if (buffer) buffer = GetInt(buffer, &timeout);

		int res = Wait(timeout);
		if (res == 0)
		{
			printf("Wait success\n");
			fflush(stdout);
		}	
		else
		{
			fprintf(stderr, "Error, wait time out\n");
			fflush(stderr);
       }
	}
	else if (strcmp("STOP", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int res = Stop();
		if (res == 0)
		{
			printf("Stop success\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, stop failed\n");
			fflush(stderr);
       }
	}
	else if (strcmp("SAVE", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int ndata = -1;
		GetInt(buffer,&ndata);
		int res = APDTest_Save(ndata);
		if (res == 0)
		{
			printf("Save success\n");
			fflush(stdout);
		}	
		else
		{
			fprintf(stderr, "Error, save failed\n");
			fflush(stderr);
       }
	}
	else if (strcmp("DATAMODE", token) == 0)
	{
		int mode = 0;
		if (strlen(buffer))
			buffer = GetInt(buffer, &mode);
		int res = DataMode(mode);
		if (res == 0)
		{
			printf("DataMode success\n");
			fflush(stdout);
       }
		else
		{
			fprintf(stderr, "DataMode failed\n");
			fflush(stderr);
		}	
	}
	else if (strcmp("FILTER", token) == 0)
	{
		int coeffs[6] = {0};
		for (int i = 0; i < 6; i++)
		{
			if (strlen(buffer))
				buffer = GetInt(buffer, &coeffs[i]);
			else
			{
				break;
			}
		}
		int res = Filter(coeffs);
		if (res == 0)
		{
    		printf("Filter setting success\n");
			fflush(stdout);
		}	
		else
		{
			printf("Filter setting failed\n");
			fflush(stderr);
		}	
	}
	else if (strcmp("CALIBRATE", token) == 0)
	{
		int res = Calibrate();
		if (res == 0)
		{
			printf("Calibration success\n");
			fflush(stdout);
		}	
		else
		{
			printf("Calibration failed\n");
			fflush(stderr);
		}	
	}
	else if (strcmp("READ", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int address;
		int subaddress;
		int numbytes;
		buffer = GetInt(buffer, &address);
		buffer = GetInt(buffer, &subaddress);
		buffer = GetInt(buffer, &numbytes);
		Read(address, subaddress, numbytes);
	}
	else if (strcmp("WRITE", token) == 0)
	{

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		int address;
		int subaddress;
		unsigned char data[MAX_RW_BYTES];
		int numbytes;

		buffer = GetInt(buffer, &address);
		buffer = GetInt(buffer, &subaddress);
		buffer = GetInt(buffer, &numbytes);
		if (numbytes > MAX_RW_BYTES)
		{
			fprintf(stderr, "Cannot write more than %d bytes!\n", MAX_RW_BYTES);
			fflush(stdout);
		}
		else
		{
			for (int iloc = 0;(iloc < numbytes) && (iloc < MAX_RW_BYTES); ++iloc)
			{
				int d;
				buffer = GetInt(buffer, &d);
				data[iloc] = d;
			}
			Write(address, subaddress, numbytes, data);
		}
	}
	//10G C&C Read & Write
	else if (strcmp("CCREAD", token) == 0 || strcmp("CCREAD-7", token) == 0)
	{
		/*
		 * Read 10G C&C card registers.
		 * acktype: type of acknowledgement, 1: writable registers, 3: read-only registers
		 * firstreg: first register to read from register table, see 10G C&C instruction manual 5.10
		 * length: number of bytes to read
		 */
		int acktype = 0;
		int firstreg = 0;
		unsigned char *value = NULL;

		int length = 0;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	


		buffer = GetInt(buffer, &acktype);
		buffer = GetInt(buffer, &firstreg);
		buffer = GetInt(buffer, &length);

		value = (unsigned char*) malloc (length);

		bool compat = (strcmp("CCREAD", token) == 0);
		if (ReadCC(acktype, value, compat ? firstreg - 7 : firstreg, length) == 0)
		{
			if (length == 1)
			{
				if (compat)
					printf("\nC&C REGISTER VALUES:\n  Acktype:      %d\n  Address:      %d\n  Value:        %d\n", acktype, firstreg, value[0]);
				else
					printf("\nC&C REGISTER VALUES:\n  Acktype:      %d\n  Address:      %d\n  Value:        0x%.2x(%c)\n", acktype, firstreg, value[0], value[0]);
			}
			else
			{
				printf("\nC&C REGISTER VALUES:\n  Acktype:        %d\n  Start address:  %d\n  Values:         ", acktype, firstreg);
				for (int i = 0; i < length; i++)
				{
					if (compat)
						printf("%d ", value[i]);
					else
					{
						if (isalnum(value[i]))
							printf("0x%.2x(%c) ", value[i], value[i]);
						else
							printf("0x%.2x(%d) ", value[i], value[i]);
					}
				}
				printf("\n\n");
				fflush(stdout);
			}
		}

		free(value);
	}
	//10G C&C Flash memory read
	else if (strcmp("FLREAD", token) == 0)
	{
		/*
		 * Read 10G C&C card flash page.
		 * PgAddress: Page address 0...8191
		 */
		int PgAddress = 0;
		unsigned char *value = NULL;

		int length = 1024;

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	


		buffer = GetInt(buffer, &PgAddress);

		value = (unsigned char*) malloc (length);

		if (ReadFlashPage(PgAddress, value) == 0)
		{
			printf("\nC&C FLASH DATA:\n  PageAddress:        %d\n  Values: ", PgAddress);
				for (int i = 0; i < length; i++)
				{
					printf("%d ", value[i]);
				}
				printf("\n\n");
				fflush(stdout);
		} 
		else
		{ 
		  fprintf(stderr, "Error reading flash memory.");
		  fflush(stdout);
		}  

		free(value);
	}
	//10G firmware update STARTFUP
	else if (strcmp("STARTFUP", token) == 0)
	{
		/*
		 * Start fimrware update with already downloaded data.
		 */

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		if (StartFUP() == 0)
		{
			printf("\nC&C Card firmware succesfully updated.\n");
			fflush(stdout);
		} 
	}
	else if (strcmp("CCCONTROL", token) == 0)
	{
		/*
		 * Control 10G C&C card.
		 * opcode: 10G commands in decimal form(!)
		 * length: instruction length, see 10G C&C instruction manual 5.1-5.10
		 * data
		 */

		int opcode;
		int length;
		unsigned char data[MAX_RW_BYTES];

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	

		buffer = GetInt(buffer, &opcode);
		buffer = GetInt(buffer, &length);
		if (length > MAX_RW_BYTES)
		{
			fprintf(stderr, "Error in CCCONTROL, cannot write more than %d bytes!\n", MAX_RW_BYTES);
			fflush(stderr);
		}
		else
		{
			for (int iloc = 0; (iloc < length) && (iloc < MAX_RW_BYTES); ++iloc)
			{
				int d;
				buffer = GetInt(buffer, &d);
				data[iloc] = d;
			}

			CCControl(opcode, length, data);
		}
	}
	else if (strcmp("STREAM-INTERFACE", token) == 0)
	{
		char ifname[512];
		buffer = GetString(buffer, ifname);

		if (g_handle == 0) 
		{
			fprintf(stderr, "Error, camera not open.\n");
			fflush(stderr);
			return -1;
		}	


		if (APDCAM_SetStreamInterface(g_handle, ifname) == ADT_OK)
		{
			printf("Interface set.\n");
			fflush(stdout);
		}
		else
		{
			fprintf(stderr, "Error, cannot set stream interface!\n");
			fflush(stderr);
		}	
	}
	else
	{
		fprintf(stderr, "WARNING: Unknown command:\n|%s|\n", token);
		fflush(stderr);
   }
	return 0;
}


int ReadLine(FILE * f, char * buffer, int size)
{
	int i;
	for (i = 0; (i < size - 1) && !feof(f); ++i)
	{
		if ((buffer[i] = fgetc(f)) == EOF)
			break;
		if ((buffer[i] == '\n') || (buffer[i] == '\r'))
		{
			buffer[i] = '\0';
			break;
		}
	}
	buffer[i] = '\0';

	return 0;
}
