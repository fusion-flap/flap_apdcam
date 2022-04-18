#pragma once
#ifndef __TYPEDEFS_H__

#define __TYPEDEFS_H__

#ifdef __cplusplus
extern "C"
{
#endif

#define APD_MAX_ADC_NUM  4

#if defined(__linux__)
#include <stdint.h>
#include <stddef.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>

typedef uint16_t      beuint16_t __attribute__((__may_alias__));
typedef uint32_t      beuint32_t __attribute__((__may_alias__));
typedef uint64_t      beuint64_t __attribute__((__may_alias__));

typedef uint8_t       UCHAR;
typedef uint16_t      _BEUSHORT;
typedef uint32_t      DWORD;
typedef uint64_t      ULONGLONG;
typedef uint8_t       UINT8;
typedef uint16_t      UINT16;
typedef uint32_t      UINT32;
typedef uint64_t      UINT64;
typedef int16_t       INT16;
typedef int64_t       LONGLONG;
typedef uint32_t      _BEULONG;
typedef wchar_t       WCHAR;
typedef WCHAR         TCHAR;
typedef void*         PVOID;
typedef unsigned int  UINT;

#else

#endif

typedef unsigned int ADT_HANDLE;
enum ADT_RESULT {ADT_OK = 0, ADT_ERROR, ADT_INVALID_HANDLE_ERROR, ADT_PARAMETER_ERROR, ADT_SETUP_ERROR, ADT_NOT_IMPLEMENTED, ADT_TIMEOUT};
enum ADT_MEASUREMENT_MODE {MM_ONE_SHOT, MM_CYCLIC};
enum ADT_CALIB_MODE {CM_NONCALIBRATED, CM_CALIBRATED};

enum ADT_TRIGGER {TR_SOFTWARE, TR_HARDWARE};
enum ADT_TRIGGER_MODE {TRM_EXTERNAL, TRM_INTERNAL};
enum ADT_TRIGGER_EDGE {TRE_NONE, TRE_RISING, TRE_FALLING, TRE_BOTH};

enum ADT_STATE { AS_STANDBY, AS_ARMED, AS_MEASURE, AS_ERROR };

typedef union _LARGE_INTEGER
{
	long long QuadPart;
} LARGE_INTEGER;

#pragma pack(push)
#pragma pack(1)
#if 0
typedef union _ADT_STATUS_1
{
	unsigned char status;
	struct
	{
		unsigned char ADC_PLL_Locked : 1;
	};
} ADT_STATUS_1;
#endif

#if 0
typedef union _ADT_STATUS_2
{
	unsigned char status;
	struct
	{
		unsigned char reserved1 : 1;
		unsigned char Overload : 1;
		unsigned char External_clock_PLL_Locked : 1;
		unsigned char reserved2 : 1;
		unsigned char ADC_1_Sample_Enabled : 1;
		unsigned char ADC_2_Sample_Enabled : 1;
		unsigned char ADC_3_Sample_Enabled : 1;
		unsigned char ADC_4_Sample_Enabled : 1;
	};
} ADT_STATUS_2;
#endif

#if 0
typedef union _ADT_CONTROL
{
	unsigned char control;
	struct
	{
		unsigned char External_Clock_Select : 1;
		unsigned char Clock_Out_Enable : 1;
		unsigned char External_Sample_Select : 1;
		unsigned char Sample_Out_Enable : 1;
		unsigned char Digital_Filter_Enable : 1;
		unsigned char Reserved : 1;
		unsigned char Reverse_Bit_Order : 1;
		unsigned char Preamble_Enable : 1;
	};
} ADT_CONTROL;
#endif

typedef union _ADT_TRIGGER_CONTROL
{
	_ADT_TRIGGER_CONTROL() :
		trigger_control(0)
	{
		Disable_Trigger_Event = 1;
	};
	unsigned char trigger_control;
	struct
	{
		unsigned char Enable_Rising_Edge : 1;
		unsigned char Enable_Falling_Edge : 1;
		unsigned char Enable_Internal_Trigger : 1;
		unsigned char bit345 : 3;
		unsigned char Disable_Trigger_Event : 1;
		unsigned char bit7 : 1;
	};
} ADT_TRIGGER_CONTROL;


typedef union _ADT_TRIGGERINFO
{
	UINT16 TriggerInfo;
	struct
	{
		UINT16 TriggerLevel : 14;
		UINT16 Sensitivity : 1; // 0: positive, 1: negative
		UINT16 Enable : 1;
	};
} ADT_TRIGGERINFO;

typedef union _ADT_FPGA_STATUS
{
	uint8_t flat;
	struct
	{
#if __BYTE_ORDER == __LITTLE_ENDIAN
		unsigned int Basic_PLL_Locked : 1;
		unsigned int Reserved : 1;
		unsigned int EDCM_Locked : 1;
		unsigned int Ext_Clock_Valid : 1;
		unsigned int CAM_Timer_State : 2;
		unsigned int Streaming_Data : 1;
		unsigned int Overload : 1;
#else
#error FIX _ADT_FPGA_STATUS
#endif
	};
} ADT_FPGA_STATUS;

typedef uint8_t ADT_CC_COUNTER[6];

#pragma pack(2)

typedef struct _FILTER_COEFFICIENTS
{
	INT16 FIR[5];
	INT16 RecursiveFilter;
	INT16 Reserved;
	INT16 FilterDevideFactor;
} FILTER_COEFFICIENTS;

#pragma pack(pop)

//10G board data
typedef struct ADC_t_
{
	uint8_t  boardAddress;
	uint8_t  boardVersion;
	uint16_t boardSerial;
} ADC_t;

typedef struct ApdCam10G_t_
{
	ApdCam10G_t_() :
		numADCBoards(0),
		ip(0),
		CCSerial(0),
		PCSerial(0),
		ADC()
	{
	};

	int        numADCBoards;
	uint32_t   ip;
	uint32_t   CCSerial;
	uint16_t   PCSerial;
	ADC_t      ADC[APD_MAX_ADC_NUM];
} ApdCam10G_t;


#ifdef __cplusplus
}
#endif


#endif  /* __TYPEDEFS_H__ */
