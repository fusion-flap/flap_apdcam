#include <netinet/ip.h>
#include <netinet/udp.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "APDLib.h"
#include "InternalFunctions.h"
#include "LowlevelFunctions.h"
#include "LnxClasses.h"
#include "Helpers.h"
#include "DataEvaluation.h"
#include "helper.h"
#include "CCRegs.h"

#define LIBVERSION_MAJOR 1
#define LIBVERSION_MINOR 2


#define STREAM_PORT_IP      "10.123.13.202"
#define STREAM_PORT_MAC     {0x90, 0xE2, 0xBA, 0x45, 0xD7, 0x6E}

#define SLOTNUMBER 2
#define MAX_STREAMNUM       4
#define MTU                 9000
#define MIN_PACKETSIZE      (sizeof(CC_STREAMHEADER) + sizeof(struct udphdr) + sizeof(struct iphdr))
#define MAX_DATASIZE        (MTU - MIN_PACKETSIZE) 
#define DEF_DATASIZE        MAX_DATASIZE 
#define DEF_OCTET           (DEF_DATASIZE / CC_OCTET_SIZE)
#define DEF_PACKETSIZE      (DEF_OCTET * CC_OCTET_SIZE + sizeof(CC_STREAMHEADER))
#define STREAM_PORT_BASE    10001
#define PAGESIZE            getpagesize()
#define MAX_SAMPLECOUNT     0xFFFFFFFFFFFF

#define NOT_IMPL   { fprintf(stderr, "%s is NOT IMPLEMENTED!\n", __FUNCTION__); return ADT_NOT_IMPLEMENTED; }

unsigned char reverseBits(unsigned char in_byte)
// Reverses the bits in a byte. This is needed in the channel mask setting in the ADC
{
  unsigned char out_byte, mask_in, mask_out;
  
  out_byte = 0;
  mask_in = 0x01;
  mask_out = 0x80;
  
  for (int i=0; i<8; i++)
  {
    if (in_byte & mask_in)
       out_byte |= mask_out;
    mask_in <<= 1;
    mask_out >>= 1;
  }        
  return out_byte;
}

union INTERNAL_HANDLE
{
	struct
	{
		unsigned int index : 8;
		unsigned int magic_number : 24;
	};
	unsigned int handle;

	INTERNAL_HANDLE() :
		handle(0)
	{
	}

	INTERNAL_HANDLE(ADT_HANDLE ah) :
		handle(ah)
	{
	}

	INTERNAL_HANDLE(unsigned int i, unsigned int mn) :
		index(i),
		magic_number(mn)
	{
	}

	INTERNAL_HANDLE &operator=(ADT_HANDLE ah)
	{
		handle = ah;
		return (*this);
	}

	operator ADT_HANDLE() const
	{
		return (ADT_HANDLE)handle;
	};
};

typedef struct _Stream
{
	int              address;
	int              bits;
	uint32_t         channelMask;
	uint16_t         stream_port_h; // port number for stream in host format.
	// Primary buffer where the server collects the incoming UDP frames.
	// Temporary buffer is for the data evaluation.
	// User buffer where the evaluated data are stored.
	// The size of non-paged memory is primeryBuffer + temporaryBuffer + CHANNEL_NUM * userBuffer
	// user_buffer_1_i = user_buffer_1 + i * user_buffer_size_1.
	CAPDServer      *stream_server;
	CNPMAllocator   *np_memory;
	CEvent          *dataNotification; // Set by the server to notify the data processor to start data evaluation;
	CEvent          *userNotification;	// Set by the data processor to notify user
	CDataEvaluation *eval;
	unsigned char   *primary_buffer;
	uint64_t         primary_buffer_size;
	unsigned char   *temp_buffer;
	uint64_t         temp_buffer_size;
	unsigned char   *user_buffer;
	uint64_t         user_buffer_size;
	uint64_t         requestedData;
} Stream;

typedef struct tagWORKING_SET
{
	// Preliminary
	// The magic_number is A random number, generated when the slot allocated in the open operation, and cleared in the close operation.
	// When the slot is accessed with a handle, this number is compared with the magic_number part of handle to validate the it.
	INTERNAL_HANDLE handle;

	//
	ADT_STATE state;

	CAPDClient *client;

	int    n_streams;
	Stream streams[MAX_STREAMNUM];
	char   streamInterface[32];

	CWaitForEvents* waitObject; // User notifiaction objects. Objects set by the data evaluators.
	CTriggerManager *triggerManager; // Used to synchronize sw triggers.

	uint32_t streamSerial_n; // The four byte long Serial used as magic number in CC_STREAMHEADER in Network Byte Order

	uint32_t ip_h; // ip in host format
	uint16_t command_port_h; // port number for commands

	// The size of user data in an UDP packet (without CW_FRAME)
	unsigned int packetsize;

	uint64_t bufferSizeInSampleNo;	// the size of buffers in samples. The real size of a buffer depends on the data type, stored in that buffer.
	bool setupComplete;

	uint64_t sampleCount;	// Number of samples, required after start or trigger;

	UINT16 sampleDiv;
	int clkSource;

	unsigned char basicPLLmul;
	unsigned char basicPLLdiv_0;
	unsigned char basicPLLdiv_1;
	unsigned char extDCMmul;
	unsigned char extDCMdiv;
} WORKING_SET;

WORKING_SET g_WorkingSets[SLOTNUMBER];

CAPDFactory* CAPDFactory::g_pFactory;


int GetIndex(ADT_HANDLE handle)
{
	INTERNAL_HANDLE h = handle;
	int index = h.index;

	if (index >= SLOTNUMBER)
		return -1;
	if (g_WorkingSets[index].handle != h)
		return -1;

	return index;
}


void APDCAM_Init()
{
	for (int i = 0; i < SLOTNUMBER; i++)
	{
		memset(&g_WorkingSets[i], 0, sizeof(g_WorkingSets[i]));
	}

	CAPDFactory::SetAPDFactory(new CLnxFactory());
}


void APDCAM_Done()
{
	for (int i = 0; i < SLOTNUMBER; i++)
	{
		if (g_WorkingSets[i].handle != 0)
		{
			APDCAM_Close(g_WorkingSets[i].handle);
		}
	}

	delete CAPDFactory::GetAPDFactory();
}


void APDCAM_GetSWOptios()
{
	printf("************* Software options *************\n");

	printf("Library: APDLib\n");
	printf("Version: %d.%d\n", LIBVERSION_MAJOR, LIBVERSION_MINOR);

	printf("Continuity counter : 48 bit\n");

	printf("********************************************\n");
}


void APDCAM_FindFirst(ApdCam10G_t *devices, UINT32 from_ip_h, UINT32 to_ip_h, const char *filter_str, int timeout)
{
	APDCAM_Find(devices, from_ip_h, to_ip_h, NULL, 0, NULL, filter_str, timeout);
}


void APDCAM_List(UINT32 from_ip_h, UINT32 to_ip_h, UINT32 *ip_table, int table_size, int *no_of_elements, const char *filter_str, int timeout)
{
	APDCAM_Find(NULL, from_ip_h, to_ip_h, ip_table, table_size, no_of_elements, filter_str, timeout);
}


