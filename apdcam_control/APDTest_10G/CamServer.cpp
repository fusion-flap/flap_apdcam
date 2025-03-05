#include <stdio.h>
#include "CamServer.h"


void CCamServer::OnRead()
{
	unsigned char *pBuffer = m_pBuffer + ((m_PacketCounter % m_MaxPacketNo) * m_PacketSize);

	int bytes_received = ReadData(pBuffer, m_PacketSize, NULL, NULL);

	if (bytes_received <= 0)
	{
		fprintf(stderr, "ERROR: %s\n", strerror(m_ErrorCode));
		return;
	}

	if (m_DumpFile)
		fwrite(pBuffer, 1, bytes_received, m_DumpFile);

	CC_STREAMHEADER *header = reinterpret_cast<CC_STREAMHEADER*>(pBuffer);
	if (header->serial != m_StreamSerial)
	{
		fprintf(stderr, "Header serial does not match: 0x%X, expected 0x%X\n", header->serial,m_StreamSerial);
		return;
	}
//	else
//	{
//		fprintf(stderr,"Header serial: 0x%X\n", header->serial);
//	}
	if (header->S1.UDP_Test_Mode)
	{
		++m_PacketCounter;
		return;
	}

	if (m_type == 0)
	{ // one-shot mode
		m_DataReceived += bytes_received;
		if (m_UserData < m_RequestedData)
		{
			++m_PacketCounter;
			m_UserData += bytes_received - sizeof(CC_STREAMHEADER);

			if (m_SignalEvent)
			{
				if (m_UserData >= m_RequestedData || (m_PacketCounter % m_SignalFrequency) == 0)
				{
					m_SignalEvent->Set();
				}
			}
		}
	}
	else
	{ // cyclic mode
		m_PacketCounter++;
		m_DataReceived += bytes_received;
		m_UserData  += bytes_received - sizeof(CC_STREAMHEADER);

		if (/*(m_PacketCounter > 0) && -- never zero here*/((m_PacketCounter % m_SignalFrequency) == 0) && (m_SignalEvent != NULL)) 
			m_SignalEvent->Set();
	}
}


int CCamServer::GetRcvBufferSize() const
{
	return 64 * 1024 * 1024;
}


uint32_t CCamServer::GetMulticastAddr() const
{
	return inet_addr("239.123.13.100");
}


const char* CCamServer::GetInterfacename() const
{
	return m_Interfacename;
}


void CCamServer::OnStop()
{
	if (m_DumpFile)
	{
		fclose(m_DumpFile);
		m_DumpFile = NULL;
	}

	if (m_SignalEvent)
		m_SignalEvent->Set();
}
