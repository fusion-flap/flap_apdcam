#pragma once
#ifndef __INTERFACEDEFS_H__

#define __INTERFACEDEFS_H__

/*
 This file defines the interfaces for class factory, clients and servers.

 The following interfaces are used:

 CAPDFactory: The base abstract class of CWinAPDFactory (used in Windows) and CLnxAPDFactory (used in Linux)

 The CAPDFactory creates the following objects:

 a descendent of CAPDClient (CWinAPDClient or CLnxAPDClient), and a descendent of CAPDSerever (CWinAPDServer or CLnxAPDServer).

*/

#include "TypeDefs.h"
#include "GECCommands.h"

#include <list>

class CEvent
{
public:
	virtual ~CEvent() {};
	virtual void Set() = 0;
	virtual void Reset() = 0;
	virtual bool IsSignaled() = 0;
	virtual bool Wait(int timeout = -1) = 0;
	// GetError returns 0 if the creation or the operation was succesfull. In the case of error, the return value is operating system dependent.
	virtual int GetError() = 0;
protected:
	CEvent() {};
private:
	CEvent(const CEvent&);
	CEvent& operator=(const CEvent&);
};

typedef std::list<CEvent*> EVENTLIST;

class CWaitForEvents
{
private:
	CWaitForEvents(const CWaitForEvents&);
	CWaitForEvents& operator=(const CWaitForEvents&);
protected:
	CWaitForEvents() : m_Events() {};
	EVENTLIST m_Events;
public:
	enum WAIT_RESULT { WR_OK, WR_TOO_MANY_OBJECTS, WR_TIMEOUT, WR_ERROR };
	virtual ~CWaitForEvents() {};
	// GetMaxWaitObjects() returns the maximum number of objects to wait for.
	virtual size_t GetMaxWaitObjects() = 0;
	// Adds a new wait object to the waiting list. If the event is in the list, does nothing.
	// Return value: WAIT_OK: succes, WAIT_TO_MANY_OBJECTS: to many wait objects.
	virtual WAIT_RESULT Add(CEvent *event) = 0;
	virtual void Remove(CEvent *event) = 0;
	virtual void RemoveAll() = 0;
	// if timeout = -1 wait infinite. Else wait timeout milisecs,
	// Return value: WAIT_OK: succes, WAIT_TIMEOUT: timeout, WAIT_ERROR: any other error. 
	virtual WAIT_RESULT WaitAll(int timeout) = 0;
	virtual WAIT_RESULT WaitAny(int *index) = 0;
	virtual WAIT_RESULT WaitAny(int timeout, int *index) = 0;
	// GetError returns 0 if the creation or the operation was succesfull. In the case of error, the return value is operating system dependent.
	virtual int GetError() = 0;
};

// The CClientContext must not create directly, only with the class factory, because its derivatives could contain additional information.
class CClientContext
{
private:
	CClientContext(const CClientContext&);
	CClientContext& operator=(const CClientContext&);
protected:
	CClientContext() : pEvent(NULL), pBuffer(NULL), bufferLength(0) {};
public:
	virtual ~CClientContext() {};
	CEvent *pEvent;				// The CAPDServer or CAPDClient can signal the caller about the arriving requested data.
	unsigned char *pBuffer;		// User buffer to collect arriving data. Allocated by the caller.
	unsigned int bufferLength;	// Length of buffer pointed by pBuffer.
};

class CAPDClient
{
public:
	virtual ~CAPDClient() {};
	virtual void SetIPAddress(UINT32 ipAddress_h) = 0;
	virtual void SetIPAddress(char *ipAddress) = 0;
	virtual void SetUDPPort(UINT16 port_h) = 0;
	virtual void SetTimeout(int timeout) = 0;
	virtual void Start() = 0;
	virtual void Stop() = 0;
	virtual bool SendData(GECCOMMAND* command, CClientContext *clientContext = 0, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0) = 0;
	virtual bool SendData(BULKCMD* commands, CClientContext *clientContext = 0, UINT32 ipAddress_h = 0, UINT16 ipPort_h = 0) = 0;
};

class CAPDServer
{
public:
	enum SERVER_TYPE { ST_ONE_SHOT, ST_CYCLIC };
	virtual ~CAPDServer() {};
	virtual void SetListeningPort(UINT16 port_h) = 0;
	virtual void SetBuffer(unsigned char *buffer, ULONGLONG size) = 0;
	virtual void SetPacketSize(unsigned int packetsize) = 0;
	virtual void SetStreamSerial(uint32_t serial) = 0;
	virtual void SetStreamInterface(const char *ifname) = 0;
	virtual void SetNotification(unsigned int requested_data, CEvent *event) = 0;
	virtual void SetSignalFrequency(unsigned int frequency) = 0;
	virtual void Reset() = 0;
	virtual bool Start() = 0;
	virtual void Stop() = 0;
	virtual void SetType(SERVER_TYPE type) = 0;
	virtual void SetDumpFile(FILE *dumpFile) = 0;
	virtual unsigned int GetReceivedData() = 0; // Returns the number of byte received, including the CW_FRAME
	virtual unsigned int GetMaxPacketNo() = 0; // Returns the...
	virtual unsigned int GetPacketNo() = 0; // Returns the...
};

/* Interface definition for non-paged memory allocator. */

class CNPMemoryException
{
public:
	CNPMemoryException() {};
};

class CNPMAllocator
{
protected:
	CNPMAllocator(ULONGLONG /*requestedSize*/) throw(CNPMemoryException) {};
public:
	virtual ~CNPMAllocator() {};
	virtual unsigned char *GetBuffer() = 0;
	virtual unsigned int GetBufferSize() = 0;
};

class CAPDFactory
{
	static CAPDFactory *g_pFactory;
public:
	inline static CAPDFactory* GetAPDFactory() { return g_pFactory; };
	inline static void SetAPDFactory(CAPDFactory *factory) { g_pFactory = factory; };

	virtual ~CAPDFactory() {};
	virtual CAPDServer* GetServer() = 0;
	virtual CAPDClient* GetClient() = 0;
	virtual CEvent* GetEvent() = 0;
	virtual CWaitForEvents* GetWaitForEvents() = 0;
	virtual CClientContext* GetClientContext() = 0;
	virtual CNPMAllocator* GetNPMemory(ULONGLONG requestedSize) = 0;
};


#endif  /* __INTERFACEDEFS_H__ */