void APDCAM_Find(ApdCam10G_t *devices, UINT32 from_ip_h, UINT32 to_ip_h, UINT32 *ip_table, int table_size, int *no_of_elements, const char *filter_str, int timeout)
{
	bool first_matching = devices != NULL;

	if (ip_table == NULL || table_size == 0 || no_of_elements == NULL)
	{
		if (first_matching == false)
			return;
	}

	CAPDClient *client = CAPDFactory::GetAPDFactory()->GetClient();
	client->Start();

	if (first_matching == false)
		*no_of_elements = 0;
	else
		devices->numADCBoards = 0;

	for (UINT32 ip_h = from_ip_h; ip_h <= to_ip_h; ++ip_h)
	{
		struct in_addr ia = {ntohl(ip_h)};
		printf("Trying %s...\n", inet_ntoa(ia));
		fflush(stdout);

		uint16_t devType;
		if (GetCCDeviceType(client, &devType, ip_h, 0, timeout))
		{
			switch (devType)
			{
				case 0xFFFF:
				{
					client->SetIPAddress(ip_h);

					if (first_matching)
					{
						devices->ip = ip_h;

						EnumerateADCBoards(client, devices);
						printf("%d ADC(s) found. Address & S/N: ", devices->numADCBoards);
						for (int j = 0; j < devices->numADCBoards; ++j)
							printf("%d: %d ", devices->ADC[j].boardAddress, devices->ADC[j].boardSerial);

						if (GetPCSerial(client, &devices->PCSerial))
						{
							printf("\nP&C found! S/N: %d\n", devices->PCSerial);
						}
						else
						{
							printf("\nP&C not found.\n");
						}
					}
					else if (*no_of_elements < table_size)
					{
						*ip_table = ip_h;
						ip_table++;
						(*no_of_elements)++;
					}
				}
					break;
				default:
					break;
			}
		}
		else
		{
			fprintf(stderr, "GetCCDeviceType() failed\n");
		}
	}

	client->Stop();
	delete client;
}


ADT_HANDLE APDCAM_Open(UINT32 ip_h)
{
	ApdCam10G_t device;
	APDCAM_FindFirst(&device, ip_h, ip_h);

	if (device.numADCBoards)
		return APDCAM_OpenDevice(&device);

	return 0;
}


ADT_HANDLE APDCAM_OpenDevice(ApdCam10G_t *device)
{
	
	int slotNumber;
	for (slotNumber = 0; slotNumber < SLOTNUMBER; slotNumber++)
	{
		if (g_WorkingSets[slotNumber].handle == 0)
			break;
	}
	if (slotNumber >= SLOTNUMBER)
		return 0;

	if (device == NULL)
		return ADT_PARAMETER_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[slotNumber];

	WorkingSet.handle.index = slotNumber;
	WorkingSet.handle.magic_number = rand() + 1;

	WorkingSet.n_streams = device->numADCBoards;

	WorkingSet.ip_h = device->ip;

	WorkingSet.state = AS_ERROR;

	WorkingSet.packetsize = DEF_PACKETSIZE;

	WorkingSet.setupComplete = false;

	WorkingSet.client = CAPDFactory::GetAPDFactory()->GetClient();
	WorkingSet.client->SetIPAddress(WorkingSet.ip_h);
	WorkingSet.client->Start();

	WorkingSet.triggerManager = new CLnxTriggerManager();

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		Stream *stream = &WorkingSet.streams[i];

		stream->address = device->ADC[i].boardAddress;
		/*
		 * TODO: read from ADC
		 */
		stream->channelMask = 0xFFFFFFFF;
		stream->bits = 8;
		stream->stream_port_h = STREAM_PORT_BASE + 1 + i + MAX_STREAMNUM * slotNumber;
		stream->stream_server = CAPDFactory::GetAPDFactory()->GetServer();
		stream->dataNotification = CAPDFactory::GetAPDFactory()->GetEvent();
		stream->userNotification = CAPDFactory::GetAPDFactory()->GetEvent();
		stream->eval = new CLnxDataEvaluation();
		stream->eval->SetServer(stream->stream_server);
		stream->eval->SetDataNotificationSignal(stream->dataNotification);
		stream->eval->SetUserNotificationSignal(stream->userNotification);
		WorkingSet.triggerManager->Add(stream->eval);
		

	}

	WorkingSet.waitObject = CAPDFactory::GetAPDFactory()->GetWaitForEvents();

	bool initRes = 1;
	initRes &= GetCCSampleCount(WorkingSet.client, &WorkingSet.sampleCount);
	WorkingSet.bufferSizeInSampleNo = WorkingSet.sampleCount;

	initRes &= GetBasicPLL(WorkingSet.client, &WorkingSet.basicPLLmul, &WorkingSet.basicPLLdiv_0, &WorkingSet.basicPLLdiv_1);

	initRes &= GetExtDCM(WorkingSet.client, &WorkingSet.extDCMmul, &WorkingSet.extDCMdiv);

	initRes &= GetSampleDiv(WorkingSet.client, &WorkingSet.sampleDiv);

	initRes &= GetCCStreamSerial(WorkingSet.client, &WorkingSet.streamSerial_n);
	WorkingSet.streamSerial_n = htonl(WorkingSet.streamSerial_n);
	
	
	if (initRes)
	{
		WorkingSet.state = AS_STANDBY;
	}

	return WorkingSet.handle;
}

ADT_RESULT APDCAM_SyncADC(ADT_HANDLE handle)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	// Syncing ADCs
	int adc_address_list[4];
	for (int i=0; i<WorkingSet.n_streams; i++) 
	{
		Stream *stream = &WorkingSet.streams[i];
		adc_address_list[i] = stream->address;
	}	
	if (syncADCs(WorkingSet.client, WorkingSet.n_streams, adc_address_list)) 
		return ADT_OK;
	else
		return ADT_ERROR;
}	

ADT_RESULT APDCAM_SetAllOffset(ADT_HANDLE handle, unsigned int offset)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	if (offset > 4095) 
		return ADT_PARAMETER_ERROR;
		
	WORKING_SET &WorkingSet = g_WorkingSets[index];

	// Syncing ADCs
	int adc_address_list[4];
	for (int i=0; i<WorkingSet.n_streams; i++) 
	{
		Stream *stream = &WorkingSet.streams[i];
		adc_address_list[i] = stream->address;
	}	
	if (setAllOffset(WorkingSet.client, WorkingSet.n_streams, adc_address_list, offset)) 
		return ADT_OK;
	else
		return ADT_ERROR;
}	

ADT_RESULT APDCAM_Close(ADT_HANDLE handle)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (WorkingSet.client)
		delete WorkingSet.client;
	WorkingSet.client = NULL;

	if (WorkingSet.waitObject)
	{
		WorkingSet.waitObject->RemoveAll();
		delete WorkingSet.waitObject;
	}
	WorkingSet.waitObject = NULL;

	if (WorkingSet.triggerManager)
	{
		WorkingSet.triggerManager->RemoveAll();
		delete WorkingSet.triggerManager;
	}
	WorkingSet.triggerManager = NULL;

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		Stream *stream = &WorkingSet.streams[i];

		if (stream->stream_server)
			delete stream->stream_server;
		stream->stream_server = NULL;
		if (stream->dataNotification)
			delete stream->dataNotification;
		stream->dataNotification = NULL;
		if (stream->userNotification)
			delete stream->userNotification;
		stream->userNotification = NULL;
		if (stream->eval)
			delete stream->eval;
		stream->eval = NULL;
		if (stream->np_memory)
			delete stream->np_memory;
		stream->np_memory = NULL;
	}

	WorkingSet.handle = 0;

	return ADT_OK;
}


