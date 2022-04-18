#ifndef __GECCOMMANDS_H__

#define __GECCOMMANDS_H__

#include <arpa/inet.h>
#include <string.h>
#include <endian.h>
#include <stdio.h>

#include "TypeDefs.h"
#include "helper.h"

/*
	History

	Ver: V1.2 Date: 2011.Jan.25 Who: STA
	CW_FRAME_V2 added (Three byte continuity counter)
*/

#pragma once

/*

4.3.3 DDToIP protocol
*/

#define COMPANY "ADIMTECH"

//10G
// ************************** Operation Codes
// General instructions:
#define OP_NOP             0x0000
#define OP_LASTINSTRUCTION 0x0001
#define OP_WAIT            0x0002
#define OP_RESET           0x0003
#define OP_LOCK            0x0004
#define OP_UNLOCK          0x0005
#define OP_SENDACK         0x0006
#define OP_READSDRAM       0x0007

//Configuration instructions:
#define OP_SETSERIAL        0x0010
#define OP_SETTYPE          0x0011
#define OP_SETNAME          0x0012
#define OP_SETUSERTEXT      0x0013
#define OP_SETCOMPANY       0x0014
#define OP_SETHOSTNAME      0x0015
#define OP_SETCONFIGURATION 0x0016
#define OP_IMPORTSETTINGS   0x001E
#define OP_SAVESETTINGS     0x001F

// Network instructions:
#define OP_SETMAC             0x0020
#define OP_SETIP              0x0021
#define OP_SETIPV4NETMASK     0x0022
#define OP_SETIPV4GATEWAY     0x0023
#define OP_SETARPREPORTPERIOD 0x0024
#define OP_SETMACMODE         0x0025

//Control Instructions
#define OP_PROGRAMBASICPLL      0x0100
#define OP_PROGRAMEXTDCM        0x0101
#define OP_SETCLOCKCONTROL      0x0102
#define OP_SETCLOCKENABLE       0x0103
#define OP_PROGRAMSAMPLEDIVIDER 0x0104
#define OP_SETSPAREIO           0x0105
#define OP_SETXFP               0x0106

//Streamer instructions
#define OP_SETSTREAMCONTROL          0x0110
#define OP_SETUDPTESTCLOCKDIVIDER    0x0111
#define OP_SETMULTICASTUDPSTREAM     0x0112
#define OP_SETMULTICASTUDPSTREAM_LEN   9
#define OP_SETUDPSTREAM              0x0113
#define OP_SETUDPSTREAM_LEN            15
#define OP_SETSAMPLECOUNT            0x0114
#define OP_SETTRIGGER                0x0115
#define OP_SETTRIGGER_LEN              5
#define OP_CLEARTRIGGERSTATUS        0x0116

//SCB instructions
#define OP_SCBWRITECA    0x0060
#define OP_SCBWRITERA    0x0061
#define OP_SCBREADCA     0x0062
#define OP_SCBREADRA     0X0063
#define OP_SCBWRITECWNET 0x0064
#define OP_SCBREADCWNET  0x0065

// Parallel Data Interface instructions:
#define OP_WRITEPDI 0x0068
#define OP_READPDI  0x0069

//Storage Flash instructions
#define OP_FLCHIPERASE   0x0070
#define OP_FLBLOCKERASE  0x0071
#define OP_FLBLOCKERASEW 0x0072
#define OP_FLPROGRAM     0x0073
#define OP_FLREAD        0x0074

//Firmware Upgrade and Test instructions
#define OP_LOADFUP   0x0800
#define OP_STARTFUP  0x0801
#define OP_SHORTBEEP 0x0810

// ************************** Answer Codes
#define AN_ACK       0xFF00
#define AN_SDRAMPAGE 0xFF01
#define AN_SCBDATA   0xFF02
#define AN_FLASHPAGE 0xFF03
#define AN_PDIDATA   0xFF04


#define COUNTER_TO_INT64(x)    n48toh64(x)
#define COUNTER_MASK           0x0000FFFFFFFFFFFFL
//#define SLOW_COUNTER
#ifdef SLOW_COUNTER
#warning Using slow, memcpy() based counter retrieving method
#define CC_PACKETCOUNTER(x)    CC_PacketCounter(x)
#define CC_SAMPLECOUNTER(x)    CC_SampleCounter(x)
#else
#define CC_PACKETCOUNTER(x)    CC_PacketCounter_fast(x)
#define CC_SAMPLECOUNTER(x)    CC_SampleCounter_fast(x)
#endif

uint64_t inline __attribute__((deprecated)) n48toh64(uint8_t msb_48[48/8])
{
	uint8_t msb_64[64/8] = {0};

	memcpy(msb_64 + 2, msb_48, sizeof(msb_48));
	return MSB_TO_HOST_64(msb_64, uint64_t);
}

