#ifndef __LNXCLASSES_H__

#define __LNXCLASSES_H__

#include <poll.h>

#include "InterfaceDefs.h"
#include "GECClient.h"
#include "CamServer.h"

class CCamClient;
#define MAXIMUM_WAIT_OBJECTS	64

class CLnxEvent : public CEvent
{
	class CLnxEventPrivate;
	friend class CLnxFactory;
	friend class CLnxWaitForEvents;
	friend class CLnxClient;
	friend class CLnxServer;
	friend class CLnxClientContext;
private:
	int readFd() const { return pipefd[0]; }

	int pipefd[2];
	int m_LastSetterErrorCode;
	int m_LastWaiterErrorCode;
public:
	CLnxEvent(int fd);
	CLnxEvent();
	~CLnxEvent();
	void Set();
	void Reset();
	bool IsSignaled();
	bool Wait(int timeout);
	int GetError() { return m_LastSetterErrorCode ? m_LastSetterErrorCode : m_LastWaiterErrorCode; };
	int GetSetterError() { return m_LastSetterErrorCode; };
	int GetWaiterError() { return m_LastWaiterErrorCode; };
};

class CLnxWaitForEvents : public CWaitForEvents
{
	friend class CLnxFactory;
private:
	struct pollfd m_pfds[MAXIMUM_WAIT_OBJECTS];
	int           m_nfds;
	unsigned int  m_LastErrorCode;

	void createPollFd();
	WAIT_RESULT WaitAny(int size, struct timeval *begin, int *timeout, bool update_timeout, int *index);
public:
	CLnxWaitForEvents() : m_pfds(), m_nfds(0), m_LastErrorCode(0) {};
	size_t GetMaxWaitObjects();
	WAIT_RESULT Add(CEvent *event);
	void Remove(CEvent *event);
	void RemoveAll();
	WAIT_RESULT WaitAll(int timeout);
	WAIT_RESULT WaitAny(int timeout, int *index);
	WAIT_RESULT WaitAny(int *index);
	int GetError() { return m_LastErrorCode; }
};

class CLnxClientContext : public CClientContext
{
	friend class CLnxFactory;
	friend class CLnxClient;
private:
	CLnxClientContext();
	CLIENTCONTEXT m_ClientContext;
public:
	void CreateCLIENTCONTEXT();
	~CLnxClientContext();
};

class CLnxClient : public CAPDClient
{
	friend class CLnxFactory;
private:
	CLnxClient();
	CLnxClient(const CLnxClient&);
	CLnxClient& operator=(const CLnxClient&);

	CCamClient *m_pClient;
	UINT32 m_IPAdress_h;
	UINT16 m_Port_h;
	int    m_Timeout;
public:
	~CLnxClient();
	void SetUDPPort(UINT16 port_h);
	void SetIPAddress(UINT32 ipAddress_h);
	void SetIPAddress(char *ipAddress);
	void SetTimeout(int timeout);
	void Start();
	void Stop();
	bool SendData(GECCOMMAND* command, CClientContext *clientContext = 0, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0);
	bool SendData(BULKCMD* commands, CClientContext *clientContext = 0, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0);
};

class CLnxServer : public CAPDServer
{
	friend class CLnxFactory;
private:
	CLnxServer();
	CLnxServer(const CLnxServer&);
	CLnxServer& operator=(const CLnxServer&);
	CCamServer *m_pServer;
public:
	~CLnxServer();
	void SetListeningPort(UINT16 port_h);
	void SetBuffer(unsigned char *buffer, ULONGLONG size);
	void SetPacketSize(unsigned int packetsize);
	void SetStreamSerial(uint32_t serial);
	void SetStreamInterface(const char *ifname);
	void SetNotification(unsigned int requested_data, CEvent *event);
	void SetSignalFrequency(unsigned int frequency);
	void Reset();
	bool Start();
	void Stop();
	void SetType(SERVER_TYPE type);
	void SetDumpFile(FILE *dumpFile);
	unsigned int GetReceivedData();
	unsigned int GetMaxPacketNo();
	unsigned int GetPacketNo();
};

class CLnxNPMAllocator : public CNPMAllocator
{
	friend class CLnxFactory;
private:
	CLnxNPMAllocator(ULONGLONG requestedSize) throw(CNPMemoryException);

	class CMemDesc
	{
	private:
		CMemDesc(const CMemDesc&);
		CMemDesc& operator=(const CMemDesc&);
	public:
		CMemDesc() : NumberOfPages(0),
				lpMemReserved(NULL)
				{}; 
		~CMemDesc();
		ULONGLONG NumberOfPages;	// number of pages to request
		void *lpMemReserved;
	};

	CMemDesc m_MemDesc;
	ULONGLONG m_BufferSize;

	static void ErrorLog(char *message);

	static ULONGLONG m_LockedSoFar;

public:
	unsigned char *GetBuffer() { return (unsigned char*)m_MemDesc.lpMemReserved; };
	unsigned int GetBufferSize() { return (unsigned int)m_BufferSize;};
};

class CLnxFactory : public  CAPDFactory
{
public:
	CAPDServer* GetServer();
	CAPDClient* GetClient();
	CEvent* GetEvent();
	CWaitForEvents* GetWaitForEvents();
	CClientContext* GetClientContext();
	CNPMAllocator* GetNPMemory(ULONGLONG requestedSize);
};

#endif  /* __LNXCLASSES_H__ */
