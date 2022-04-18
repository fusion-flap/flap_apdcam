#include <stdio.h>
#include <unistd.h>

#include "TypeDefs.h"
#include "DataEvaluation.h"
#include "InternalFunctions.h"
#include "Helpers.h"

#define GET_BYTE(p)  (*((uint8_t*)(p)))

/* ********** Helpers for data evaluation  ********** */
static UINT16 GetMask(int bitsPerSample)
{
	UINT16 mask = 0xFFFF;
	return mask >> (16 - bitsPerSample);
}


inline uint16_t GetData8(const unsigned char *pData, int offset)
{
	int byteOffset = offset >> 3; // / 8
	uint16_t data = GET_BYTE(pData + byteOffset);
	return data;
}


inline uint16_t GetData12(const unsigned char *pData, int offset)
{
	int byteOffset = offset >> 3; // / 8
	uint16_t data;

	if (offset % 8 == 0)
		data = (GET_BYTE(pData + byteOffset) << 4) | (GET_BYTE(pData + byteOffset + 1) >> 4);
	else
		data = (GET_BYTE(pData + byteOffset) << 8) | GET_BYTE(pData + byteOffset + 1);
	return data & 0x0FFF;
}


inline uint16_t GetData14(const unsigned char *pData, int offset)
{
	int byteOffset = offset >> 3; // / 8
	int bitOffset = offset & 0x07; // % 8;
	uint16_t data;

	if (bitOffset == 0)
		data = (GET_BYTE(pData + byteOffset) <<  6) | (GET_BYTE(pData + byteOffset + 1) >> 2);
	else if (bitOffset == 6)
		data = (GET_BYTE(pData + byteOffset) << 12) | (GET_BYTE(pData + byteOffset + 1) << 4) | (GET_BYTE(pData + byteOffset + 2) >> 4);
	else if (bitOffset == 4)
		data = (GET_BYTE(pData + byteOffset) << 10) | (GET_BYTE(pData + byteOffset + 1) << 2) | (GET_BYTE(pData + byteOffset + 2) >> 6);
	else if (bitOffset == 2)
		data = (GET_BYTE(pData + byteOffset) <<  8) | GET_BYTE(pData + byteOffset + 1);
	else
	{
		data = 0;
		fprintf(stderr, "\n\n\nWrong bitlength!!!\n\n\n");
	}
	return data & 0x3FFF;
}


/* ********** CDataEvaluation class methods  ********** */

CDataEvaluation::CDataEvaluation() :
	m_TriggerManager(NULL),
	m_Triggered(false),
	m_pDataNotificationSignal(NULL),
	m_pUserNotificationSignal(NULL),
	m_PacketNo(0),
	m_ChannelData(),
	m_ChannelMap(),
	m_ActiveChannelNo(0),
	m_Server(NULL),
	m_SrcBuffer(NULL),
	m_WritePtr(0),
	m_DataLength(0),
	m_Running(false),
	m_Calibrated(false),
	m_WorkBuffer(NULL),
	m_UserBuffer(NULL),
	m_UserBufferSize(0),
	m_Bits(0),
	m_ChannelMask(0),
	m_ADCPacketSize(0),
	m_CCPacketSize(sizeof(CC_STREAMHEADER)),
	m_BlockSize(0),
	m_PaddedBlockSize(0),
	m_Mask(0),
	m_ChannelOffsets(),
	m_MaxNoofBlocks(0),
	m_ExpectedPacketCounter(1),
	m_ContinuityError(false),
	m_SampleCount(0),
	m_SampleIndex(0),
	m_UserBufferSizeInSample(0),
	m_StopAt(0),
	m_StreamNo(0),
	m_ProcessingCount(0),
	m_CallingCount(0),
	dumpFile(NULL),
	m_StreamSerial(0)
{
	for (unsigned int i = 0; i < sizeof(m_TriggerInfo) / sizeof(m_TriggerInfo[0]); ++i)
	{
		m_TriggerInfo[i].TriggerInfo = 0;
		m_TriggerEnabled[i] = 0;
		m_TriggerLevels[i] = 0;
	}

	m_ProcessingTime.QuadPart = 0;
	m_LastCallingTime.QuadPart = 0;
	m_AvarageCallingTime.QuadPart = 0;
	memset(m_ChannelOffsets, 0, sizeof(m_ChannelOffsets));
}


CDataEvaluation::~CDataEvaluation()
{
	Stop();
if (dumpFile)
	fclose(dumpFile);
}