ADT_RESULT APDCAM_Save(ADT_HANDLE handle, uint64_t sampleCount)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (!WorkingSet.setupComplete)
	{
		return ADT_SETUP_ERROR;
	}

#define CONTINUOUS_STREAM_DAT
	int i;
	int ch = 0;
	for (i = 0; i < WorkingSet.n_streams; ++i)
	{
		if (WorkingSet.streams[i].eval == NULL)
		{
			ch += CHANNEL_NUM;
			continue;
		}

		int n = 0, s;
		int bit = 1;
		uint64_t real_sampleCount = WorkingSet.streams[i].eval->GetSampleCount();
		uint64_t save_sampleCount = real_sampleCount;
		if (sampleCount && save_sampleCount > sampleCount)
			save_sampleCount = sampleCount;

		for (n = 0, s = 0; n < CHANNEL_NUM; ++n, bit <<= 1, ++ch)
		{
			if (bit & WorkingSet.streams[i].channelMask)
			{
				char filename[32];
#ifdef CONTINUOUS_STREAM_DAT
				snprintf(filename, sizeof(filename), "Channel_%03d.dat", ch);
#else
				snprintf(filename, sizeof(filename), "Channel_%1d_%02d.dat", i, n);
#endif
				FILE *file = fopen(filename, "w");
				if (file == NULL)
				{
					int lerrno = errno;
					fprintf(stderr, "===Cannot create file '%s': %s===\n", filename, strerror(lerrno));
				}
				else
					fwrite(WorkingSet.streams[i].eval->GetChannelData(s), sizeof(INT16), save_sampleCount, file);
				++s;
			}
		}
	}

	return ADT_OK;
}


ADT_RESULT APDCAM_Test(ADT_HANDLE handle)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0) return ADT_INVALID_HANDLE_ERROR;

	ADT_RESULT res = ADT_OK;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	/* Test channel setting routines */
	unsigned char ch1 = 0xFF;
	unsigned char ch2 = 0x55;
	unsigned char ch3 = 0xAA;
	unsigned char ch4 = 0x00;

	if (!SetChannel_1(WorkingSet.client, ch1)) res = ADT_ERROR;
	if (!SetChannel_2(WorkingSet.client, ch2)) res = ADT_ERROR;
	if (!SetChannel_3(WorkingSet.client, ch3)) res = ADT_ERROR;
	if (!SetChannel_4(WorkingSet.client, ch4)) res = ADT_ERROR;

	unsigned char ch1_back, ch2_back, ch3_back, ch4_back;

	if (!GetChannels(WorkingSet.client, &ch1_back, &ch2_back, &ch3_back, &ch4_back)) res = ADT_ERROR;
	if (ch1 != ch1_back || ch2 != ch2_back || ch3 != ch3_back || ch4 != ch4_back) res = ADT_ERROR;
	if (res != ADT_OK) printf("Error in channel setting routines");
	/* End channel setting routines test. */

	return res;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_WritePDI(ADT_HANDLE handle, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (WritePDI(WorkingSet.client, address, subaddress, buffer, noofbytes))
		return ADT_OK;

	return ADT_ERROR;
}


ADT_RESULT APDCAM_ReadPDI(ADT_HANDLE handle, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (ReadPDI(WorkingSet.client, address, subaddress, buffer, noofbytes))
		return ADT_OK;

	return ADT_ERROR;
}


#if 0
ADT_RESULT APDCAM_SetupAllTS(ADT_HANDLE handle)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;
	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (SetupAllTS(WorkingSet.client, WorkingSet.packetsize_1, WorkingSet.packetsize_2, WorkingSet.packetsize_3, WorkingSet.packetsize_4))
		return ADT_OK;

	return ADT_ERROR;
}
#endif


#if 0
ADT_RESULT APDCAM_ShutupAllTS(ADT_HANDLE handle)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;
	WORKING_SET &WorkingSet = g_WorkingSets[index];

	return ADT_OK;
#if 0
	if (ShutupAllTS(WorkingSet.client))
		return ADT_OK;

	return ADT_ERROR;
#endif
}
#endif


ADT_RESULT APDCAM_Allocate(ADT_HANDLE handle, uint64_t sampleCount, int bits, uint32_t channelMask_1, uint32_t channelMask_2, uint32_t channelMask_3, uint32_t channelMask_4, int primary_buffer_size)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (bits != 8 && bits != 12 && bits != 14)
	{
		return ADT_PARAMETER_ERROR;
	}

	primary_buffer_size = std::max(primary_buffer_size, 10);
	primary_buffer_size = std::min(primary_buffer_size, 100);

	if (sampleCount > MAX_SAMPLECOUNT)
	{
		return ADT_PARAMETER_ERROR;
	}

	// After switching on, the sampleCount read back from the ADC board is invalid.
	if (sampleCount == 0 && WorkingSet.bufferSizeInSampleNo == 0)
	{
		return ADT_PARAMETER_ERROR;
	}

	// Delete old setup
	WorkingSet.setupComplete = false;

//#warning FIXME: increasing sampleCount by one to workaround possible firmware bug
	// Save new parameters
	if (sampleCount > 0)
		WorkingSet.bufferSizeInSampleNo = ++sampleCount;

	WorkingSet.streams[0].channelMask = channelMask_1;
	WorkingSet.streams[1].channelMask = channelMask_2;
	WorkingSet.streams[2].channelMask = channelMask_3;
	WorkingSet.streams[3].channelMask = channelMask_4;

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		Stream *stream = &WorkingSet.streams[i];

		if (stream->np_memory)
			delete stream->np_memory;
		stream->np_memory = NULL;

		stream->bits = bits;

		/*
		 * Number of enabled channels
		 */
		unsigned int channels = GetBitCount(stream->channelMask);
		/*
		 * Number of bytes in a sample (with possible _bit_ padding)
		 */
		unsigned int blockSize = GetBlockSize(channels, stream->bits);
		/*
		 * Size of the data portion of a stream packet
		 */
		unsigned int dataSize = WorkingSet.packetsize - sizeof(CC_STREAMHEADER);
		/*
		 * Total number of _data_ bytes requested (ie. just the samples but _with_ padding to CC_OCTET_SIZE)
		 */
		if (blockSize % CC_OCTET_SIZE)
			blockSize += CC_OCTET_SIZE - (blockSize % CC_OCTET_SIZE);
		uint64_t requestedDataSize = blockSize * WorkingSet.bufferSizeInSampleNo;
		/*
		 * Total number of byes requested (ie. including the stream header)
		 */
		uint64_t networkData = (double)requestedDataSize * (double)WorkingSet.packetsize / (double)dataSize;
		/*
		 * Scale to primary_buffer_size percent
		 */
		networkData *= primary_buffer_size / 100.0;
		/*
		 * Enlarge buffersize to packetsize boundary
		 */
		unsigned int buffersize = (networkData / WorkingSet.packetsize + 1) * WorkingSet.packetsize;
		/*
		 * Enlarge buffersize to pagesize boundary
		 */
		stream->primary_buffer_size = (buffersize / PAGESIZE + 1) * PAGESIZE;
		/*
		 * Need to hold a packet
		 */
		stream->temp_buffer_size = (WorkingSet.packetsize - sizeof(CC_STREAMHEADER) / PAGESIZE + 1) * PAGESIZE;
		/*
		 * Every sample is stored in its 16 bit word (ie. unpacked)
		 * Enlarge it to PAGESIZE boundary so that it can be properly aligned
		 */
		stream->user_buffer_size = ((WorkingSet.bufferSizeInSampleNo * sizeof(UINT16)) / PAGESIZE + 1) * PAGESIZE;
		/*
		 * Every channel has its own buffer
		 */
		uint64_t size = stream->primary_buffer_size + stream->temp_buffer_size + CHANNEL_NUM * stream->user_buffer_size;

		stream->np_memory = CAPDFactory::GetAPDFactory()->GetNPMemory(size);
		stream->primary_buffer = stream->np_memory->GetBuffer();
		stream->temp_buffer = stream->primary_buffer + stream->primary_buffer_size;
		stream->user_buffer = stream->temp_buffer + stream->temp_buffer_size;
		stream->requestedData = requestedDataSize;
		stream->eval->SetBuffers(stream->primary_buffer, stream->temp_buffer, stream->user_buffer, stream->user_buffer_size);
		stream->eval->SetParams(stream->bits, stream->channelMask, WorkingSet.packetsize - sizeof(CC_STREAMHEADER));

		SetChannel_1(WorkingSet.client, stream->address, reverseBits(stream->channelMask & 0xFF));
		SetChannel_2(WorkingSet.client, stream->address, reverseBits((stream->channelMask >> 8) & 0xFF));
		SetChannel_3(WorkingSet.client, stream->address, reverseBits((stream->channelMask >> 16) & 0xFF));
		SetChannel_4(WorkingSet.client, stream->address, reverseBits((stream->channelMask >> 24) & 0xFF));
	}

	WorkingSet.setupComplete = true;

	return ADT_OK;
}


