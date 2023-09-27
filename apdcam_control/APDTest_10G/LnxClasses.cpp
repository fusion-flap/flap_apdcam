#include <list>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/capability.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <iostream>
using namespace std;

#include "LnxClasses.h"
#include "CamClient.h"

/* ******************* CLnxEvent ******************* */

typedef std::list<CEvent*> EVENTLIST;

static void millisec_to_timeval(int msec, struct timeval *tval)
{
	tval->tv_sec = msec / 1000;
	tval->tv_usec = (msec % 1000) * 1000;
}


static int timeval_to_millisec(struct timeval *tv)
{
	return tv->tv_sec * 1000 + tv->tv_usec / 1000;
}


CLnxEvent::CLnxEvent() :
	m_LastSetterErrorCode(0),
	m_LastWaiterErrorCode(0)
{
	if (pipe(pipefd))
		m_LastSetterErrorCode = m_LastWaiterErrorCode = errno;
	else
	{
		fcntl(pipefd[0], F_SETFD, FD_CLOEXEC);
		fcntl(pipefd[1], F_SETFD, FD_CLOEXEC);

		fcntl(pipefd[0], F_SETFL, O_NONBLOCK);
		fcntl(pipefd[1], F_SETFL, O_NONBLOCK);
	}
}

CLnxEvent::CLnxEvent(int fd) :
	m_LastSetterErrorCode(0),
	m_LastWaiterErrorCode(0)
{
	pipefd[0] = fd;
	pipefd[1] = -1;
}

CLnxEvent::~CLnxEvent()
{
	if (pipefd[1] != -1)
	{
		close(pipefd[0]);
		close(pipefd[1]);
	}
}

void CLnxEvent::Set() 
{
	uint8_t set = 0xFF;

	m_LastSetterErrorCode = 0;
	while (write(pipefd[1], &set, sizeof(set)) < 0)
	{
		m_LastSetterErrorCode = errno;
		if (errno != EINTR)
		{
			fprintf(stderr, "Cannot set event: %s\n", strerror(m_LastSetterErrorCode));
			break;
		}
	}
}

void CLnxEvent::Reset() 
{
	/*
	 * NEVER reset an event bound to a real network socket
	 */
	if (pipefd[1] == -1)
		return;

	m_LastWaiterErrorCode = 0;
	if (IsSignaled() == false)
		return;

	uint8_t reset;
	errno = 0;
	m_LastWaiterErrorCode = 0;
	while (read(pipefd[0], &reset, sizeof(reset)) < 1)
	{
		m_LastWaiterErrorCode = errno;
		if (errno != EINTR)
		{
			fprintf(stderr, "Cannot reset event: %s\n", strerror(m_LastWaiterErrorCode));
			break;
		}
		errno = 0;
	}
}

bool CLnxEvent::IsSignaled()
{
	return Wait(0);
}

bool CLnxEvent::Wait(int timeout)
{
	struct pollfd pfd;
	struct timeval begin;

	pfd.fd = pipefd[0];
	pfd.events = POLLIN;
	pfd.revents = 0;

	if (timeout > 0)
		gettimeofday(&begin, NULL);

	do
	{
            int p = poll(&pfd, 1, timeout);
            if (p == 0)
                return false;
            else if (p == 1)
                return true;
            
            m_LastWaiterErrorCode = errno;
            if (m_LastWaiterErrorCode != EINTR)
                break;
            
            if (timeout > 0)
            {
                struct timeval now;
                gettimeofday(&now, NULL);
                timeout -= timeval_to_millisec(&now) - timeval_to_millisec(&begin);
                if (timeout <= 0)
                    return false;
            }
	} while (true);

        fprintf(stderr, "CLnxEvent::Wait() : %s\n", strerror(m_LastWaiterErrorCode));
	return false;
}



/* ******************* CLnxWaitForEvents ******************* */

size_t CLnxWaitForEvents::GetMaxWaitObjects()
{
	return MAXIMUM_WAIT_OBJECTS;
}


