#pragma once
#ifndef __UDPSERVER_H__

#define __UDPSERVER_H__

#include "InterfaceDefs.h"
#include "SysLnxClasses.h"

class CUDPServer : public UDPBase, public Thread
{
public:
	CUDPServer(void);
	virtual ~CUDPServer(void);
	void SetListeningPort(int port_h) { m_port_n = htons(port_h); };

private:
	unsigned int Handler(void);
	int m_port_n;

protected:
	int ReadData(unsigned char *buffer, int length, sockaddr *from, socklen_t *fromlen);
	virtual void OnRead() = 0;
	virtual int GetRcvBufferSize() const = 0;
	virtual uint32_t GetMulticastAddr() const = 0;
	virtual const char* GetInterfacename() const = 0;
};

#endif  /* __UDPSERVER_H__ */