ADT_RESULT APDCAM_GetBuffers(ADT_HANDLE handle, INT16 **buffers)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	int i = 0;
	for (i = 0; i < WorkingSet.n_streams; ++i)
	{
		if (WorkingSet.streams[i].eval)
			memcpy(buffers + i * CHANNEL_NUM, WorkingSet.streams[i].eval->GetChannelData(0), CHANNEL_NUM * sizeof(INT16*));
		else
			memset(buffers + i * CHANNEL_NUM, 0, CHANNEL_NUM * sizeof(INT16*));
	}
	for (; i < MAX_STREAMNUM; ++i)
	{
		memset(buffers + i * CHANNEL_NUM, 0, CHANNEL_NUM * sizeof(INT16*));
	}

	return ADT_OK;
}


ADT_RESULT APDCAM_GetSampleInfo(ADT_HANDLE handle, ULONGLONG *sampleCounts, ULONGLONG *sampleIndices)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;
	if (sampleCounts == NULL)
		return ADT_PARAMETER_ERROR;
	if (sampleIndices == NULL)
		return ADT_PARAMETER_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	int i = 0;
	for (i = 0; i < WorkingSet.n_streams; ++i)
	{
		if (WorkingSet.streams[i].eval)
		{
			*(sampleCounts + i) = WorkingSet.streams[i].eval->GetSampleCount();
			*(sampleIndices + i) = WorkingSet.streams[i].eval->GetSampleIndex();
		}
		else
		{
			*(sampleCounts + i) = 0;
			*(sampleIndices + i) = 0;
		}
	}
	for (; i < MAX_STREAMNUM; ++i)
	{
		*(sampleCounts + i) = 0;
		*(sampleIndices + i) = 0;
	}

	return ADT_OK;
}


ADT_RESULT APDCAM_ARM(ADT_HANDLE handle, ADT_MEASUREMENT_MODE mode, uint64_t sampleCount, ADT_CALIB_MODE calibMode, int signalFrequency)
{
	APDCAM_Stop(handle);
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (!WorkingSet.setupComplete)
	{
		return ADT_SETUP_ERROR;
	}

	if (sampleCount > MAX_SAMPLECOUNT)
		return ADT_PARAMETER_ERROR;

	if (sampleCount > 0)
	{
//#warning FIXME: increasing sampleCount by one to workaround possible firmware bug
// Changed by S. Zoletnik   10.07.2014  
// All measurements stopped with timeout
// Trying to reduce the number of samples to wait for
//		WorkingSet.sampleCount = sampleCount + 1;
 WorkingSet.sampleCount = sampleCount;
	}

	if (mode == MM_ONE_SHOT && WorkingSet.sampleCount == 0)
	{
		return ADT_SETUP_ERROR;
	}

	if (WorkingSet.bufferSizeInSampleNo < WorkingSet.sampleCount)
	{
		return ADT_SETUP_ERROR;
	}

	ADT_RESULT res = ADT_OK;

	// Disables HW trigger
	// Commented by S. Zoletnik   10.06.2014
	//ADT_TRIGGER_CONTROL tc;
	//bool b = SetTrigger(WorkingSet.client, tc, 0);

/*
	INT16 dacValues[32];
	// Set dac values (adc offset) to factory calibration values. (Read from the calibration table) Those are the initial values.
	for (int i = 0; i < 32; i++)
	{
		dacValues[i] = 0;
	}
	// Set adc offsets to values, stored in the dacValues array)
	SetDACOffset(WorkingSet.client, dacValues, 0, 32);
*/

	GetCCStreamSerial(WorkingSet.client, &WorkingSet.streamSerial_n);
	WorkingSet.streamSerial_n = htonl(WorkingSet.streamSerial_n);

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		Stream *stream = &WorkingSet.streams[i];

		if (!SetResolution(WorkingSet.client, stream->address, stream->bits))
		{
			// Error handling
			res = ADT_ERROR;
		}

		int channels = GetBitCount(stream->channelMask);
		int blockSize = GetBlockSize(channels, stream->bits);
		/*
		 * Include possible padding
		 */
		if (blockSize % CC_OCTET_SIZE)
			blockSize += CC_OCTET_SIZE - (blockSize % CC_OCTET_SIZE);
		stream->requestedData = blockSize * WorkingSet.sampleCount;
		stream->dataNotification->Reset();
		stream->stream_server->SetNotification(stream->requestedData, stream->dataNotification);

		// Server for stream
		stream->stream_server->Reset();
		stream->stream_server->SetListeningPort(stream->stream_port_h);
		stream->stream_server->SetBuffer(stream->primary_buffer, stream->primary_buffer_size);
		stream->stream_server->SetPacketSize(WorkingSet.packetsize);
		stream->stream_server->SetStreamSerial(WorkingSet.streamSerial_n);
		stream->stream_server->SetStreamInterface(WorkingSet.streamInterface);
//		stream->eval->SetDumpFile(fopen("dump01_samples.dat", "wb"));

		stream->userNotification->Reset();
		stream->eval->SetStreamSerial(WorkingSet.streamSerial_n);
		stream->eval->SetUserNotificationSignal(stream->userNotification);
		WorkingSet.waitObject->Add(stream->userNotification);

		int primary_buffer_size_in_packets = stream->primary_buffer_size / WorkingSet.packetsize;
		int signal_frequency = std::min(signalFrequency, primary_buffer_size_in_packets / 4);
		signal_frequency = std::max(signal_frequency, 100);
		stream->stream_server->SetSignalFrequency(signal_frequency);

		stream->eval->SetCalibratedMode(calibMode == CM_CALIBRATED);
		stream->eval->DisableTrigger();

		unsigned char satabit;
		if (GetCCReg(WorkingSet.client, CC_SETTINGS_TABLE, &satabit, CC_REG_SATACONTROL, CC_REG_SATACONTROL_LEN) == false)
		{
			// Error handling
			res = ADT_ERROR;
		}
		printf("SATA register: %d\n",(int)satabit);
#define MULTICAST
#ifdef MULTICAST
               
		if (satabit) 
		{
                  printf("Running in DualSATA mode\n");
		  if (SetMulticastUDPStream(WorkingSet.client, i*2 + 1, DEF_OCTET, ntohl(inet_addr("239.123.13.100")), stream->stream_port_h) == false)
			fprintf(stderr, "Error setting UDP stream %d\n", i + 1);
		} else
		{
		  if (SetMulticastUDPStream(WorkingSet.client, i + 1, DEF_OCTET, ntohl(inet_addr("239.123.13.100")), stream->stream_port_h) == false)
			fprintf(stderr, "Error setting UDP stream %d\n", i + 1);
		}
#else
		uint8_t mac[] = STREAM_PORT_MAC;
		if (satabit) 
		{
                  printf("Running in DualSATA mode\n");
		  if (SetUDPStream(WorkingSet.client, i*2 + 1, DEF_OCTET, mac, ntohl(inet_addr(STREAM_PORT_IP)), stream->stream_port_h) == false)
			fprintf(stderr, "Error setting UDP stream %d\n", i + 1);
		} else {
		  if (SetUDPStream(WorkingSet.client, i + 1, DEF_OCTET, mac, ntohl(inet_addr(STREAM_PORT_IP)), stream->stream_port_h) == false)
			fprintf(stderr, "Error setting UDP stream %d\n", i + 1);
		}
#endif

		if (mode == MM_ONE_SHOT)
		{
			stream->stream_server->SetType(CAPDServer::ST_ONE_SHOT);
			if (stream->requestedData != 0)
			{
				if (stream->stream_server->Start())
				{
					printf("Stream %d started\n", i + 1);
// Changed by S. Zoletnik    10.07.2014
// Wait for less samples
// stream->eval->SetStopAt(WorkingSet.sampleCount);
					stream->eval->SetStopAt(WorkingSet.sampleCount);
					stream->eval->Start();
				}
				else
				{
					fprintf(stderr, "Could not start Stream %d\n", i + 1);
					res = ADT_ERROR;
				}
	               
			}
		}
		else
		{
			stream->stream_server->SetType(CAPDServer::ST_CYCLIC);
			if (stream->stream_server->Start())
			{
				printf("Stream %d started\n", i + 1);
				stream->eval->SetStopAt(0);
				stream->eval->Start();
			}
			else
			{
				fprintf(stderr, "Could not start Stream %d\n", i + 1);
				res = ADT_ERROR;
			}
		}
	}

	unsigned int octet = (WorkingSet.packetsize - sizeof(CC_STREAMHEADER)) / CC_OCTET_SIZE;

	CCControl(WorkingSet.client, 0x001F);
	Sleep(100);

	if (mode == MM_ONE_SHOT)
	{
		if (!SetCCSampleCount(WorkingSet.client, WorkingSet.sampleCount))
		{
			// Error handling
			res = ADT_ERROR;
		}
	}
	else
	{
		if (!SetCCSampleCount(WorkingSet.client, 0))
		{
			// Error handling
			res = ADT_ERROR;
		}
	}