CWaitForEvents::WAIT_RESULT CLnxWaitForEvents::Add(CEvent *event) 
{
	if (m_Events.size() >= GetMaxWaitObjects())
	{
		return WR_TOO_MANY_OBJECTS;
	}

	m_Events.push_back(event);
	m_Events.unique();

	createPollFd();

	return WR_OK;
}


void CLnxWaitForEvents::Remove(CEvent *event) 
{
	m_Events.remove(event);

	createPollFd();
}


void CLnxWaitForEvents::RemoveAll()
{
	m_Events.clear();
	m_nfds = 0;
}


void CLnxWaitForEvents::createPollFd()
{
	int i = 0;

	for (EVENTLIST::const_iterator itr = m_Events.begin(); itr != m_Events.end(); ++itr, ++i)
	{
		m_pfds[i].fd = ((CLnxEvent*)(*itr))->readFd();

		m_pfds[i].events = POLLIN;
		m_pfds[i].revents = 0;
	}

	m_nfds = m_Events.size();
}


CWaitForEvents::WAIT_RESULT CLnxWaitForEvents::WaitAll(int timeout) 
{
    struct timeval begin;
    int n = m_nfds;

    if (timeout > 0)
        gettimeofday(&begin, NULL);

    if (n == 1)
    {
        return WaitAny(1, &begin, &timeout, false, NULL);
    }

    WAIT_RESULT res = WR_OK;
    while (n)
    {
        int index;

        res = WaitAny(n, &begin, &timeout, true, &index);

        if (res != WR_OK)
            break;

        --n;
        m_pfds[index].fd = m_pfds[n].fd;
        m_pfds[index].revents = 0;
    }

    /*
     * Recreate m_pfds
     */
    createPollFd();

    return res;
}


CWaitForEvents::WAIT_RESULT CLnxWaitForEvents::WaitAny(int size, struct timeval *begin, int *timeout, bool update_timeout, int *index)
{
	int i = 0;

	do
	{
		i = poll(m_pfds, size, *timeout);
		if (i == 0)
		{
			*timeout = 0;
			return WR_TIMEOUT;
		}

		if (i > 0 && update_timeout == false)
			break;

		/*
		 * Calculate remaining timeout
		 * Needed if called from WaitAll() or if (i < 0 && errno == EINTR)
		 */
		if (*timeout > 0)
		{
			struct timeval now;
			gettimeofday(&now, NULL);

			*timeout -= timeval_to_millisec(&now) - timeval_to_millisec(begin);
			if (*timeout < 0)
				*timeout = 0;
		}

		if (i > 0)
			break;

		m_LastErrorCode = errno;

		if (m_LastErrorCode != EINTR)
		{
fprintf(stderr, "CLnxWaitForEvents::WaitAny: %s\n", strerror(m_LastErrorCode));
			return WR_ERROR;
		}
	} while (true);

	if (index == NULL)
		return WR_OK;

	i = 0;
	for (i = 0; i < size; ++i)
	{
		if (m_pfds[i].revents == POLLIN)
		{
			*index = i;
			break;
		}
	}

	return WR_OK;
}


CWaitForEvents::WAIT_RESULT CLnxWaitForEvents::WaitAny(int *index)
{
	int timeout = -1;
	return WaitAny(m_nfds, NULL, &timeout, false, index);
}


CWaitForEvents::WAIT_RESULT CLnxWaitForEvents::WaitAny(int timeout, int *index)
{
	struct timeval begin;

	if (timeout > 0)
		gettimeofday(&begin, NULL);

	return WaitAny(m_nfds, &begin, &timeout, false, index);
}



/* ******************* CLnxClientContext ******************* */

CLnxClientContext::CLnxClientContext() :
	m_ClientContext()
{
	m_ClientContext.pBuffer = NULL;
	m_ClientContext.bufferLength = 0;
	m_ClientContext.dataLength = 0;
	m_ClientContext.hEvent = NULL;
}

CLnxClientContext::~CLnxClientContext()
{
}