class CReplyCmdSet
{
public:
	static bool In(int cmd)
	{
		for (int i = 0; i < 4; i++)
		{
			if (cmd == g_CmdSet[i]) return true;
		}
		return false;
	}
private:
	static int g_CmdSet[4];
};

#pragma pack(push)
#pragma pack(1)

typedef union _CC_S1
{
	uint16_t S1;
	struct
	{
#if __BYTE_ORDER == __LITTLE_ENDIAN
		unsigned int Reserved : 6;
		unsigned int Stream_num : 2;
		unsigned int Sample_Start_Condition : 1;
		unsigned int UDP_Test_Mode : 1;
//		unsigned int Reserved2 : 6;
#else
#error FIX _CC_S1
#endif
	};
} CC_S1;

typedef union _CC_S2
{
	uint16_t S2;
	struct
	{
#if __BYTE_ORDER == __LITTLE_ENDIAN
		ADT_FPGA_STATUS FPGA_Status;
		unsigned int DSLV_Lock_Status : 8;
#else
#error FIX _CC_S2
#endif
	};
} CC_S2;

typedef union _CC_S3
{
	uint16_t S3;
	struct
	{
		unsigned char Reserved_1 : 8;
		unsigned char Reserved_2 : 8;
	};
} CC_S3;

//10G C&C header
#define CC_OCTET_SIZE 8
struct CC_STREAMHEADER
{
	UINT32         serial;
	CC_S1          S1;
	CC_S2          S2;
	ADT_CC_COUNTER packetCounter;
	CC_S3          S3;
	ADT_CC_COUNTER sampleCounter;
};

uint64_t inline CC_PacketCounter_fast(CC_STREAMHEADER* header)
{
#if __BYTE_ORDER == __LITTLE_ENDIAN
	return MSB_TO_HOST_64(&header->S2, uint64_t) & COUNTER_MASK;
#else
#warning Falling back to SLOW method
#define ENABLE_SLOW_COUNTER
	PacketCounter(header);
#endif
}

uint64_t inline CC_SampleCounter_fast(CC_STREAMHEADER* header)
{
#if __BYTE_ORDER == __LITTLE_ENDIAN
	return MSB_TO_HOST_64(&header->S3, uint64_t) & COUNTER_MASK;
#else
#warning Falling back to SLOW method
#define ENABLE_SLOW_COUNTER
	SampleCounter(header);
#endif
}

#ifdef ENABLE_SLOW_COUNTER
uint64_t inline CC_PacketCounter(CC_STREAMHEADER* header)
{
	return COUNTER_TO_INT64(header->packetCounter);
}

uint64_t inline CC_SampleCounter(CC_STREAMHEADER* header)
{
	return COUNTER_TO_INT64(header->sampleCounter);
}
#endif

uint8_t inline CC_StreamNum(CC_STREAMHEADER* header)
{
	return header->S1.Stream_num + 1;
}

uint8_t inline CC_SampleStart(CC_STREAMHEADER* header)
{
	return header->S1.Sample_Start_Condition;
}



struct DDTOIPHEADER
{
	DDTOIPHEADER();
	UINT8 DDToIp[6];
	char UserText[15];
	UINT8 V;

	void Prepare(char *_usertext);
	bool Validate();
};

struct INSTRUCTIONHEADER
{
	UINT16 opCode; //GEC UINT8
	_BEUSHORT length;
	inline UINT16 GetOpCode() const { return (ntohs(opCode));}; //GEC UINT8
	inline UINT16 GetDataLength() const { return (ntohs(length)); };
	inline UINT16 GetInstructionLength() const { return (GetDataLength() + sizeof(INSTRUCTIONHEADER)); };
	inline UINT16 GetCmdLength() const { return (GetInstructionLength() + sizeof(DDTOIPHEADER)); };
};

struct SENDACK_I : INSTRUCTIONHEADER
{
	UINT16 ACKType; 
	void Prepare(UINT16 _type)
	{
		opCode = htons(OP_SENDACK);
		length = htons(2);
		ACKType = htons(_type);
	}
};

struct FLREAD_I : INSTRUCTIONHEADER
{
	UINT16 PgAddress;
	void Prepare(UINT16 _addr)
	{
		opCode = htons(OP_FLREAD);
		length = htons(2);
		PgAddress = htons(_addr);
	}
};

struct STARTFUP_I : INSTRUCTIONHEADER
{
	unsigned char FUPdate[4];
	void Prepare(unsigned char * _FUPdate)
	{
		opCode = htons(OP_STARTFUP);
		length = htons(4);
		FUPdate[0] = _FUPdate[0];
		FUPdate[1] = _FUPdate[1];
		FUPdate[2] = _FUPdate[2];
		FUPdate[3] = _FUPdate[3];
	}
};
			
struct WRITEPDI_I : INSTRUCTIONHEADER
{
	UINT8 Addr;
	_BEULONG SubAddr;
	UINT8 data[1024];