#if 0
	ADT_STATUS_1 status1;
	if (GetStatus1(WorkingSet.client, &status1.status))
	{
		if (!status1.ADC_PLL_Locked) res = ADT_ERROR;
		//if (!status1.Stream_PLL_Locked) res = ADT_ERROR;
	}
	else
	{
		res = ADT_ERROR;
	}

	ADT_STATUS_2 status2;
	if (GetStatus2(WorkingSet.client, &status2.status))
	{
	}
	else
	{
		res = ADT_ERROR;
	}
#endif

	if (res == ADT_OK)
	{
		WorkingSet.state = AS_ARMED;
	}

	return res;
}


ADT_RESULT APDCAM_StreamDump(ADT_HANDLE handle, uint8_t streamNo, const char *dumpFileName)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	switch (streamNo)
	{
		case 1:
		case 2:
		case 3:
		case 4:
			if (WorkingSet.streams[streamNo - 1].stream_server)
				WorkingSet.streams[streamNo - 1].stream_server->SetDumpFile(fopen(dumpFileName, "wb"));
			break;
		default:
			return ADT_PARAMETER_ERROR;
	}

	return ADT_OK;
}


ADT_RESULT APDCAM_Start(ADT_HANDLE handle)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (WorkingSet.state != AS_ARMED)
	{
		return ADT_SETUP_ERROR;
	}

	ADT_RESULT res = ADT_OK;

	LARGE_INTEGER frequency;
	QueryPerformanceFrequency(&frequency);

	LARGE_INTEGER performanceCount1, performanceCount2;
	QueryPerformanceCounter(&performanceCount1);

#if 0
	WorkingSet.eval_1->m_ReferenceTime = performanceCount1;
	WorkingSet.eval_2->m_ReferenceTime = performanceCount1;
	WorkingSet.eval_3->m_ReferenceTime = performanceCount1;
	WorkingSet.eval_4->m_ReferenceTime = performanceCount1;
#endif

	WorkingSet.state = AS_MEASURE;

	unsigned char control = 0x0F; // Enables streams on all ADCs
	if (!SetCCStreamControl(WorkingSet.client, control))
	{
		// Error handling
		res = ADT_ERROR;
	}

	return res;
}


ADT_RESULT APDCAM_Wait(ADT_HANDLE handle, int timeout)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (WorkingSet.state != AS_MEASURE)
		return ADT_ERROR;

	ADT_RESULT res = ADT_OK;

	CWaitForEvents::WAIT_RESULT wres = WorkingSet.waitObject->WaitAll(timeout);
	if (wres != CWaitForEvents::WR_OK)
	{
		fprintf(stderr, "%s: TimeOut\n", __FUNCTION__);
		res = ADT_TIMEOUT;
	}

	ADT_RESULT stop_res = APDCAM_Stop(handle);

	if (stop_res != ADT_OK)
		return stop_res;

	return res;
}


ADT_RESULT APDCAM_Stop(ADT_HANDLE handle)
{
	int index = GetIndex(handle);

	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	ADT_RESULT res = ADT_OK;

	unsigned char command = 0x00; // Disables streams on all ADCs
	if (!SetCCStreamControl(WorkingSet.client, command))
	{
		// Error handling
		res = ADT_ERROR;
		return res;
	}

	if (WorkingSet.state != AS_MEASURE)
   		return ADT_OK;

	Sleep(100);

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		WorkingSet.streams[i].stream_server->Stop();
	}

	WorkingSet.waitObject->RemoveAll();

	Sleep(500);

	WorkingSet.state = AS_STANDBY;

	for (int i = 0; i < WorkingSet.n_streams; ++i)
	{
		WorkingSet.streams[i].eval->Stop();
	}

	return res;
}


ADT_RESULT APDCAM_Trigger(ADT_HANDLE handle, ADT_TRIGGER trigger, ADT_TRIGGER_MODE mode, ADT_TRIGGER_EDGE edge, int triggerDelay, ADT_TRIGGERINFO* triggerInfo)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