void CLnxClientContext::CreateCLIENTCONTEXT()
{
	m_ClientContext.hEvent = pEvent;
	m_ClientContext.pBuffer = pBuffer;
	m_ClientContext.bufferLength = bufferLength;
	m_ClientContext.dataLength = 0;
}

/* ******************* CLnxClient ******************* */

CLnxClient::CLnxClient() :
	m_pClient(new CCamClient()),
	m_IPAdress_h(ntohl(inet_addr("10.123.13.102"))),
	m_Port_h(56666),
	m_Timeout(5000)
{
}

CLnxClient::~CLnxClient()
{
	if (m_pClient)
	{
		delete m_pClient;
		m_pClient = NULL;
	}
}

void CLnxClient::SetUDPPort(UINT16 port_h)
{
	m_Port_h = port_h;
	if (m_pClient)
		m_pClient->SetPort(m_Port_h);
}

void CLnxClient::SetIPAddress(UINT32 ipAddress_h)
{
	m_IPAdress_h = ipAddress_h;
	if (m_pClient)
		m_pClient->SetIPAddress(m_IPAdress_h);
}

void CLnxClient::SetIPAddress(char *ipAddress)
{
	UINT32 ip_n = inet_addr(ipAddress);
	m_IPAdress_h = ntohl(ip_n);
}

void CLnxClient::SetTimeout(int timeout)
{
	m_Timeout = timeout;
	if (m_pClient)
		m_pClient->SetTimeout(m_Timeout);
}

void CLnxClient::Start()
{
	if (m_pClient)
	{
		m_pClient->SetIPAddress(m_IPAdress_h);
		m_pClient->SetPort(m_Port_h);
		m_pClient->SetTimeout(m_Timeout);
		m_pClient->Start(true);
	}
}

void CLnxClient::Stop()
{
	if (m_pClient)
	{
		m_pClient->Stop();
	}
}

bool CLnxClient::SendData(GECCOMMAND* command, CClientContext *clientContext, UINT32 ipAddress_h, UINT16 ipPort_h)
{
	if (m_pClient && clientContext)
	{
		((CLnxClientContext*)clientContext)->CreateCLIENTCONTEXT();
		return m_pClient->SendData((unsigned char*)command, ((GENERAL_MESSAGE*)command)->GetCommandLength(), ipAddress_h, ipPort_h, (void*)&((CLnxClientContext*)clientContext)->m_ClientContext);
	}
	return false;
}

bool CLnxClient::SendData(BULKCMD* commands, CClientContext *clientContext, UINT32 ipAddress_h, UINT16 ipPort_h)
{
	if (m_pClient && clientContext)
	{
		((CLnxClientContext*)clientContext)->CreateCLIENTCONTEXT();
		return m_pClient->SendData((unsigned char*)commands, commands->GetCommandLength(), ipAddress_h, ipPort_h, (void*)&((CLnxClientContext*)clientContext)->m_ClientContext);
	}
	return false;
}



/* ******************* CLnxServer ******************* */

CLnxServer::CLnxServer() :
	m_pServer(new CCamServer())
{
}


CLnxServer::~CLnxServer()
{
	if (m_pServer)
	{
		delete m_pServer;
		m_pServer = NULL;
	}
}


void CLnxServer::SetListeningPort(UINT16 port_h)
{
	if (m_pServer)
		m_pServer->SetListeningPort(port_h);
}


void CLnxServer::SetBuffer(unsigned char *buffer, ULONGLONG size)
{
	if (m_pServer)
		m_pServer->SetBuffer(buffer, size);
}


void CLnxServer::SetPacketSize(unsigned int packetsize)
{
	if (m_pServer)
		m_pServer->SetPacketSize(packetsize);
}


void CLnxServer::SetStreamSerial(uint32_t serial)
{
	if (m_pServer)
		m_pServer->SetStreamSerial(serial);
}


void CLnxServer::SetStreamInterface(const char *ifname)
{
	if (m_pServer)
		m_pServer->SetInterfacename(ifname);
}


