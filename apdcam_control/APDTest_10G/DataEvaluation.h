#ifndef __DATAEVALUATION_H__

#define __DATAEVALUATION_H__

#include <list>

#include "CamClient.h"
#include "TypeDefs.h"

#include "LnxClasses.h"
#include "SysLnxClasses.h"

#define MAX_PACKET_LOSS 50

void EvaluateData(unsigned char* pData, int length, int noofSample, UCHAR channelMask, int bits, int channelOffset);

#define CHANNEL_NUM    32
class CTriggerManager;

class CDataEvaluation : public Thread
{
	friend class CTriggerManager;

private:
	CDataEvaluation(const CDataEvaluation&);
	CDataEvaluation& operator=(const CDataEvaluation&);
protected:
	void ProcessData();
	void ProcessFrame(const CC_STREAMHEADER *header, const unsigned char *pFrame, unsigned int packetNo);
	void ProcessBlock(unsigned char *pData);
	void Trigger(int channel, INT16 data);
	void FillMap();

	CTriggerManager *m_TriggerManager;

public:
	CDataEvaluation();
	virtual ~CDataEvaluation();
	unsigned int Handler();

	inline ULONGLONG GetSampleCount()
	{
		return m_SampleCount;
	};

	inline ULONGLONG GetSampleIndex()
	{
		return m_SampleIndex;
	};

	inline void SetStopAt(ULONGLONG stopAt)
	{
		m_StopAt = stopAt;
	}

	bool SetParams(unsigned int bits, uint32_t channelMask, unsigned int packetSize);
	inline void SetBuffers(unsigned char* srcBuffer, unsigned char* workBuffer, unsigned char* userBuffer, uint64_t userBufferSize) 
	{
		m_SrcBuffer = srcBuffer;
		m_WorkBuffer = workBuffer;
		m_UserBuffer = userBuffer;
		m_UserBufferSize = userBufferSize;
	};

	inline void SetServer(CAPDServer *server)
	{
		m_Server = server;
	};

	void SetStreamSerial(uint32_t serial)
	{
		m_StreamSerial = serial;
	};

	inline void SetDataNotificationSignal(CEvent *dataNotification)
	{
		m_pDataNotificationSignal = dataNotification;
	};

	inline void SetUserNotificationSignal(CEvent *userNotification)
	{
		m_pUserNotificationSignal = userNotification;
	};

	void SetCalibratedMode(bool calibrated);
	inline void DisableTrigger()
	{
		m_Triggered = true;
	};

	void SetTrigger(ADT_TRIGGERINFO *triggerInfo);
	bool ContinuityError() const
	{
		return m_ContinuityError;
	}

	void SetDumpFile(FILE *d)
	{
		if (dumpFile)
			fclose(dumpFile);
		dumpFile = d;
	}

	void OnStop()
	{
		if (dumpFile)
		{
			fclose(dumpFile);
			dumpFile = NULL;
		}
	}

	// Trigger
protected:
	bool m_Triggered;
	ADT_TRIGGERINFO m_TriggerInfo[CHANNEL_NUM];
	int m_TriggerEnabled[CHANNEL_NUM];
	INT16 m_TriggerLevels[CHANNEL_NUM];

public:
	void DoTrigger();

	// The SetupCalibrationData must be called after the SetParams, becaues it uses the bits and channelmask.
	// The routin reads the appropiate calibration data from theADC board, normalizes them (according to bit number) and arrenges it, according to channel mask.
	// The streamNo is 1..4
	bool SetupCalibrationData(CAPDClient *client, int streamNo);
protected:
	CEvent *m_pDataNotificationSignal;
	CEvent *m_pUserNotificationSignal;
	unsigned int m_PacketNo;

public:
	const INT16* GetChannelData(uint8_t ch) const
	{
		if (ch > CHANNEL_NUM)
			return NULL;
		return m_ChannelData[ch];
	}

protected:
	INT16 *m_ChannelData[CHANNEL_NUM];
	int m_ChannelMap[CHANNEL_NUM];
	int m_ActiveChannelNo;

protected:
	CAPDServer *m_Server;
	unsigned char* m_SrcBuffer;
	unsigned int m_WritePtr;	// indicates the where have to write: (m_TempBuffer+m_WritePtr)
	int m_DataLength;			// The amount of data to be processed.
	bool m_Running;
	bool m_Calibrated;

	unsigned char* m_WorkBuffer;

	unsigned char *m_UserBuffer;	// points to the 0. channel
	uint64_t m_UserBufferSize;	// per channel

	unsigned int m_Bits;		// bit resolution. Values: 8,12,14
	uint32_t m_ChannelMask;
	unsigned int m_ADCPacketSize;
	unsigned int m_CCPacketSize;
	int m_BlockSize;			// Size of one sample.
	int m_PaddedBlockSize;			// Size of one sample padded to OCTET size
	UINT16 m_Mask;		// Used in data decoding. Its value can be 0x3FFF (14 bit), 0x0FFF (12 bit) or 0x00FF (8 bit)

	// The channel offset values in packed format. E.g. If 1st and 3rd channel are used, the m_ChannelOffsets[0] is for 1st, m_ChannelOffsets[1] is for 3rd.
	INT16 m_ChannelOffsets[CHANNEL_NUM]; 

	unsigned int m_MaxNoofBlocks;
	uint64_t     m_ExpectedPacketCounter;
	bool m_ContinuityError;
	ULONGLONG m_SampleCount;
	ULONGLONG m_SampleIndex;  // Index in the ring buffer, where the data must be placed.
	ULONGLONG m_UserBufferSizeInSample;
	ULONGLONG m_StopAt;

	unsigned int m_StreamNo;

	void InternalStop();

public:
	// Win specific
	LARGE_INTEGER m_ReferenceTime;
	LARGE_INTEGER m_ProcessingTime;
	int m_ProcessingCount;
	LARGE_INTEGER m_LastCallingTime;
	LARGE_INTEGER m_AvarageCallingTime;
	int m_CallingCount;
	FILE *dumpFile;
	uint32_t m_StreamSerial;
};

class CLnxDataEvaluation : public CDataEvaluation
{
};

class CTriggerManager
{
	std::list<CDataEvaluation*> m_DataEvaluators;
	ULONGLONG m_Delay;
public:
	CTriggerManager();
	virtual ~CTriggerManager();
	inline void SetDelay(ULONGLONG delay)
	{
		m_Delay = delay;
	};

	void Add(CDataEvaluation* dataEvaluator);
	void Remove(CDataEvaluation* dataEvaluator);
	void RemoveAll();
	void Trigger(LONGLONG count);
protected:
	virtual void lock() = 0;
	virtual void unlock() = 0;
};

class CLnxTriggerManager : public CTriggerManager
{
protected:

public:
	CLnxTriggerManager();
	~CLnxTriggerManager();

protected:
	virtual void lock();
	virtual void unlock();
};

#endif  /* __DATAEVALUATION_H__ */