/*	
	Do we need this? Removed S. Zoletnik 8.9.2018
	if (WorkingSet.state != AS_ARMED)
	{
		return ADT_SETUP_ERROR;
	}
*/
	ADT_RESULT res = ADT_OK;

	if (ClearTrigger(WorkingSet.client) == false)
		res = ADT_SETUP_ERROR;

	ADT_TRIGGER_CONTROL tc;
	tc.Disable_Trigger_Event = 1;
	tc.Enable_Rising_Edge = 0;
	tc.Enable_Falling_Edge = 0;			

	if (trigger == TR_HARDWARE)
	{  // Setup hardware trigger
		if (mode == TRM_EXTERNAL)
		{
			if (edge == TRE_RISING)
				tc.Enable_Rising_Edge = 1;
			else
				tc.Enable_Falling_Edge = 1;
		}
		else
		{
			return ADT_NOT_IMPLEMENTED;
		}

	}
	if (SetTrigger(WorkingSet.client, tc, triggerDelay) == false)
		res = ADT_SETUP_ERROR;

	return res;
}


ADT_RESULT APDCAM_SWTrigger(ADT_HANDLE handle)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (WorkingSet.state != AS_MEASURE)
	{
		return ADT_ERROR;
	}

	uint64_t sc = WorkingSet.eval_1->GetSampleCount();
	sc = std::max(sc, WorkingSet.eval_2->GetSampleCount());
	sc = std::max(sc, WorkingSet.eval_3->GetSampleCount());
	sc = std::max(sc, WorkingSet.eval_4->GetSampleCount());

	uint64_t stopAt = sc + WorkingSet.sampleCount; // stopDelay
	WorkingSet.eval_1->SetStopAt(stopAt);
	WorkingSet.eval_2->SetStopAt(stopAt);
	WorkingSet.eval_3->SetStopAt(stopAt);
	WorkingSet.eval_4->SetStopAt(stopAt);

	return ADT_OK;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_SetIP(ADT_HANDLE handle, UINT32 ip_h)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	ADT_RESULT retVal = ADT_OK;

	if (SetIP(WorkingSet.client, ip_h))
	{
		WorkingSet.ip_h = ip_h;
		WorkingSet.client->SetIPAddress(WorkingSet.ip_h);
		Sleep(100);
	}
	else
	{
		retVal = ADT_ERROR;
	}

	return retVal;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_SetStreamInterface(ADT_HANDLE handle, const char *ifname)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	strncpy(WorkingSet.streamInterface, ifname, sizeof(WorkingSet.streamInterface));
	WorkingSet.streamInterface[sizeof(WorkingSet.streamInterface) - 1] = '\0';

	return ADT_OK;
}


ADT_RESULT APDCAM_SetTiming(ADT_HANDLE handle, int basicPLLmul, int basicPLLdiv_0, int basicPLLdiv_1, int clkSource, int extDCMmul, int extDCMdiv)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (basicPLLmul < 0)
		basicPLLmul = WorkingSet.basicPLLmul;
	if (basicPLLdiv_0 < 0)
		basicPLLdiv_0 = WorkingSet.basicPLLdiv_0;
	if (basicPLLdiv_1 < 0)
		basicPLLdiv_1 = WorkingSet.basicPLLdiv_1;
	if (extDCMmul < 0)
		extDCMmul = WorkingSet.extDCMmul;
	if (extDCMdiv < 0)
		extDCMdiv = WorkingSet.extDCMdiv;

	if (basicPLLmul < 20 || 50 < basicPLLmul)
		return ADT_PARAMETER_ERROR;
//	if (basicPLLdiv_0 < 8 || 100 < basicPLLdiv_0)
//		return ADT_PARAMETER_ERROR;
	if (basicPLLdiv_1 < 8 || 100 < basicPLLdiv_1)
		return ADT_PARAMETER_ERROR;

	if (20*basicPLLmul/basicPLLdiv_1 > 35) 
		return ADT_PARAMETER_ERROR;
	if (clkSource)
	{
		if (extDCMmul < 2 || 33 < extDCMmul)
			return ADT_PARAMETER_ERROR;
		if (extDCMdiv < 1 || 32 < extDCMdiv)
			return ADT_PARAMETER_ERROR;
	}

	if (basicPLLmul > 0)
		WorkingSet.basicPLLmul = basicPLLmul;
	if (basicPLLdiv_0 > 0)
		WorkingSet.basicPLLdiv_0 = basicPLLdiv_0;
	if (basicPLLdiv_1 > 0)
		WorkingSet.basicPLLdiv_1 = basicPLLdiv_1;
	if (extDCMmul > 0)
		WorkingSet.extDCMmul = extDCMmul;
	if (extDCMdiv > 0)
		WorkingSet.extDCMdiv = extDCMdiv;

	ADT_RESULT retVal = ADT_OK;

	// Auto ext clock off, sample internal
	printf("%d\n",clkSource);
	if (SetClockControl(WorkingSet.client, clkSource, 0, 0) == false)
	   return ADT_ERROR;

	bool initRes = SetBasicPLL(WorkingSet.client, WorkingSet.basicPLLmul, WorkingSet.basicPLLdiv_0, WorkingSet.basicPLLdiv_1);
	if (clkSource && initRes)
	{
		initRes &= SetExtDCM(WorkingSet.client, extDCMmul, extDCMdiv);
		
	}

	if (!initRes)
		retVal = ADT_ERROR;

	return retVal;;
}


ADT_RESULT APDCAM_Sampling(ADT_HANDLE handle, int sampleDiv, int /*sampleSrc*/)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (sampleDiv == 0)
		return ADT_PARAMETER_ERROR;
	if (sampleDiv > 0xFFFF)
		return ADT_PARAMETER_ERROR;
	if (sampleDiv > 0)
		WorkingSet.sampleDiv = sampleDiv;

	if (SetSampleDiv(WorkingSet.client, WorkingSet.sampleDiv))
		return ADT_OK;

	return ADT_ERROR;
}


ADT_RESULT APDCAM_DataMode(ADT_HANDLE handle, int modeCode)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (SetTestMode(WorkingSet.client, modeCode))
		return ADT_OK;

	return ADT_ERROR;
}


