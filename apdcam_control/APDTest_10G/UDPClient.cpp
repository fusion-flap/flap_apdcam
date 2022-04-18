#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/ip.h>

#include "UDPClient.h"
#include "LnxClasses.h"



CUDPClient::CUDPClient(void) :
	m_ItemList(),
	m_SendSignal(new CLnxEvent()),
	m_csSend(),
	m_ulIPAddress_n(inet_addr("127.0.0.1")),
	m_usPort_n(htons(23)),
	m_bBindClient(false),
	m_usClientPort_n(9999),
	m_Timeout(5000)
{
}


CUDPClient::~CUDPClient(void)
{
	Stop();
	delete m_SendSignal;
}


bool CUDPClient::SetIPAddress(char *ipAddress)
{
	UINT32 ulIPAddress_n = inet_addr(ipAddress);
	if (ulIPAddress_n != INADDR_NONE)
	{
		m_ulIPAddress_n = ulIPAddress_n;
	}
	return (ulIPAddress_n != INADDR_NONE);
}


bool CUDPClient::SetIPAddress(UINT32 ipAddress_h)
{
	m_ulIPAddress_n = htonl(ipAddress_h);
	return true;
}


void CUDPClient::SetPort(UINT16 port_h)
{
	m_usPort_n = htons(port_h);
}


void CUDPClient::SetTimeout(int timeout)
{
	m_Timeout = timeout;
}


void CUDPClient::BindClient(UINT16 client_port_h)
{
	m_bBindClient = true;
	m_usClientPort_n = client_port_h;

}


bool CUDPClient::SendData(unsigned char* buffer, int length, UINT32 ipAddress_h, UINT16 ipPort_h, void *userData)
{
	bool retVal = false;

	MutexGuard lock(m_csSend);

	unsigned char *ptr = (unsigned char*)malloc(length);
	memcpy_s(ptr, length, buffer, length);

	DATADESCRIPTOR ds(ptr, length, htonl(ipAddress_h), htons(ipPort_h), userData);
	m_ItemList.push_front(ds);
	m_SendSignal->Set();
	retVal = true;

	return retVal;
}


unsigned int CUDPClient::Handler(void)
{
//fprintf(stderr, "UDPClient::Handler is running\n");
	try
	{
		if (CreateSocket() == false)
		{
			return 0;
		}

		socketRAII sockraii(m_Socket);

		int recvto = GetRecvTO();
		struct timeval tv = {recvto / 1000, (recvto % 1000) * 1000};
		if (setsockopt(m_Socket, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) != 0)
		{
			m_ErrorCode = errno;
			fprintf(stderr, "Cannot set SO_RCVTIMEO: %s\n", strerror(m_ErrorCode));
			return 0;
		}

		int yes = true;
		setsockopt(m_Socket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

		if (m_bBindClient)
		{
			sockaddr_in sckdrTCPAddr;
			sckdrTCPAddr.sin_family = AF_INET;
			sckdrTCPAddr.sin_port = m_usClientPort_n;
			sckdrTCPAddr.sin_addr.s_addr = htonl(INADDR_ANY); // inet_addr("127.0.0.1");

			// Binds listening socket to the address and port.
			if (bind(m_Socket, (const sockaddr*)&sckdrTCPAddr, sizeof(sckdrTCPAddr)) != 0)
			{
				m_ErrorCode = errno;
				fprintf(stderr, "Cannot bind to INADDR_ANY:%d : %s", m_usClientPort_n, strerror(m_ErrorCode));
				return 0;
			}
		}

		CLnxWaitForEvents waitObjects;
		CLnxEvent networkEvent(m_Socket);

		waitObjects.Add(m_SendSignal);
		waitObjects.Add(&networkEvent);
		waitObjects.Add(m_ExitSignal);

		m_ErrorCode = 0;
		InitDone();

		bool quit = false;
		while (!quit)
		{
			int index = -1;
			if (waitObjects.WaitAny(-1, &index) != CWaitForEvents::WR_OK)
			{
				fprintf(stderr, "WaitAny is not WR_OK!\n");
			}

			switch (index)
			{
			case -1:
fprintf(stderr, "WaitAny() returned W/O any of the objects posted!\n");
				break;
			case 0:
				{
					InternalSend();
					m_SendSignal->Reset();
				}
				break;
			case 1:
				{
					OnNetworkEvent(m_Socket);
				}
				break;
			case 2:
				quit = true;
				break;
			default:
fprintf(stderr, "Unhandled event: %d\n", index);
				break;
			}
		}
	}
	catch (...)
	{
	}

	return 0;
}


void CUDPClient::InternalSend()
{
	if (m_ItemList.empty()) return;

	int length;
	unsigned char *buffer;
	UINT32 ipAddress_n;
	UINT16 ipPort_n;
	void *userData;

	{
		MutexGuard lock(m_csSend);

		const DATADESCRIPTOR &ds = m_ItemList.back();
		length = ds.length;
		buffer = ds.buffer;
		ipAddress_n = ds.ipAddress_n;
		ipPort_n = ds.ipPort_n;
		userData = ds.userData;
		m_ItemList.pop_back();
	}

	m_ErrorCode = 0;
	// Set up the sckdrAddr structure with the IP address of
	// the receiver and the specified port number.
	sockaddr_in sockdrAddr;
	sockdrAddr.sin_family = AF_INET;
	sockdrAddr.sin_port = ipPort_n == 0 ? m_usPort_n : ipPort_n;
	sockdrAddr.sin_addr.s_addr = ipAddress_n == 0 ? m_ulIPAddress_n : ipAddress_n;

	OnBeforeSend(m_Socket, buffer, length, sockdrAddr, userData);

	int have_to_send = length;
	unsigned char *send_buffer = buffer;
	do
	{
		int res = sendto(m_Socket, (char*)send_buffer, have_to_send, 0, (const sockaddr*) &sockdrAddr, sizeof(sockdrAddr));
		if (res == -1 || res == 0)
		{
			m_ErrorCode = errno;
			fprintf(stderr, "Cannot sendto %s:%d : %s\n", inet_ntoa(sockdrAddr.sin_addr), ntohs(sockdrAddr.sin_port), strerror(m_ErrorCode));
			break;
		}
		else
		{
			send_buffer += res;
			have_to_send -= res;
		}
	} while (have_to_send);

	OnAfterSend(m_Socket, buffer, length, userData);

	free(buffer);
}
