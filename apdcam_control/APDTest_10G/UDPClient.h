#pragma once
#ifndef __UDPCLIENT_H__

#define __UDPCLIENT_H__

#include <list>

#include "SysLnxClasses.h"

#include "InterfaceDefs.h"

struct DATADESCRIPTOR
{
	/*
	 * The ipAddress and ipPort are in network byte order.
	 */
	DATADESCRIPTOR() : ipAddress_n(0), ipPort_n(0), buffer(NULL), length(0), userData(0) {};
	DATADESCRIPTOR(unsigned char *_buffer, int _length, UINT32 _ipAddress_n = 0, UINT16 _ipPort_n = 0, void *_userData = 0) :ipAddress_n(_ipAddress_n), ipPort_n(_ipPort_n), buffer(_buffer) , length(_length), userData(_userData) {};
	UINT32 ipAddress_n;
	UINT16 ipPort_n;
	unsigned char *buffer;
	int length;
	void *userData;
};

typedef std::list<DATADESCRIPTOR> ITEMLIST;

class CUDPClient : public UDPBase, public Thread
{
public:
	CUDPClient(void);
	~CUDPClient(void);

	// The ipAddress and ipPort must be in host byte order. The methode convert them using the
	// htonl() (host to network long) or htons() (host to network short) respectively.
	bool SetIPAddress(char *ipAddress);
	bool SetIPAddress(UINT32 ipAddress_h);
	void SetPort(UINT16 port_h);
	void SetTimeout(int timeout);
	void BindClient(UINT16 client_port_h); 
	bool SendData(unsigned char* buffer, int length, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0, void *userData = 0);

private:
	CUDPClient(const CUDPClient&);
	CUDPClient& operator=(const CUDPClient&);

	unsigned int Handler(void);
	virtual int GetRecvTO() { return m_Timeout;};

	void InternalSend();

	virtual void OnBeforeSend(int clientSocket, unsigned char *buffer, int length, sockaddr_in &sckadddr, void *userData) = 0;
	virtual void OnAfterSend(int clientSocket, unsigned char *buffer, int length, void *userData) = 0;
	virtual void OnNetworkEvent(int & /*clientSocket*/) = 0;

	ITEMLIST  m_ItemList;
	CEvent   *m_SendSignal;
	Mutex     m_csSend;
	/* The m_ulIPAddress and m_usPort store address and port number in network byte order (big-endian) */
	UINT32    m_ulIPAddress_n;
	UINT16    m_usPort_n;
	bool      m_bBindClient;	// if true, binds the client to the fix m_usClientPort_n port
	UINT16    m_usClientPort_n;
	int       m_Timeout;
};

#endif  /* __UDPCLIENT_H__ */
