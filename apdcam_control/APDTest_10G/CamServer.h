#pragma once
#ifndef __CAMSERVER_H__

#define __CAMSERVER_H__

#include <net/if.h>

#include "InterfaceDefs.h"
#include "UDPServer.h"

class CCamServer : public CUDPServer
{
public:
	CCamServer() :
		m_type(0),
		m_PacketSize(0),
		m_RequestedData(0),
		m_SignalEvent(NULL),
		m_pBuffer(NULL),
		m_Length(0),
		m_DataReceived(0),
		m_UserData(0),
		m_MaxPacketNo(0),
		m_PacketCounter(0),
		m_SignalFrequency(1),
		m_DumpFile(NULL),
		m_StreamSerial(0),
		m_MulticastAddr(0),
		m_Interfacename()
	{
	};

	~CCamServer()
	{
		if (m_DumpFile)
			fclose(m_DumpFile);
	};

	void SetBuffer(uint8_t *buffer, uint64_t length)
	{
		m_pBuffer = buffer;
		m_Length = length;
		m_MaxPacketNo = (m_PacketSize > 0) ? (unsigned int)(m_Length / m_PacketSize): 0;
	};

	void SetPacketSize(int packetSize)
	{
		m_PacketSize = packetSize;
		m_MaxPacketNo = (m_PacketSize > 0) ? (unsigned int)(m_Length / m_PacketSize): 0;
	};

	void SetStreamSerial(uint32_t serial)
	{
		m_StreamSerial = serial;
	};

	void SetNotification(uint64_t requestedData, CEvent *hEvent)
	{
		m_RequestedData = requestedData;
		m_SignalEvent = hEvent;
	};

	void SetSignalFrequency(unsigned int frequency)
	{
		if (frequency > 0)
		{
			m_SignalFrequency = std::min(frequency, m_MaxPacketNo / 2);
		}
	};

	void Reset()
	{
		m_DataReceived = 0;
		m_UserData = 0;
		m_PacketCounter = 0;
	};

	void SetType(int type)
	{
		m_type = type;
	};

	void SetDumpFile(FILE *_d)
	{
		if (m_DumpFile)
			fclose(m_DumpFile);
		m_DumpFile = _d;
	};

	void SetInterfacename(const char *ifname)
	{
		strncpy(m_Interfacename, ifname, IFNAMSIZ);
		m_Interfacename[IFNAMSIZ] = '\0';
	}

	uint64_t GetReceivedData() { return m_DataReceived; };
	uint64_t GetMaxPacketNo() { return m_MaxPacketNo; };
	uint64_t GetPacketNo() { return m_PacketCounter; };

private:
	CCamServer(const CCamServer&);
	CCamServer& operator=(const CCamServer&);

	void OnRead();
	int GetRcvBufferSize() const;
	uint32_t GetMulticastAddr() const;
	const char* GetInterfacename() const;
	void OnStop();

	int m_type; // 0_ one-shot, 1:cyclic
	int m_PacketSize;
	uint64_t m_RequestedData;
	CEvent *m_SignalEvent;

	unsigned char *m_pBuffer; 
	uint64_t m_Length;
	uint64_t m_DataReceived;
	uint64_t m_UserData;
	unsigned int m_MaxPacketNo;  // The size of buffer measured in packets.
	unsigned int m_PacketCounter;
	unsigned int m_SignalFrequency; // In Cyclic mode the event is signaled when m_PacketCounter % m_SignalFrequency == 0;

	FILE* m_DumpFile;
	uint32_t m_StreamSerial;
	uint32_t m_MulticastAddr;
	char     m_Interfacename[IFNAMSIZ + 1];
};

#endif  /* __CAMSERVER_H__ */