void CLnxServer::SetNotification(unsigned int requested_data, CEvent *event)
{
	if (m_pServer)
		m_pServer->SetNotification(requested_data, event);
}


void CLnxServer::SetSignalFrequency(unsigned int frequency)
{
	if (m_pServer)
		m_pServer->SetSignalFrequency(frequency);
}


void CLnxServer::Reset()
{
	if (m_pServer)
		m_pServer->Reset();
}


bool CLnxServer::Start()
{
	if (m_pServer)
		return m_pServer->Start(true);

	return false; // throw ??
}


void CLnxServer::Stop()
{
	if (m_pServer)
		m_pServer->Stop();
}


void CLnxServer::SetType(SERVER_TYPE type)
{
	if (!m_pServer)
		return; // throw ?
	if (type == ST_ONE_SHOT)
		m_pServer->SetType(0);
	else
		m_pServer->SetType(1);
}


void CLnxServer::SetDumpFile(FILE *dumpFile)
{
	if (m_pServer)
		m_pServer->SetDumpFile(dumpFile);
}


unsigned int CLnxServer::GetReceivedData()
{
	if (m_pServer)
		return (unsigned int)m_pServer->GetReceivedData();

	return 0; // throw ??
}


unsigned int CLnxServer::GetMaxPacketNo()
{
	if (m_pServer)
		return (unsigned int)m_pServer->GetMaxPacketNo();

	return 0; // throw ??
}


unsigned int CLnxServer::GetPacketNo()
{
	if (m_pServer)
		return (unsigned int)m_pServer->GetPacketNo();

	return 0; // throw ??
}



/* ****** CLnxNPMAllocator ******* */
#define MESSAGE_SIZE 1024

ULONGLONG CLnxNPMAllocator::m_LockedSoFar = 0;