void CDataEvaluation::InternalStop()
{
	m_ExitSignal->Set();
}


unsigned int CDataEvaluation::Handler()
{
	/*
	 * FIXME: reset values!!!
	 *  (ie. just restore what was originally here...)
	 */
	m_PacketNo = 0;
	m_WritePtr = 0;
	m_DataLength = 0;
	m_MaxNoofBlocks = 0;
	m_ExpectedPacketCounter = 1;
	m_ContinuityError = false;
	m_SampleCount = 0;
	m_SampleIndex = 0;
	m_StreamNo = 0;

	FillMap();
	m_BlockSize = GetBlockSize(m_ActiveChannelNo, m_Bits);
	if (m_BlockSize % CC_OCTET_SIZE)
		m_PaddedBlockSize = m_BlockSize + CC_OCTET_SIZE - (m_BlockSize % CC_OCTET_SIZE);
	else
		m_PaddedBlockSize = m_BlockSize;
	m_Mask = GetMask(m_Bits);

	for (int channel = 0; channel < CHANNEL_NUM; ++channel)
	{
		m_ChannelData[channel] = (INT16*)(m_UserBuffer + m_UserBufferSize * channel);
	}

	m_UserBufferSizeInSample = m_UserBufferSize / sizeof(UINT16);

	m_LastCallingTime.QuadPart = 0;

	CWaitForEvents *waitObject = CAPDFactory::GetAPDFactory()->GetWaitForEvents();
	if (!waitObject)
		return 1;

	waitObject->Add(m_pDataNotificationSignal);
	waitObject->Add(m_ExitSignal);

	m_Running = true;

	InitDone();

	bool bQuit = false;
	while (!bQuit)
	{
		int index = -1;
		int retVal = waitObject->WaitAny(-1, &index);
		if (retVal != CWaitForEvents::WR_OK)
			continue;

		switch (index) 
		{
			case 0:	// data arrived signal 
				{
					m_pDataNotificationSignal->Reset();
					LARGE_INTEGER performanceCount1, performanceCount2;
					QueryPerformanceCounter(&performanceCount1);

					if (m_LastCallingTime.QuadPart != 0)
					{
						m_AvarageCallingTime.QuadPart += performanceCount1.QuadPart - m_LastCallingTime.QuadPart;
						m_CallingCount++;
					}
					m_LastCallingTime.QuadPart = performanceCount1.QuadPart;

					ProcessData();
                 if (m_ContinuityError)  bQuit = true;
                 
					QueryPerformanceCounter(&performanceCount2);
					m_ProcessingTime.QuadPart += performanceCount2.QuadPart - performanceCount1.QuadPart;
					m_ProcessingCount++;
				}
				break;
			case 1:	// exit thread signal
				{ 
					LARGE_INTEGER frequency;
					QueryPerformanceFrequency(&frequency);

					double ce = 1000*(double)(m_AvarageCallingTime.QuadPart)/(double)frequency.QuadPart;
					if (m_CallingCount)
					{
						ce = ce / m_CallingCount;
//						printf("Average calling time: %g ms (%d)\n",ce, m_StreamNo);
					}

					ce = 1000*(double)(m_ProcessingTime.QuadPart)/(double)frequency.QuadPart;
					if (m_ProcessingCount)
					{
						ce = ce / m_ProcessingCount;
//						printf("Average data conversion time: %g ms (%d)\n",ce, m_StreamNo);
					}

					bQuit = true;
				}
				break;
			default:
				// other unknown error (timeout, etc.)
				break;
		}
	}
	if (!m_ContinuityError)
	{ 
	  printf("Packets received: %u (Stream: %u)\n", m_Server->GetPacketNo(), m_StreamNo);
//	  printf("Max noof blocks: %u, %" PRIu64 " (Stream: %u)\n", m_MaxNoofBlocks, m_SampleCount, m_StreamNo);
	  fflush(stdout);
   }
   else
   {
      exit(1);
   }
	delete waitObject;

	return 0;
}


