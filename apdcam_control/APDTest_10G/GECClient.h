#pragma once
#ifndef __GECCLIENT_H__

#define __GECCLIENT_H__

#include "UDPClient.h"
#include "GECCommands.h"
#include "InterfaceDefs.h"

struct CLIENTCONTEXT
{
	CEvent *hEvent;
	unsigned int bufferLength;
	unsigned int dataLength;
	unsigned char *pBuffer;
};

class CGECClient : public CUDPClient
{
public:
	CGECClient():m_userData(0) {};
	virtual ~CGECClient() {};

private:
	CGECClient(const CGECClient&);
	CGECClient& operator=(const CGECClient&);

// Overrides:
private:
	virtual void OnNetworkEvent(int &clientSocket);
	virtual void OnBeforeSend(int clientSocket, unsigned char *buffer, int length, sockaddr_in &sockAddr, void *userData);
	virtual void OnAfterSend(int clientSocket, unsigned char *buffer, int length, void *userData);

// New:	
private:
	virtual void OnDataArrived(unsigned char *buffer, int length, void *userData);
	virtual void OnAck(unsigned char * /*buffer*/, int /*length*/, void* /*userData*/) {};
	virtual void OnFlashData(unsigned char * /*buffer*/, int /*length*/, void* /*userData*/) {};
	virtual void OnPdiData(unsigned char * /*buffer*/, int /*length*/, void* /*userData*/) {};
	virtual void OnError(unsigned char * /*buffer*/, int /*length*/, void* /*userData*/) {};

	void *m_userData;

protected:
	virtual void OnSocketClosed(void *userData);
	virtual void OnReceiveError(void *userData);

};

#endif  /* __GECCLIENT_H__ */