ADT_RESULT APDCAM_Filter(ADT_HANDLE handle, FILTER_COEFFICIENTS filterCoefficients)
{
#if 0
	ADT_RESULT retVal = ADT_OK;

	int index = GetIndex(handle);
	if (index < 0) return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	bool res = SetFilterCoefficients(WorkingSet.client, (UINT16*)&filterCoefficients);
	if (!res)  retVal = ADT_ERROR;

	return retVal;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_CalibLight(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_Shutter(ADT_HANDLE handle, int open)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	if (open != 0 || open != 1)
		return ADT_PARAMETER_ERROR; //Added by SP

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	ADT_RESULT retVal = ADT_OK;

	int mode;
	if (GetShutterMode(WorkingSet.client, &mode) == false)
		return ADT_ERROR;

	if (mode != 0)
		return ADT_ERROR;

	if (SetShutterState(WorkingSet.client, open))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT SetShutterMode(ADT_HANDLE handle, int mode)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	if (mode < 0 || mode > 1)
		return ADT_PARAMETER_ERROR; //Added by SP

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (SetShutterMode(WorkingSet.client, mode))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT GetShutterMode(ADT_HANDLE handle, int *mode)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (GetShutterMode(WorkingSet.client, mode))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_CalibLight(ADT_HANDLE handle, int value)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	if (value < 0 || value > 4095)
		return ADT_PARAMETER_ERROR; //Added by SP

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (SetCalibLight(WorkingSet.client, value))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_GetCalibLight(ADT_HANDLE handle, int *value)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (GetCalibLight(WorkingSet.client, value))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


#define BASE_LEVEL 14745.0

// Offszet kalibracio. (Kell meg gain calib)
ADT_RESULT APDCAM_Calibrate(ADT_HANDLE handle)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	ADT_RESULT res;
	int basicPLLmul = 20, basicPLLdiv_0  = 40, basicPLLdiv_1  = 40, clkSrc = 0, extDCMmul = -1, extDCMdiv = -1;
	res = APDCAM_SetTiming(handle, basicPLLmul, basicPLLdiv_0, basicPLLdiv_1, clkSrc, extDCMmul, extDCMdiv);

	int sampleDiv = 5; // 2Mhz de 1 khz-en kellene
	int sampleSrc = 0; // internal
	res = APDCAM_Sampling(handle, sampleDiv, sampleSrc);

	// For calibration about 10000 measurements are used
	uint64_t sampleCount = 10000;
	int bits = 14;
	int channelMask_1 = 255, channelMask_2 = 255, channelMask_3 = 255, channelMask_4 = 255;
	res = APDCAM_Allocate(handle, sampleCount, bits, channelMask_1, channelMask_2, channelMask_3, channelMask_4);

	CDataEvaluation *dataEvaluate[4];
	dataEvaluate[0] = WorkingSet.eval_1;
	dataEvaluate[1] = WorkingSet.eval_2;
	dataEvaluate[2] = WorkingSet.eval_3;
	dataEvaluate[3] = WorkingSet.eval_4;

	//Close shutter
	// Switch of calibration light

	INT16 dacValues[32];
	// Set dac values (adc offset) to factory calibration values. (Read from the calibration table) Those are the initial values.
	for (int i = 0; i < 32; i++)
	{
		dacValues[i] = 2048;
	}

	double adcOffsets[32];
	INT16 step = 1024; // 1/4 of range 2^12

	while (step > 0)
	{
		// Set adc offsets to values, stored in the dacValues array)
		SetDACOffset(WorkingSet.client, dacValues, 0, 32);

		// Makes about 10000 measurement
		res = APDCAM_ARM(handle, MM_ONE_SHOT, sampleCount, CM_NONCALIBRATED);
		res = APDCAM_Start(handle);
		//res = APDCAM_Wait(handle);

		// Calculates mean for each channel
		for (int channel = 0; channel < 32; channel ++)
		{
			int streamIndex = channel / 4;
			int channelIndex = channel % 4;
			CDataEvaluation *eval = dataEvaluate[streamIndex];
			INT16 *buffer = eval->m_ChannelData[channelIndex];
			double mean = 0;
			for (int sample = 0; sample < sampleCount; sample++)
			{
				mean += (double)(*buffer);
				buffer++;
			}
			mean = mean / sampleCount;
			// When the dac values are calibrated, the mean must be about 2^14 * 0.9 ~ 16386*0.9 = 14745 (BASE_LEVEL)
			// some margin must be left.

			adcOffsets[channel] = mean;
			if (mean < BASE_LEVEL)
			{ // increase dac value
				dacValues[channel] = std::min(dacValues[channel] + step, 4096);
			}
			else
			{ // decrease dac value
				dacValues[channel] = std::max(dacValues[channel] - step, 0);
			}
		}
		step = step / 2;
	}

	// Set adc offsets to values, stored in the dacValues array)
	SetDACOffset(WorkingSet.client, dacValues, 0, 32);

	// At the end the adc values are measured, as calibration data, and stored in the calibration table
	INT16 shAdcOffsets[32];
	for (int i = 0; i < 32; i++)
	{
		shAdcOffsets[i] = (INT16)floor(adcOffsets[i] + 0.5);
	}
	bool b = StoreADCOffsets(WorkingSet.client, shAdcOffsets, 0, 32);

	return res;
#else
	NOT_IMPL;
#endif
}


//10G Control
ADT_RESULT APDCAM_CCControl(ADT_HANDLE handle, int opcode, int length, unsigned char *buffer)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (CCControl(WorkingSet.client, opcode, length, buffer))
		return ADT_OK;

	return ADT_ERROR;
}


ADT_RESULT APDCAM_ReadCC(ADT_HANDLE handle, int acktype, unsigned char *value, int firstreg, int length)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (GetCCReg(WorkingSet.client, acktype, value, firstreg, length))
		return ADT_OK;

	return ADT_ERROR;
}

ADT_RESULT APDCAM_ReadFlashPage(ADT_HANDLE handle, int PgAddress, unsigned char *value)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;
	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (GetFlashPage(WorkingSet.client, PgAddress, value))
		return ADT_OK;

	return ADT_ERROR;
}

ADT_RESULT APDCAM_StartFUP(ADT_HANDLE handle)
{
	time_t currTime;
	struct tm *localTime;
    	currTime = time(NULL);
	localTime = localtime (&currTime);
        unsigned char date[4];
        date[0] = (localTime->tm_year+1900) >> 8;
	date[1] = (localTime->tm_year+1900) & 0xff;
	date[2] = localTime->tm_mon+1;
	date[3] = localTime->tm_mday;
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;
	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (StartFirmwareUpdate(WorkingSet.client, date))
		return ADT_OK;

	return ADT_ERROR;
}
	        