void CDataEvaluation::ProcessData()
{
   /* This routine processes the incoming UDP packets.
   Handling of packet loss, and other problems:

    - We allow for the loss of MAX_PACKET_LOSS number of packets. If the packet counter jumps less than
      this number we fill in the missing data by 0.
    - If the packet number jumps backwards we assume that the measurement was restarted and we drop all data before. 
      We also assume that the measurements start with packet number 1. If this is not the case the packet loss
      strategy is used.
   */
	bool errorCondition = false;
	unsigned int packetNo = m_Server->GetPacketNo(); // Returns the packet counter
	unsigned int maxPacketNo = m_Server->GetMaxPacketNo();

	m_MaxNoofBlocks = std::max(m_MaxNoofBlocks, (packetNo - m_PacketNo)); // Maximum number of blocks to process

   // m_PacketNo is the next packet
	if (m_PacketNo == 0 && packetNo)
	{
	   // If this is the first packet and there is a packet available
		unsigned char* pSource = m_SrcBuffer;
		CC_STREAMHEADER *header = reinterpret_cast<CC_STREAMHEADER*>(pSource);

		if (header->serial != m_StreamSerial)
		{
			fprintf(stderr, "Error in stream number: 0x%X (expected:%d)\n", header->serial,m_StreamSerial);
			fflush(stderr);
			return;
		}
 
		m_ExpectedPacketCounter = 1;
		m_StreamNo = CC_StreamNum(header);
	}

	while (m_PacketNo < packetNo)  // Processing packets up to the number in the buffer
	{
		unsigned char* pSource = m_SrcBuffer + ((m_PacketNo % maxPacketNo) * m_CCPacketSize);
		CC_STREAMHEADER *header = reinterpret_cast<CC_STREAMHEADER*>(pSource);

		if (header->serial != m_StreamSerial)
		{
    		// If stream number changes this is a fatal error, hve to stop.
			fprintf(stderr, "Error in stream number. Packet: %d  Header stream No: 0x%X (expected: %d)\n", m_PacketNo, header->serial, m_StreamNo);
			fflush(stderr);
			errorCondition = true;
			break;
		}

                // Reading the packet counter from the packet
		uint64_t packetCounter = CC_PACKETCOUNTER(header);
	
// This is for testing packet loss   S. Zoletnik 4.9.2018 		
//		if (packetCounter == 100) 
//		{
//		  m_PacketNo++;
//		  continue;
//		}

		if (packetCounter < m_ExpectedPacketCounter)
		{
			fprintf(stderr,"Error, unexpected packet received. Packet counter: %" PRIu64 " (expected: %" PRIu64 ". (stream: %d)\n", 
				          packetCounter, m_ExpectedPacketCounter, m_StreamNo);
			fflush(stderr);
				++m_PacketNo;
				m_ContinuityError = true;
				errorCondition = true;
				break;
		}


		if (m_ExpectedPacketCounter != packetCounter)
		{
        	    if (packetCounter-m_ExpectedPacketCounter-1 > MAX_PACKET_LOSS)
        	    {
        	       fprintf(stderr, "Error, too many packet lost: %" PRIu64 " (after packet: %d, stream: %d)\n", 
                	   packetCounter-m_ExpectedPacketCounter-1, m_PacketNo, m_StreamNo);
					  fflush(stderr);
					  ++m_PacketNo;
					  m_ContinuityError = true;
					  errorCondition = true;
					  break;
        	    }
          				
          	 printf("Warning, %" PRIu64 " packet lost. (After packet: %d, stream: %d). Inserting zero data.\n", 
                 packetCounter-m_ExpectedPacketCounter, m_PacketNo, m_StreamNo);
			// Inserting empty packets
			CC_STREAMHEADER empty_header;
			unsigned char empty_data[m_ADCPacketSize];
			for (unsigned int i=0; i<m_ADCPacketSize; i++) empty_data[i] = 0;
			for (unsigned int i=0; i<packetCounter-m_ExpectedPacketCounter; i++)
			{
			  for (unsigned int j=0; j<sizeof(ADT_CC_COUNTER); j++) empty_header.packetCounter[j] = 
			                                            (unsigned char) ((m_ExpectedPacketCounter >> j) & 0xFF);
			  ProcessFrame(reinterpret_cast<CC_STREAMHEADER*>(&empty_header), empty_data, m_PacketNo);
        	  ++m_ExpectedPacketCounter;
        	}  
		}

		ProcessFrame(header, pSource + sizeof(CC_STREAMHEADER), m_PacketNo);

		++m_PacketNo;
		++m_ExpectedPacketCounter;
	}

	if (errorCondition)
	{
		m_WritePtr = 0;
		m_DataLength = 0;
	}
}