	void Prepare(unsigned char _addr, unsigned int _subaddr, unsigned char *_data, int _length)
	{
		_length = MIN(_length, 1024);
		opCode = htons(OP_WRITEPDI);
		length = htons(_length + 5);
		Addr = _addr;
		SubAddr = htonl(_subaddr);
		memcpy_s(data, 1024, _data, _length); 
	}
};

struct READPDI_I : INSTRUCTIONHEADER
{
	UINT8 Addr;
	_BEULONG SubAddr;
	_BEUSHORT NOB;

	void Prepare(unsigned char _addr, unsigned int _subaddr, UINT16 _nob)
	{
		opCode = htons(OP_READPDI);
		length = htons(7);
		Addr = _addr;
		SubAddr = htonl(_subaddr);
		NOB = htons(_nob);
	}
};

struct SETIP_I : INSTRUCTIONHEADER
{
	char reserved[12];
	_BEULONG IPAddr;

	void Prepare(UINT32 _ip_h)
	{
		memset(this, 0, sizeof(SETIP_I));
		opCode = htons(OP_SETIP);
		length = htons(0x05);
		IPAddr = htonl(_ip_h);
	}
};

//10G Control
struct CCCONTROL_I : INSTRUCTIONHEADER
{
	UINT8 data[2000];

	int Prepare(int16_t _opcode, unsigned int _length, unsigned char *_data)
	{
		opCode = htons(_opcode);
		_length = MIN(_length, sizeof(data));
		length = htons(_length);
		memcpy_s(data, sizeof(data), _data, _length);

		return _length;
	}
};

#if 0
//Edited 2013.09.03. - 10G Stream options
struct SENDTS_I : INSTRUCTIONHEADER
{
	UINT8 stream;
	UINT8 octet;
	//UINT8 MAC[6];
	union
	{
		UINT8 IP[16];
		_BEULONG IPv4;
	};
	_BEUSHORT Port;

	void Prepare(unsigned char _stream, unsigned int _octet, UINT16 _port)
	{
		memset(this, 0, sizeof(SENDTS_I));
		opCode = htons(OP_SETMULTICASTUDPSTREAM);
		length = htons(0x09);
		stream = _stream;
		octet = htons(_octet);
		IPv4 = 0;
		Port = htons(_port);
	}
};

struct DONTSENDTS_I : INSTRUCTIONHEADER
{
	UINT8 channel;
	void Prepare(unsigned char _channel)
	{
//		opCode = OP_DONTSENDTS;
		length = htons(1);
		channel = _channel;
	}
};
#endif

struct GECCOMMANDBASE
{
	DDTOIPHEADER header;
};


struct GECCOMMAND : GECCOMMANDBASE 
{
};


struct __attribute__((__may_alias__)) GENERAL_MESSAGE  : GECCOMMAND
{
	INSTRUCTIONHEADER instructionheader;
	bool Validate() { return header.Validate(); }
	int GetOpCode() { return (int)instructionheader.GetOpCode(); };
	int GetDataLength() { return (int)instructionheader.GetDataLength(); };
	int GetInstructionLength() { return (int)instructionheader.GetInstructionLength(); };
	int GetCommandLength() { return (int)instructionheader.GetCmdLength(); }
};

struct BULKCMD : GECCOMMANDBASE
{
	BULKCMD() : length(0) {};
	UINT8 instructions[1024];
	void Add(GECCOMMAND &command)
	{
		GENERAL_MESSAGE &cmd = reinterpret_cast<GENERAL_MESSAGE&>(command);
		int len = cmd.GetInstructionLength();
		if (length + len < 1024)
		{
			memcpy(&instructions[length], &cmd.instructionheader, len);
			length += len;
		}
	}
	void Reset() { length = 0;};
	int GetCommandLength() { return length + sizeof(DDTOIPHEADER);};

private:
	int length;
};

struct SENDACK : GECCOMMAND
{
	SENDACK_I instruction;
};

struct FLREAD : GECCOMMAND
{
	FLREAD_I instruction;
};

struct STARTFUP : GECCOMMAND
{
	STARTFUP_I instruction;
};

struct WRITEPDI : GECCOMMAND
{
	WRITEPDI_I instruction;
};

struct READPDI : GECCOMMAND
{
	READPDI_I instruction;
};

struct SETIP : GECCOMMAND
{
	SETIP_I instruction;
};

//10G Control
struct CCCONTROL : GECCOMMAND
{
	CCCONTROL_I instruction;
};

#if 0
struct SENDTS : GECCOMMAND
{
	SENDTS_I instruction;
};
#endif

#if 0
struct DONTSENDTS : GECCOMMAND
{
	DONTSENDTS_I instruction;
};
#endif

#pragma pack(pop)

#endif  /* __GECCOMMANDS_H__ */