ADT_RESULT APDCAM_Gain(ADT_HANDLE handle, double highVoltage1, double highVoltage2, double highVoltage3, double highVoltage4, int state)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (state < 0 || state > 1)
		return ADT_PARAMETER_ERROR; //Added by SP

	ADT_RESULT res = ADT_OK;

	if (state != 0)
	{
		ADT_FACTORY_DATA dataType = AFD_ADC_TABLE_STATUS;
		FACTORY_DATA factoryData = {0};
		bool b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
		int tableStat = factoryData.PCTableStatus;
		if (factoryData.PCTableStatus < 1)
		{  // Empty factory table
			res = ADT_FACTORY_SETUP_ERROR;
			return res;
		}

		// Reads back factory calibration data, needed for perform calibration.
		/*ADT_FACTORY_DATA*/ dataType = AFD_OUTPUT_HV_CALIB;
		//FACTORY_DATA factoryData;
		/*bool*/ b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
		float outputHvCalib1 = factoryData.OutputHVCalib[0];
		float outputHvCalib2 = factoryData.OutputHVCalib[1];
		dataType = AFD_OUTPUT_HV_CALIB_2;
		b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
		float outputHvCalib3 = factoryData.OutputHVCalib2[0];
		float outputHvCalib4 = factoryData.OutputHVCalib2[1];


		if (_isnan(outputHvCalib1) || outputHvCalib1 < 0 || 1 < outputHvCalib1)
		{
			res = ADT_FACTORY_SETUP_ERROR;
			return res;
		}

		if (_isnan(outputHvCalib2) || outputHvCalib2 < 0 || 1 < outputHvCalib2)
		{
			res = ADT_ERROR;
			return res;
		}

		if (_isnan(outputHvCalib3) || outputHvCalib3 < 0 || 1 < outputHvCalib3)
		{
			res = ADT_FACTORY_SETUP_ERROR;
			return res;
		}

		if (_isnan(outputHvCalib4) || outputHvCalib4 < 0 || 1 < outputHvCalib4)
		{
			res = ADT_ERROR;
			return res;
		}

		// Set detector bias voltage, enables and switches on.
		// 0,12V / digit.
		int binValue1 = (int)(highVoltage1 / outputHvCalib1);
		int binValue2 = (int)(highVoltage2 / outputHvCalib2);
		int binValue3 = (int)(highVoltage3 / outputHvCalib3);
		int binValue4 = (int)(highVoltage4 / outputHvCalib4);
		if (!SetHV1(WorkingSet.client, binValue1))
		{
			res = ADT_ERROR;
			return res;
		};
		//int binValue_1;
		//GetHV1(WorkingSet.client, &binValue_1);

		if (!SetHV2(WorkingSet.client, binValue2))
		{
			res = ADT_ERROR;
			return res;
		};
		//int binValue_2;
		//GetHV2(WorkingSet.client, &binValue_2);
		if (!SetHV3(WorkingSet.client, binValue3))
		{
			res = ADT_ERROR;
			return res;
		};
		//int binValue_3;
		//GetHV1(WorkingSet.client, &binValue_3);

		if (!SetHV4(WorkingSet.client, binValue4))
		{
			res = ADT_ERROR;
			return res;
		};
		//int binValue_4;
		//GetHV2(WorkingSet.client, &binValue_4);

		if (!EnableHV(WorkingSet.client, true))
		{
			res = ADT_ERROR;
			return res;
		};

		if (!SetHVState(WorkingSet.client, 1))
		{
			res = ADT_ERROR;
		};
//		int s = 0;
//		GetHVState(WorkingSet.client, &s);
//		unsigned short hvMonitor[4] = {0};
//		b = GetAllHVMonitor(WorkingSet.client, hvMonitor);
	}
	else
	{
		if (!SetHVState(WorkingSet.client, 0)) { res = ADT_ERROR; };
		if (!EnableHV(WorkingSet.client, false)) { res = ADT_ERROR; };
	}

	unsigned short fwVersion;
	GetPCFWVersion(WorkingSet.client, &fwVersion);
	//printf("fw: %d\n", fwVersion);

	if (fwVersion >= 120 && state >= 1)
	{
		bool ret = SetAnalogPower(WorkingSet.client, 1);
		if (!ret) res = ADT_ERROR;
	}
	else
	{
		bool ret = SetAnalogPower(WorkingSet.client, 0);
		if (!ret) res = ADT_ERROR;
	}

	/*int astate;
	bool ret = GetAnalogPower(WorkingSet.client, &astate);
	printf("analog: %d\n", astate);*/

	return res;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_GetHV(ADT_HANDLE handle, double &highVoltage1, double &highVoltage2, double &highVoltage3, double &highVoltage4, int &state)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	ADT_RESULT res = ADT_OK;

	ADT_FACTORY_DATA dataType = AFD_ADC_TABLE_STATUS;
	FACTORY_DATA factoryData = {0};
	bool b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
	int tableStat = factoryData.PCTableStatus;
	if (factoryData.PCTableStatus < 1)
	{  // Empty factory table
		res = ADT_FACTORY_SETUP_ERROR;
		return res;
	}

	// Reads back factory calibration data, needed for perform calibration.
	dataType = AFD_OUTPUT_HV_CALIB;
	memset(&factoryData, 0, sizeof(FACTORY_DATA));
	b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
	float outputHvCalib1 = factoryData.OutputHVCalib[0];
	float outputHvCalib2 = factoryData.OutputHVCalib[1];

	dataType = AFD_OUTPUT_HV_CALIB_2;
	memset(&factoryData, 0, sizeof(FACTORY_DATA));
	b = GetFactoryData(WorkingSet.client, dataType, &factoryData);
	float outputHvCalib3 = factoryData.OutputHVCalib2[0];
	float outputHvCalib4 = factoryData.OutputHVCalib2[1];

	if (_isnan(outputHvCalib1) || outputHvCalib1 < 0 || 1 < outputHvCalib1)
	{
		res = ADT_FACTORY_SETUP_ERROR;
		return res;
	}

	if (_isnan(outputHvCalib2) || outputHvCalib2 < 0 || 1 < outputHvCalib2)
	{
		res = ADT_ERROR;
		return res;
	}

	if (_isnan(outputHvCalib3) || outputHvCalib3 < 0 || 1 < outputHvCalib3)
	{
		res = ADT_FACTORY_SETUP_ERROR;
		return res;
	}

	if (_isnan(outputHvCalib4) || outputHvCalib4 < 0 || 1 < outputHvCalib4)
	{
		res = ADT_ERROR;
		return res;
	}

	int binValue1 = 0, binValue2 = 0, binValue3 = 0, binValue4 = 0;
	if (!GetHV1(WorkingSet.client, &binValue1))
	{
		res = ADT_ERROR;
		return res;
	};

	if (!GetHV2(WorkingSet.client, &binValue2))
	{
		res = ADT_ERROR;
		return res;
	};

	if (!GetHV3(WorkingSet.client, &binValue3))
	{
		res = ADT_ERROR;
		return res;
	};

	if (!GetHV4(WorkingSet.client, &binValue4))
	{
		res = ADT_ERROR;
		return res;
	};

	highVoltage1 = binValue1 * outputHvCalib1;
	highVoltage2 = binValue2 * outputHvCalib2;
	highVoltage3 = binValue3 * outputHvCalib3;
	highVoltage4 = binValue4 * outputHvCalib4;

	if (!GetHVState(WorkingSet.client, &state))
	{
		res = ADT_ERROR;
		return res;
	}
	return res;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_SetRingbufferSize(ADT_HANDLE handle, unsigned short bufferSize)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (bufferSize < 0 || bufferSize > 1023)
	{
		return ADT_PARAMETER_ERROR;
	}


	if (SetRingbufferSize(WorkingSet.client, bufferSize))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_GetRingbufferSize(ADT_HANDLE handle, unsigned short *bufferSize)
{
#if 0
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (GetRingbufferSize(WorkingSet.client, bufferSize))
		return ADT_OK;

	return ADT_ERROR;
#else
	NOT_IMPL;
#endif
}


ADT_RESULT APDCAM_SetBasicPLL(ADT_HANDLE handle, unsigned char mul, unsigned char div0, unsigned char div1)
{
	int index = GetIndex(handle);
	if (index < 0)
		return ADT_INVALID_HANDLE_ERROR;

	WORKING_SET &WorkingSet = g_WorkingSets[index];

	if (SetBasicPLL(WorkingSet.client, mul, div0, div1))
		return ADT_OK;

	return ADT_ERROR;
}


ADT_RESULT APDCAM_MeasMode(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_SetOffset(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_Overload(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_Temperature(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}

ADT_RESULT APDCAM_Fans(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_Reset(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_SaveCalibration(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_LoadCalibration(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_SaveSetup(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_LoadSetup(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_GetStatus(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


ADT_RESULT APDCAM_GetInfo(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}


/*
ADT_RESULT APDCAM_AllocateBuffer(ADT_HANDLE handle)
{
	NOT_IMPL;
}
*/


ADT_RESULT APDCAM_CheckSetup(ADT_HANDLE /*handle*/)
{
	NOT_IMPL;
}