// This processes the contents of one UDP packet
// pFrame is the start of the data
void CDataEvaluation::ProcessFrame(const CC_STREAMHEADER *header, const unsigned char *pFrame, unsigned int packetNo)
{
	if (!m_Running)
		return;

	memcpy(m_WorkBuffer + m_WritePtr, pFrame, m_ADCPacketSize);
	m_DataLength += m_ADCPacketSize;

	unsigned char* pData = m_WorkBuffer;

        // Prpcess until there is data for a full sample
	while (m_DataLength >= m_BlockSize)
	{
		++m_SampleCount;

		ProcessBlock(pData); // ProcessBlock(m_TempBuffer + m_ReadPtr);

		pData += m_PaddedBlockSize;
		m_DataLength -= m_PaddedBlockSize;
	}

        // If some data is left move it to the beginning of the buffer and put the write buffer at the end
        // The next packet will add more data
	if (m_DataLength)
		memcpy(m_WorkBuffer, pData, m_DataLength); // memcpy(m_WorkBuffer, m_WorkBuffer + m_ReadPtr, m_DataLength);
	m_WritePtr = m_DataLength;
}


// Reads data of all channels from one sample block and places into the channel buffers 
// pdata is the byte pointer of the start of the sample block
void CDataEvaluation::ProcessBlock(unsigned char *pData)
{
	if (m_Running || m_StopAt == 0)
	{
		int offset = 0;
        //int *channelMap = m_ChannelMap;
		uint32_t mask=1;
		int channel=0;
		// Looping through the 4 ADC blocks in one ADC card
        for (int i_block=0; i_block<4; i_block++)
		{
			// Looping thorugh the 8 channels in one ADC block
			for (int i_ch=0; i_ch<8; i_ch++)
			{
                if (m_ChannelMask & mask)
				{
					// Get data from sample block
                    int16_t data = 0;
					switch (m_Bits)
					{
						case 8:
							data = (int16_t)GetData8(pData, offset);
							break;
						case 12:
							data = (int16_t)GetData12(pData, offset);
							break;
						case 14:
							data = (int16_t)GetData14(pData, offset);
							break;
						default:
							data = 0xFFFF;
							break;
					}
                    //bitcount += m_Bits;
                   // int luv = *channelMap++; // Gets the real channelindex
                    Trigger(channel,data);
                    *(m_ChannelData[channel++] + m_SampleIndex) = data;
					offset += m_Bits;
				}
				mask <<= 1;
			}
                	// Padding to byte boundary
			if (offset % 8)
                offset = (offset / 8 +1)*8;
		}

		m_SampleIndex++;
		if (m_SampleIndex >= m_UserBufferSizeInSample)
			m_SampleIndex = 0;

		if (m_StopAt != 0 && m_SampleCount == m_StopAt && m_pUserNotificationSignal)
		{
			m_Running = false;
			m_pUserNotificationSignal->Set();
		}
	}
}





void CDataEvaluation::Trigger(int channel, INT16 data)
{
	if (m_Triggered)
	{
		int info = m_TriggerEnabled[channel];
		if (info)
		{
			if (info == 1)
			{//Sensitivity == 0
				if (m_TriggerLevels[channel] < data)
				{
					DoTrigger();
				}
			}
			else
			{//Sensitivity == 1
				if (m_TriggerLevels[channel] > data)
				{
					DoTrigger();
				}
			}
		}
	}
}


/*
E.g. For 01101001

map[0] = 0
map[1] = 3
map[2] = 5
map[3] = 6
map[4] = n/a
map[5] = n/a 
map[6] = n/a
map[7] = n/a

no = 4;
*/
void CDataEvaluation::FillMap()
{
	uint32_t mask = m_ChannelMask;

	for (unsigned int i = 0; i < CHANNEL_NUM; ++i)
		m_ChannelMap[i] = -1;
	m_ActiveChannelNo = 0;
	for (unsigned int i = 0; i < CHANNEL_NUM; ++i)
	{
		if ((mask & 0x01))
		{
			m_ChannelMap[m_ActiveChannelNo] = i;
			m_ActiveChannelNo++;
		}
		mask = mask >> 1;
	}
}


bool CDataEvaluation::SetParams(unsigned int bits, uint32_t channelMask, unsigned int packetSize) 
{
	if (bits != 8 && bits != 12 && bits != 14)
		return false;
	m_Bits = bits;
	m_ChannelMask = channelMask;
	m_ADCPacketSize = packetSize;
	m_CCPacketSize = m_ADCPacketSize + sizeof(CC_STREAMHEADER);

	return true;
}