CLnxNPMAllocator::CLnxNPMAllocator(uint64_t requestedSize) throw (CNPMemoryException) : CNPMAllocator(requestedSize),
	m_MemDesc(),
	m_BufferSize(0)
{
	int pageSize = getpagesize();
	// Calculate the number of pages of memory to request.
	m_MemDesc.NumberOfPages = uint64_t((requestedSize + pageSize) - 1) / pageSize;
	if (m_MemDesc.NumberOfPages == 0)
	{
		return;
	}

	int map_locked = 0;

	// Round up requested size to the next page boundary.
	m_BufferSize = m_MemDesc.NumberOfPages * pageSize;

	struct rlimit rlim;
	if (getrlimit(RLIMIT_MEMLOCK, &rlim))
	{
		int lerrno = errno;
		char message[MESSAGE_SIZE];

		snprintf(message, MESSAGE_SIZE, "Cannot get resource limits: %s\n", strerror(lerrno));
		ErrorLog(message);
	}
	printf( "Lockable memory limits: %ld:%ld\n", rlim.rlim_cur, rlim.rlim_max);
	fflush(stdout);
	if (rlim.rlim_cur < m_BufferSize + m_LockedSoFar)
	{
		fprintf(stderr, "Trying to adjust the size of the lockable memory from %ld to %" PRIu64 "...\n", rlim.rlim_cur, m_LockedSoFar + m_BufferSize);
		fprintf(stderr, "Hardlimit: %ld\n", rlim.rlim_max);
		rlim.rlim_cur = m_LockedSoFar + m_BufferSize;
		if (rlim.rlim_max < rlim.rlim_cur)
		{
			cap_t caps;
			cap_flag_value_t cap_eff_state = CAP_CLEAR;
			cap_flag_value_t cap_perm_state = CAP_CLEAR;
			cap_flag_value_t cap_inh_state = CAP_CLEAR;

			if ((caps = cap_get_proc()) == NULL)
			{
				int lerrno = errno;
				char message[MESSAGE_SIZE];

				snprintf(message, MESSAGE_SIZE, "Cannot get capabilities: %s\n", strerror(lerrno));
				ErrorLog(message);
			}
			cap_get_flag(caps, CAP_SYS_RESOURCE, CAP_EFFECTIVE, &cap_eff_state);
			cap_get_flag(caps, CAP_SYS_RESOURCE, CAP_PERMITTED, &cap_perm_state);
			cap_get_flag(caps, CAP_SYS_RESOURCE, CAP_INHERITABLE, &cap_inh_state);
fprintf(stderr, "CAP_INHERITABLE is %s on CAP_SYS_RESOURCE\n", cap_inh_state == CAP_SET ? "set" : "not set");
			if (cap_eff_state == CAP_CLEAR && cap_perm_state == CAP_CLEAR)
			{
				char message[MESSAGE_SIZE];

				snprintf(message, MESSAGE_SIZE, "Cannot acquire CAP_SYS_RESOURCE\n");
				ErrorLog(message);
			}
			cap_value_t new_caps = CAP_SYS_RESOURCE;
			if (cap_set_flag(caps, CAP_PERMITTED, 1, &new_caps, CAP_SET))
			{
				int lerrno = errno;
				fprintf(stderr, "Cannot CAP_PERMITTED cap_set_flag: %s\n", strerror(lerrno));
			}
			if (cap_set_flag(caps, CAP_EFFECTIVE, 1, &new_caps, CAP_SET))
			{
				int lerrno = errno;
				fprintf(stderr, "Cannot CAP_EFFECTIVE cap_set_flag: %s\n", strerror(lerrno));
			}
			else if (cap_set_proc(caps))
			{
				int lerrno = errno;
				fprintf(stderr, "Cannot set CAP_SYS_RESOURCE: %s\n", strerror(lerrno));
			}

			cap_free(caps);
			rlim.rlim_max = rlim.rlim_cur;
		}
		if (setrlimit(RLIMIT_MEMLOCK, &rlim))
		{
			int lerrno = errno;
			char message[MESSAGE_SIZE];

			snprintf(message, MESSAGE_SIZE, "Cannot set resource limits: %s\n", strerror(lerrno));
			ErrorLog(message);
		}
		else
			map_locked = MAP_LOCKED;
	}
	else
		map_locked = MAP_LOCKED;

	void *addr = mmap(NULL, m_BufferSize, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE | map_locked /*| MAP_HUGETLB*/, -1, 0);

	if (addr == MAP_FAILED)
	{
		int lerrno = errno;
		char message[MESSAGE_SIZE];

		snprintf(message, MESSAGE_SIZE, "Cannot mmap() %" PRIu64 " bytes of memory: %s\n", m_BufferSize, strerror(lerrno));
		ErrorLog(message);
		throw CNPMemoryException();
	}

	m_LockedSoFar += m_BufferSize;
	m_MemDesc.lpMemReserved = addr;
}

void CLnxNPMAllocator::ErrorLog(char *message)
{
	fprintf(stderr, message);
}

CLnxNPMAllocator::CMemDesc::~CMemDesc()
{
	if (lpMemReserved)
	{
		if (munmap(lpMemReserved, NumberOfPages * getpagesize()))
		{
			int lerrno = errno;
			char message[MESSAGE_SIZE];

			snprintf(message, MESSAGE_SIZE, "Cannot munmap() memory: %s\n", strerror(lerrno));
			ErrorLog(message);
		}
	}
}

/* ****** CLnxFactory ******* */
CAPDServer* CLnxFactory::GetServer()
{
	return new CLnxServer();
}

CAPDClient* CLnxFactory::GetClient() 
{
	return new CLnxClient();
}

CEvent* CLnxFactory::GetEvent()
{
	return new CLnxEvent();
}

CWaitForEvents* CLnxFactory::GetWaitForEvents()
{
	return new CLnxWaitForEvents();
}

CClientContext* CLnxFactory::GetClientContext()
{
	return new CLnxClientContext();
}

CNPMAllocator* CLnxFactory::GetNPMemory(ULONGLONG requestedSize)
{
	CLnxNPMAllocator *pAllocator = NULL;
	try
	{
		pAllocator = new CLnxNPMAllocator(requestedSize);
	}
	catch (const CNPMemoryException &e)
	{
	}

	return pAllocator;
}
