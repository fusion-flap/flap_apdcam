#include <stdio.h>
#include <unistd.h>
#include <netinet/in.h>
#include <sys/ioctl.h>
#include <sys/socket.h>

#include "UDPServer.h"
#include "LnxClasses.h"


CUDPServer::CUDPServer(void) : UDPBase(), Thread(),
	m_port_n(0)
{
}


CUDPServer::~CUDPServer(void)
{
	Stop();
}


unsigned int CUDPServer::Handler(void)
{
	sockaddr_in sockAddr;

	try
	{
		if (CreateSocket() == false)
		{
			return -1;
		}

		socketRAII sockraii(m_Socket);

		int rcvBufferSize = GetRcvBufferSize();
		if (rcvBufferSize != 0)
		{
			socklen_t size = sizeof(rcvBufferSize);
			int actualRcvBufferSize = 0;
			if (getsockopt(m_Socket, SOL_SOCKET, SO_RCVBUF, &actualRcvBufferSize, &size) == 0)
			{
				/*
				 * The Linux kernel doubles the RCVBUFSIZE value to allow space for bookkeeping overhead and
				 * returns this doubled value.
				 */
				actualRcvBufferSize /= 2;
			}
			else
				fprintf(stderr, "Cannot getsockopt(): %s\n", strerror(errno));

			if (actualRcvBufferSize < rcvBufferSize)
			{
fprintf(stderr, "(%u) SO_RCVBUF is %d should be %d\n", size, actualRcvBufferSize, rcvBufferSize);
				fprintf(stderr, "Setting SO_RCVBUF to %d\n", rcvBufferSize);
				if (setsockopt(m_Socket,  SOL_SOCKET, SO_RCVBUFFORCE, &rcvBufferSize, size))
				{
fprintf(stderr, "Cannot set SO_RCVBUFFORCE: %s\n", strerror(errno));
					if (setsockopt(m_Socket,  SOL_SOCKET, SO_RCVBUF, &rcvBufferSize, size))
					{
						m_ErrorCode = errno;
						fprintf(stderr, "Cannot set SO_RCVBUF: %s\n", strerror(m_ErrorCode));
						return -1;
					}
				}
				actualRcvBufferSize = 0;
				size = sizeof(actualRcvBufferSize);
				getsockopt(m_Socket, SOL_SOCKET, SO_RCVBUF, &actualRcvBufferSize, &size);
				actualRcvBufferSize /= 2;
				if (actualRcvBufferSize < rcvBufferSize)
				{
					m_ErrorCode = EPERM;
					fprintf(stderr, "\nCannot set Receiver Buffer Size to %d bytes!\nPossible workarounds:\n - Run as root\n - Increase /proc/sys/net/core/rmem_max\n\n", rcvBufferSize);
					return -1;
				}
			}
		}

		sockAddr.sin_family = AF_INET;
		sockAddr.sin_port = m_port_n;
		sockAddr.sin_addr.s_addr = htonl(INADDR_ANY);

		// Binds listening socket to the addres and port.
		if (bind(m_Socket, reinterpret_cast<const sockaddr*>(&sockAddr), sizeof(sockAddr)))
		{
			m_ErrorCode = errno;
			fprintf(stderr, "Cannot bind to INADDR_ANY:%d : %s", m_port_n, strerror(m_ErrorCode));
			return -1;
		}

		int ifindex = 0;
		if (GetInterfacename()[0] != '\0')
		{
			struct ifreq ifr;
			const char *ifname = GetInterfacename();

			strncpy(ifr.ifr_name, ifname, IFNAMSIZ);
			if (ioctl(m_Socket, SIOCGIFINDEX, &ifr))
				fprintf(stderr, "Cannot get ifindex: %s\n", strerror(errno));
			else
				ifindex = ifr.ifr_ifindex;

#if 0
			if (setsockopt(m_Socket, SOL_SOCKET, SO_BINDTODEVICE, ifname, strlen(ifname)) < 0)
				fprintf(stderr, "Cannot bind to device %s: %s\n", ifname, strerror(errno));
#endif
		}

#ifndef NEVER
		if (GetMulticastAddr())
		{
			struct ip_mreqn mult;
			mult.imr_multiaddr.s_addr = GetMulticastAddr();
			mult.imr_address.s_addr = INADDR_ANY;
			mult.imr_address.s_addr = inet_addr("10.123.13.200");
			mult.imr_ifindex = ifindex;
			if (setsockopt(m_Socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mult, sizeof(mult)) < 0)
			{
				m_ErrorCode = errno;
				fprintf(stderr, "Socket multicast-group setting error %s.\n", strerror(errno));
				return -1;
			}
		}
#endif
		CLnxEvent networkEvent(m_Socket);

		CLnxWaitForEvents waitObjects;
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
				case 0:
					// Read data
					OnRead ();

					break;
				case 1:
					// Close request
					quit = true;
					m_ExitSignal->Reset();

					break;
				default:
					break;
			}
		}
	}
	catch (...)
	{
	}

	return 0;
}


int CUDPServer::ReadData(unsigned char *buffer, int length, sockaddr *from, socklen_t *fromlen)
{
	int bytes_received = recvfrom(m_Socket, buffer, length, 0, (struct sockaddr *)from, fromlen);
	if (bytes_received == -1)
	{
		m_ErrorCode = errno;
		fprintf(stderr, "!!!---recvfrom() %s\n", strerror(errno));
	}

	return bytes_received;
}