void CDataEvaluation::SetCalibratedMode(bool calibrated) 
{ 
	m_Calibrated = calibrated;
	if (!m_Calibrated)
	{
		INT16 max_value = 16383;
		switch (m_Bits)
		{
			case 8:
				max_value = 255;
				break;
			case 12:
				max_value = 4095;
				break;
		}
		for (int i = 0; i < CHANNEL_NUM; ++i)
		{
			m_ChannelOffsets[i] = max_value;
		}
	}
}


void CDataEvaluation::SetTrigger(ADT_TRIGGERINFO *triggerInfo)
{
	m_Triggered = true;
//	m_StopAt = 0;
	memcpy(m_TriggerInfo, triggerInfo, 8*sizeof(ADT_TRIGGERINFO));
	for (int i = 0; i < 8; i++)
	{
		if (!m_TriggerInfo[i].Enable)
		{
			m_TriggerEnabled[i] = 0;
		}
		else if (m_TriggerInfo[i].Sensitivity == 0)
		{
			m_TriggerEnabled[i] = 1;
			m_TriggerLevels[i] = m_TriggerInfo[i].TriggerLevel;
		}
		else
		{
			m_TriggerEnabled[i] = 2;
			m_TriggerLevels[i] = m_TriggerInfo[i].TriggerLevel;
		}
	}
}


bool CDataEvaluation::SetupCalibrationData(CAPDClient *client, int streamNo)
{
	if (m_Bits != 8 && m_Bits != 12 && m_Bits != 14)
		return false;

	INT16 dacOffsets[32];
	int channelIndex = (streamNo -1) * 8;
	// Retrieves the dac offsets from the calibration table.
	bool retVal = RetrieveDACOffsets_01mV(client, dacOffsets, channelIndex, 8);
	if (!retVal) return retVal; // Error reading calibration data
	// Set dac offsets in the hw, using SetDACOffset()
	retVal = SetDACOffset(client, dacOffsets, channelIndex, 8);
	if (!retVal) return retVal; // Error while set DAC data

	// Retrieve ADC offsets from the non-volative store, normalize them, according to the actual bitnumber.
	INT16 adcOffsets[32];
	retVal = RetrieveADCOffsets(client, adcOffsets, channelIndex, 8);
	if (!retVal) return retVal; // Error while retrieving adc offsets
	
	if (m_Bits < 14)
	{
		for (int i = 0; i < 8; i++)
		{
			adcOffsets[i] = adcOffsets[i] >> (14 - m_Bits);
		}
	}
	// Pack normalized adc offsets, according to the channel mask.
	FillMap();
	for (int i = 0; i < 8; i++)
	{
		m_ChannelOffsets[i] = adcOffsets[i];
	}

	return retVal;
}


void CDataEvaluation::DoTrigger()
{
	if (m_TriggerManager && (m_StopAt == 0))
	{
		ULONGLONG l = GetSampleCount();
//		printf("Trigger %d\n", (int)l);
		m_TriggerManager->Trigger(l);
	}
}


/* CTriggerManager */

CTriggerManager::CTriggerManager() :
	m_DataEvaluators(),
	m_Delay(0)
{
}


CTriggerManager::~CTriggerManager()
{
}


void CTriggerManager::Add(CDataEvaluation* dataEvaluator)
{
	lock();
	dataEvaluator->m_TriggerManager = this;
	m_DataEvaluators.push_front(dataEvaluator);
	unlock();
}


void CTriggerManager::Remove(CDataEvaluation* dataEvaluator)
{
	lock();
	dataEvaluator->m_TriggerManager = NULL;
	m_DataEvaluators.remove(dataEvaluator);
	unlock();
}


void CTriggerManager::RemoveAll()
{
	lock();

	for (std::list<CDataEvaluation*>::iterator itr = m_DataEvaluators.begin(); itr != m_DataEvaluators.end(); ++itr)
	{
		(*itr)->m_TriggerManager = NULL;
	}
	m_DataEvaluators.clear();

	unlock();
}


void CTriggerManager::Trigger(LONGLONG count)
{
	lock();

	for (std::list<CDataEvaluation*>::iterator itr = m_DataEvaluators.begin(); itr != m_DataEvaluators.end(); ++itr)
	{
		(*itr)->SetStopAt(count + m_Delay);
	}

	unlock();
}


CLnxTriggerManager::CLnxTriggerManager()
{
}


CLnxTriggerManager::~CLnxTriggerManager()
{
}


void CLnxTriggerManager::lock()
{
}


void CLnxTriggerManager::unlock()
{
}
